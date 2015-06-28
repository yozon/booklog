# encoding: utf-8
import requests
import pickle
import re
import datetime
import time
import csv
import os
import pprint
import configparser
from requests_oauthlib import OAuth1

config = configparser.ConfigParser()
config.read('twi.ini', encoding="UTF-8")

api_key = config.get('api_key', 'api_key')
api_secret = config.get('api_key', 'api_secret')
token = config.get('api_key', 'token')
token_secret = config.get('api_key', 'token_secret')

auth = OAuth1(api_key, api_secret, token, token_secret)

query = "python exclude%3Aretweets -source%3A""IFTTT"" -monty -lang%3Aru -from%3Apython_octopus"

url = "https://api.twitter.com/1.1/search/tweets.json?&q=" + query
params = {'count': 100, 'include_rts': False, 'result_type': 'recent', 'include_entities': True}

res = requests.get(url, auth=auth, params=params)
if res.status_code == 200:
    print("OK")
else:
    print("Error: %d" % res.status_code)
tweetdata = res.json()['statuses']
# pprint.pprint(tweetdata[0])
if not os.path.exists('./tw.tw') :
    with open('./tw.tw', mode='wb') as f:
        pickle.dump(tweetdata, f)

with open('./tw.tw', mode='rb') as f:
    oldtweets = pickle.load(f)
    gottweets = len(oldtweets)

yesterday = datetime.date.today() - datetime.timedelta(1)
maxid = 0
gettweets = 0
lasttweetday = datetime.datetime.date(datetime.datetime.strptime(tweetdata[-1]['created_at'],
                                  '%a %b %d %H:%M:%S +0000 %Y') + datetime.timedelta(hours=9))
while True:
    if len(tweetdata) == 0:
        break
    if lasttweetday < yesterday:
        break
    elif oldtweets[0]['id'] < tweetdata[-1]['id']:
        maxid = tweetdata[-1]['id']
        params['max_id'] = maxid - 1
        res = requests.get(url, auth=auth, params=params)
        tweetdata += res.json()['statuses']
    else:
        break

# 除外ワード
ngsource = config.get('ng', 'ngsource').split(",")
ngword = config.get('ng', 'ngword').split(",")
ngname = 'ython'
# whitelist = ["pypi_updates"]

# tweetデータの削減と除外候補選定
dlist = []
dcount = 0
c = 0
for i in tweetdata:
    if oldtweets[0]['id'] == tweetdata[0]['id']:
        tweetdata = []
        break
    elif oldtweets[0]['id'] > i['id']:
        gettweets = len(tweetdata[:c-1])
        tweetdata = tweetdata[:c-1]
        break
    c += 1
    # 除外候補
    for ngs in ngsource:
        if ngs in i['source']:
            dlist.append(dcount)
    for ngw in ngword:
        if ngw in i['text']:
            dlist.append(dcount)
    if i['source'].endswith('bot</a>') or i['source'].endswith('Bot</a>'):
        dlist.append(dcount)
    elif re.search(r"@[^\s]*python[^\s]*", i['text'], re.I):
        dlist.append(dcount)
    elif ngname in i['user']['screen_name']:
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

# 保存していたツイートと取得したツイートを結合する
tweetdata = tweetdata + oldtweets

# 5000以上たまったら古いツイートを削除
if len(tweetdata) > 5000:
    del tweetdata[4999:]

with open('tw.tw', mode='wb') as f:
    pickle.dump(tweetdata, f)

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
    twtext = re.sub(r"(https?://t.co/[a-zA-Z0-9]*)", "<a href=\"\g<1>\">\g<1></a>", tw['text'])
    twtext = re.sub(r"@([a-zA-Z0-9_]*)", "@<a href=\"http://twitter.com/\g<1>/with_replies\">\g<1></a>", twtext)
    twtext = re.sub(r"#([a-zA-Z0-9_]*)", "<a href=\"https://twitter.com/search?q=%23\g<1>\">#\g<1></a>", twtext)
    twuser = "<a href=\"http://twitter.com/" + tw['user']['screen_name'] + "/with_replies\">" + tw['user']['screen_name'] + "</a>"
    # twdate = datetime.datetime.strptime(tw['created_at'], '%a %b %d %H:%M:%S +0000 %Y') + datetime.timedelta(hours=9)
    html_twdate = "<a href=\"http://twitter.com/{}/status/{}\">{}</a>".\
        format(tw['user']['screen_name'], tw['id_str'], tw['created_at'].strftime('%m/%d %H:%M:%S'))
    html_body += "<tr><td><img src=\"{}\"></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".\
        format(tw['user']['profile_image_url'], twtext, twuser, html_twdate, tw['source'])
html_body += "</table></body></html>"

with open("C:\\Users\\owner\\Dropbox\\twiSearch\\" + str(yesterday) + ".html", mode='w', encoding='utf-8') as f:
    f.write(html_body)

# feed(atom)の作成
header = "<?xml version='1.0' encoding='UTF-8'?>\n"
url = "http://aaa.jp/"
feed_link = "<feed xmlns=\"http://www.w3.org/2005/Atom\">\n"
title = "<title>twitter search feed</title>\n<link rel=\"self\" href=\"" + url + "feed.xml\">\n"
author = "<author><name>John</name></author>\n"
feed_id = "<id>tag:twi.py,2015:01</id>\n"

file_name = os.listdir("./twi/")
sorted(file_name)
entry = ""
entry_date = ""
for i in file_name:
    try:
        entry_link = url + i
        entry_title = i.replace(".html", "")
        entry_date = entry_title + "T16:00:00+09:00"
        entry_id = "tag:twi.py," + entry_title
        entry += "<entry>\n<title>" + entry_title + "</title>\n" + "<link href=\"" + entry_link + "\"/>\n" +\
               "<id>" + entry_id + "</id>\n" + "<publised>" + entry_date + "</publised>\n" + "</entry>\n"
    except:
        pass

feed_updated = "<publised>" + entry_date + "</publised>\n"
feed = header + feed_link + title + feed_updated + author + feed_id + entry + "</feed>"

with open('./feed.xml', mode='w', encoding='UTF-8') as f:
    f.write(feed)

"""
# 確認用
for tw in deltweets[:100]:
    print(tw['text'], "||", tw['user_screen_name'], "||", re.sub(r"<[^>]*?>", "", tw['source']), "||",
          tw['created_at'])
"""
print("-----------------------------------------")
print("get " + str(gettweets))
print("del " + str(len(deltweets)))
print("tweets " + str(len(tweetdata)) + " 差分+ " + str(len(tweetdata) - gottweets))
rate = requests.get(url="https://api.twitter.com/1.1/application/rate_limit_status.json?", auth=auth).json()
print("api limit {} / {}".format(rate['resources']['search']['/search/tweets']['remaining'],
                             rate['resources']['search']['/search/tweets']['limit']))
tm = time.localtime(rate['resources']['search']['/search/tweets']['reset'])
print("Reset Time  {}:{}".format(tm.tm_hour, tm.tm_min))
print("-----------------------------------------\n")
