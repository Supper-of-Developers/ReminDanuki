# coding=utf-8
from pytz import timezone
from datetime import datetime
from linebot import (
    LineBotApi,
)
from linebot.models import (
    TextSendMessage, TemplateSendMessage, ButtonsTemplate, DatetimePickerTemplateAction,
    CarouselTemplate,CarouselColumn,URITemplateAction,PostbackTemplateAction
)
import mysql.connector
import sqlalchemy.pool as pool
import redis
import config
import urllib

line_bot_api = LineBotApi(config.ACCESS_TOKEN)

def reply_message(reply_token, message_object):
    """
    LINEメッセージ返信method
    Args:
        reply_token (str): 返信用トークン
        message_object (linebot.models.send_messages.SendMessage): 返信メッセージオブジェクト
    """
    line_bot_api.reply_message(
            reply_token,
            message_object)

def getMysqlConnection():
    con = mysql.connector.connect(**config.MYSQL_CONFIG)
    return con

def getMysqlPoolConnection():
    mypool = pool.QueuePool(getMysqlConnection, max_overflow=10, pool_size=5)
    con = mypool.connect()
    return con

def create_datepicker(context):
    """
    datepickerオブジェクト作成method
    Args:
        context (str): 会話から受け取った予定
    Rerurns:
        linebot.models.template.TemplateSendMessage: datepickerオブジェクト
    """
    now_date = datetime.now(timezone('Asia/Tokyo')).strftime("%Y-%m-%dt%H:%M")
    date_picker = TemplateSendMessage(
        alt_text='「' + context + '」をいつ教えてほしいぽん？',
        template=ButtonsTemplate(
            text= '「' + context + '」をいつ教えてほしいぽん？\n「キャンセル」って言ってくれればやめるたぬ～',
            actions=[
                DatetimePickerTemplateAction(
                    label='設定',
                    data='createdatepicker',
                    mode='datetime',
                    initial=now_date,
                    min=now_date,
                    max='2099-12-31t23:59'
                )
            ]
        )
    )

    return date_picker

def get_send_id(event):
    """
    送信元タイプを利用して送信元IDを特定するmethod
    Args:
        event (linebot.models.events.MessageEvent): LINE Webhookイベントオブジェクト
    Returns:
        str: send_id 送信元ID
    """
    send_id = ""
    if event.source.type == 'user':
        send_id = event.source.user_id
    elif event.source.type == 'group':
        send_id = event.source.group_id
    elif event.source.type == 'room':
        send_id = event.source.room_id

    return send_id

def get_remind_list(send_id):
    """
    リマインダーリスト取得method
    Args:
        send_id (str): 送信元ID
    Return:
        list: list 現在日時から近い予定から最大10件のリスト
    """
    # mysqlに接続
    mysql_connection = getMysqlPoolConnection()
    cursor = mysql_connection.cursor(dictionary=True)

    # 現在日時を取得
    now_date = datetime.now(timezone('Asia/Tokyo')).strftime("%Y-%m-%d %H:%M:%s")

    sql = ('SELECT '
           'reminders.remind_at, reminders.text, reminders.id '
           'FROM '
           'reminders, senders '
           'WHERE '
           'reminders.sender_id = senders.id AND senders.send_id = %s AND reminders.remind_at > %s '
           'ORDER BY reminders.remind_at '
           'LIMIT 10;')

    cursor.execute(sql, (send_id,now_date))
    
    ret_list = []
    rows = cursor.fetchall()
    if rows:
        print(rows)
        column = []
        for row in rows:
            text = row['text']
            # 日付文字列をフォーマット
            hiduke = row['remind_at'].strftime('%Y年%m月%d日 %H時%M分')
            id = row["id"] #MySQLのremindersテーブルのid
            columns = CarouselColumn(
                    title=text,
                    text=hiduke,
                    actions=[
                        PostbackTemplateAction(
                            label="予定の変更",
                            data='action=update_contents&reminders_id=' + str(id)
                            
                        ),
                        PostbackTemplateAction(
                            label="時間の変更",
                            data='action=update_remind_time&reminders_id=' + str(id)
                        ),
                        PostbackTemplateAction(
                            label='予定のキャンセル',
                            data='action=cancel&reminders_id=' + str(id)
                        )
                    ]
                )
            column.append(columns)
            
        carousel_template_message = TemplateSendMessage(
        alt_text='Carousel template',
        template=CarouselTemplate(
            columns=column
        )
        )
        return carousel_template_message
            
    else :
        ret_list.append(TextSendMessage(text="君に教えることは何もないぽん\n「新しいリマインダ」と入力して予定を入力して欲しいぽん"))
    # mysqlから切断
    cursor.close()
    mysql_connection.close()
    
    return ret_list

