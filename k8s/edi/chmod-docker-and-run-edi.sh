#!/bin/sh
set -e

dockerd &
sleep 3
chmod a+rwx /var/run/docker.sock

exec "$@"