#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import os, sys, re, json, traceback
import urllib
import requests

try:
    from urlparse import parse_qsl
    from urllib import urlencode
    from urllib import quote
except ImportError: # py2 / py3
    from urllib.parse import parse_qsl
    from urllib.parse import urlencode
    from urllib.parse import quote

ADDON = xbmcaddon.Addon()
ID = ADDON.getAddonInfo('id')
HANDLE = int(sys.argv[1])

def log(msg):
    xbmc.log(msg='{addon}: {msg}'.format(addon=ID, msg=msg), level=xbmc.LOGINFO)

class MetadataBase(object):
    def get_params(self):
        if not sys.argv[2]:
            return {}
        return dict(parse_qsl(sys.argv[2].lstrip('?')))

    def send_search(self, module_name, keyword, year, manual, settings):
        url = '{ddns}/metadata/api/{module_name}/search?keyword={keyword}&manual={manual}&year={year}&call=kodi&apikey={apikey}'.format(
            ddns=settings['sjva_url'], 
            module_name=module_name, 
            keyword=keyword, 
            manual=manual, 
            year=year, 
            apikey=settings['sjva_apikey']
        )
        log(url)
        return requests.get(url).json()

    def send_info(self, module_name, code, settings, title=None):
        url = '{ddns}/metadata/api/{module_name}/info?code={code}&call=kodi&apikey={apikey}'.format(
            ddns=settings['sjva_url'], 
            module_name=module_name, 
            code=code, 
            apikey=settings['sjva_apikey']
        )
        if title is not None:
            url += '&title=' + title
        log(url)
        return requests.get(url, timeout=30000).json()

    def send_episode_info(self, module_name, code, settings):
        url = '{ddns}/metadata/api/{module_name}/episode_info?code={code}&call=kodi&apikey={apikey}'.format(
            ddns=settings['sjva_url'],
            module_name=module_name,
            code=quote(code),
            apikey=settings['sjva_apikey']
        )
        log(url)
        return requests.get(url, timeout=10000).json()

    def get_stream_info(self, module_name, code, settings):
        if settings is None:
            settings = {}
            filename = xbmc.translatePath(os.path.join(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')), 'settings.xml'))
            import xml.etree.ElementTree as ET
            root = ET.parse(filename).getroot()
            tags = root.findall('setting')
            for tag in tags:
                log(tag.attrib)
                settings[tag.attrib['id']] = tag.text

        url = '{ddns}/metadata/api/{module_name}/stream?code={code}&call=kodi&apikey={apikey}'.format(
            ddns=settings['sjva_url'],
            module_name=module_name,
            code=code,
            apikey=settings['sjva_apikey']
        )
        log(url)
        return requests.get(url, timeout=10000).json()
