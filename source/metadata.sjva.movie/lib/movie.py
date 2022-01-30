#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import os,sys,re, json, traceback, urllib, requests
from .base import MetadataBase, log, ADDON, ID, HANDLE, parse_qsl, urlencode

class MetadataMovie(MetadataBase):
    def __init__(self, module_name):
        self.module_name = module_name
    
    def run(self):
        try:
            params=self.get_params()
            settings = None
            if 'pathSettings' in params:
                settings = json.loads(params['pathSettings'])
            if 'action' in params:
                action = params['action']
                if action == 'find' and 'title' in params:
                    self.find(params["title"], params.get('year', None), settings)
                elif action == 'getdetails' and 'url' in params:
                    self.getdetails(params['url'], settings)
                elif action == 'play' and 'code' in params:
                    self.play(params['code'], settings)
                elif action == 'play_gds':
                    self.play_gds(params['type'], params['id'])
            xbmcplugin.endOfDirectory(HANDLE)
        except Exception as e:
            log('Exception : %s' % str(e))
            log(traceback.format_exc())

    def find(self, title, year, settings):
        search_results = self.send_search(self.module_name, title, year, True, settings)
        for movie in search_results:
            movie_info = {'title': movie['title'], 'year':movie['year']}
            movie_label = movie['title']
            movie_label += ' ({}) / {}'.format(movie['year'], movie['site'])
            listitem = xbmcgui.ListItem(movie_label, offscreen=True)
            listitem.setInfo('video', movie_info)
            if movie['image_url'] != '':
                listitem.setArt({'thumb': movie['image_url']})
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=movie['code'], listitem=listitem, isFolder=True)

    def getdetails(self, code, settings):
        details = self.send_info(self.module_name, code, settings)
        listitem = xbmcgui.ListItem(details['title'], offscreen=True)
        listitem.setInfo('video', details['info'])
        listitem.setCast(details['cast'])
        listitem.setUniqueIDs(details['code'], 'sjva')
        fanart = []
        for art in details['art']:
            if art['aspect'] == 'fanart':
                fanart.append({'image':art['value'], 'preview':art['thumb'] if 'thumb' in art else ''})
            else:
                listitem.addAvailableArtwork(art['value'], art['aspect'])
        listitem.setAvailableFanart(fanart)
        if 'ratings' in details and details['ratings'] is not None:
            for item in details['ratings']:
                listitem.setRating(item['name'], item['value'])
        xbmcplugin.setResolvedUrl(handle=HANDLE, succeeded=True, listitem=listitem)

    ################################################################################
    def play(self, code, settings):
        data = self.get_stream_info(self.module_name, code, settings)
        if 'wavve_url' in data:
            wavve_data = requests.get(data['wavve_url'].replace('authtype=url', 'authtype=cookie')).json()
            if 'drmhost' in wavve_data['drm']:
                ret = {}
                ret['uri'] = wavve_data['playurl'] + '|Cookie=' + wavve_data['awscookie'] 
                ret['drm_scheme'] = 'widevine'
                ret['drm_license_uri'] = wavve_data['drm']['drmhost']
                ret['drm_key_request_properties'] = {
                    'origin' : 'https://www.wavve.com',
                    'sec-fetch-site' : 'same-site',
                    'sec-fetch-mode' : 'cors',
                    'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36',
                    'referer' : 'https://www.wavve.com/',
                    'pallycon-customdata' : wavve_data['drm']['customdata'],
                    'cookie' : wavve_data['awscookie'],
                    'content-type' : 'application/octet-stream',
                }
                data = ret
            else:
                wavve_data = requests.get(data['wavve_url'].replace('action=dash', 'action=hls')).json()
                log(json.dumps(wavve_data, indent=4))
                data = {'hls':wavve_data['playurl']}

        if 'hls' in data:
            listitem = xbmcgui.ListItem(path=data['hls'])
            listitem.setProperty('inputstream', 'inputstream.adaptive')
            listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        else:
            listitem = xbmcgui.ListItem (path=data['uri'])
            listitem.setContentLookup(False)
            listitem.setMimeType('application/xml+dash')
            if sys.version_info[0] == 2:
                import inputstreamhelper
                listitem.setProperty('inputstreamaddon', inputstreamhelper.Helper('mpd', drm='widevine').inputstream_addon)
            else:
                listitem.setProperty('inputstream', 'inputstream.adaptive')
            listitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
            listitem.setProperty('inputstream.adaptive.license_key', data['drm_license_uri'] + '|' + urlencode(data['drm_key_request_properties']) + '|R{SSM}|' )
            if 'cookie' in data['drm_key_request_properties']:
                listitem.setProperty('inputstream.adaptive.stream_headers', 'user-agent=%s&Cookie=%s' % (data['drm_key_request_properties']['user-agent'], data['drm_key_request_properties']['cookie']))
            else:
                listitem.setProperty('inputstream.adaptive.stream_headers', 'user-agent=%s' % (data['drm_key_request_properties']['user-agent']))
        xbmcplugin.setResolvedUrl(handle=HANDLE, succeeded=True, listitem=listitem)


    def play_gds(self, content_type, content_id):
        settings = self.get_settings()
        url = 'https://sjva.me/sjva/gds.php?action=play&type=%s&id=%s&call=kodi&user_id=%s&user_apikey=%s' % (content_type, content_id, settings['sjva_me_id'], settings['sjva_apikey'])
        data = requests.get(url).json()
        if data['ret'] == 'success':
            listitem = xbmcgui.ListItem(path=data['data']['video_url'])
            if data['data']['sub_url']:
                listitem.setSubtitles(data['data']['sub_url'])
            xbmcplugin.setResolvedUrl(handle=HANDLE, succeeded=True, listitem=listitem)
    
    