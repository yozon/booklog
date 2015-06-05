# encoding: utf-8
import requests
import json
import re
import datetime
from requests_oauthlib import OAuth1

api_key      = "6FPsRuJagpscBpj8Nsm9w"
api_secret   = "jbeTUVJkyjwSSKDUjxAZyZFUJXvTcbfTqe59cxY"
token        = "73069717-wcbvBQ89AuOqsmp4uCIxR5r84cu77I8x2ijGg10DJ"
token_secret = "ZNpk7wTFPh62IktKi9MdK54ir3XULkz8xCX0orJ06jGp7"

auth = OAuth1(api_key, api_secret, token, token_secret)

query = "python exclude%3Aretweets -source%3AIFTTT -io_python -monty"

url = "https://api.twitter.com/1.1/search/tweets.json?&q=" + query
params = {'count': 200, 'include_rts': False, 'result_type': 'recent'}

res = requests.get(url, auth=auth, params=params)
if res.status_code == 200:
    print("OK")
else:
    print("Error: %d" % res.status_code)
data = res.json()['statuses']
# a = data[0].keys()
# print(a)
# 除外候補
ngsource = ['IFTTT', 'dlvr.it', 'twittbot.net', 'twitterfeed']
ngword = '楽天'
dlist = []
dcount = 0

# 除外候補
for i in data:
    for ngs in ngsource:
        if ngs in i['source']:
            dlist.append(dcount)
    if i['source'].endswith('bot</a>') or i['source'].endswith('Bot</a>'):
        dlist.append(dcount)
    for ngw in ngword:
        if ngw in i['text']:
            dlist.append(dcount)
    if 'python' in i['user']['screen_name']:
        dlist.append(dcount)
    dcount += 1

# 除外処理
dlist.reverse()
print(len(dlist))
for i in dlist:
    del data[i]

old_tweet = data[0]

# htmlへ加工
html_body = "<html><body><table>"
for tw in data:
    twtext = re.sub(r"(https?://t.co/[^\s]*)", "<a href=\"\g<1>\">\g<1></a>", tw['text'])
    twtext = re.sub(r"@([^\s]*)", "@<a href=\"http://twitter.com/\g<1>/with_replies\">\g<1></a>", twtext)
    twuser = "<a href=\"http://twitter.com/%s/with_replies\">%s</a>" % (tw['user']['screen_name'], tw['user']['screen_name'])
    twdate = datetime.datetime.strptime(tw['created_at'],'%a %b %d %H:%M:%S +0000 %Y') + datetime.timedelta(hours=9)
    twdate = "<a href=\"http://twitter.com/%s/status/%s\">%s</a>" % (tw['user']['screen_name'], tw['id_str'], twdate.strftime('%m/%d %H:%M:%S'))
    html_body += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (twtext, twuser, twdate, tw['source'])
html_body += "</table></body></html>"

f = open('index.html', mode = 'w', encoding = 'utf-8')
f.write(html_body)
f.close()

for tw in data:
    print(tw['text'], "||", re.sub(r"<[^>]*?>", "", tw['source']))