def regist_reminder(event, send_id, remind_at):
    """
    リマインダー登録method
    Args:
        event (linebot.models.events.MessageEvent): LINE Webhookイベントオブジェクト
        send_id (str): 送信元ID
        remind_at (datetime): 会話から受け取ったリマインド時刻
    Return:
        str: context 会話から受け取った予定
    """
    # mysqlに接続
    mysql_connection = getMysqlPoolConnection()
    cursor = mysql_connection.cursor(dictionary=True)

    # redisから入力された予定を取得
    redis_connection = redis.StrictRedis(host=config.REDIS_URL, port=config.REDIS_PORT, db=0)
    if redis_connection.get(send_id):
        context = redis_connection.get(send_id).decode('utf-8')
    else:
        # リマインダ設定フロー以外のpostbackはスルー
        return

    # 送信元IDが未登録なら登録、登録済みなら取得のみ
    id = check_sender_id(mysql_connection, cursor, send_id)
    # リマインダーを登録
    insert_reminder(mysql_connection, cursor, id, context, remind_at)

    # mysqlから切断
    cursor.close()
    mysql_connection.close()

    # redisの値を削除
    redis_connection.delete(send_id)

    return context

def check_sender_id(mysql_connection, cursor, send_id):
    """
    送信元をチェックし、DB登録に未登録なら登録して送信元管理IDを返し、登録済みなら取得した送信元管理IDを返すmethod
    Args:
        mysql_connection (mysql.connector.connect): MySQLコネクター
        cursor (mysql.connector.connect.cursor): MySQLカーソル
        send_id (str): 送信元ID
    Returns:
        int: id 送信元管理ID
    """
    id = 0
    # 送信元が登録済みか確認
    cursor.execute("SELECT id FROM senders WHERE send_id = %s;", (send_id,))
    row = cursor.fetchone()
    if row is None:
        # 未登録の送信元だったら登録する
        cursor.execute('INSERT INTO senders (send_id) VALUES (%s);', (send_id,))
        mysql_connection.commit()
        # insertしたIDを取得
        cursor.execute("SELECT LAST_INSERT_ID() as id;")
        row = cursor.fetchone()
        id = row['id']
    else:
        id = row['id']

    return id

def insert_reminder(mysql_connection, cursor, sender_id, context, remind_at):
    """
    リマインダー登録SQL実行method
    Args:
        mysql_connection (mysql.connector.connect): MySQLコネクター
        cursor (mysql.connector.connect.cursor): MySQLカーソル
        send_id (str): 送信元ID
        context (str): 会話から受け取った予定
        remind_at (datetime): 会話から受け取ったリマインド時刻
    """
    cursor.execute('INSERT INTO reminders (sender_id, text, remind_at) VALUES (%s, %s, %s);', (sender_id, context, remind_at))
    mysql_connection.commit()

def update_calendar_id(send_id,calendar_id):
    """
    カレンダーID登録SQL実行method
    Args:
        mysql_connection (mysql.connector.connect): MySQLコネクター
        cursor (mysql.connector.connect.cursor): MySQLカーソル
        send_id (str): 送信元ID
        calendar_id: 登録するgoogleカレンダーID
    """
    # mysqlに接続
    mysql_connection = getMysqlPoolConnection()
    cursor = mysql_connection.cursor(dictionary=True)
    
    # 送信元IDのgoogleカレンダーIDを登録
    cursor.execute('UPDATE senders SET calendar_id = %s WHERE send_id = %s;', (calendar_id,send_id,))
    mysql_connection.commit()

def select_calendar_id(send_id):
    """
    カレンダーID取得method
    Args:
        mysql_connection (mysql.connector.connect): MySQLコネクター
        cursor (mysql.connector.connect.cursor): MySQLカーソル
        send_id (str): 送信元ID
    Return:
        calendar_id: 登録するgoogleカレンダーID
    """
    # googleカレンダーIDを取得
    cursor.execute('SELECT calendar_id FROM senders WHERE send_id = %s;',(send_id,))
    row = cursor.fetchone()
    calendar_id=""
    if row :
        calendar_id=row['calendar_id']

    return calendar_id

