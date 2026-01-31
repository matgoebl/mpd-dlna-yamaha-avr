FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y --no-install-recommends mpd mpc git && \
    echo 'for variant mpd-pulseaudio-mqtt-ir:' && apt-get install -y --no-install-recommends pulseaudio-utils && \
    echo 'for variant mpd-snapcast:' && apt-get install -y --no-install-recommends snapserver curl unzip && \
    rm -rf /var/lib/apt/

# for variant mpd-snapcast:
RUN curl -sL https://github.com/badaix/snapweb/releases/download/v0.7.0/snapweb.zip -o snapweb.zip && \
    unzip snapweb.zip -d /usr/share/snapserver/snapweb

RUN groupadd --gid 10001 kubeuser && \
    groupadd --gid 10002 kubefs && \
    useradd  --uid 10001 --gid 10001 --groups 10002 --home /home/kubeuser --no-user-group kubeuser

RUN mkdir -p /var/lib/mpd/data/ /var/lib/mpd/music/playlists/ && chown -R 10001 /var/lib/mpd/ && \
    echo 'for variant mpd-snapcast:' && mkdir -p /var/lib/snapserver/ && chown -R 10001 /var/lib/snapserver/

RUN pip3 install --no-cache-dir --no-build-isolation python-musicpd && \
    echo 'for variant mpd-dlna-yamaha-avr:' && pip3 install --no-cache-dir --no-build-isolation git+https://github.com/wuub/rxv.git git+https://github.com/matgoebl/nano-dlna.git@dev && \
    echo 'for variant mpd-pulseaudio-mqtt-ir:' && pip3 install --no-cache-dir --no-build-isolation paho-mqtt

COPY mpd-dlna-yamaha-avr.conf mpd-pulseaudio-mqtt-ir.conf mpd-snapcast.conf /etc/
COPY mpd-dlna-yamaha-avr.py entrypoint-mpd-dlna-yamaha-avr.sh mpd-mqtt-ir-bridge.py entrypoint-mpd-pulseaudio-mqtt-ir.sh /usr/bin/

ARG BUILDTAG=unknown
ENV BUILDTAG=${BUILDTAG}
RUN echo "${BUILDTAG}" > /buildtag

VOLUME /var/lib/mpd
WORKDIR /var/lib/mpd
USER 10001
# for variant mpd-dlna-yamaha-avr: 6600 6601
# for variant mpd-pulseaudio-mqtt-ir: 6600
# for variant mpd-snapcast: 6600 1704 1705 1780
EXPOSE 6600 6601 1704 1705 1780

CMD ["/usr/bin/entrypoint-mpd-dlna-yamaha-avr.sh"]
