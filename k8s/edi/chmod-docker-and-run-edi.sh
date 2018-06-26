#!/bin/sh
set -e

docker daemon \
			--host=unix:///var/run/docker.sock &

chmod a+rwx /var/run/docker.sock

exec "$@"