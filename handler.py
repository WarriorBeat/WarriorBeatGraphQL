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


def insert_poll_vote(option_id):
    vote_table = dynamodb.Table(TABLES['poll_votes']['table_name'])
    date = datetime.datetime.now()
    vote = {
        'id': str(uuid.uuid4()),
        'option_id': option_id,
        'created_at': datetime.date.isoformat(date)
    }
    vote_table.put_item(Item=vote)
    return vote


def get_poll_results(poll_id):
    opt_table = dynamodb.Table(TABLES['poll_options']['table_name'])
    vote_table = dynamodb.Table(TABLES['poll_votes']['table_name'])
    results = {
        "poll_id": poll_id,
        "total_votes": 0,
        "results": []
    }
    # Get Poll Option IDS
    resp = opt_table.query(
        IndexName='pollId-index',
        Select="ALL_PROJECTED_ATTRIBUTES",
        KeyConditionExpression=Key('poll_id').eq(poll_id)
    )
    options = resp.get("Items")
    for opt in options:
        opt_id = opt['id']
        resp = vote_table.query(
            IndexName="optionId-index",
            Select="ALL_PROJECTED_ATTRIBUTES",
            KeyConditionExpression=Key('option_id').eq(opt_id)
        )
        votes = resp.get("Items")
        vote_count = len(votes)
        results["total_votes"] += vote_count
        results['results'].append({
            "id": opt_id,
            "poll_id": poll_id,
            "text": opt['text'],
            "votes": vote_count
        })
    return results


def lambda_handler(event, context):
    print("Got an Invoke Request")
    print(f"Event: {event}")
    print(f"Context: {context.__dict__}")

    field = event['field']
    args = event['arguments']

    if field == 'insertPollVote':
        return insert_poll_vote(**args)

    if field == 'getPollResults':
        return get_poll_results(**args)
    return {}
