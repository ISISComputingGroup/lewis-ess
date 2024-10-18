# Release 1.0.1

This release is the first one under the name "Lewis". Its main purpose is to make a PyPI package
available as well as online documentation under the new name.

Nevertheless version 1.0.1 fixes some bugs and introduces a few new features that were originally
scheduled for release 1.1 but had already been finished at the time of the release.

## New features
 - It is now possible to obtain device interface documentation via the command line
   and the control server, making it easier to communicate with unfamiliar devices.
   For command line invocation there is a new flag: ``lewis -i linkam_t95``.
   Thanks to `David Michel` for requesting this feature.
 - Lewis is now available as a `PyPI`-package and can be installed via ``pip install lewis``.
 - Documentation is now generated via Sphinx and has been made available online on `RTD`_.

## Bug fixes and other improvements
 - The control server can now be bound to a hostname instead of an IP-address (very useful
   for ``localhost`` in particular).
 - pcaspy is now an optional requirement that has to be enabled explicitly in the requirements.txt
   file or installation via ``pip install lewis[epics]``.
 - Error messages displayed on the command line have been improved.
 - A flake8 job has been added to the continuous integration pipeline to enforce Python
   style guidelines in the codebase.

