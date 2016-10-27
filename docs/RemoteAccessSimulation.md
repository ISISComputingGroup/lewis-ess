## Remote access to simulation parameters

*Please note that this functionality should only be used on a trusted network.*

Certain control over the simulation is also exposed in the shape of an object named `simulation` if Plankton is started with `-r`. The simulation can be paused and resumed using the control script:

```
$ ./plankton-control.py simulation pause
$ ./plankton-control.py simulation resume
```

With these commands, the simulation is paused, while the communication with the device remains responsive. The communication channel (for example TCP stream server) would still respond to queries and commands, but they would not be processed by the device. To simulate a complete loss of connection, another pair of functions is available:

```
$ ./plankton-control.py simulation disconnect_device
$ ./plankton-control.py simulation connect_device
```

This basically shows the opposite effect, the device simulation continues running, but the communication channel is not processed anymore and the device appears disconnected.

The speed of the simulation can be adjusted as well, along with the number of cycles that are processed per second (via the `cycle_delay` parameter).

```
$ ./plankton-control.py simulation speed 10
$ ./plankton-control.py simulation cycle_delay 0.05
```

This will cause the twice as many cycles per second to be computed compared to the default, and the simulation runs ten times faster than actual time.

It's also possible to obtain some information about the simulation, for example how long it has been running and how much simulated time has passed:

```
$ ./plankton-control.py simulation uptime
$ ./plankton-control.py simulation runtime
```

Finally, the simulation can also be stopped:

```
$ ./plankton-control.py simulation stop
```

It is not possible to recover from that, as the processing of remote commands stops as well. The only way to restart the simulation is to run Plankton again with the same parameters.
