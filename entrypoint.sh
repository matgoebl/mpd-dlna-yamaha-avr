#!/bin/sh

# better use docker compose - but this is only for testing as I deploy into a kubernetes cluster
/usr/bin/mpd --no-daemon --stdout /etc/mpd.conf &

export MPD_HOST=192.168.16.1 #97
export MPD_PORT=8888
export MPD_PORT=6600
export MPD_STREAM_HOSTPORT=192.168.16.1:8888
export VERBOSE=3
export YAMAHA_HOST=192.168.16.29
export YAMAHA_HOST=192.168.16.197
export MAX_VOLUME_DB=60
exec /usr/bin/mpd-dlna-yamaha-avr.py
