# -*- coding: utf-8 -*-
# *********************************************************************
# lewis - a library for creating hardware device simulators
# Copyright (C) 2016-2021 European Spallation Source ERIC
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# *********************************************************************

import inspect
from datetime import datetime
from functools import wraps

from lewis.core.adapters import Adapter
from lewis.core.devices import InterfaceBase
from lewis.core.exceptions import (
    AccessViolationException,
    LewisException,
    LimitViolationException,
)
from lewis.core.logging import has_log
from lewis.core.utils import FromOptionalDependency, format_doc_text, seconds_since

# pcaspy might not be available. To make EPICS-based adapters show up
# in the listed adapters anyway dummy types are created in this case
# and the failure is postponed to runtime, where a more appropriate
# LewisException can be raised.
missing_pcaspy_exception = LewisException(
    "In order to use EPICS-interfaces, pcaspy must be installed:\n"
    "\tpip install pcaspy\n"
    "A fully working installation of EPICS-base is required for this package. "
    "Please refer to the documentation for advice."
)

Driver, SimpleServer = FromOptionalDependency(
    "pcaspy", missing_pcaspy_exception
).do_import("Driver", "SimpleServer")

pcaspy_manager = FromOptionalDependency(
    "pcaspy.driver", missing_pcaspy_exception
).do_import("manager")


class BoundPV:
    """
    Class to represent PVs that are bound to an adapter

    This class is very similar to :class:`~lewis.adapters.stream.Func`, in that
    it is the result of a binding operation between a user-specified :class:`PV`-object
    and a Device and/or Adapter object. Also, it should rarely be used directly. objects
    are generated automatically by :class:`EpicsAdapter`.

    The binding happens by supplying a ``target``-object which has an attribute or a property
    named according to the property-name stored in the PV-object, and a ``meta_target``-object
    which has an attribute named according to the meta_data_property in PV.

    The properties ``read_only``, ``config``,  and ``poll_interval`` simply forward the
    data of PV, while ``doc`` uses the target object to potentially obtain the property's
    docstring.

    To get and set the value of the property on the target, the ``value``-property of
    this class can be used, to get the meta data dict, there's a ``meta``-property.

    :param pv: PV object to bind to target and meta_target.
    :param target: Object that has an attribute named pv.property.
    :param meta_target: Object that has an attribute named pv.meta_data_property.
    """

    def __init__(self, pv, target, meta_target=None):
        self._meta_target = meta_target
        self._target = target
        self._pv = pv

    @property
    def value(self):
        """Value of the bound property on the target."""
        return getattr(self._target, self._pv.property)

    @value.setter
    def value(self, new_value):
        if self.read_only:
            raise AccessViolationException(
                "The property {} is read only.".format(self._pv.property)
            )

        setattr(self._target, self._pv.property, new_value)

    @property
    def meta(self):
        """Value of the bound meta-property on the target."""
        if not self._pv.meta_data_property or not self._meta_target:
            return {}

        return getattr(self._meta_target, self._pv.meta_data_property)

    @property
    def read_only(self):
        """True if the PV is read-only."""
        return self._pv.read_only

    @property
    def config(self):
        """Config dict passed on to pcaspy-machinery."""
        return self._pv.config

    @property
    def poll_interval(self):
        """Interval at which to update PV in pcaspy."""
        return self._pv.poll_interval

    @property
    def doc(self):
        """Docstring of property on target or override specified on PV-object."""
        return (
            self._pv.doc
            or inspect.getdoc(getattr(type(self._target), self._pv.property, None))
            or ""
        )


