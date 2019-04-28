"""
    WarriorBeatGraphQL
    GraphQL Resolvers
"""

try:
    import unzip_requirements
except ImportError:
    pass
import uuid
from datetime import datetime
from itertools import chain

import requests
from bs4 import BeautifulSoup
from data import DynamoDB, S3Storage
from slugify import slugify


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


def handle_article_like(*args, **kwargs):
    """handles user liking article, returns article"""
    post_id = kwargs.get('id')
    user_id = kwargs.get('userId')
    likes_table = DynamoDB("article_likes")
    article_table = DynamoDB("article")
    article = article_table.get_item(post_id)
    query_filter = ("postId", post_id)
    likes = likes_table.query(user_id, key="userId",
                              filters=query_filter, index="user-index")
    if any(likes):
        like = likes[0]
        likes_table.delete_item(like['id'])
        return article
    like = {
        "id": str(uuid.uuid4()),
        "postId": post_id,
        "userId": user_id
    }
    likes_table.add_item(like)
    return article


def handle_slug(*args, **kwargs):
    """returns slugified version of toSlug kwargs"""
    text = kwargs.get("toSlug")
    slug = slugify(text, lowercase=True, separator='_')
    return slug


def handle_paginate(*args, **kwargs):
    """returns paginated resource scan"""
    resource = kwargs.get("typeResource")
    sort_by = kwargs.get("sortOrder", None)
    limit = kwargs.get("limit", 20)
    next_token = kwargs.get("nextToken", None)
    table = DynamoDB(resource)
    items = table.scan(limit=limit, next_token=next_token)
    if sort_by:
        key = sort_by.get('key')
        values = sort_by.get('values')
        sort_key = list(map(lambda x: values.index(
            x[key]) if x[key] in values else len(items)+1, items))
        items = [i for _, i in sorted(
            zip(sort_key, items), key=lambda p: p[0])]
    return {"items": items}


def handle_author_title(*args, **kwargs):
    """returns formatted Author role"""
    title = kwargs.get("roles")
    ignored_roles = ['administrator', 'author', 'contributor',
                     'customer', 'editor', 'shop_manager', 'subscriber']
    titles = [t for t in title if not t in ignored_roles]
    for t in titles:
        t = t.split('_')
        t = [i.capitalize() for i in t]
        title = " ".join(t)
    return title


def handle_poll_has_voted(*args, **kwargs):
    """checks if user has voted on poll, returns PollOption"""
    user_id = kwargs.get("userId")
    poll = kwargs.get("poll")
    options_table = DynamoDB("poll_options")
    votes_table = DynamoDB("poll_votes")
    options = options_table.query(
        poll['id'], key="pollId", index="pollId-index")
    option_ids = [opt.get('id') for opt in options]
    user_votes = list(chain.from_iterable([votes_table.query(
        user_id, key="userId", range_key=('optionId', i), index="userId-index") for i in option_ids]))
    print("User Votes:", user_votes)
    if len(user_votes) >= 1:
        voted_option = next(
            i for i in options if i['id'] == user_votes[0]['optionId'])
        print("Voted Option:", voted_option)
        return voted_option
    return None


def handle_get_about_meta(*args, **kwargs):
    """Returns About Us Meta Info"""
    url = "https://ogwarriorbeat.com/about/"
    page = requests.get(url)
    html = BeautifulSoup(page.content, 'html.parser')
    content = html.find("div", class_="postarea")
    [s.extract() for s in content('h1')]
    cont = content.find('a').parent
    cont.extract()
    return {
        "key": "about",
        "content": str(content)
    }


def handle_get_meta(*args, **kwargs):
    """Handles Meta Info"""
    meta_resolver = {
        'about': handle_get_about_meta
    }
    key = kwargs.get("key")
    resolve = meta_resolver[key]
    return resolve(*args, **kwargs)


resolvers = {
    'mediaCreate': handle_media_create,
    'mediaDelete': handle_media_delete,
    'articleGetByCategory': handle_article_by_category,
    'category_slug': handle_slug,
    'categoryList': handle_paginate,
    'author_title': handle_author_title,
    'poll_hasVoted': handle_poll_has_voted,
    'resolveMeta': handle_get_meta
}


def lambda_handler(event, context):
    print("Got an Invoke Request")
    print(f"Event: {event}")
    print(f"Context: {context.__dict__}")

    field = event['field']
    args = event['args']

    resolve = resolvers[field]
    return resolve(**args)
