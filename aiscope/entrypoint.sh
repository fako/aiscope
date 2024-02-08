#!/usr/bin/env bash


# Exit immediately on error
set -e

# TODO: check empty directory??
if [ "$DJANGO_DEBUG" == "1" ]  && [ -d "/usr/src/datagrowth" ] && [ -f "/usr/src/datagrowth/setup.py" ] && \
    [ $(pip show datagrowth | grep "Location:" | awk -F "/" '{print $NF}') == "site-packages" ]
then
    echo "Replacing datagrowth PyPi installation with editable version"
    pip uninstall -y datagrowth
    pip install -e /usr/src/datagrowth
fi


# Executing the normal commands
exec "$@"
