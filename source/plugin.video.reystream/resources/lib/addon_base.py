# -*- coding: utf-8 -*-
import os, sys, traceback, urllib
import xbmc, xbmcplugin, xbmcgui, xbmcaddon

try:
    is_py3 = False
    from urlparse import parse_qsl
    from urllib import urlencode
    from urllib import quote
except ImportError:
    is_py3 = True
    from urllib.parse import parse_qsl
    from urllib.parse import urlencode
    from urllib.parse import quote


class AddonBase(object):
    def __init__(self):
        self.ADDON = xbmcaddon.Addon()
        self.ID = self.ADDON.getAddonInfo('id')
        self.HANDLE = int(sys.argv[1])

    def get_params(self):
        if not sys.argv[2]:
            return {}
        return dict(parse_qsl(sys.argv[2].lstrip('?')))
    
    def log(self, msg):
        xbmc.log(msg='{addon}: {msg}'.format(addon=self.ID, msg=msg), level=xbmc.LOGINFO)

    def make_item(self, title, mode, param=None, img=None, infoLabels=None, isFolder=True):
        if param is None:
            param = {}
        param['mode'] = mode
        url = '%s?%s' % (sys.argv[0], urlencode(param))
        #listitem = xbmcgui.ListItem(title, thumbnailImage=img)
        listitem = xbmcgui.ListItem(title)
        if infoLabels: 
            listitem.setInfo(type="Video", infoLabels=infoLabels)
        if not isFolder: 
            listitem.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(self.HANDLE, url, listitem, isFolder)

    def addon_noti(self, msg):
        try:
            dialog = xbmcgui.Dialog()
            dialog.notification(self.ADDON.getAddonInfo('name'), msg)
        except Exception as e:
            self.log('Exception : %s' % str(e))
            self.log(traceback.format_exc())
    
    def get_hls_item(self, url, headers=None):
        if is_py3:
            item = xbmcgui.ListItem(path=url)
            item.setProperty('inputstream', 'inputstream.adaptive')
            item.setProperty('inputstream.adaptive.manifest_type', 'hls')
            if headers is not None:
                item.setProperty('inputstream.adaptive.stream_headers', 'referer=https://reystream.tv/')
            return item
        else:
            if headers is not None:
                url += '|' + headers
            return xbmcgui.ListItem(path=url)


