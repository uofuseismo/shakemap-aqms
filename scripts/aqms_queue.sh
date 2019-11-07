#!/usr/bin/env bash

start() {
  source /home/shake/.bashrc
  conda activate shakemap
  python /home/shake/shakemap-aqms/bin/aqms_queue &
  echo $! > /tmp/aqms_queue.pid
}

stop() {
  kill $(cat /tmp/aqms_queue.pid)
  rm /home/shake/shakemap_profiles/default/install/logs/aqms_queue.pid
}

case $1 in
  start|stop) "$1";;
esac
