#!/bin/bash

#Force bash if it isn't the shell already
if [ "$(ps -p "$$" -o comm=)" != "bash" ]; then
  bash "$0" "$@"
  exit "$?"
fi

#DIR should be the location of app-config.  This can be overriden for cases like
#vagrant, which execute this script from /tmp instead of from /vagrant
echo $1
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
if [ -n "$1" ]; then
  DIR="$1";
fi

# install and config
sudo yum -y install mailman

# create default list
sudo /usr/lib/mailman/bin/newlist mailman admin@project.org some_password

# start mailman-api


