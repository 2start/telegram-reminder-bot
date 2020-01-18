import boto3
from boto3.dynamodb.conditions import Key, Attr
import requests
import time
import json
from decimal import *

dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')
reminder_table = dynamodb.Table('reminder')

def process_reminders():
    expired_reminders = get_expired_reminders()
    send_reminders(expired_reminders)
    delete_reminders(expired_reminders)

def send_reminders(expired_reminders):
    for reminder in expired_reminders:
        response_msg = u'\U0000261D'
        chat_id = int(reminder['chat_id'])
        msg_id = int(reminder['msg_id'])
        response = { "chat_id" : chat_id, "text" : response_msg, "reply_to_message_id": msg_id}
        headers = {'content-type': 'application/json'}
        url = "https://api.telegram.org/bot911585183:AAG0nkfnWgVdTuPLuANOzpF93-EBVHLjKSo/sendMessage"
        requests.post(url, data=json.dumps(response), headers=headers)
        return 

def get_expired_reminders():
    curr_time = Decimal(time.time())
    scan_response = reminder_table.scan(
        FilterExpression=Attr('remind_time').lt(curr_time),
    )
    return scan_response['Items']

def delete_reminders(reminders):
    for reminder in reminders:
        reminder_table.delete_item(
            Key={
                "remind_time": reminder['remind_time'],
                "chat_name": reminder['chat_name']
            }
        )
    return

while True:
    process_reminders()
