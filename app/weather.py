
#pushメッセージ送る上で必要なインポート
from linebot.models import (TextSendMessage)
from linebot import (LineBotApi)
import mysql.connector
import config
import function as func

line_bot_api = LineBotApi(config.ACCESS_TOKEN)

#cron用の天気予報
def morning_news():
    weather = func.weather_information()
    rows = func.get_sql_send_id()
    if rows:
        for row in rows:
            line_bot_api.push_message(row['send_id'], TextSendMessage(text= weather))
    
morning_news()
