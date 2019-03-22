try:
    import unzip_requirements
except ImportError:
    pass
import json
import boto3
from boto3.dynamodb.conditions import Key
import uuid
import datetime

TABLES = {
    'polls': {
        'table_name': 'Polls',
        'primary_key': 'id'
    },
    'poll_options': {
        'table_name': 'PollOptions',
        'primary_key': 'id'
    },
    'poll_votes': {
        'table_name': 'PollVotes',
        'primary_key': 'id'
    },
}

dynamodb = boto3.resource("dynamodb")


def lambda_handler(event, context):
    print("Got an Invoke Request")
    print(f"Event: {event}")
    print(f"Context: {context.__dict__}")

    field = event['field']
    args = event['arguments']

    return {}
