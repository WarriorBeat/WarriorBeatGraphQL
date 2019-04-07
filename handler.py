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


def get_utc_now():
    """returns UTC now with zulu suffix"""
    utc_now = datetime.utcnow()
    utc_zulu = utc_now.strftime(
        '%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return utc_zulu


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
    create_date = get_utc_now()
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
    base_key = f"{media['authorId']}_{media['id']}"
    media['url'], media['key'] = media_s3.upload_from_url(
        media['source'], key=base_key)
    media_table.add_item(media)
    return media


def handle_article_by_category(*args, **kwargs):
    """Returns Articles sorted by Category"""
    article_table = DynamoDB('article')
    category = kwargs.get("categoryId")
    articles = [
        art for art in article_table.all if category in art['categories']]
    return articles


resolvers = {
    'mediaCreate': handle_media_create,
    'mediaDelete': handle_media_delete,
    'articleGetByCategory': handle_article_by_category
}


def lambda_handler(event, context):
    print("Got an Invoke Request")
    print(f"Event: {event}")
    print(f"Context: {context.__dict__}")

    field = event['field']
    args = event['args']

    resolve = resolvers[field]
    return resolve(**args)
