#!/bin/sh
set -e

chmod a+rwx /var/run/docker.sock

exec "edi" "--verbose"