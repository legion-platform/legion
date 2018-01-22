#!/bin/sh
set -e

JUSER="jenkins"

sudo chmod a+rwx /var/run/docker.sock

exec su $JUSER -c "/usr/local/bin/jenkins.sh"