class PV:
    """
    The PV-class is used to declare the EPICS-interface exposed by a sub-class of
    EpicsAdapter. The ``target_property`` argument specifies which property of the adapter
    the PV maps to. To make development easier it can also be a part of the exposed
    device. If the property exists on both the Adapter-subclass and the device, the former
    has precedence. This is useful for overriding behavior for protocol specific "quirks".

    If the PV should be read only, this needs to be specified via
    the corresponding parameter. The information about the poll interval is used
    py EpicsAdapter to update the PV in regular intervals. All other named arguments
    are forwarded to the pcaspy server's `pvdb`, so it's possible to pass on
    limits, types, enum-values and so on.

    In case those arguments change at runtime, it's possible to provide ``meta_data_property``,
    which should contain the name of a property that returns a dict containing these values.
    For example if limits change:

    .. sourcecode:: Python

        class Interface(EpicsInterface):
            pvs = {
                'example': PV('example', meta_data_property='example_meta')
            }

            @property
            def example_meta(self):
                return {
                    'lolim': self.device._example_low_limit,
                    'hilim': self.device._example_high_limit,
                }

    The PV infos are then updated together with the value, determined by ``poll_interval``.

    In cases where the device is accessed via properties alone, this class provides the possibility
    to expose methods as PVs. A common use case would be to model a getter:

    .. sourcecode:: Python

        class SomeDevice(Device):
            def get_example(self):
                return 42

        class Interface(EpicsInterface):
            pvs = {
                'example': PV('get_example')
            }

    It is also possible to model a getter/setter pair, in this case a tuple has to be provided:

    .. sourcecode:: Python

        class SomeDevice(Device):
            _ex = 40

            def get_example(self):
                return self._ex + 2

            def set_example(self, new_example):
                self._ex = new_example - 2

        class Interface(EpicsInterface):
            pvs = {
                'example': PV(('get_example', 'set_example'))
            }

    Any of the two members in the tuple can be substituted with ``None`` in case it does not apply.
    Besides method names it is also allowed to provide callables. Valid callables are for example
    bound methods and free functions, but also lambda expressions and partials.

    There are however restrictions for the supplied functions (be it as method names or directly
    as callables) with respect to their signature. Getter functions must be callable without any
    arguments, setter functions must be callable with exactly one argument. The ``self`` of
    methods does not count towards this.


    :param target_property: Property or method name, getter function, tuple of getter/setter.
    :param poll_interval: Update interval of the PV.
    :param read_only: Should be True if the PV is read only. If not specified, the PV is
                      read_only if only a getter is supplied.
    :param meta_data_property: Property or method name, getter function, tuple of getter/setter.
    :param doc: Description of the PV. If not supplied, docstring of mapped property is used.
    :param kwargs: Arguments forwarded into pcaspy pvdb-dict.
    """

    def __init__(
        self,
        target_property,
        poll_interval=1.0,
        read_only=False,
        meta_data_property=None,
        doc=None,
        **kwargs
    ):
        self.property = "value"
        self.read_only = read_only
        self.poll_interval = poll_interval
        self.meta_data_property = "meta"
        self.doc = doc
        self.config = kwargs

        value = self._get_specification(target_property)
        meta = self._get_specification(meta_data_property)

        self._specifications = {"value": value, "meta": meta}

    def bind(self, *targets):
        """
        Tries to bind the PV to one of the supplied targets. Targets are inspected according to
        the order in which they are supplied.

        :param targets: Objects to inspect from.
        :return: BoundPV instance with the PV bound to the target property.
        """
        self.property = "value"
        self.meta_data_property = "meta"

        return BoundPV(
            self,
            self._get_target(self.property, *targets),
            self._get_target(self.meta_data_property, *targets),
        )

    def _get_specification(self, spec):
        """
        Helper method to create a homogeneous representation of a specified getter or
        getter/setter pair.

        :param spec: Function specification 'getter', (getter,) or (getter,setter)
        :return:  Harmonized getter/setter specification, (getter, setter)
        """
        if spec is None or callable(spec) or isinstance(spec, str):
            spec = (spec,)
        if len(spec) == 1:
            spec = (spec[0], None)
        return spec

    def _get_target(self, prop, *targets):
        """
        The actual target methods are retrieved (possibly from the list of targets) and a
        wrapper-property is installed on a throwaway type that is specifically created for
        the purpose of holding this property if necessary. In that case, an instance of this type
        (with the wrapper-property forwarding calls to the correct target) is returned so
        that :class:`BoundPV` can do the right thing.

        .. seealso:: :meth:`_create_getter`, :meth:`_create_setter`

        :param prop: Property, is either 'value' or 'meta'.
        :param targets: List of targets with decreasing priority for finding the wrapped method.
        :return: Target object to be used by :class:`BoundPV`.
        """

        if prop is None:
            return None

        raw_getter, raw_setter = self._specifications.get(prop, (None, None))

        target = None

        if isinstance(raw_getter, str):
            target = next(
                (
                    obj
                    for obj in targets
                    if isinstance(getattr(type(obj), raw_getter, None), property)
                    or not callable(getattr(obj, raw_getter, lambda: True))
                ),
                None,
            )

        if target is not None:
            # If the property is an actual property and has no setter, read_only can be
            # set to True at this point automatically.
            target_prop = getattr(type(target), raw_getter, None)

            if (
                prop == "value"
                and isinstance(target_prop, property)
                and target_prop.fset is None
            ):
                self.read_only = True

            # Now the target does not need to be constructed, property or meta_data_property
            # needs to change.
            setattr(
                self,
                "property" if prop == "value" else "meta_data_property",
                raw_getter,
            )
            return target

        getter = self._create_getter(raw_getter, *targets)
        setter = self._create_setter(raw_setter, *targets)

        if getter is None and setter is None:
            return None

        if prop == "value" and setter is None:
            self.read_only = True

        return type(prop, (object,), {prop: property(getter, setter)})()

    def _create_getter(self, func, *targets):
        """
        Returns a function wrapping the supplied function. The returned wrapper can be used as the
        getter in a property definition. Raises a RuntimeError if the signature of the supplied
        function is not compatible with the getter-concept (no arguments except self).

        :param func: Callable or name of method on one object in targets.
        :param targets: List of targets with decreasing priority for finding func.
        :return: Getter function for constructing a wrapper-property.
        """
        if not func:
            return None

        final_callable = self._get_callable(func, *targets)

        if not self._function_has_n_args(final_callable, 0):
            raise RuntimeError(
                "The function '{}' does not look like a getter function. A valid getter "
                "function has no arguments that do not have a default. The self-argument of "
                "methods does not count towards that number.".format(
                    final_callable.__name__
                )
            )

        @wraps(final_callable)
        def getter(obj):
            return final_callable()

        return getter

    def _create_setter(self, func, *targets):
        """
        Returns a function wrapping the supplied function. The returned wrapper can be used as the
        setter in a property definition. Raises a RuntimeError if the signature of the supplied
        function is not compatible with the setter-concept (exactly one argument except self).

        :param func: Callable or name of method on one object in targets.
        :param targets: List of targets with decreasing priority for finding func.
        :return: Setter function for constructing a wrapper-property or ``None``.
        """
        if not func:
            return None

        func = self._get_callable(func, *targets)

        if not self._function_has_n_args(func, 1):
            raise RuntimeError(
                "The function '{}' does not look like a setter function. A valid setter "
                "function has exactly one argument without a default. The self-argument of "
                "methods does not count towards that number.".format(func.__name__)
            )

        def setter(obj, value):
            func(value)

        return setter

    def _get_callable(self, func, *targets):
        """
        If func is already a callable, it is returned directly. If it's a string, it is assumed
        to be a method on one of the objects supplied in targets and that is returned. If no
        method with the specified name is found, an AttributeError is raised.

        :param func: Callable or name of method on one object in targets.
        :param targets: List of targets with decreasing priority for finding func.
        :return: Callable.
        """
        if not callable(func):
            func_name = func
            func = next(
                (getattr(obj, func, None) for obj in targets if func in dir(obj)), None
            )

            if not func:
                raise AttributeError(
                    "No method with the name '{}' could be found on any of the target objects "
                    "(device, interface). Please check the spelling.".format(func_name)
                )

        return func

    def _function_has_n_args(self, func, n):
        """
        Returns true if func has n arguments. Arguments with default and self for
        methods are not considered.
        """
        if inspect.ismethod(func):
            n += 1

        argspec = inspect.getargspec(func)
        defaults = argspec.defaults or ()

        return len(argspec.args) - len(defaults) == n


