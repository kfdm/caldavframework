#!/bin/sh

set -e

if [ "${1:0:1}" = '-' ]; then
	set -- pomodoro "$@"
fi

case "$1" in
worker)
  # Shortcut to start a celery worker for Promgen
  set -- celery "-A" pomodoro.standalone "$@"
  ;;
web)
  # Shortcut for launching a Promgen web worker under gunicorn
  shift
  set -- gunicorn "pomodoro.standalone.wsgi:application" -b 0.0.0.0 "$@"
  ;;
esac

# Finally exec our command
exec "$@"
