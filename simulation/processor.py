class CanProcess(object):
    """
    The CanProcess class is meant as a base for all things that
    are able to process on the bases of a time delta (dt).

    Subclasses should implement the process-method.
    """

    def __init__(self):
        super(CanProcess, self).__init__()

    def process(self, dt):
        pass


class CanProcessComposite(CanProcess):
    """
    This subclass of CanProcess is a convenient way of collecting
    multiple items that implement the CanProcess interface.

    Items can be added to the composite like this:

        composite = CanProcessComposite()
        composite += item_that_implements_CanProcess

    The process-method calls the process-method of each contained
    item. Before doing that it calls the 'compositeProcess'-method
    that can optionally be implemented by sub-classes to add some
    processing specific to the composite and not captured in the
    process-methods of the contained items.
    """

    def __init__(self, iterable=()):
        super(CanProcessComposite, self).__init__()

        self._processors = []

        for item in iterable:
            self.__iadd__(item)

    def __iadd__(self, other):
        if isinstance(other, CanProcess):
            self._appendSimulation(other)

    def _appendSimulation(self, other):
        self._processors.append(other)

    def process(self, dt):
        if hasattr(self, 'compositeProcess'):
            self.compositeProcess(dt)

        for simulation in self._processors:
            simulation.process(dt)
