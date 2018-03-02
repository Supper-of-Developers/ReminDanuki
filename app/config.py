# coding=utf-8
import os

# LINE API情報
ACCESS_TOKEN   = os.environ['ACCESS_TOKEN']
CHANNEL_SECRET = os.environ['CHANNEL_SECRET']

# redis接続情報
REDIS_URL  = os.environ['REDIS_URL']
REDIS_PORT = os.environ['REDIS_PORT']

# MySQL接続情報
MYSQL_CONFIG= {
    "host": os.environ['MYSQL_HOST'],
    "port": os.environ['MYSQL_PORT'],
    "user": os.environ['MYSQL_USER'],
    "password": os.environ['MYSQL_PASS'],
    "database": os.environ['MYSQL_DATABASE'],
    "charset": 'utf8'
}
