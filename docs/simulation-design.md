# Design of the chopper simulation

This document contains some ideas and suggestions on how what the design of the chopper simulation should look like.

## First overview

The design should closely model the physical choppers. For our current purposes I suggest that we have a class `Chopper` that is composed of the following components:

 - `Bearing`: In the beginning we need `MagneticBearing` and `MechanicalBearing`, but they will mainly differ in their internal state machine and consequently the status they report.
 - `Motor`: Here we probably don't need any more granularity at the moment. Sub-classes should implement concrete behavior, such as delays when setting speed/phase, speed- and phase jitter, and so on.
 - `Disc`: This does currently nothing, so maybe we can leave it out in the first approximation. Later on I think this should contain the geometry of the disc (diameter, cut-outs, position of TDC and so on).
 - `ReferencePulseSource`: Not sure about the naming on this one, but we need something that actually gives us a pulse with respect to which the phase is defined.
 - `InterlockSystem`: This will probably be something that we could choose to attach to a chopper so that it won't start unless this object says it's okay for the chopper to start operation.
 
The `Bearing` and `Motor` classes will have some internal state machines according to the document we had before. Although they seem connected at first I think there's merit in separating them from each other (especially since the state machine of a `MechanicalBearing` will be very different from the `MagneticBearing`-machine). Furthermore it will be easier to test and change the state machines inside these classes compared to a monolithic one.

The `Motor`, `Disc` and `ReferencePulseSource` will be coupled somehow, maybe this coupling happens in the actual `Chopper`-class?

## Some technology choices

** State machine library **
I really like `Fysom` and unless it turns out to have some fundamental shortcoming for our use cases that can't be overcome I'd like to stick with it. It seems to do what we need and finding other modules would require investing some more time.

** Observer pattern **
Due to how the state machine works (with callbacks) I'm very much inclined to think that it may be beneficial to do things "event based" in general using the observer pattern. Not sure on the technical details here yet, will have to do some research how that is done properly in Python.

