from instabot import Bot
import argparse
import os
from dotenv import load_dotenv
import datetime
import pprint
import requests
import collections


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', help='социальная сеть: facebook, vk или instagram',
                        choices=['instagram', 'vk', 'facebook'])
    return parser


def get_instagram_user_ids(bot, instagram_username, period=90 * 24 * 60 * 60):
    user_id = bot.get_user_id_from_username(instagram_username)
    posts = bot.get_total_user_medias(user_id)
    all_comments = []
    for post in posts:
        comments = bot.get_media_comments_all(post)
        all_comments.extend(comments)
    now = datetime.datetime.now().timestamp()
    threshold = now - period
    filtered_user_ids = [comment['user_id'] for comment in all_comments if comment["created_at_utc"] > threshold]
    users_count = collections.Counter(filtered_user_ids)
    return users_count


def get_vk_posts_from_wall(access_token, group, limited=False):
    vk_wall_get_url = 'https://api.vk.com/method/wall.get'
    offset = 0
    all_posts = []
    post_count = 0
    if limited:
        vk_wall_get_params = {
            'domain': group,
            'count': 100,
            'offset': offset,
            "access_token": access_token,
            'v': '5.101',
        }
        response = requests.get(vk_wall_get_url, params=vk_wall_get_params)
        response.raise_for_status()
        json_data = response.json()['response']
        return json_data['items']
    while offset <= post_count:
        vk_wall_get_params = {
            'domain': group,
            'count': 100,
            'offset': offset,
            "access_token": access_token,
            'v': '5.101',
        }
        response = requests.get(vk_wall_get_url, params=vk_wall_get_params)
        response.raise_for_status()
        json_data = response.json()['response']
        posts = json_data['items']
        all_posts.extend(posts)
        offset += 100
        post_count = json_data['count']
    return all_posts


def get_vk_comments_from_post(post, owner_id, access_token):
    vk_wall_get_comments_url = 'https://api.vk.com/method/wall.getComments'
    offset = 0
    comments_count = 0
    all_comments = []
    while offset <= comments_count:
        vk_wall_get_comments_params = {
            'owner_id': -owner_id,
            'post_id': post,
            'count': 100,
            'offset': offset,
            "access_token": access_token,
            'v': '5.101',
        }
        response = requests.get(vk_wall_get_comments_url, params=vk_wall_get_comments_params)
        response.raise_for_status()
        json_data = response.json()['response']
        comments = json_data['items']
        comments_count = json_data['count']
        all_comments.extend(comments)
        offset += 100
    return all_comments


def filter_vk_comments(comments, period=24 * 60 * 60 * 14):
    filtered_comments = []
    for comment in comments:
        if comment['date'] > datetime.datetime.now().timestamp() - period:
            filtered_comments.append(comment)
    return filtered_comments


def get_vk_user_ids_from_comments(comments):
    user_ids = []
    for comment in comments:
        if comment.get('from_id'):
            user_id = comment['from_id']
            if user_id > 0:
                user_ids.append(user_id)
    return set(user_ids)


def get_vk_user_ids_liked_post(post, owner_id, access_token):
    vk_likes_get_list_url = 'https://api.vk.com/method/likes.getList'
    offset = 0
    count_user_ids = 0
    all_user_ids = []
    while offset <= count_user_ids:
        vk_likes_get_list_params = {
            'type': 'post',
            'owner_id': -owner_id,
            'item_id': post,
            'count': 1000,
            'offset': offset,
            "access_token": access_token,
            'v': '5.101',
        }
        response = requests.get(vk_likes_get_list_url, params=vk_likes_get_list_params)
        response.raise_for_status()
        json_data = response.json()['response']
        user_ids = json_data['items']
        count_user_ids = json_data['count']
        all_user_ids.extend(user_ids)
        offset += 1000
    return set(all_user_ids)


def get_vk_group_id_from_group_name(token, group_name):
    vk_groups_get_by_id_url = 'https://api.vk.com/method/groups.getById'
    vk_groups_get_by_id_params = {
        'group_ids': group_name,
        "access_token": token,
        'v': '5.101',
    }
    response = requests.get(vk_groups_get_by_id_url, params=vk_groups_get_by_id_params)
    response.raise_for_status()
    group_id = response.json()['response'][0]['id']
    return group_id


def get_fb_post_ids(token, group_id):
    fb_url = f'https://graph.facebook.com/{group_id}'
    fb_params = {
        'fields': 'id,name,groups,feed',
        'access_token': token
    }
    response = requests.get(fb_url, params=fb_params)
    response.raise_for_status()
    fb_posts = response.json()['feed']['data']
    fb_post_ids = []
    for post in fb_posts:
        fb_post_ids.append(post['id'])
    return fb_post_ids


