# MPD-DLNA-Yamaha-AVR
Stream from Music Player Daemon to Yamaha AVR Receiver via DLNA with Volume and Player Control.

(c) 2022 matthias.goebl (at) goebl.net

Published under the Apache License Version 2.0


## Motivation

I want to stream music from my home server to a receiver located in the living room - over the network and without the need to add another intermediate device like a Raspberry Pi 4.
I like the [Music Player Daemon](https://www.musicpd.org/) because it provides a central playlist that can be controlled with a wide choice of [clients](https://www.musicpd.org/clients/).

My receiver provides DLNA support, so I tried DNLA clients on my mobile devices. Unfortunately the playlist then lives on the currently controlling client (called DLNA control point) and cannot be modified from another device.

Additionally the receiver must be initially set to DNLA mode (switch input to 'SERVER'). The volume cannot be controlled via DLNA. So you have to switch between the yamaha app and the DLNA player app.

### My DLNA History

When I bought the yamaha receiver years ago, I tried to stick to the modern DLNA path.
As I like listening to DJ mixes with a playing time of more than one hour, seeking is an important feature for me. It turned out, that my yamaha receiver is a bit picky about seeking and I found only one open source player that satisfied my needs: [YAACC](http://www.yaacc.de/).

To easy the power-on and switch-to-DLNA steps, I [patched YAACC](https://sourceforge.net/u/mgoebl/yaacc/ci/926229cedc7e8700ba792995520ef9103b95ae6a/tree/yaacc/src/de/yaacc/player/AVTransportPlayer.java?diff=f1fb67599b52dd61c194d3455ab55d90ff23e96f).
You can find my historic version at [sourceforge](https://sourceforge.net/u/mgoebl/yaacc/).

But over the years, DLNA control suffered from the one-client-only limitation and YAACC hasn't been maintained intensively.
So I looked for an alternative solution.

### My MPD History

I should tell, that I already used MPD about 15 years ago, running on a [NSLU2](https://en.wikipedia.org/wiki/NSLU2).
The NSLU2 is a linux-powered embedded device, like a Raspberry PI, but introduced several years before.
The NSLU2 was sitting on top the receiver, running the MPD, played via an USB audio adapter to
the receiver.
I [patched LIRC](https://github.com/torvalds/linux/commit/1beef3c1c6af76895411691d08630757243984d0#diff-b4b2579a39af489dcd4882e4a81d86b9be2ae466e6784391f52c422b99d57f9eR198)
(has been [removed](https://github.com/torvalds/linux/commit/3746cfb684cdd9cce843e914012ec56e7064dbe2#diff-2540f7f74f47bef4743f788b7e8570948a2902d971cec119ce6cbf9d9e30332bL202) since then)
to allow infrared sending and receiving from the NSLU2 with [little additional hardware](https://web.archive.org/web/20130131110958/http://www.nslu2-linux.org/wiki/HowTo/AddAnInfraredReceiverAndTransmitterWithLIRC) connected to its [GPIOs](https://web.archive.org/web/20130131105936/http://www.nslu2-linux.org/wiki/HowTo/AddASimpleTenPinConnector).
I powered on the receiver, switched source and controlled volume by automatically sending infrated commands to the receiver.
I also attached an [HD44780 display via I2C](https://web.archive.org/web/20130131110109/http://www.nslu2-linux.org/wiki/HowTo/AddATextDisplayOnI2CWithLCDproc) using a [patched LCDproc](https://github.com/lcdproc/lcdproc/blob/master/server/drivers/hd44780-i2c.c) to the NSLU2 to display current track information.


### Solution

With [nano-dlna](https://github.com/gabrielmagno/nano-dlna) I found a python tool to command my receiver to play any DLNA url.
The python library [rxv](https://github.com/wuub/rxv) neatly replaces my previous shell script to command the yamaha receiver via curl. The command line tool [rxvc](https://github.com/Raynes/rxvc) uses this library as well.

So the only missing task was to connect those components to MPD. That glue job is exactly what mpd-dlna-yamaha-avr does.



## Architecture

MPD-DLNA-Yamaha-AVR is a small daemon, that connects to the Music Player Daemon and listenes for play/pause/stop and volume change events.
In case of a volume change event it forwards the new volume using the RXV library to the Yamaha AVR Receiver via HTTP. The 100% volume equivalent can configured.
In case of a play event the receiver is switched on, set to `SERVER` input and switch to the configured surround_program. In case of a stop event, the receiver is sent to standby, but only if it is still play from the `SERVER` input.

The following drawing shows the complete architecture:


    +---------------------+           +--------------------------------------------------+
    | Music Player Daemon +---------->|         Yamaha AVR Receiver RX-Vxxx              |
    |  (HTTP/DLNA Server) |MP3 stream |              (DLNA Renderer)                     |
    +----+----------------+           +--------------------------------------------------+
         |                                               ^     ^
         |                                  DLNA control |     | remote commands
         | MPD events                        (play URL)  |     | (power on, input, volume)
         | (play/stop,                                   |     |
         |  volume)                   +------------------+-+ +-+-------------------------+
         |                            |     Nano-DLNA      | |           RXV             |
         v                            |(DLNA Control Point)| |(Remote Control Automation)|
    +---------------------------------+--------------------+-+---------------------------+
    |                         MPD-DLNA-Yamaha-AVR                                        |
    | (MPD event translation: play -> RXV: power-on + set-input, DLNA: play HTTP stream) |
    +------------------------------------------------------------------------------------+

(created using https://asciiflow.com/)


## Dependencies

- Nano-DLNA: https://github.com/gabrielmagno/nano-dlna with several patches collected in https://github.com/matgoebl/nano-dlna
- RXV: https://github.com/wuub/rxv
- python-musicpd: https://kaliko.gitlab.io/python-musicpd/
- a Yamaha AVR Receiver, tested with a Yamaha RX-V475 (2019-01.Firmware)



# Installation

## Usage

    usage: mpd-dlna-yamaha-avr.py [-h] [-m MPD_HOST] [-y YAMAHA_HOST] [-b MAX_VOLUME_DB] [-p SURROUND_PROGRAM] [-v]

    Stream from Music Player Daemon to Yamaha AVR Receiver via DLNA with Volume and Player Control.

    optional arguments:
      -h, --help            show this help message and exit
      -m MPD_HOST, --mpd_host MPD_HOST
                            Hostname/address of Music Player Daemon.
      -y YAMAHA_HOST, --yamaha_host YAMAHA_HOST
                            Hostname/address of Yamaha AVR Receiver.
      -b MAX_VOLUME_DB, --max_volume_db MAX_VOLUME_DB
                            Maximum AVR volume in dB for mpd volume of 100%.
      -p SURROUND_PROGRAM, --surround_program SURROUND_PROGRAM
                            Surround program to be set when switching to DLNA playback.
      -v, --verbose         Be more verbose, can be repeated (up to 3 times).


## Test

    make install
    make run



## Daemon Usage

Install mpd-dlna-yamaha-avr as system service starting e.g.

    mpd-dlna-yamaha-avr.py --mpd_host 192.168.1.1 --yamaha_host 192.168.1.10 --verbose


### MPD configuration

Add this snippet to /etc/mpd.conf:

    audio_output {
            type            "httpd"
            name            "Music Stream"
            encoder         "lame"
            port            "8000"
            bitrate         "256"
            format          "44100:16:1"
            max_clients     "0"
            mixer_type      "null"
    }

