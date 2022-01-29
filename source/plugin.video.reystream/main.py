# -*- coding: utf-8 -*-
import os, sys, xbmcaddon, re, requests
sys.path.append(os.path.join( xbmc.translatePath( xbmcaddon.Addon().getAddonInfo('path') ), 'resources', 'lib' ))
from addon_base import *

class RayStream(AddonBase):
    def __init__(self):
        super(RayStream, self).__init__()

    def run(self):
        params = self.get_params()
        mode = 'list'
        if 'mode' in params:
            mode = params['mode']
        if mode == 'list': self.mode_list()
        elif mode == 'play': self.mode_play(params)
    
    def mode_list(self):
        items = self.get_items()
        for item in items:
            title = u'[{}-{}] {}'.format(item['cate'], item['leauge'], item['title'])
            infoLabels = {"mediatype":"episode","label":title ,"title":title,"plot":title}
            del item['title']
            self.make_item(title, 'play', param=item, infoLabels=infoLabels, isFolder=False)
        xbmcplugin.endOfDirectory(self.HANDLE)

    def get_items(self):
        data = requests.get('https://tv.cooltv111.com/tv/cooltv/index.php').text
        tmps = data.split('not_onair_channels.png')[0].split("<tr class='cate_")
        ret = []
        regex  = [re.compile(r'<td>(?P<leauge>[\w\s]+)</td>', re.MULTILINE), re.compile(r"load_video\((?P<data>\d+,'1',.*?)\);", re.MULTILINE)]
        for tmp in tmps[1:]:
            if tmp.find(u'문자중계') != -1: continue
            if tmp.find(u'방송전') != -1: continue
            item = {'cate' : tmp.split("'")[0], 'leauge' : regex[0].search(tmp).group('leauge')}
            item['index'], d, item['title'], t = regex[1].search(tmp).group('data').split(',')
            item['title'] = re.sub('\(\d+\)', '', item['title'].replace("'", '').replace('	', ' ')).strip()
            ret.append(item)
        return ret

    def mode_play(self, params):
        if len(params['index']) == 2:
            video_url = 'https://kcdn.reystream.tv/fadostream%s/playlist.m3u8' % params['index']
        elif len(params['index']) == 3:
            data = requests.get("https://reystream.tv/nbox/ncdn%s.php" % params['index'], headers={'referer' : 'https://tv.cooltv111.com/'}).text
            video_url = data.split("var videoSrc = '")[1].split("'")[0]
        else:
            self.addon_noti('notify to dev.')
            return
        item = self.get_hls_item(video_url, headers='referer=https://reystream.tv/')
        xbmcplugin.setResolvedUrl(self.HANDLE, True, item)


if __name__ == '__main__':
    RayStream().run()
