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

 - Go to https://github.com/DMSC-Instrument-Data/lewis/milestones
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

 - Draft release blurb at https://github.com/DMSC-Instrument-Data/lewis/releases
 

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

   $ virtualenv env
   $ . env/bin/activate
   (env) $ git clone https://github.com/DMSC-Instrument-Data/lewis.git
   (env) $ cd lewis
   (env) $ python setup.py sdist bdist_wheel


Test PyPI Package
-----------------

Ideally, `.tar.gz` and `.whl` produced in previous step should also be shared
with and tested by another developer.

Make sure tests are run in a fresh virtual environment:

.. code-block:: bash

   $ virtualenv test
   $ . test/bin/activate
   (test) $ git clone https://github.com/DMSC-Instrument-Data/lewis.git
   (test) $ cd lewis
   (test) $ pip install -e ".[dev]"
   (test) $ tox


Git Release
-----------

 - Finalize and submit release blurb at: 
   https://github.com/DMSC-Instrument-Data/lewis/releases
 - Close the current milestone at:
   https://github.com/DMSC-Instrument-Data/lewis/milestones
 

Upload PyPI Package
-------------------

The ``twine`` utility can be used to upload the packages to PyPI:

.. code-block:: bash

   $ pip install twine
   $ twine register dist/lewis-x.y.z.tar.gz
   $ twine register dist/lewis-x.y.z-py2.py3-none-any.whl
   $ twine upload dist/*


Docker
------

When the changes made in the prepare step were merged into master, it will have
triggered TravisCI to build a new docker image tagged as ``dmscid/lewis:edge``.

Releasing a new docker image is therefore just a matter of retagging it:

.. code-block:: bash

   $ docker pull dmscid/lewis:edge
   $ docker tag dmscid/lewis:edge dmscid/lewis:latest
   $ docker tag dmscid/lewis:edge dmscid/lewis:vX.Y.Z
   $ docker push dmscid/lewis:latest
   $ docker push dmscid/lewis:vX.Y.Z