def cancel_reminder(id):
    """リマインダ削除用メソッド
    Args:
        id (dict)  parse_pbd = urllib.parse.parse_qs(postback_data)
                   id=parse_pbd["reminders_id"] カルーセルメッセージオブジェクトに紐づけられたid
    Returns:
        str: delete_text 削除したリマインダーテキスト
    """
    #mysqlに接続
    mysql_connection = getMysqlPoolConnection()
    cursor = mysql_connection.cursor(dictionary=True)
    #完了メッセージに表示するため削除前にテキストを保持しておく
    cursor.execute("SELECT text FROM reminders WHERE id = %s", (id,))
    row = cursor.fetchone() 
    #mysqlから切断
    cursor.close()
    mysql_connection.close()  
    #データベースに対象の予定があれば削除する
    if　row :
        delete_text = row["text"]
        delete_reminder(mysql_connection,cursor,id)
        return delete_text
    else :
        return "その予定は既にわすれたぬ。"
  
def delete_reminder(mysql_connection, cursor, id):
    """リマインダ削除SQL実行用メソッド
    Args:
        mysql_connection (mysql.connector.connect): MySQLコネクター
        cursor (mysql.connector.connect.cursor): MySQLカーソル
        id (dict)  parse_pbd = urllib.parse.parse_qs(postback_data)
            id=parse_pbd["reminders_id"] カルーセルメッセージオブジェクトに紐づけられたid
    """
    #メッセージオブジェクトからidを受け取って、同id行を削除
    cursor.execute("DELETE FROM reminders WHERE id = %s", (id,))
    mysql_connection.commit()     
    
def update_datetimepicker(event,id):
    """日付の更新用のボタンテンプレートメッセージ
    Args:
        event (linebot.models.events.MessageEvent): LINE Webhookイベントオブジェクト
        id (dict)  parse_pbd = urllib.parse.parse_qs(postback_data)
                   id=parse_pbd["reminders_id"] カルーセルメッセージオブジェクトに紐づけられたid
    """
    now_date = datetime.now(timezone('Asia/Tokyo')).strftime("%Y-%m-%dt%H:%M")
    new_datetimepicker = TemplateSendMessage(
        alt_text='時間を入力するぽん',
        template=ButtonsTemplate(
            text= '変更後の時間を入力するぽん',
            actions=[
                DatetimePickerTemplateAction(
                    label='設定',
                    data='dateupdater&reminders_id=' +str(id[0]),
                    mode='datetime',
                    initial=now_date,
                    min=now_date,
                    max='2099-12-31t23:59'
                )
            ]
        )
    )
    reply_message(event.reply_token, new_datetimepicker)
  
def update_datetime_reminder(event, new_remind_at, id):
    """登録したリマインダーのリマインド時刻を更新するメソッド
    Args
        event (linebot.models.events.MessageEvent): LINE Webhookイベントオブジェクト
        new_remind_at リマインド時刻更新用ボタンテンプレートメッセージで入力された時刻
        id (dict)  parse_pbd = urllib.parse.parse_qs(postback_data)
                   id=parse_pbd["reminders_id"] カルーセルメッセージオブジェクトに紐づけられたid
    Returns:
        str: 時刻を更新したぽん！（更新完了を伝えるメッセージ）
    """

    #mysqlに接続
    mysql_connection = getMysqlPoolConnection()
    cursor = mysql_connection.cursor(dictionary=True)
    
    #カラムとDBのidが等しい行の日付の値を更新
    cursor.execute("UPDATE reminders SET remind_at = %s WHERE id = %s", (new_remind_at, id))
    mysql_connection.commit()
    
    #mysqlから切断
    cursor.close()
    mysql_connection.close()
    
    return "時刻を更新したぽん！"

def update_contents_reminder(new_context, id):
    """登録したリマインダーの内容を更新するメソッド
    Args:
        new_context 更新フロー中に入力された新しい予定内容
        id (dict)  parse_pbd = urllib.parse.parse_qs(postback_data)
                   id=parse_pbd["reminders_id"] カルーセルメッセージオブジェクトに紐づけられたid
    Returns:
        str: 予定を更新したぽん！（更新完了を伝えるメッセージ）
    """
    #mysqlに接続
    mysql_connection = getMysqlPoolConnection()
    cursor = mysql_connection.cursor(dictionary=True)
    
    #カラムとDBのidが等しい行のテキストを更新
    cursor.execute("UPDATE reminders SET text = %s WHERE id = %s", (new_context,id))
    mysql_connection.commit()
    
    #mysqlから切断
    cursor.close()
    mysql_connection.close()
    
    return "予定を更新したぽん！"

def get_sql_send_id():
    """登録されているsend_idの一覧を返すメソッド
    Returns:
        rows: 登録されている全send_idのdict
    """
    # mysqlに接続
    mysql_connection = getMysqlPoolConnection()
    cursor = mysql_connection.cursor(dictionary=True)
    
    sql = "SELECT send_id FROM senders;"
    cursor.execute(sql)
    rows = cursor.fetchall()
    # mysqlから切断
    cursor.close()
    mysql_connection.close()
    return rows
