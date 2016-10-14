## Usage with Docker

Docker Engine must be installed in order to run the Plankton Docker image. Detailed installation instructions for various OSes may be found [here](https://docs.docker.com/engine/installation/).

On OSX and Windows, we recommend simply installing the [Docker Toolbox](https://www.docker.com/products/docker-toolbox). It contains everything you need and is (currently) more stable than the "Docker for Windows/Mac" beta versions.

On Linux, to avoid manually copy-pasting your way through the rather detailed instructions linked to above, you can let the Docker installation script take care of everything for you:

```
$ curl -fsSL https://get.docker.com/ | sh
```

Once Docker is installed, Plankton can be run using the following general format:

```
$ docker run -it [docker args] dmscid/plankton [plankton args] [-- [adapter args]]
```

For example, to simulate a Linkam T95 **d**evice and expose it via the TCP Stream **p**rotocol:

```
$ docker run -it dmscid/plankton -p stream linkam_t95
```

To change the rate at which simulation cycles are calculated, increase or decrease the cycle delay, via the `-c` or `--cycle-delay` option. Smaller values mean more cycles per second, 0 means greates possible speed.

```
$ docker run -it dmscid/plankton -p stream -c 0.05 linkam_t95
```

For long running devices it might be useful to speed up the simulation using the `-e` or `--speed` parameter, which is a factor by which actual time is multiplied to determine the simulated time in each simulation cycle. To run a simulation 10 times faster:

```
$ docker run -it dmscid/plankton -p stream -e 10 linkam_t95
```

Details about parameters for the various adapters, and differences between OSes are covered in the "Adapter Specifics" sections.

