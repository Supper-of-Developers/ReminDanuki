FROM python:alpine3.7

LABEL maintainer K.Naito

ENV CHANNEL_SECRET=93c57484b48ecc584fcfbacd7fed5087 \
    ACCESS_TOKEN=0IOGfO9CedLZreFoGW8EWg2ObVeriKNABl8G4uT5jUR5efEaFnknUEjBOYy+twd7uR1N04vwNd0xDi7UZ6pAXKdJs5PesiMWBphZR5bqflsiJSYQbL6dKQRbbZmb+1K/NXE2i2xkdKjJow+sjpj0uwdB04t89/1O/w1cDnyilFU= \
    MYSQL_HOST=infonic-tokyo-rds.cak2s2vj9zrr.ap-northeast-1.rds.amazonaws.com \
    MYSQL_USER=infonic_tokyo \
    MYSQL_PASS=inf-TS-6310 \
    MYSQL_PORT=3306 \
    MYSQL_DATABASE=remindanuki \
    REDIS_URL=inf-redis.jixro2.0001.apne1.cache.amazonaws.com \
    REDIS_PORT=6379

RUN pip install --upgrade pip \
    && pip install flask gunicorn line-bot-sdk redis mysql-connector-python-rf pytz crontab \
    && adduser -D botter \
    && mkdir /home/botter/app

USER botter

WORKDIR /home/botter/app

COPY ./crontabs/root /etc/crontabs/

EXPOSE 3000

ENTRYPOINT crond & gunicorn -b 0.0.0.0:3000 bot:app --log-file=- --log-level=debug --reload
