# encoding: utf-8
import requests
import pickle
import re
import datetime
import csv
from requests_oauthlib import OAuth1

api_key = "6FPsRuJagpscBpj8Nsm9w"
api_secret = "jbeTUVJkyjwSSKDUjxAZyZFUJXvTcbfTqe59cxY"
token = "73069717-wcbvBQ89AuOqsmp4uCIxR5r84cu77I8x2ijGg10DJ"
token_secret = "ZNpk7wTFPh62IktKi9MdK54ir3XULkz8xCX0orJ06jGp7"

auth = OAuth1(api_key, api_secret, token, token_secret)

query = "python exclude%3Aretweets -source%3Atwitterfeed -monty -lang%3Aru -from%3Apython_octopus"

url = "https://api.twitter.com/1.1/search/tweets.json?&q=" + query
params = {'count': 200, 'include_rts': False, 'result_type': 'recent', 'include_entities': True}

res = requests.get(url, auth=auth, params=params)
if res.status_code == 200:
    print("OK")
else:
    print("Error: %d" % res.status_code)
tweetdata = res.json()['statuses']
# a = data[0].keys()
# print(a)
# 除外候補
ngsource = ['IFTTT', 'dlvr.it', 'twittbot.net', 'twitterfeed', 'LinkedIn', 'connpass']
ngword = ['楽天', '【定期】', 'item.rakuten.co.jp', 'shopstyle.com', "#fashion", "#Fashion"]
dlist = []
dcount = 0

# 除外候補
for i in tweetdata:
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
    elif 'ython' in i['user']['screen_name']:
        dlist.append(dcount)
    dcount += 1

# 除外処理
dlist = list(set(dlist))  # 重複削除
dlist.reverse()
deltweets = []
for i in dlist:
    deltweets.append(tweetdata[i])  # 削除したツイートを保存
    del tweetdata[i]


with open('tw.tw', mode='rb') as f:
    oldtweets = pickle.load(f)

def loop():
    for i in oldtweets:
        if i['str'] < tweetdata[-1]['str']:
            tweetdata += oldtweets[i:]
            return
        else:
            pass

with open('tw.tw', mode='wb') as f:
    pickle.dump(tweetdata, f)

"""
paramnames = "id,profile_image,text,screen_name,created_at,source\n"
csvdata = paramnames

for tw in tweetdata:
    csvdata += tw['id_str'] + "," + tw['user']['profile_image_url'] + ",\"" + tw['text'].replace('\r\n', '').replace('\"', '\"\"') + "\"," + tw['user']['screen_name'] + "," + tw['created_at'] + "\",\"" + tw['source'] + "\n"

with open('tweets.csv', mode='w', encoding='utf-8') as f:
 f.write(csvdata)
"""

# htmlへ加工

tweetdata.reverse()
# lasttweet = "<!-- "+tweetdata[0]['id']+" -->\n"
html_body = ""
for tw in tweetdata:
    twtext = re.sub(r"(https?://t.co/[a-zA-Z0-9]*)", "<a href=\"\g<1>\">\g<1></a>", tw['text'])
    twtext = re.sub(r"@([a-zA-Z0-9\_]*)", "@<a href=\"http://twitter.com/\g<1>/with_replies\">\g<1></a>", twtext)
    twtext = re.sub(r"#([^\s]*)", "<a href=\"https://twitter.com/search?q=%23\g<1>\">#\g<1></a>", twtext)
    twuser = "<a href=\"http://twitter.com/" + tw['user']['screen_name'] + "/with_replies\">" + tw['user'][
        'screen_name'] + "</a>"
    twdate = datetime.datetime.strptime(tw['created_at'], '%a %b %d %H:%M:%S +0000 %Y') + datetime.timedelta(hours=9)
    twdate = "<a href=\"http://twitter.com/%s/status/%s\">%s</a>" % (
    tw['user']['screen_name'], tw['id_str'], twdate.strftime('%m/%d %H:%M:%S'))
    html_body += "<tr><td><img src=\"%s\"></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (tw['user']['profile_image_url'], twtext, twuser, twdate, tw['source'])
html_body = "<html><body><table>"+html_body+"</table></body></html>"

with open('index.html', mode='w', encoding='utf-8') as f:
    f.write(html_body)

for tw in deltweets:
    print(tw['text'], "||", tw['user']['screen_name'], "||", re.sub(r"<[^>]*?>", "", tw['source']))
print("-----------\n", len(dlist))
