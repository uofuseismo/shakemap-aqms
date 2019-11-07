#!/usr/bin/env bash

start() {
  source /home/shake/.bashrc
  conda activate shakemap
  /home/shake/shakemap_src/contrib/init.sh start
}

stop() {
  /home/shake/shakemap_src/contrib/init.sh stop
}

case $1 in
  start|stop) "$1";;
esac
