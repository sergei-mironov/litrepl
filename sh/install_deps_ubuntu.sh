#!/bin/sh
set -e -x

sudo apt-get update >/dev/null
sudo apt-get install -y socat vim
pip install setuptools tqdm coverage coverage_badge lark psutil ipython