@has_log
class PropertyExposingDriver(Driver):
    def __init__(self, interface, device_lock):
        super(PropertyExposingDriver, self).__init__()

        self._interface = interface
        self._device_lock = device_lock
        self._set_logging_context(interface)

        self._timers = {k: 0.0 for k in self._interface.bound_pvs.keys()}
        self._last_update_call = None

    def write(self, pv, value):
        self.log.debug("PV put request: %s=%s", pv, value)

        pv_object = self._interface.bound_pvs.get(pv)

        if not pv_object:
            return False

        try:
            with self._device_lock:
                pv_object.value = value
                self.setParam(pv, pv_object.value)

                return True
        except LimitViolationException as e:
            self.log.warning(
                "Rejected writing value %s to PV %s due to limit " "violation. %s",
                value,
                pv,
                e,
            )
        except AccessViolationException:
            self.log.warning(
                "Rejected writing value %s to PV %s due to access "
                "violation, PV is read-only.",
                value,
                pv,
            )

        return False

    def _get_param_info(self, pv, meta_keys):
        """
        Get PV info fields from pcaspy's "manager" object. This function returns a dictionary
        with info/value pairs, where each entry of meta_keys results in a dictionary entry if
        pcaspy's PVInfo-object has such an attribute. Attributes that do not exist are ignored.
        Valid attributes are the same as specified in the ``pvdb``-argument that

        :param pv: PV base name
        :param meta_keys: List of keys for what information to obtain
        :return:
        """
        # TODO: Submit upstream patch to make this method available in base class
        pv = pcaspy_manager.pvs[self.port][pv]

        info_dict = {}
        for key in meta_keys:
            if hasattr(pv.info, key):
                info_dict[key] = getattr(pv.info, key)

        return info_dict

    def process_pv_updates(self, force=False):
        """
        Update PV values that have changed for PVs that are due to update according to their
        respective poll interval timers.

        :param force: If True, will force updates to all PVs regardless of timers.
        """
        dt = seconds_since(self._last_update_call or datetime.now())

        # Cache details of PVs that need to update
        value_updates = []
        meta_updates = []

        with self._device_lock:
            for pv, pv_object in self._interface.bound_pvs.items():
                self._timers[pv] = self._timers.get(pv, 0.0) + dt
                if self._timers[pv] >= pv_object.poll_interval or force:
                    try:
                        if self.getParam(pv) != pv_object.value or force:
                            value_updates.append((pv, pv_object.value))

                        pv_meta = pv_object.meta
                        if self._get_param_info(pv, pv_meta.keys()) != pv_meta or force:
                            meta_updates.append((pv, pv_meta))

                    except (AttributeError, TypeError):
                        self.log.exception(
                            "An error occurred while updating PV %s.", pv
                        )
                    finally:
                        self._timers[pv] = 0.0

        self._process_value_updates(value_updates)
        self._process_meta_updates(meta_updates)

        self._last_update_call = datetime.now()

    def _process_value_updates(self, updates):
        if updates:
            update_log = []
            for pv, value in updates:
                self.setParam(pv, value)
                update_log.append("{}={}".format(pv, value))

            self.log.info("Processed PV updates: %s", ", ".join(update_log))

            # Calling this manually is only required for values, not for meta
            self.updatePVs()

    def _process_meta_updates(self, updates):
        if updates:
            update_log = []
            for pv, info in updates:
                self.setParamInfo(pv, info)
                update_log.append("{}={}".format(pv, info))

            self.log.info("Processed PV-info updates: %s", ", ".join(update_log))


