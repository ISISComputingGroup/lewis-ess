Release 1.0
===========

The initial release of Lewis (at that point still plankton). These release notes have been
compiled after the release as we were not keeping any release notes at that time.

Features
--------

 - Cycle-based, deterministic device simulations based on finite state machines
 - Control over the simulation's time granularity and speed (slow motion, fast forward)
 - Simulation and device control via command line and via optional network service
 - Two ready to use simulated devices using different protocols:

    - ESS chopper abstraction (CHIC) using EPICS Channel Access
    - Linkam T95 temperature controller using TCP Stream protocol

 - Docker image available on `docker hub`_ containing all dependencies
 - Documentation in Markdown format for viewing in Github, both for users and developers
 - Examples for implementing Stream protocol based devices

.. _pcaspy: https://github.com/paulscherrerinstitute/pcaspy
.. _docker hub: https://hub.docker.com/r/dmscid/lewis/