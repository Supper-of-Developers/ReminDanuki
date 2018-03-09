FROM python:alpine3.7

LABEL maintainer K.Naito

ENV CHANNEL_SECRET=YOUR_CHANNEL_SECRET \
    ACCESS_TOKEN=YOUR_ACCESS_TOKEN \
    MYSQL_HOST=YOUR_MYSQL_HOST \
    MYSQL_USER=YOUR_MYSQL_USER \
    MYSQL_PASS=YOUR_MYSQL_PASS \
    MYSQL_PORT=YOUR_MYSQL_PORT \
    MYSQL_DATABASE=YOUR_MYSQL_DATABASE \
    REDIS_URL=YOUR_REDIS_URL \
    REDIS_PORT=YOUR_REDIS_PORT

RUN pip install --upgrade pip \
    && pip install flask gunicorn line-bot-sdk redis mysql-connector-python-rf pytz crontab sqlalchemy \
    && adduser -D botter \
    && mkdir /home/botter/app

USER botter

WORKDIR /home/botter/app

COPY ./crontabs/root /etc/crontabs/

EXPOSE 3000

ENTRYPOINT crond & gunicorn -b 0.0.0.0:3000 bot:app --log-file=- --log-level=debug --reload
