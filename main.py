from instabot import Bot
import argparse
import os
from dotenv import load_dotenv
import datetime
import pprint
import requests


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', help='социальная сеть: facebook, vk или instagram')
    return parser


def instagram_get_user_ids():
    bot = Bot()
    bot.login(username=INSTAGRAM_LOGIN, password=INSTAGRAM_PASSWORD)
    user_id = bot.get_user_id_from_username(INSTAGRAM_USERNAME)
    posts = bot.get_user_medias_total(user_id, filtration=False)
    comments_all = []
    for post in posts:
        comments = bot.get_media_comments_all(post)
        for comment in comments:
            comment_user_id = comment['user_id']
            comment_created_at = comment['created_at_utc']
            comments_all.append({
                "comment_user_id": comment_user_id,
                "comment_created_at": comment_created_at,
            })
    now = datetime.datetime.now().timestamp()
    threshold = now - INSTAGRAM_PERIOD
    filtered_user_ids = {}
    for comment in comments_all:
        if comment["comment_created_at"] > threshold:
            if comment['comment_user_id'] in filtered_user_ids.keys():
                filtered_user_ids[comment['comment_user_id']] += 1
            else:
                filtered_user_ids[comment['comment_user_id']] = 1
    return filtered_user_ids


def vk_get_posts_from_wall(limited=False):
    vk_wall_get_url = 'https://api.vk.com/method/wall.get'
    offset = 0
    posts = []
    vk_wall_get_params = {
        'domain': VK_GROUP,
        'count': 100,
        'offset': offset,
        "access_token": VK_ACCESS_TOKEN,
        'v': '5.101',
    }
    response = requests.get(vk_wall_get_url, params=vk_wall_get_params)
    if limited:
        return response.json()['response']['items']
    while offset < response.json()['response']['count']:
        vk_wall_get_params = {
            'domain': VK_GROUP,
            'count': 100,
            'offset': offset,
            "access_token": VK_ACCESS_TOKEN,
            'v': '5.101',
        }
        response = requests.get(vk_wall_get_url, params=vk_wall_get_params)
        posts.extend(response.json()['response']['items'])
        offset += 100
    return posts


def vk_get_comments_from_post(post, owner_id):
    vk_wall_get_comments_url = 'https://api.vk.com/method/wall.getComments'
    vk_wall_get_comments_params = {
        'owner_id': -owner_id,
        'post_id': post,
        'count': 1,
        "access_token": VK_ACCESS_TOKEN,
        'v': '5.101',
    }
    response = requests.get(vk_wall_get_comments_url, params=vk_wall_get_comments_params)
    offset = 0
    comments = []
    while offset < response.json()['response']['count']:
        vk_wall_get_comments_params = {
            'owner_id': -owner_id,
            'post_id': post,
            'count': 100,
            'offset': offset,
            "access_token": VK_ACCESS_TOKEN,
            'v': '5.101',
        }
        response = requests.get(vk_wall_get_comments_url, params=vk_wall_get_comments_params)
        comments.extend(response.json()['response']['items'])
        offset += 100
    return comments


def vk_filter_comments(comments):
    filtered_comments = []
    for comment in comments:
        if comment['date'] > datetime.datetime.now().timestamp() - VK_PERIOD:
            filtered_comments.append(comment)
    return filtered_comments


def vk_get_user_ids_from_comments(comments):
    user_ids = []
    for comment in comments:
        if comment.get('from_id'):
            user_id = comment['from_id']
            if user_id > 0:
                user_ids.append(user_id)
    return set(user_ids)


def vk_get_user_ids_liked_post(post, owner_id):
    vk_likes_get_list_url = 'https://api.vk.com/method/likes.getList'
    vk_likes_get_list_params = {
        'type': 'post',
        'owner_id': -owner_id,
        'item_id': post,
        'count': 1,
        "access_token": VK_ACCESS_TOKEN,
        'v': '5.101',
    }
    response = requests.get(vk_likes_get_list_url, params=vk_likes_get_list_params)
    offset = 0
    user_ids = []
    while offset < response.json()['response']['count']:
        vk_likes_get_list_params = {
            'type': 'post',
            'owner_id': -owner_id,
            'item_id': post,
            'count': 1000,
            'offset': offset,
            "access_token": VK_ACCESS_TOKEN,
            'v': '5.101',
        }
        response = requests.get(vk_likes_get_list_url, params=vk_likes_get_list_params)
        user_ids.extend(response.json()['response']['items'])
        offset += 1000
    return set(user_ids)


def vk_get_group_id_from_group_name(group_name):
    vk_groups_get_by_id_url = 'https://api.vk.com/method/groups.getById'
    vk_groups_get_by_id_params = {
        'group_ids': group_name,
        "access_token": VK_ACCESS_TOKEN,
        'v': '5.101',
    }
    response = requests.get(vk_groups_get_by_id_url, params=vk_groups_get_by_id_params)
    return response.json()['response'][0]['id']


