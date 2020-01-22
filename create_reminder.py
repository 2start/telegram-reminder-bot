from flask import Flask
from flask import request
import json
import requests
import boto3
import re
import time
import logging
from decimal import * 

logging.basicConfig(level=logging.DEBUG)
logging.info("Webserver started.")
app = Flask(__name__)
dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')

reminder_table = dynamodb.Table('reminder')
duration_regex = re.compile(r"\s*(\d+)\s*(\S+)\s*")
activation_regex = re.compile(r"([Rr]emind|[Ee]rinner)")

@app.route('/', methods= ['POST'])
def remind_me():
    data = request.json
    logging.debug("Post data: " + str(data))
    msg = get_msg(data)
    logging.debug("Message: " + msg)

    activated = activation_regex.search(msg)
    if not activated:
        return 'OK'

    # Try to parse the reminder duration.
    epoch_remind_time = parse_remind_time(msg)
    if not epoch_remind_time:
        return 'OK'

    chat_id = get_chat_id(data)
    store_reminder(get_username(data), epoch_remind_time, chat_id, get_msg_id(data), msg)
    response_msg = "I will remind you at " + time.ctime(epoch_remind_time) + "."
    response = { "chat_id" : chat_id, "text" : response_msg }
    headers = {'content-type': 'application/json'}
    url = "https://api.telegram.org/bot911585183:AAG0nkfnWgVdTuPLuANOzpF93-EBVHLjKSo/sendMessage"
    requests.post(url, data=json.dumps(response), headers=headers)
    return 'OK'
    
def store_reminder(username, remind_time, chat_id, msg_id, msg):
    reminder_table.put_item(
        Item={
            'chat_name': username,
            'remind_time': Decimal(remind_time), 
            'chat_id': chat_id,
            'msg_id': msg_id,
            'msg': msg
        }
    )
    return

def parse_remind_time(msg):
    m = duration_regex.search(msg)
    if not m:
        return
    
    multiplier = int(m.group(1))
    unit = m.group(2)

    unit_seconds = extract_seconds(unit)
    if not unit_seconds:
        return

    
    duration = multiplier * unit_seconds
    logging.debug("Extracted duration: " + str(duration) + "s.")
    remind_time = time.time() + duration
    return remind_time

def extract_seconds(unit_str):
    supported_units = {
            "seconds" : 1,
            "secs": 1,
            "sec": 1,
            "s": 1,
            "mins": 60,
            "minutes" : 60,
            "min": 60,
            "m": 60,
            "hours": 60*60,
            "hour": 60*60,
            "h": 60*60,
            "d": 60*60*24,
            "days": 60*60*24,
            "day": 60*60*24,
            "w": 60*60*24*7,
            "weeks": 60*60*24*7,
            "week": 60*60*24*7
    }

    return supported_units.get(unit_str)
        
def get_chat_id(data):
    return data['message']['chat']['id']

def get_msg(data):
    return data['message']['text']

def get_msg_id(data):
    return data['message']['message_id']

def get_username(data):
    return data['message']['from']['username']
        
if __name__ == "__main__":
    app.run()
