# coding=utf-8
import logging
from flask import Flask, request, abort
from datetime import datetime

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, PostbackEvent, Postback, TemplateSendMessage, ButtonsTemplate, DatetimePickerTemplateAction
)
import redis
import config
import function as func
import urllib
from pytz import timezone

app = Flask(__name__)

handler = WebhookHandler(config.CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    """
    メインメソッド /callbackにアクセスされた時に実行される
    """
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    messageイベントを受け取るmethod
    Args:
        event (linebot.models.events.MessageEvent): LINE Webhookイベントオブジェクト
    """
    # 送信元
    send_id = func.get_send_id(event)
    
    # redisに接続
    redis_connection = redis.StrictRedis(host=config.REDIS_URL, port=config.REDIS_PORT, db=0)
    context = ""
    if redis_connection.get(send_id):
        context = redis_connection.get(send_id).decode('utf-8')
   
    if event.message.text == "新しいリマインダ" :
        func.reply_message(event.reply_token, TextSendMessage(text="リマインドして欲しい予定を入力するぽん！\n例：「お買い物」「きつねさんとランチ」「お金の振り込み」"))
    elif context != "" and event.message.text == "キャンセル":
        # redisのコンテキストを削除
        redis_connection.delete(send_id)
        func.reply_message(event.reply_token, TextSendMessage(text="また何かあったら言って欲しいたぬ～"))
    elif event.message.text == "一覧":
        # DBからその送信元に紐づくリマインダーを現在日時に近いものから最大10件取得する
        remind_list = func.get_remind_list(send_id)
        func.reply_message(event.reply_token, remind_list)
    elif redis_connection.get(send_id+"_update") :
        new_context = event.message.text
        id = redis_connection.get(send_id+"_update")
        func.update_contents_reminder(event,new_context,id)
        #redisのidとnew_contextを削除
        redis_connection.delete(send_id+"_update")
        new_message = func.update_contents_reminder(event,new_context,id)   
        func.reply_message(event.reply_token, TextSendMessage(text=new_message))
    else :
        # redisにコンテキストを保存
        redis_connection.set(send_id, event.message.text)
        # datepickerの作成
        date_picker = func.create_datepicker(event.message.text)
        func.reply_message(event.reply_token, date_picker)
        

@handler.add(PostbackEvent)
def handle_datetime_postback(event):
    """
    datetimeのpostbackイベントを受け取るmethod
    Args:
        event (linebot.models.events.MessageEvent): LINE Webhookイベントオブジェクト
    """
    postback_data = event.postback.data 

    #カルーセルオブジェクトのdataにreminders_idが含まれていれば、dataを解析してidを入手する
    if "reminders_id" in postback_data :
        parse_pbd = urllib.parse.parse_qs(postback_data)
        #グローバル変数としてidを定義
        global id
        id=parse_pbd["reminders_id"]
    
    if "createdatepicker" in postback_data :
        # 送信元
        send_id = func.get_send_id(event)
        
        # 日付文字列をdatetimeに変換
        date = event.postback.params['datetime'].replace('T', ' ')
        remind_at = datetime.strptime(date, "%Y-%m-%d %H:%M")

        # リマインド内容を保存する
        context = func.regist_reminder(event, send_id, remind_at)

        # 登録完了メッセージを返す
        hiduke = remind_at.strftime('%Y年%m月%d日 %H時%M分')
        func.reply_message(event.reply_token, TextSendMessage("了解だぽん！\n" + hiduke + "に「" + context + "」のお知らせをするぽん！"))
    elif "cancel" in postback_data :
        #「予定のキャンセル」が押された場合のポストバックアクション
        delete_text = func.cancel_reminder(event,id[0])
        func.reply_message(event.reply_token, TextSendMessage(text="「"+delete_text+"」を完璧に忘れたぽん。データベースからも消したから安心するぽん。"))
      
    elif "update" in postback_data and "remind_time" in postback_data:
        #「時間の変更」ボタンが押された場合のポストバックアクション
        func.update_datetimepicker(event,id)
      
    elif "dateupdater" in postback_data:
        #変更後の時刻が入力された場合のポストバックアクション
        #変更後のリマインド時刻を受け取る
        new_date = event.postback.params['datetime'].replace('T', ' ')
        new_remind_at = datetime.strptime(new_date, "%Y-%m-%d %H:%M")
        new_message = func.update_datetime_reminder(event,new_remind_at,id[0])
        func.reply_message(event.reply_token, TextSendMessage(text=new_message))
    elif "update" in postback_data and "contents" in postback_data:
        #「予定の変更」ボタンが押された場合のポストバックアクション 
        #redisに接続
        redis_connection = redis.StrictRedis(host=config.REDIS_URL, port=config.REDIS_PORT, db=0)
        send_id = func.get_send_id(event)
        
        #redisにオブジェクトに紐づいているidを保存
        redis_connection.set(send_id+"_update", id[0])
        func.reply_message(event.reply_token, TextSendMessage(text="新しい予定を入力するぽん"))

# Gunicorn用Logger設定
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Flask利用のため
if __name__ == "__main__":
    app.run(port=3000)         

    

        
            
    

                
                
           
               