def fb_get_post_ids():
    fb_url = f'https://graph.facebook.com/{FB_GROUP_ID}'
    fb_params = {
        'fields': 'id,name,groups,feed',
        'access_token': FB_TOKEN
    }
    response = requests.get(fb_url, params=fb_params)
    fb_posts = response.json()['feed']['data']
    fb_post_ids = []
    for post in fb_posts:
        fb_post_ids.append(post['id'])
    return fb_post_ids


def fb_get_comment_user_ids(post_ids):
    comments = []
    fb_params = {
        'access_token': FB_TOKEN
    }
    for post_id in post_ids:
        fb_url = f'https://graph.facebook.com/{post_id}/comments'
        response = requests.get(fb_url, params=fb_params)
        post_comments = response.json()['data']
        if post_comments:
            comments.extend(post_comments)
    user_ids = []
    for comment in comments:
        comment_date = datetime.datetime.strptime(comment['created_time'], "%Y-%m-%dT%H:%M:%S+0000")
        comment_timestamp = datetime.datetime.timestamp(comment_date)
        if comment_timestamp > datetime.datetime.now(tz=datetime.timezone.utc).timestamp() - FB_PERIOD:
            user_ids.append(comment['from']['id'])
    return set(user_ids)


def fb_get_reactions_user_ids(post_ids):
    reactions = []
    fb_params = {
        'access_token': FB_TOKEN
    }
    for post_id in post_ids:
        fb_url = f'https://graph.facebook.com/{post_id}/reactions'
        response = requests.get(fb_url, params=fb_params)
        post_reactions = response.json()['data']
        if post_reactions:
            reactions.extend(post_reactions)
    user_ids = []
    for reaction in reactions:
        user_ids.append(reaction['id'])
    user_ids = set(user_ids)
    users = {}
    for user_id in user_ids:
        user_reactions = []
        for reaction in reactions:
            if user_id == reaction['id']:
                user_reactions.append(reaction['type'])
        user_emotions = {
            "LIKE": user_reactions.count('LIKE'),
            "LOVE": user_reactions.count('LOVE'),
            "WOW": user_reactions.count('WOW'),
            "HAHA": user_reactions.count('HAHA'),
            "SAD": user_reactions.count('SAD'),
            "ANGRY": user_reactions.count('ANGRY'),
            "THANKFUL": user_reactions.count('THANKFUL')
        }
        users[user_id] = user_emotions
    return users


if __name__ == '__main__':
    load_dotenv()
    parser = create_parser()
    mode = parser.parse_args().mode


    if mode == 'vk':
        VK_PERIOD = 24 * 60 * 60 * int(os.getenv('VK_PERIOD'))
        VK_ACCESS_TOKEN = os.getenv('VK_ACCESS_TOKEN')
        VK_GROUP = os.getenv('VK_GROUP')
        vk_group_id = vk_get_group_id_from_group_name(VK_GROUP)
        vk_posts = vk_get_posts_from_wall()
        vk_comments = []
        for vk_post in vk_posts:
            vk_comments.extend(vk_get_comments_from_post(vk_post[0]['id'], vk_group_id))
        filtered_comments = vk_filter_comments(vk_comments, VK_PERIOD)
        vk_user_ids = vk_get_user_ids_from_comments(filtered_comments)
        vk_liked_user_ids = vk_get_user_ids_liked_post(vk_posts[0]['id'])
        vk_audience = vk_liked_user_ids.intersection(vk_user_ids)
        pprint.pprint(vk_audience)
    elif mode == 'instagram':
        INSTAGRAM_PERIOD = int(os.getenv('INSTAGRAM_PERIOD')) * 24 * 60 * 60
        INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
        INSTAGRAM_LOGIN = os.getenv('LOGIN_INSTAGRAM')
        INSTAGRAM_PASSWORD = os.getenv('PASSWORD_INSTAGRAM')
        instagram_user_ids = instagram_get_user_ids()
        pprint.pprint(instagram_user_ids)
    elif mode == 'facebook':
        FB_GROUP_ID = os.getenv('FB_GROUP_ID')
        FB_TOKEN = os.getenv('FACEBOOK_TOKEN')
        FB_PERIOD = 60 * 60 * 24 * int(os.getenv('FB_PERIOD'))
        try:
            fb_post_ids = fb_get_post_ids()
        except KeyError:
            exit('Неверный токен фейсбука')
        fb_comment_user_ids = fb_get_comment_user_ids(fb_post_ids)
        fb_user_reactions = fb_get_reactions_user_ids(fb_post_ids)
        pprint.pprint(fb_comment_user_ids)
        pprint.pprint(fb_user_reactions)
    else:
        print('Доступны только три соц. сети: vk, instagram, facebook')