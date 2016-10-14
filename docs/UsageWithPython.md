## Usage with Python

To use Plankton directly via Python you must first install its dependencies:

- Python 2.7+ or 3.4+
- EPICS Base R3.14.12.5 (optional, for EPICS based devices)
- PIP 8.1+

Clone the repository in a location of your choice:

```
$ git clone https://github.com/DMSC-Instrument-Data/plankton.git
```

If you do not have [git](https://git-scm.com/) available, you can also download this repository as an archive and unpack it somewhere. A few additional dependencies must be installed. This can be done through pip via the requirements.txt file:

```
$ pip install -r requirements.txt
```

**NOTE:** If you have not installed EPICS, you need to remove pcaspy from the requirements.txt file.

If you also want to run Plankton's unit tests, you may also install the development dependencies:

```
$ pip install -r requirements-dev.txt
```

If you want to use the EPICS adapter, you will also need to configure EPICS environment variables correctly. If you only want to communicate using EPICS locally via the loopback device, you can configure it like this:

```
$ export EPICS_CA_AUTO_ADDR_LIST=NO
$ export EPICS_CA_ADDR_LIST=localhost
$ export EPICS_CAS_INTF_ADDR_LIST=localhost
```

Once all dependencies and requirements are satisfied, Plankton can be run using the following general format (from inside the Plankton directory):

```
$ python plankton.py [plankton args] [-- [adapter args]]
```

You can then run Plankton as follows (from within the plankton directory):

```
$ python plankton.py -p epics chopper
```

Details about parameters for the various adapters, and differences between OSes are covered in the "Adapter Specifics" sections.