def get_fb_comment_user_ids(token, post_ids, period=24 * 60 * 60 * 30):
    comments = []
    fb_params = {
        'access_token': token
    }
    for post_id in post_ids:
        fb_url = f'https://graph.facebook.com/{post_id}/comments'
        response = requests.get(fb_url, params=fb_params)
        response.raise_for_status()
        post_comments = response.json()['data']
        if post_comments:
            comments.extend(post_comments)
    user_ids = []
    for comment in comments:
        comment_date = datetime.datetime.strptime(comment['created_time'], "%Y-%m-%dT%H:%M:%S+0000")
        comment_timestamp = datetime.datetime.timestamp(comment_date)
        if comment_timestamp > datetime.datetime.now(tz=datetime.timezone.utc).timestamp() - period:
            user_id = comment['from']['id']
            user_ids.append(user_id)
    return set(user_ids)


def get_fb_reactions_user_ids(token, post_ids):
    reactions = []
    fb_params = {
        'access_token': token
    }
    for post_id in post_ids:
        fb_url = f'https://graph.facebook.com/{post_id}/reactions'
        response = requests.get(fb_url, params=fb_params)
        response.raise_for_status()
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


def main():
    load_dotenv()
    parser = create_parser()
    mode = parser.parse_args().mode

    if mode == 'vk':
        vk_period = 24 * 60 * 60 * int(os.getenv('VK_PERIOD'))
        vk_access_token = os.getenv('VK_ACCESS_TOKEN')
        vk_group = os.getenv('VK_GROUP')
        try:
            vk_group_id = get_vk_group_id_from_group_name(vk_access_token, vk_group)
        except requests.exceptions.HTTPError as error:
            print(error.response.json()['error']['error_user_msg'])
        try:
            vk_posts = get_vk_posts_from_wall(vk_access_token, vk_group)
        except requests.exceptions.HTTPError as error:
            print(error.response.json()['error']['error_user_msg'])
        vk_comments = []
        for vk_post in vk_posts:
            vk_comments.extend(get_vk_comments_from_post(vk_post['id'], vk_group_id, access_token=vk_access_token))
        filtered_comments = filter_vk_comments(vk_comments, vk_period)
        vk_user_ids = get_vk_user_ids_from_comments(filtered_comments)
        try:
            vk_liked_user_ids = get_vk_user_ids_liked_post(vk_posts[0]['id'], vk_group_id, access_token=vk_access_token)
        except requests.exceptions.HTTPError as error:
            print(error.response.json()['error']['error_user_msg'])
        vk_audience = vk_liked_user_ids.intersection(vk_user_ids)
        pprint.pprint(vk_audience)
    elif mode == 'instagram':
        instagram_period = int(os.getenv('INSTAGRAM_PERIOD')) * 24 * 60 * 60
        instagram_username = os.getenv('INSTAGRAM_USERNAME')
        instagram_login = os.getenv('LOGIN_INSTAGRAM')
        instagram_password = os.getenv('PASSWORD_INSTAGRAM')
        bot = Bot()
        bot.login(username=instagram_login, password=instagram_password)
        instagram_user_ids = get_instagram_user_ids(bot, instagram_username, period=instagram_period)
        pprint.pprint(instagram_user_ids)
    elif mode == 'facebook':
        fb_group_id = os.getenv('FB_GROUP_ID')
        fb_token = os.getenv('FACEBOOK_TOKEN')
        fb_period = 60 * 60 * 24 * int(os.getenv('FB_PERIOD'))
        try:
            fb_post_ids = get_fb_post_ids(fb_token, fb_group_id)
        except KeyError:
            exit('Неверный токен фейсбука')
        except requests.exceptions.HTTPError as error:
            print(error.response.json()['error']['error_user_msg'])
        try:
            fb_comment_user_ids = get_fb_comment_user_ids(fb_token, fb_post_ids, period=fb_period)
        except requests.exceptions.HTTPError as error:
            print(error.response.json()['error']['error_user_msg'])
        try:
            fb_user_reactions = get_fb_reactions_user_ids(fb_token, fb_post_ids)
        except requests.exceptions.HTTPError as error:
            print(error.response.json()['error']['error_user_msg'])
        pprint.pprint(fb_comment_user_ids)
        pprint.pprint(fb_user_reactions)
    else:
        print('Доступны только три соц. сети: vk, instagram, facebook')


if __name__ == '__main__':
    main()
