# coding=utf-8
from linebot import (
    LineBotApi
)
from linebot.models import (
    TextSendMessage
)
from pytz import timezone
from datetime import datetime
import mysql.connector
import config
import function as func
import random


line_bot_api = LineBotApi(config.ACCESS_TOKEN)

# mysqlに接続
mysql_connection = func.getMysqlPoolConnection()
cursor = mysql_connection.cursor(dictionary=True)

# 現在日時を取得
now_date = datetime.now(timezone('Asia/Tokyo')).strftime("%Y-%m-%d %H:%M:00")

# 送信元が登録済みか確認
sql = "SELECT send_id, text FROM reminders, senders WHERE reminders.sender_id = senders.id AND remind_at = %s;"
cursor.execute(sql, (now_date,)) # 後ろにカンマを付けないとプレースホルダとして使えないらしい
rows = cursor.fetchall()
message = ["ファイトだぽん！","急いでたぬ！","覚えてたかな…"]
message = random.choice(message)

if rows:
    for row in rows:
        ret_text = "「" + row['text'] + "」の時間だぽん！" + message
        line_bot_api.push_message(row['send_id'], TextSendMessage(text=ret_text))

# mysqlから切断
cursor.close()
mysql_connection.close()
