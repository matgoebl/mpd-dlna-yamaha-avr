#!/bin/sh

export PIPE_COMMAND="netcat 192.168.1.1 1234"

# better use docker compose - but this is only for testing as I deploy into a kubernetes cluster
/usr/bin/mpd --no-daemon --stdout /etc/mpd-pipe-mqtt-ir.conf &
#sleep 2

export MPD_HOST=192.168.1.1
export MPD_PORT=6600
export VERBOSE=3
export MQTT_CONFIG=...,...,.....  # you must set this
exec /usr/bin/mpd-mqtt-ir-bridge.py
