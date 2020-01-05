### Delayed reposting in social networks
The program collect active users from a group in three social networks:
1. [VKontakte](https://vk.com/)
2. [Instagram](https://instagram.com/)
3. [Facebook](https://www.facebook.com/)

### How to install
To get started, get a token from VK, it can be obtained as follows:

You must follow the link: https://oauth.vk.com/authorize?client_id=`Your_ID_client`&scope=photos,groups,wall,offline&response_type=token
where `Your_ID_ID` is the application ID that can be viewed in the settings of your [application](https://vk.com/apps?act=manage)

You also need a key (access token) with the right to `groups_access_member_info` from Facebook, you can get it by following the [link](https://developers.facebook.com/tools/explorer/)
 
The following data must be written to the `.env` file:
```text
LOGIN_INSTAGRAM="your_login"
PASSWORD_INSTAGRAM='your_password'
INSTAGRAM_USERNAME='cocacolarus' #name of username where you will collect users
INSTAGRAM_PERIOD='90' # collecting period
VK_ACCESS_TOKEN="Your key to Vkontakte"
VK_GROUP='name of your VKontakte group'
VK_PERIOD='14' # collecting period
FB_GROUP_ID='Your Facebook Group ID'
FACEBOOK_TOKEN='Your Facebook Key'
FB_PERIOD='30' # collecting period
```

Python3 should already be installed.
Then use `pip` (or` pip3`, there is a conflict with Python2) to install the dependencies:
```
pip install -r requirements.txt
```

### How to run

You need run the script by type in console:

- for vk users:
```
py main.py vk
```
- for facebook users
```
py main.py facebook
```
- for instagram users
```
py main.py instagram
```

### Objective of the project

The code is written for educational purposes on the online course for web developers [dvmn.org](https://dvmn.org/).