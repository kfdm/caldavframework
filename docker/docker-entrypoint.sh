#!/bin/sh

set -e

if [ "${1:0:1}" = '-' ]; then
	set -- todo-server "$@"
fi

case "$1" in
web)
  # Shortcut for launching a web worker under gunicorn
  shift
  set -- gunicorn "todo.standalone.wsgi:application" -b 0.0.0.0 "$@"
  ;;
esac

# Finally exec our command
exec "$@"
