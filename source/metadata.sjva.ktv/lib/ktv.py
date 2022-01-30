#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import os,sys,re, json, traceback
import urllib
import requests
from .base import MetadataBase, log, ADDON, ID, HANDLE, parse_qsl, urlencode

class MetadataKtv(MetadataBase):
    def __init__(self):
        self.module_name = 'ktv'

    def run(self):
        try:
            params=self.get_params()
            settings = None
            if 'pathSettings' in params:
                settings = json.loads(params['pathSettings'])
            if 'action' in params:
                action = params["action"]
                log('KTV PARAM : %s' % params)
                if action == 'find' and 'title' in params:
                    self.find(params["title"], params.get("year", None), settings)
                elif action == 'getdetails' and 'url' in params:
                    self.getdetails(params["url"], settings)
                elif action == 'getepisodelist' and 'url' in params:
                    self.getepisodelist(params["url"], settings)
                elif action == 'getepisodedetails' and 'url' in params:
                    self.getepisodedetails(params["url"], settings)
                elif action == 'getartwork' and 'id' in params:
                    self.getartwork(params["id"], settings)
            xbmcplugin.endOfDirectory(HANDLE)
        except Exception as e:
            log('Exception : %s' % str(e))
            log(traceback.format_exc())
    
    ################################################################################

    def find(self, title, year, settings):
        search_results = self.send_search(self.module_name, title, year, True, settings)
        #log(json.dumps(search_results, indent=4))
        if self.module_name == 'ktv':
            self.process_find_ktv(search_results)
    
    def process_find_ktv(self, search_results):
        if 'daum' in search_results:
            data = search_results['daum']
            title = '%s (%s)' % (data['title'], data['year']) if data['year'] != '' else data['title']
            title += ' - ' + data['extra_info']
            listitem = xbmcgui.ListItem(title, offscreen=True)
            if data['image_url'] != '':
                listitem.setArt({'thumb': data['image_url']})
            listitem.setProperty('relevance', '1')
            url = u'{code}|{title}'
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=url.format(title=data['title'], code=data['code']), listitem=listitem, isFolder=True)
        
            for index, series in enumerate(data['series'][1:]):
                title = '%s (%s)' % (series['title'], series['year']) if series['year'] != '' else series['title']
                listitem = xbmcgui.ListItem(title, offscreen=True)
                xbmcplugin.addDirectoryItem(handle=HANDLE, url=url.format(title=series['title'], code=series['code']), listitem=listitem, isFolder=True)
            
        tmp_list = []
        if 'wavve' in search_results and len(search_results['wavve']) > 0:
            tmp_list += search_results['wavve']
        if 'tving' in search_results and len(search_results['tving']) > 0:
            tmp_list += search_results['tving']
        
        if tmp_list:
            tmp_list = sorted(tmp_list, key=lambda k: k['score'], reverse=True)
            for item in tmp_list:
                info = {'title': item['title']}
                movie_label = '%s / %s' % (item['title'], item['site'])
                listitem = xbmcgui.ListItem(movie_label, offscreen=True)
                listitem.setInfo('video', info)
                if item['image_url'] != '':
                    listitem.setArt({'thumb': item['image_url']})
                xbmcplugin.addDirectoryItem(handle=HANDLE, url=item['code'], listitem=listitem, isFolder=True)


    def get_info(self, url, settings):
        tmp = url.split('|')
        if len(tmp) == 2:
            code = tmp[0]
            title = tmp[1]
        else:
            code = url
            title = None
        return self.send_info(self.module_name, code, settings, title=title)


    def getdetails(self, url, settings):
        details = self.get_info(url, settings)
        #log(json.dumps(details, indent=4))
        listitem = xbmcgui.ListItem(details['title'], offscreen=True)
        details['info']['episodeguide'] = url
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


    def getepisodelist(self, url, settings):
        details = self.get_info(url, settings)
        #log(json.dumps(details, indent=4))
        data = details['extra_info']['episodes']
        for key, value in data.items():
            info = {'season':1, 'episode':int(key)}
            if 'daum' in value:
                info['aired'] = value['daum']['premiered']
                param = value['daum']['code']
            elif 'tving' in value:
                info['aired'] = value['tving']['premiered']
                param = '%s|%s|%s|%s' % (value['tving']['code'], key, value['tving']['thumb'], value['tving']['plot'])
            elif 'wavve' in value:
                info['aired'] = value['wavve']['premiered']
                param = '%s|%s|%s|%s|%s' % (value['wavve']['code'], key, value['wavve']['thumb'], value['wavve']['title'], value['wavve']['plot'])
            listitem = xbmcgui.ListItem('', offscreen=True)
            listitem.setInfo('video', info)
            xbmcplugin.addDirectoryItem(handle=HANDLE, url=param, listitem=listitem, isFolder=False)


    def getepisodedetails(self, param, settings):
        info = {'title':''}
        thumb = None
        if param.upper().startswith('KD'):
            data = self.send_episode_info(self.module_name, 'KD'+param[2:], settings)
            info['plot'] = data['plot']
            info['episode'] = data['episode']
            info['title'] = data['title']
            if 'thumb' in data and len(data['thumb']) > 0:
                thumb = data['thumb'][0]['value']
        elif param.upper().startswith('KW'):
            code, episode, thumb, info['title'], info['plot']  = param.split('|')
            info['episode'] = int(episode)
        elif param.upper().startswith('KV'):
            code, episode, thumb, info['plot']  = param.split('|')
            info['episode'] = int(episode)
        listitem = xbmcgui.ListItem(info['title'], offscreen=True)
        listitem.setInfo('video', info)
        if thumb is not None:
            listitem.addAvailableArtwork(thumb, "thumb")
        xbmcplugin.setResolvedUrl(handle=HANDLE, succeeded=True, listitem=listitem)

    def getartwork(self, param, settings):
        log(param)