class EpicsAdapter(Adapter):
    """
    This adapter provides ChannelAccess server functionality through the pcaspy module.

    It's possible to configure the prefix for the PVs provided by this adapter. The
    corresponding key in the ``options`` dictionary is called ``prefix``:

    .. sourcecode:: Python

        options = {
            'prefix': 'PVPREFIX:'
        }

    :param options: Dictionary with options.
    """

    default_options = {"prefix": ""}

    def __init__(self, options=None):
        super(EpicsAdapter, self).__init__(options)

        self._server = None
        self._driver = None

    @property
    def documentation(self):
        pvs = []

        for name, pv in self.interface.bound_pvs.items():
            complete_name = self._options.prefix + name

            data_type = pv.config.get("type", "float")
            read_only_tag = ", read only" if pv.read_only else ""

            pvs.append(
                "{} ({}{}):\n{}".format(
                    complete_name, data_type, read_only_tag, format_doc_text(pv.doc)
                )
            )

        return "\n\n".join([inspect.getdoc(self.interface) or "", "PVs\n==="] + pvs)

    def start_server(self):
        """
        Creates a pcaspy-server.

        .. note::

            The server does not process requests unless :meth:`handle` is called regularly.
        """
        if self._server is None:
            self._server = SimpleServer()
            self._server.createPV(
                prefix=self._options.prefix,
                pvdb={k: v.config for k, v in self.interface.bound_pvs.items()},
            )
            self._driver = PropertyExposingDriver(
                interface=self.interface, device_lock=self.device_lock
            )
            self._driver.process_pv_updates(force=True)

            self.log.info(
                "Started serving PVs: %s",
                ", ".join(
                    (
                        self._options.prefix + pv
                        for pv in self.interface.bound_pvs.keys()
                    )
                ),
            )

    def stop_server(self):
        self._driver = None
        self._server = None

    @property
    def is_running(self):
        return self._server is not None

    def handle(self, cycle_delay=0.1):
        """
        Call this method to spend about ``cycle_delay`` seconds processing
        requests in the pcaspy server. Under load, for example when running ``caget`` at a
        high frequency, the actual time spent in the method may be much shorter. This effect
        is not corrected for.

        :param cycle_delay: Approximate time to be spent processing requests in pcaspy server.
        """
        if self._server is not None:
            self._server.process(cycle_delay)
            self._driver.process_pv_updates()


