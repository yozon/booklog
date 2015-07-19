# encoding: utf-8
import requests
import re
import datetime
import time
import os
import pprint
import configparser
from requests_oauthlib import OAuth1

config = configparser.ConfigParser()
config.read('roguelike.ini', encoding="UTF-8")

api_key = config.get('api_key', 'api_key')
api_secret = config.get('api_key', 'api_secret')
token = config.get('api_key', 'token')
token_secret = config.get('api_key', 'token_secret')
auth = OAuth1(api_key, api_secret, token, token_secret)

query = config.get('query', 'query')

url = "https://api.twitter.com/1.1/search/tweets.json?&q=" + query
params = {'count': 100, 'include_rts': False, 'result_type': 'recent', 'include_entities': True}

res = requests.get(url, auth=auth, params=params)
if res.status_code == 200:
    print("OK")
else:
    print("Error: %d" % res.status_code)
    if res.status_code == 429:
        rate = requests.get(url="https://api.twitter.com/1.1/application/rate_limit_status.json?", auth=auth).json()
        tm = time.localtime(rate['resources']['search']['/search/tweets']['reset'])
        print("Reset Time  {}:{}".format(tm.tm_hour, tm.tm_min))
tweetdata = res.json()['statuses']
# pprint.pprint(tweetdata[0])

yesterday = datetime.date.today() - datetime.timedelta(1)
maxid = 0
lasttweetday = datetime.datetime.date(datetime.datetime.strptime(tweetdata[-1]['created_at'],
                                  '%a %b %d %H:%M:%S +0000 %Y') + datetime.timedelta(hours=9))
while True:
    lasttweetday = datetime.datetime.date(datetime.datetime.strptime(tweetdata[-1]['created_at'],
                                  '%a %b %d %H:%M:%S +0000 %Y') + datetime.timedelta(hours=9))
    if len(tweetdata) == 0:
        break
    if lasttweetday < yesterday:
        break
    elif lasttweetday >= yesterday:
        maxid = tweetdata[-1]['id']
        params['max_id'] = maxid - 1
        res = requests.get(url, auth=auth, params=params)
        tweetdata += res.json()['statuses']
    else:
        break

gettweets = len(tweetdata)

# 除外ワード
ngsource = config.get('ng', 'ngsource').split(",")
ngword = config.get('ng', 'ngword').split(",")
ngscreenname = config.get('ng', 'ngscreenname').split(",")
ngname = config.get('ng', 'ngname').split(",")
# whitelist = ["pypi_updates"]

# 除外候補選定
dlist = []
dcount = 0

for i in tweetdata:
    # 除外候補
    for ngs in ngsource:
        if ngs in i['source']:
            dlist.append(dcount)
    for ngw in ngword:
        if ngw in i['text']:
            dlist.append(dcount)
    for ngsn in ngscreenname:
        if ngsn in i['user']['screen_name']:
            dlist.append(dcount)
    for ngn in ngname:
        if ngn in i['user']['name']:
            dlist.append(dcount)
    if i['source'].endswith('bot</a>') or i['source'].endswith('Bot</a>'):
        dlist.append(dcount)
    elif re.search(r"@[^\s]*python[^\s]*", i['text'], re.I):
        dlist.append(dcount)
    dcount += 1

# 除外処理
dlist = list(set(dlist))  # 重複削除
dlist = sorted(dlist)
dlist.reverse()
deltweets = []
for i in dlist:
    try:
        deltweets.append(tweetdata[i])
        del tweetdata[i]
    except:
        print("????????")

# 昨日のツイートを選別
yesterday_tweets = []
for tw in tweetdata:
    tw['created_at'] = datetime.datetime.strptime(tw['created_at'], '%a %b %d %H:%M:%S +0000 %Y') + datetime.timedelta(hours=9)
    if datetime.datetime.date(tw['created_at']) == yesterday:
        yesterday_tweets.append(tw)
    elif datetime.datetime.date(tw['created_at']) < yesterday:
        break

