Quickstart
===========

Installation
------------

.. code-block:: sh

    $ python setup.py install



Distro Packages
+++++++++++++++

We are currently working to provide linux packages (deb and rpm). Stay tunned!

.. TODO: Add here links to official packages (.deb and .rpm)



Running the Sevice
-------------------


To start the service manually just run the `mailman-api` command.

If you installed mailman-api from a distribution package you should be able to start your service by running `service mailman-api start`.


Usage: mailman-api [options]

Options:
  -h, --help            show this help message and exit
  -b BIND, --bind=BIND  Bind address. Default: '127.0.0.1:8124'.
  -l MAILMANLIB_PATH, --mailman-lib-path=MAILMANLIB_PATH
                        Path to mailman libs directory. Default:
                        '/usr/lib/mailman'.

