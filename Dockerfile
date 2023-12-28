FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y --no-install-recommends mpd mpc git pulseaudio-utils netcat-traditional && rm -rf /var/lib/apt/
RUN mkdir -p /var/lib/mpd/data/ /var/lib/mpd/music/playlists/ && chown -R mpd /var/lib/mpd

RUN pip3 install --no-cache-dir --no-build-isolation python-musicpd paho-mqtt

COPY mpd.conf /etc/mpd.conf
COPY mpd-mqtt-ir-bridge.py entrypoint.sh /usr/bin/

VOLUME /var/lib/mpd
WORKDIR /var/lib/mpd
EXPOSE 6600

CMD ["/usr/bin/entrypoint.sh"]
