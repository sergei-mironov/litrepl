#!/bin/sh

PIDS=''
trap "kill \$PIDS" SIGINT
st -t litrepl-demo -e vim-demo -X _test/_test1.md &
PIDS="$PIDS $!"
sleep 1
while ! wmctrl -i -r $(wmctrl -l | grep -v grep | grep litrepl-demo | awk '{print $1}') -e 0,100,100,546,382 ; do echo -n . ; sleep 0.5 ; done
# peek &
peek --no-headerbar &
sleep 1
off=`expr 372 - 346 + 6`
h2=`expr 100 + $off`
while ! wmctrl -i -r $(wmctrl -l | grep -v grep | grep Peek | awk '{print $1}') -e 0,100,$h2,546,374 ; do echo -n . ; sleep 0.5 ; done
PIDS="$PIDS $!"
wait $PIDS
