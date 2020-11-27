Release Checklist
=================

This document provides a check list of steps to take and things to watch out
for when preparing a new release of Lewis. It is organized roughly in the order
that these things need to be done or checked.

If any issues are found, it is best to start again at the top once they are
resolved and the fix is merged.


Preparing for Release
~~~~~~~~~~~~~~~~~~~~~

These steps are to prepare for a release on Git, and to commit as a pull
request named "Prepare release x.y.z". This pull request should be merged
prior to proceeding to the next section.

Git Milestones
--------------

 - Go to https://github.com/ess-dmsc/lewis/milestones
 - Ensure all issues and PRs included in this release are tagged correctly
 - Create milestone for next release
 - Ensure any open issues or PRs not included are tagged for next release


Release Notes
-------------

 - Ensure release notes are up to date against all included changes
 - If changes to existing devices may be required to update Lewis, include an
   Update Guide section in the release notes
 - Include new release notes in ``docs/release_notes/index.rst``
 - Remove orphan tag from release notes for this release


Update Version
--------------

 - Update ``__version__`` in ``lewis/__init__.py``
 - Update ``release`` in ``docs/conf.py``
 - Update ``version`` in ``setup.py``
 - Update ``framework_version`` for each device under ``devices`` and ``examples``


GitHub Release
--------------

 - Draft release blurb at https://github.com/ess-dmsc/lewis/releases


Merge Changes
-------------

 - Merge any changes made in this section into master
 - Ensure this pull request is also tagged for the current version


Build and Finalize Release
~~~~~~~~~~~~~~~~~~~~~~~~~~

These steps should be taken once the ones in the previous section have been
completed.

Build PyPI Package
------------------

This should be done in a clean directory.

.. code-block:: bash

   $ python -m venv build
   $ . build/bin/activate
   (build) $ git clone https://github.com/ess-dmsc/lewis.git
   (build) $ cd lewis
   (build) $ pip install twine wheel
   (build) $ python setup.py sdist bdist_wheel
   (build) $ twine check dist/*
   (build) $ deactivate


Test PyPI Package
-----------------

Ideally, `.tar.gz` and `.whl` produced in previous step should also be shared
with and tested by another developer.

Make sure tests are run in a fresh virtual environment:

.. code-block:: bash

   $ python -m venv targz
   $ . targz/bin/activate
   (targz) $ pip install lewis/dist/lewis-X.Y.Z.tar.gz
   (targz) $ lewis linkam_t95
   ...
   (targz) $ deactivate

   $ python -m venv whl
   $ . whl/bin/activate
   (whl) $ pip install lewis/dist/lewis-X.Y.Z-py3-none-any.whl
   (whl) $ lewis linkam_t95
   ...
   (whl) $ deactivate

Since these are release packages, unit tests aren't available. Run a few manual
tests against the packaged version of Lewis to double check that things still
work as expected.


Git Release
-----------

 - Finalize and submit release blurb at:
   https://github.com/ess-dmsc/lewis/releases
 - Close the current milestone at:
   https://github.com/ess-dmsc/lewis/milestones


Upload PyPI Package
-------------------

The ``twine`` utility can be used to upload the packages to PyPI:

.. code-block:: bash

   $ twine register dist/lewis-x.y.z.tar.gz
   $ twine register dist/lewis-x.y.z-py3-none-any.whl
   $ twine upload dist/*
