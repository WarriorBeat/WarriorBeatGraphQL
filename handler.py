"""
    WarriorBeatGraphQL
    GraphQL Resolvers
"""

try:
    import unzip_requirements
except ImportError:
    pass
import json
import uuid
import os
from datetime import datetime
from data import DynamoDB, S3Storage


def handle_media_delete(*args, **kwargs):
    """
    Deletes file from S3 and DynamoDB
    Returns Media
    """
    media_table = DynamoDB('media')
    media_s3 = S3Storage('media')
    media_id = kwargs.get("id")
    media_obj = media_table.get_item(media_id)
    media_s3_key = media_obj['key']

    media_s3.delete(media_s3_key)
    media_table.delete_item(media_id)
    return kwargs


def handle_media_create(*args, **kwargs):
    """
    Creates file in S3 from source
    Create media item entry in database
    returns Media
    """
    media_table = DynamoDB('media')
    media_s3 = S3Storage('media')
    create_date = str(datetime.now().isoformat())
    input_args = kwargs.get("media")
    media = {
        'id': str(uuid.uuid4()),
        'authorId': input_args.get('authorId'),
        'source': input_args.get('source'),
        'credits': input_args.get('credits', ''),
        'caption': input_args.get('caption', ''),
        'createdOn': create_date,
        'lastUpdated': create_date,
        'key': '',
        'url': ''
    }
    key = f"{media['authorId']}_{media['id']}"
    media['url'], _ = media_s3.upload_from_url(media['source'], key=key)
    media['key'] = key
    media_table.add_item(media)
    print(media)
    return media


resolvers = {
    'mediaCreate': handle_media_create,
    'mediaDelete': handle_media_delete
}


def lambda_handler(event, context):
    print("Got an Invoke Request")
    print(f"Event: {event}")
    print(f"Context: {context.__dict__}")

    field = event['field']
    args = event['args']
    print("Environment:", os.environ)

    resolve = resolvers[field]
    return resolve(**args)
