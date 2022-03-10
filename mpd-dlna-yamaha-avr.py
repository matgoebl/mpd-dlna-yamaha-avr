#!/usr/bin/env python3

import musicpd
import argparse
import os
import time
import nanodlna

from nanodlna import devices, dlna
import rxv
import logging


def main():
    global rxv_ctrl_url, rxv_media_url, mpd_stream_url
    parser = argparse.ArgumentParser(
        description='Stream from Music Player Daemon to Yamaha AVR Receiver via DLNA with Volume and Player Control.')
    parser.add_argument('-m', '--mpd_host',    default=os.environ.get('MPD_HOST','127.0.0.1'),    help='Hostname/address of Music Player Daemon.' )
    parser.add_argument('-y', '--yamaha_host', default=os.environ.get('YAMAHA_HOST','127.0.0.1'), help='Hostname/address of Yamaha AVR Receiver.' )
    parser.add_argument('-b', '--max_volume_db', default=os.environ.get('MAX_VOLUME_DB','-40'),   help='Maximum AVR volume in dB for mpd volume of 100%%.')
    parser.add_argument('-p', '--surround_program', default=os.environ.get('SURROUND_PROGRAM','Straight'), help='Surround program to be set when switching to DLNA playback.')
    parser.add_argument('-v', '--verbose',     action='count', default=int(os.environ.get('VERBOSE','0')), help="Be more verbose, can be repeated (up to 3 times)." )
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING-10*args.verbose,handlers=[logging.StreamHandler()],format="[%(levelname)s] %(message)s")

    run_daemon(args.mpd_host, args.yamaha_host, int(args.max_volume_db), args.surround_program)


def run_daemon(mpd_host, yamaha_host, max_volume_db, surround_program):
    logging.info(f"mpd-dlna-yamaha-avr starting...")
    client = musicpd.MPDClient()
    client.connect(mpd_host)
    logging.info(f"Connected to server {os.environ.get('MPD_HOST')} version {client.mpd_version}")

    rxv_ctrl_url   = "http://" + yamaha_host + "/YamahaRemoteControl/ctrl"
    rxv_media_url  = "http://" + yamaha_host + ":8080/MediaRenderer/desc.xml"
    mpd_stream_url = "http://" + mpd_host    + ":8000/stream.mp3"

    dlna_device = nanodlna.devices.register_device(rxv_media_url)

    rx = rxv.RXV(rxv_ctrl_url)

    old_state = client.status()["state"]
    old_volume = client.getvol()["volume"]

    while True:
        try:
            logging.info(f"RXV Status: {rx.basic_status} Player: {rx.play_status()}. Now waiting for MPD event...")

            event = client.idle("player","mixer","output")
            new_state = client.status()["state"]
            new_volume = client.getvol()["volume"]

            logging.info(f"Event {event}: player state {old_state} -> {new_state}, volume: {old_volume} -> {new_volume}")
            logging.info(f"RXV Status: {rx.basic_status} Player: {rx.play_status()}")

            if new_volume != old_volume:
                if rx.on and rx.input == 'SERVER':
                    logging.info(f"New volume: {new_volume}")
                    rx.volume = int( ( int(new_volume) / 100 * abs(max_volume_db) - 80 ) * 2 ) / 2

                old_volume = new_volume

            if new_state != old_state:
                if new_state == "play":
                    logging.info(f"Waking up player...")
                    if not ( rx.on and rx.input == 'SERVER' and rx.is_playback_supported() ):
                        rx.on = True
                        time.sleep(0.5)
                        rx.input = 'SERVER'
                        rx.mute = False
                        rx.surround_program = surround_program
                        rx.volume = -80
                        time.sleep(0.5)
                        old_volume = 0
                        client.setvol(50)

                    logging.info(f"Starting stream on player...")
                    nanodlna.dlna.play({"file_video": mpd_stream_url}, dlna_device)


                if new_state == "stop" and (rx.on and rx.input == 'SERVER'):
                    logging.info(f"Shutting down player...")
                    rx.on = False

                old_state = new_state

        except Exception as e:
            logging.error(e)
            time.sleep(1)


    client.disconnect()


if __name__ == '__main__':
    main()