# htmlへ加工と書き込み
yesterday_tweets.reverse()
html_body = "<html><body><table>"
for tw in yesterday_tweets:
    twtext = tw['text']
    if tw['entities']['urls']:
        for i in tw['entities']['urls']:
            twtext = re.sub(i['url'], "<a href=\"{}\">{}</a>".format(i['expanded_url'], i['display_url']), twtext)
    twtext = re.sub(r"(https?://t.co/[a-zA-Z0-9]*)", "<a href=\"\g<1>\">\g<1></a>", twtext)
    twtext = re.sub(r"@([a-zA-Z0-9_]*)", "@<a href=\"http://twitter.com/\g<1>/with_replies\">\g<1></a>", twtext)
    twtext = re.sub(r"#([\S]*)", "<a href=\"https://twitter.com/search?q=%23\g<1>\">#\g<1></a>", twtext)
    twuser = "<a href=\"http://twitter.com/" + tw['user']['screen_name'] + "/with_replies\">" + tw['user']['screen_name'] + "</a>"
    # twdate = datetime.datetime.strptime(tw['created_at'], '%a %b %d %H:%M:%S +0000 %Y') + datetime.timedelta(hours=9)
    html_twdate = "<a href=\"http://twitter.com/{}/status/{}\">{}</a>".\
        format(tw['user']['screen_name'], tw['id_str'], tw['created_at'].strftime('%m/%d %H:%M:%S'))
    if 14 < tw['retweet_count'] + tw['favorite_count'] < 50:
        html_body += "<tr><td><img src=\"{}\"></td><td>{}</td><td bgcolor=\"MistyRose\">{}</td><td>{}</td><td>{}</td></tr>".\
                    format(tw['user']['profile_image_url'], twtext, twuser, html_twdate, tw['source'])
    elif 49 < tw['retweet_count'] + tw['favorite_count'] < 100:
        html_body += "<tr><td><img src=\"{}\"></td><td>{}</td><td bgcolor=\"LightSalmon\">{}</td><td>{}</td><td>{}</td></tr>".\
                    format(tw['user']['profile_image_url'], twtext, twuser, html_twdate, tw['source'])
    elif 99 < tw['retweet_count'] + tw['favorite_count']:
        html_body += "<tr><td><img src=\"{}\"></td><td>{}</td><td bgcolor=\"Red\">{}</td><td>{}</td><td>{}</td></tr>".\
                    format(tw['user']['profile_image_url'], twtext, twuser, html_twdate, tw['source'])
    else:
        html_body += "<tr><td><img src=\"{}\"></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".\
                    format(tw['user']['profile_image_url'], twtext, twuser, html_twdate, tw['source'])

html_body += "</table></body></html>"

with open("C:\\Users\\owner\\Dropbox\\twiSearch\\" + str(yesterday) + ".html", mode='w', encoding='utf-8') as f:
    f.write(html_body)

# feed(atom)の作成
header = "<?xml version='1.0' encoding='UTF-8'?>\n"
url = "https://www.dropbox.com/home/twiSearch"
feed_link = "<feed xmlns=\"http://www.w3.org/2005/Atom\">\n"
title = "<title>twitter search feed</title>\n<link rel=\"self\" href=\"" + url + "/feed.xml\"/>\n"
author = "<author><name>John</name></author>\n"
feed_id = "<id>tag:twi.py,2015:01</id>\n"

file_name = os.listdir("C:\\Users\\owner\\Dropbox\\twiSearch\\")
sorted(file_name)
entry = ""
entry_date = ""
for i in file_name:
    if ".html" in i:
        entry_link = url
        entry_title = i.replace(".html", "")
        entry_content = i
        entry_date = entry_title + "T16:00:00+09:00"
        entry_id = "tag:twi.py,2015:" + entry_title
        entry += "<entry>\n<title>" + entry_title + "</title>\n" + "<content>" + entry_content + "</content>\n" +\
                 "<link href=\"" + entry_link + "\"/>\n" + "<id>" + entry_id + "</id>\n" + \
                 "<updated>" + entry_date + "</updated>\n" + "</entry>\n"
    else:
        pass

feed_updated = "<updated>" + entry_date + "</updated>\n"
feed = header + feed_link + title + feed_updated + author + feed_id + entry + "</feed>"

with open("C:\\Users\\owner\\Dropbox\\twiSearch\\feed.xml", mode='w', encoding='UTF-8') as f:
    f.write(feed)


""" # 確認用
for tw in yesterday_tweets:
    print(tw['text'] + "||", tw['user']['screen_name'] + "||", re.sub(r"<[^>]*?>", "", tw['source']) + "||",
          tw['created_at'], "||", tw['favorite_count'])
"""
print("-----------------------------------------")
print("get " + str(gettweets))
print("del " + str(len(deltweets)))
print("tweets " + str(len(tweetdata)))
rate = requests.get(url="https://api.twitter.com/1.1/application/rate_limit_status.json?", auth=auth).json()
print("api limit {} / {}".format(rate['resources']['search']['/search/tweets']['remaining'],
                             rate['resources']['search']['/search/tweets']['limit']))
tm = time.localtime(rate['resources']['search']['/search/tweets']['reset'])
print("Reset Time  {}:{}".format(tm.tm_hour, tm.tm_min))
print("-----------------------------------------\n")

pid = os.startfile('"C:\Program Files (x86)\Dropbox\Client\Dropbox.exe"')