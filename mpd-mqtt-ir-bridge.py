#!/usr/bin/env python3

import musicpd
import argparse
import os
import time
import logging
import select

import paho.mqtt.client as mqtt
import ssl
import time
import sys
import json
import enum

POWERON_VOLUME=16

class IRCmd(enum.Enum):
    VolUp=18
    VolDn=19
    Mute=20
    Pwr=21
    Aux=29
    On=46
    Off=47

def irsend(mqtt_client, ircmd):
    addr=16
    cmd=ircmd.value
    irdata_=(addr<<7) + cmd
    numbits=12
    irdata= sum(1<<(numbits-1-i) for i in range(numbits) if irdata_>>i&1)
    logging.info(f"IR SEND: 0x{irdata:X} {irdata:012b} {irdata_:012b} {addr:05b}b/{addr:02X}h/{addr:02} {cmd:07b}b/{cmd:02X}h/{cmd:03}")
    mqtt_client.publish(mqtt_send_topic,f'{{"Protocol":"SONY","Bits":12,"Data":"0x{irdata:x}","DataLSB":"0x5081","Repeat":0}}')
    time.sleep(0.3)

def on_message(mqtt_client, userdata, message):
    msg = str(message.payload.decode("utf-8"))
    topic = message.topic
    data = json.loads(msg)
    dt = time.strftime("%Y-%m-%d %H:%M:%S")
    irdata = int(data['IrReceived']['Data'],16)
    numbits=12
    irdata_ = sum(1<<(numbits-1-i) for i in range(numbits) if irdata>>i&1)
    cmd = irdata_ & 0x7f
    addr = ( irdata_ >> 7) & 0x1f
    # print(f"{dt} {topic} {msg} {irdata} {irdata:012b} {irdata_:012b} {addr:05b}b/{addr:02x}h/{addr:02} {cmd:07b}b/{cmd:02x}h/{cmd:03}")
    logging.info(f"IR RECEIVED: {msg} {addr:05b}b/{addr:02x}h/{addr:02} {cmd:07b}b/{cmd:02x}h/{cmd:03}")
    # {"IrReceived":{"Protocol":"SONY","Bits":12,"Data":"0x481","DataLSB":"0x2081","Repeat":0}}

def on_connect(mqtt_client, userdata, flags, result):
    logging.info(f"MQTT CONNECTED ({result})")
    mqtt_client.subscribe(mqtt_recv_topic)

def hifi_off():
    logging.info(f"TASK: switching hifi off")
    irsend(mqtt_client,IRCmd.Off)

def hifi_on(poweron_volume = POWERON_VOLUME):
    logging.info(f"TASK: switching hifi on with volume {poweron_volume}")
    irsend(mqtt_client,IRCmd.On)
    irsend(mqtt_client,IRCmd.Aux)
    for i in range(0,32):
        irsend(mqtt_client,IRCmd.VolDn)
    irsend(mqtt_client,IRCmd.Aux)
    for i in range(0,poweron_volume):
        irsend(mqtt_client,IRCmd.VolUp)

def mqtt_connect(MQTT_CONFIG):
    global mqtt_client,mqtt_host,mqtt_port,mqtt_client_id,mqtt_user,mqtt_pass,mqtt_send_topic,mqtt_recv_topic
    mqtt_host,mqtt_port,mqtt_client_id,mqtt_user,mqtt_pass,mqtt_send_topic,mqtt_recv_topic = MQTT_CONFIG.split(',')
    mqtt_client = mqtt.Client(mqtt_client_id)
    # mqtt_client.tls_set(ca_certs="mqtt-ca.crt",cert_reqs=ssl.CERT_NONE)
    mqtt_client.tls_set(cert_reqs=ssl.CERT_NONE)
    mqtt_client.username_pw_set(mqtt_user,mqtt_pass)
    mqtt_client.on_message=on_message
    mqtt_client.on_connect = on_connect
    mqtt_client.connect(mqtt_host,port=int(mqtt_port),keepalive=60)
    mqtt_client.loop()


mqtt_client = None

MQTT_CONFIG=""


def main():
    global rxv_ctrl_url, rxv_media_url, mpd_stream_url
    parser = argparse.ArgumentParser(description='Stream from Music Player Daemon to Yamaha AVR Receiver via DLNA with Volume and Player Control.')
    parser.add_argument('-m', '--mpd_host', default=os.environ.get('MPD_HOST','127.0.0.1'),                            help='Hostname/IP of Music Player Daemon.' )
    parser.add_argument('-b', '--poweron_volume', default=os.environ.get('POWERON_VOLUME','16'),                       help='Default volume.')
    parser.add_argument('-t', '--mqtt_config', default=os.environ.get('MQTT_CONFIG',MQTT_CONFIG),                      help='MQTT Config.' )
    parser.add_argument('-v', '--verbose', action='count', default=int(os.environ.get('VERBOSE','0')),                 help="Be more verbose, can be repeated (up to 3 times)." )
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING-10*args.verbose,handlers=[logging.StreamHandler()],format="[%(levelname)s] %(message)s")

    run_daemon(args.mpd_host, int(args.poweron_volume), args.mqtt_config)


def run_daemon(mpd_host, poweron_volume, mqtt_config):

    while True:
        try:

            logging.info(f"mpd-mqtt-ir-bridge starting...")
            logging.info(f"Connecting to Music Player Daemon at {os.environ.get('MPD_HOST')}...")
            client = musicpd.MPDClient()
            client.socket_timeout = 3
            client.connect(mpd_host)
            logging.info(f"Connected to server {os.environ.get('MPD_HOST')} version {client.mpd_version}")

            logging.info(f"Connecting to MQTT at {mqtt_config}...")
            mqtt_connect(mqtt_config)

            fds = [client,mqtt_client.socket()]

            old_state = client.status()["state"]
            old_volume = 0 #client.getvol()["volume"]

            while True:
                logging.info(f"Now waiting for MPD event...")

                # event = client.idle("player","mixer","output")
                event = None
                client.send_idle("player","mixer","output")
                _read, _write, _exception = select.select(fds, [], [], 5)
                _read_filenos = [ sock.fileno() for sock in _read ]
                if client.fileno() in _read_filenos:
                    logging.debug("Event from MPD")
                    event = client.fetch_idle()
                else:
                    client.noidle()
                if mqtt_client.socket().fileno() in _read_filenos:
                    logging.debug("Event from MQTT")
                mqtt_client.loop()

                new_state = client.status()["state"]
                new_volume = 0 #client.getvol()["volume"]

                logging.info(f"Event {event}: player state {old_state} -> {new_state}, volume: {old_volume} -> {new_volume}")

                if new_volume != old_volume:
                    logging.info(f"New volume: {new_volume}")

                    old_volume = new_volume

                if new_state != old_state:
                    if new_state == "play":
                        logging.info(f"Waking up player...")
                        hifi_on(poweron_volume)

                    if new_state == "stop":
                        logging.info(f"Shutting down player...")
                        hifi_off()

                    old_state = new_state

            # never reached
            client.disconnect()

        except Exception as e:
            logging.error(e)
            time.sleep(3)

if __name__ == '__main__':
    main()
