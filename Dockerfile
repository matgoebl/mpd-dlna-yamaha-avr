FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y --no-install-recommends mpd mpc git && rm -rf /var/lib/apt/

RUN groupadd --gid 10001 kubeuser && \
    groupadd --gid 10002 kubefs && \
    useradd  --uid 10001 --gid 10001 --groups 10002 --home /home/kubeuser --no-user-group kubeuser

RUN mkdir -p /var/lib/mpd/data/ /var/lib/mpd/music/playlists/ && chown -R 10001 /var/lib/mpd/

RUN pip3 install --no-cache-dir --no-build-isolation python-musicpd git+https://github.com/wuub/rxv.git git+https://github.com/matgoebl/nano-dlna.git@dev

COPY mpd.conf /etc/mpd.conf
COPY mpd-dlna-yamaha-avr.py entrypoint.sh /usr/bin/

VOLUME /var/lib/mpd
WORKDIR /var/lib/mpd
USER 10001
EXPOSE 6600 6601

CMD ["/usr/bin/entrypoint.sh"]
