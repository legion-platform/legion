#!/usr/bin/env bash

CMD="airflow"
TRY_LOOP=${TRY_LOOP:-"10"}

POSTGRES_HOST=${POSTGRES_HOST:-"postgres"}
POSTGRES_PORT=${POSTGRES_PORT:-"5432"}

REDIS_HOST=${REDIS_HOST:-"redis"}
REDIS_CLI=${REDIS_CLI:-"/usr/bin/redis-cli"}

BOOTUP_CHECK_TIMEOUT=${BOOTUP_CHECK_TIMEOUT:-"10"}
BOOTUP_DIRECTORY=${BOOTUP_DIRECTORY:-"/opt/bootup"}

# wait for redis
if [ "$2" = "webserver" ] || [ "$2" = "worker" ] || [ "$2" = "scheduler" ] || [ "$2" = "flower" ] ; then
  echo "CHECKING REDIS"
  X="`timeout $BOOTUP_CHECK_TIMEOUT $REDIS_CLI -h $REDIS_HOST ping`"
  j=0
  while [ "${X}" != "PONG" ]; do
    j=`expr $j + 1`
    if [ $j -ge $TRY_LOOP ]; then
      echo "$(date) - $REDIS_HOST still not reachable, giving up"
      exit 1
    fi
    echo "$(date) - waiting for Redis... $j/$TRY_LOOP"
    sleep 5
    X="`timeout $BOOTUP_CHECK_TIMEOUT $REDIS_CLI -h $REDIS_HOST ping`"
  done
  echo "REDIS READY"
fi

# wait for DB
if [ "$2" = "webserver" ] || [ "$2" = "worker" ] || [ "$2" = "scheduler" ]; then
  echo "CHECKING PG"
  i=0
  while ! nc -v -w $BOOTUP_CHECK_TIMEOUT  $POSTGRES_HOST $POSTGRES_PORT >/dev/null 2>&1 < /dev/null; do
    i=`expr $i + 1`
    if [ $i -ge $TRY_LOOP ]; then
      echo "$(date) - ${POSTGRES_HOST}:${POSTGRES_PORT} still not reachable, giving up"
      exit 1
    fi
    echo "$(date) - waiting for ${POSTGRES_HOST}:${POSTGRES_PORT}... $i/$TRY_LOOP"
    sleep 5
  done
  echo "PG READY"

  if [ "$2" = "webserver" ] ; then
    echo "Initialize database..."
    $CMD initdb

    python3 create_secrets.py
  fi
  sleep 5
fi

exec "$@"