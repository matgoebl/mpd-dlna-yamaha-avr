#!/bin/sh

# better use docker compose - but this is only for testing as I deploy into a kubernetes cluster
export PULSE_SERVER=tcp:192.168.1.1:4713
export PULSE_SINK=alsa_output.usb-1234_USB_Speakers-00.analog-stereo

/usr/bin/mpd --no-daemon --stdout /etc/mpd.conf &
sleep 2

export MPD_HOST=192.168.1.1
export MPD_PORT=6600
export VERBOSE=3
export MQTT_CONFIG=...,...,.....  # you must set this
exec /usr/bin/mpd-mqtt-ir-bridge.py