class EpicsInterface(InterfaceBase):
    """
    Inheriting from this class provides an EPICS-interface to a device for use with
    :class:`EpicsAdapter`. In the simplest case all that is required is to inherit
    from this class and override the ``pvs``-member. It should be a dictionary
    that contains PV-names (without prefix) as keys and instances of PV as
    values. The prefix is handled by ``EpicsAdapter``.

    For a simple device with two properties, speed and position, the first of which
    should be read-only, it's enough to define the following:

    .. sourcecode:: Python

        class SimpleDeviceEpicsInterface(EpicsInterface):
            pvs = {
                'VELO': PV('speed', read_only=True),
                'POS': PV('position', lolo=0, hihi=100)
            }

    For more complex behavior, the interface could contain properties that do not
    exist in the device itself. If the device should also have a PV called STOP
    that "stops the device", the interface could look like this:

    .. sourcecode:: Python

        class SimpleDeviceEpicsInterface(EpicsInterface):
            pvs = {
                'VELO': PV('speed', read_only=True),
                'POS': PV('position', lolo=0, hihi=100),
                'STOP': PV('stop', type='int'),
            }

            @property
            def stop(self):
                return 0

            @stop.setter
            def stop(self, value):
                if value == 1:
                    self.device.halt()

    Even though the device does *not* have a property called ``stop`` (but a method called
    ``halt``), issuing the command

    ::

        $ caput STOP 1

    will achieve the desired behavior, because ``EpicsInterface`` merges the properties
    of the device into ``SimpleDeviceEpicsInterface`` itself, so that it is does not
    matter whether the specified property in PV exists in the device or the adapter.

    The intention of this design is to keep device classes small and free of
    protocol specific stuff, such as in the case above where stopping a device
    via EPICS might involve writing a value to a PV, whereas other protocols may
    offer an RPC-way of achieving the same thing.
    """

    protocol = "epics"
    pvs = None

    def __init__(self):
        super(EpicsInterface, self).__init__()
        self.bound_pvs = None

    @property
    def adapter(self):
        return EpicsAdapter

    def _bind_device(self):
        """
        This method transforms the ``self.pvs`` dict of :class:`PV` objects ``self.bound_pvs``,
        a dict of :class:`BoundPV` objects, the keys are always the PV-names that are exposed
        via ChannelAccess.

        In the transformation process, the method tries to find whether the attribute specified by
        PV's ``property`` (and ``meta_data_property``) is part of the internally stored device
        or the interface and constructs a BoundPV, which acts as a forwarder to the appropriate
        objects.
        """
        self.bound_pvs = {}

        for pv_name, pv in self.pvs.items():
            try:
                self.bound_pvs[pv_name] = pv.bind(self, self.device)
            except (AttributeError, RuntimeError) as e:
                self.log.debug(
                    "An exception was caught during the binding step of PV '%s'.",
                    pv_name,
                    exc_info=e,
                )
                raise LewisException(
                    "The binding step for PV '{}' failed, please check the interface-"
                    "definition or contact the device author. More information is "
                    "available with debug-level logging (-o debug).".format(pv_name)
                )
