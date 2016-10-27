FROM ubuntu:14.04

MAINTAINER epoitras@linuxfoundation.org

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update

RUN apt-get install -y python-dev mailman python-pip python-nose git

RUN pip install --upgrade pip

RUN pip install --upgrade setuptools

RUN pip install coverage flake8 coveralls
