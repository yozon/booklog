# encoding: utf-8
import requests
import pickle
import re
import datetime
import csv
import os
from requests_oauthlib import OAuth1

api_key = "6FPsRuJagpscBpj8Nsm9w"
api_secret = "jbeTUVJkyjwSSKDUjxAZyZFUJXvTcbfTqe59cxY"
token = "73069717-wcbvBQ89AuOqsmp4uCIxR5r84cu77I8x2ijGg10DJ"
token_secret = "ZNpk7wTFPh62IktKi9MdK54ir3XULkz8xCX0orJ06jGp7"

auth = OAuth1(api_key, api_secret, token, token_secret)

query = "python exclude%3Aretweets -source%3A""IFTTT"" -monty -lang%3Aru -from%3Apython_octopus"

url = "https://api.twitter.com/1.1/search/tweets.json?&q=" + query
params = {'count': 200, 'include_rts': False, 'result_type': 'recent', 'include_entities': True}

res = requests.get(url, auth=auth, params=params)
if res.status_code == 200:
    print("OK")
else:
    print("Error: %d" % res.status_code)
tweetdata = res.json()['statuses']

# 除外ワード
ngsource = ['IFTTT', 'dlvr.it', 'twittbot.net', 'twitterfeed', 'LinkedIn', 'connpass']
ngword = ['楽天', 'ヤフオク', '【定期】', 'item.rakuten.co.jp', 'shopstyle.com', "#fashion", "#Fashion", "adf.ly"]
ngname = 'ython'
# whitelist = ["pypi_updates"]

# tweetデータの削減と除外候補選定
dlist = []
dcount = 0
for i in tweetdata:
    # 削減
    i['user_screen_name'] = i['user']['screen_name']
    i['user_name'] = i['user']['name']
    i['user_profile_image_url'] = i['user']['profile_image_url']
    del i['user']
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
    elif ngname in i['user_screen_name']:
        dlist.append(dcount)
    dcount += 1

# 除外処理
dlist = list(set(dlist))  # 重複削除
dlist.reverse()
deltweets = []
for i in dlist:
    try:
        deltweets.append(tweetdata[i])  # 削除したツイートを保存
    except:
        print("????????")
    del tweetdata[i]

if not os.path.exists('./tw.tw'):
    with open('./tw.tw', mode='w', encoding='UTF-8') as f:
        f.write("")

with open('tw.tw', mode='rb') as f:
    oldtweets = pickle.load(f)

# 保存していたツイートと取得したツイートを結合する
flag = False
count = 0
for i in oldtweets:
    if i['id'] < tweetdata[-1]['id']:
        tweetdata = tweetdata + oldtweets[count:]
        flag = True
    else:
        pass
    count += 1
    if flag:
        break
print(len(tweetdata))
with open('tw.tw', mode='wb') as f:
    pickle.dump(tweetdata, f)

"""cvs
paramnames = "id,profile_image,text,screen_name,created_at,source\n"
csvdata = paramnames

for tw in tweetdata:
    csvdata += tw['id_str'] + "," + tw['user_profile_image_url'] + ",\"" +\
     tw['text'].replace('\r\n', '').replace('\"', '\"\"') + "\"," + tw['user_screen_name'] +\
      "," + tw['created_at'] + "\",\"" + tw['source'] + "\n"

with open('tweets.csv', mode='w', encoding='utf-8') as f:
 f.write(csvdata)
"""

yesterday = datetime.date.today() - datetime.timedelta(1)

# 昨日のツイートを選別
yesterday_tweets = []
for tw in tweetdata:
    tw['created_at'] = datetime.datetime.strptime(tw['created_at'], '%a %b %d %H:%M:%S +0000 %Y') + datetime.timedelta(hours=9)
    if datetime.datetime.date(tw['created_at']) == yesterday:
        yesterday_tweets.append(tw)
    elif datetime.datetime.date(tw['created_at']) < yesterday - datetime.timedelta(1):
        break

# htmlへ加工と書き込み
yesterday_tweets.reverse()
html_body = "<html><body><table>"
for tw in yesterday_tweets:
    twtext = re.sub(r"(https?://t.co/[a-zA-Z0-9]*)", "<a href=\"\g<1>\">\g<1></a>", tw['text'])
    twtext = re.sub(r"@([a-zA-Z0-9_]*)", "@<a href=\"http://twitter.com/\g<1>/with_replies\">\g<1></a>", twtext)
    twtext = re.sub(r"#([a-zA-Z0-9_]*)", "<a href=\"https://twitter.com/search?q=%23\g<1>\">#\g<1></a>", twtext)
    twuser = "<a href=\"http://twitter.com/" + tw['user_screen_name'] + "/with_replies\">" + tw['user_screen_name'] + "</a>"
    # twdate = datetime.datetime.strptime(tw['created_at'], '%a %b %d %H:%M:%S +0000 %Y') + datetime.timedelta(hours=9)
    html_twdate = "<a href=\"http://twitter.com/{}/status/{}\">{}</a>".\
        format(tw['user_screen_name'], tw['id_str'], tw['created_at'].strftime('%m/%d %H:%M:%S'))
    html_body += "<tr><td><img src=\"{}\"></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".\
        format(tw['user_profile_image_url'], twtext, twuser, html_twdate, tw['source'])
html_body += "</table></body></html>"

with open("./twi/" + str(yesterday) + ".html", mode='w', encoding='utf-8') as f:
    f.write(html_body)

# feed(atom)の作成
header = "<?xml version='1.0' encoding='UTF-8'?>\n"
url = "http://aaa.jp/"
feed_link = "<feed xmlns=\"http://www.w3.org/2005/Atom\">\n"
title = "<title>twitter search feed</title>\n<link rel=\" elf\" href=\"" + url + "feed.xml\">\n"
author = "<author><name>John</name></author>\n"
feed_id = "<id>tag:twi.py,2015:01</id>\n"

file_name = os.listdir("./twi/")
sorted(file_name)
entry = ""
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

# 確認用
for tw in deltweets:
    print(tw['text'], "||", tw['user_screen_name'], "||", re.sub(r"<[^>]*?>", "", tw['source']), "||",
          datetime.datetime.strptime(tw['created_at'], '%a %b %d %H:%M:%S +0000 %Y') + datetime.timedelta(hours=9))
print("-----------\n", len(deltweets))
