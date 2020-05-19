#!/usr/bin/env bash

start() {
  source /home/shake/.bashrc
  conda activate shakemap
  rm -f /home/shake/shakemap_profiles/default/install/logs/aqms_queue.pid.lock
  rm -f /home/shake/shakemap_profiles/default/install/logs/aqms_queue.pid
  python /home/shake/shakemap-aqms/bin/aqms_queue &
  echo $! > /tmp/aqms_queue.pid
#  fi
}

stop() {
  kill $(cat /tmp/aqms_queue.pid)
  rm -f /home/shake/shakemap_profiles/default/install/logs/aqms_queue.pid
}


case $1 in
  start|stop) "$1";;
  restart|reload|condrestart)
        stop
        start
        ;;
  *)
esac

exit 0
