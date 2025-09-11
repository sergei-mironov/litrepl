#!/bin/sh
set -e -x

apt-get update >/dev/null
apt-get install -y python3-setuptools socat
