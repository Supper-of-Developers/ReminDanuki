"""
Shows basic usage of the Google Calendar API. Creates a Google Calendar API
service object and outputs a list of the next 10 events on the user's calendar.
"""
from __future__ import print_function
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import datetime
import re
from pytz import timezone
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, PostbackEvent, Postback, TemplateSendMessage, ButtonsTemplate, DatetimePickerTemplateAction,FollowEvent
)
import random
import function as func

def formatEventDateToJapanese(date_str, timing):
    if ":" == date_str[-3:-2]:
        date_str = date_str[:-3]+date_str[-2:]
    elif re.match('^(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$', date_str) :
        if timing == 0:
            date_str = '朝'
        else :
            date_str = '夜'
    else :
        date = datetime.datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
        date_str = date.strftime('%H:%M') 
    return date_str 

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = './client_secret.json'


def getCal(send_id):
    # Setup the Calendar API
    store = file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))
    
    # Call the Calendar API
    min = datetime.datetime.now(timezone('Asia/Tokyo')).strftime('%Y-%m-%dT00:00:00%z') # 'Z' indicates UTC time
    max = datetime.datetime.now(timezone('Asia/Tokyo')).strftime('%Y-%m-%dT23:59:59%z')
    cal_id=func.select_calendar_id(send_id)
    if cal_id == "":
        return TextSendMessage(text="GoogleIDが未登録だぽん！\n先に「カレンダー」と入力してIDを登録して欲しいたぬ～")
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId=cal_id, timeMin=min,timeMax=max,
                                          maxResults=10, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    
    # calendarlist = [] （１つのメッセージに１つの予定の場合）
    msg='' # 1つのメッセージに予定をまとめる場合
    today = datetime.datetime.today()
    today = today.strftime('%Y年%m月%d日')
    message = ["今日も頑張れ~! ٩(ˊᗜˋ*)و ","一日一日を大事にして、悔いなき人生を - 金澤 嘉市","為せば成る! (*•̀ᴗ•́*)و ̑̑","Enjoy, the pain that you can't avoid!\n(避けられないなら楽しめ!)"]
    message = random.choice(message)

    if not events:
        print('No upcoming events found.')
        # calendarlist = "\n今日の予定がないぽん！"   
        msg='\n今日の予定がないぽん！'
    for event in events:
        start = formatEventDateToJapanese(event['start'].get('dateTime', event['start'].get('date')), 0)
        end = formatEventDateToJapanese(event['end'].get('dateTime',event['end'].get('date')), 1)
        # calendarlist.append(TextSendMessage(text=start + "~" + end + ": "+ event['summary']))
        msg += "\n" + start + " ~ " + end + " : 【"+ event['summary']+ "】  "
        print(start, event['summary'])
        
    return TextSendMessage(text=today+"の予定だぽん!"+ msg + "\n\n"+ message)

# [END calendar_quickstart]