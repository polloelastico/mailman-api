Tests!
======

To make it easier to run the tests we require `Docker` to be installed. NOTE: on Debian-like systems, 'docker' suits for a graphical dock-like widgets, you may want to install 'docker.io' instead.

To run the tests, do the following:
* Go into the `tests` folder
* Build the docker image for testing (only required once): `make image`
* Run `make tests`

The first run will take the longest as it's pulling all the dependencies.
