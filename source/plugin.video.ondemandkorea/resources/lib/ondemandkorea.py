# -*- coding: utf-8 -*-
"""
    ondemandkorea.com

    /includes/latest.php?cat=<name>
    /includes/episode_page.php?cat=<name>&id=<num>&page=<num>
"""
import re
import json
from bs4 import BeautifulSoup
import time
import random
import os

root_url = "https://www.ondemandkorea.com"
cat_json_url = root_url+"/includes15/categories/{genre:s}_{language:s}"
#mp4_url = "http://{hostname:s}.ondemandkorea.com/{genre:s}/{program:s}/{program:s}_{date:s}.{resolution:s}.{bitrate:s}.mp4"
img_base = "http://max.ondemandkorea.com/includes/timthumb.php?w=175&h=100&src="
# mimic iPad
default_hdr = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Connection': 'keep-alive'}

tablet_UA = 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Safari/535.19'

eplist_url = "/includes15/episode_page/{program:s}_{videoid:s}_ko_{page:d}"

bitrate2resolution = ['180p', '240p', '300p', '360p', '480p', '720p', '1080p']

############################################################################
# by soju6jan. 2021-03-07
############################################################################
import xbmc, xbmcaddon, requests, copy
mp4_url = "http://aws2.ondemandkorea.com/v1/{month}/{genre:s}/{program:s}/{program_code:s}_{date:s}_{resolution:s}.mp4"
default_hdr2 = copy.copy(default_hdr)
default_hdr2['Accept-Langauge'] = 'ko'
default_hdr2['Cookie'] = 'language=ko'

def log(msg):
    xbmc.log(msg='{msg}'.format(msg=msg), level=xbmc.LOGINFO)

def get_setting(key):
    return xbmcaddon.Addon().getSetting(key)

def get_proxies():
    proxy = get_setting('proxy_url')
    if proxy is None:
        return
    return {'http':proxy, 'https':proxy}

def get_response(url, headers_dict=None, referer=None):
    headers = default_hdr2 if get_setting('koPage')=='true' else default_hdr
    headers = copy.copy(headers)
    if referer:
        headers['Referer'] = referer
    if headers_dict:
        for key, value in headers_dict.items():
            headers[key] = value
    return requests.get(url, headers=headers, proxies=get_proxies())
############################################################################


def extract_time(item):
    try:
        # Also convert to int since update_time will be string.  When comparing
        # strings, "10" is smaller than "2".
        return int(item['latest'])
    except KeyError:
        return 0
		
def parseGenre(genre, koPage=True):
    ts = int(time.mktime(time.gmtime()) / 1000 / 60 / 5)
    lang = "ko" if koPage else "en"
    url = cat_json_url.format(genre=genre, language=lang, timestamp=ts)
    obj = get_response(url).json()
    items = []
    for item in obj:
        items.append({'title':item['title'], 'url':root_url+item['post_name'], 'thumbnail':item['poster_url'], 'latest':item['latest']})
    items.sort(key=extract_time, reverse=True)
    return items

def parseEpisodePage(page_url, page=1, koPage=True):
    html = get_response(page_url).text
    soup = BeautifulSoup(html)
    result = {'episode':[]}
    for node in soup.findAll('div', {'class':re.compile('^(?:ep|ep_last)$')}):
        if not node.b:
            continue
        title = node.b.string.replace('&amp;','&').replace('&lt;','<').replace('&gt;','>')
        thumb = node.find('img', {'title':True})['src']
        dt = node.b.findNextSibling(text=True)
        bdate = dt.string.split(':',1)[1].strip() if dt else ''
        result['episode'].append({'title':title, 'broad_date':bdate, 'url':root_url+node.a['href'], 'thumbnail':thumb})
    # no page navigation
    return result

def parseEpisodePage2(page_url, page=1, koPage=True):
    # 1. 
    #   $.getJSON( "/includes/episode_page.php", {cat: '<program>',id: <videoid>,page : pg)
    # 2. 
    #   "program" : "<program>",
    #   "videoid" : "<videoid>",
    html = get_response(page_url).text
    match = re.compile("odkEpisode.setPageDataUrl\('(.*?)'\);").search(html)
    eplist_url = match.group(1)
    eplist_url = eplist_url[:eplist_url.rfind("_")+1]
			
    list_url = root_url+eplist_url+str(page)
    obj = get_response(list_url, referer=page_url).json()
    result = {'episode':[]}
    for item in obj['list']:
        lairdate = item['on_air_date']
        result['episode'].append({'title':item['title'], 'broad_date':item['on_air_date'], 'root':root_url, 'url':item['url'], 'thumbnail':item["thumbnail"], 'videoid':item['url'], 'lairdate':item['on_air_date']})
    if obj['current_page'] > 1:
        result['prevpage'] = page-1
    if obj['current_page'] < obj['page_count']:
        result['nextpage'] = page+1
    return result


def guessVideoUrl(page_url, genre='drama', koPage=True):
    html = get_response(root_url+page_url, headers_dict={'User-Agent':tablet_UA}).text
    vid_title = re.compile('<p class="episode_title">(.*?)</p>', re.S).search(html).group(1).strip()
    thumb = re.compile('<meta property="og:image" content="([^"]*)"').search(html).group(1)
    program = '-'.join(page_url.replace('/', '').replace('.html', '').split('-')[:-1])
    program_code, date = re.compile("/([^/_]*)_(\d+)").search(thumb).group(1,2)
    videos = dict()
    for resolution in bitrate2resolution:
        vid_url = mp4_url.format(program=program, program_code=program_code, date=date, month=date[:6], resolution=resolution, genre=genre)
        videos[resolution] = {'url':vid_url}
    return {'title':vid_title, 'videos':videos}
