# Adapter Specifics

## EPICS Adapter Specifics
The EPICS adapter takes only one optional argument:

-  ``prefix``: This string is prefixed to all PV names. Defaults to empty / no prefix.

Arguments meant for the adapter can be specified with the adapter options.
For example:

```
$ python lewis.py chopper --adapter-options "epics: {prefix: 'SIM2:'}"
```

On Linux, this means that ``EPICS_CA_ADDR_LIST`` must include this
networks broadcast address:
```
$ export EPICS_CA_AUTO_ADDR_LIST=NO
$ export EPICS_CA_ADDR_LIST=172.17.255.255
$ export EPICS_CAS_INTF_ADDR_LIST=localhost
```

## Stream Adapter Specifics
The TCP Stream adapter has the following optional arguments:
-  ``bind_address``: Address of network adapter to listen on.
   Defaults to "0.0.0.0" (all network adapters).
-  ``port``: Port to listen for connections on. Defaults to 9999.
-  ``telnet_mode``: When True, overrides both in and out terminators
   to CRNL for telnet compatibility. Defaults to False.

Arguments meant for the adapter can be specified with the adapter options.
For example:
```
$ python lewis.py linkam_t95 -p "stream: {bind_address: localhost, port: 1234}"
```
