# -*- coding: utf-8 -*-
import os, sys, re, requests
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
from soju6jan_common import BaseAddon

class RayStream(BaseAddon):
    def __init__(self):
        super(RayStream, self).__init__()

    def run(self):
        params = self.get_params()
        self.log(params)
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
            if item['cate'] == 'tv' and item['leauge'] == 'KM': continue
            ret.append(item)
        return ret

    def mode_play(self, params):
        if len(params['index']) == 2:
            video_url = 'https://kcdn.reystream.tv/fadostream%s/playlist.m3u8' % params['index']
            self.log("aaaaaaaaaaaaaaaaaaaaaaaa")
        elif len(params['index']) == 3:
            self.log("bbbbbbbbbbbbbbbbbbbbbbbbb")
            data = requests.get("https://reystream.tv/nbox/ncdn%s.php" % params['index'], headers={'referer' : 'https://reystream.tv/'}).text
            video_url = data.split("var videoSrc = '")[1].split("'")[0]
        else:
            self.addon_noti('notify to dev.')
            return
        self.log("11111111111111111")
        self.log(video_url)
        item = self.get_hls_item(video_url, headers={'referer':'https://reystream.tv/'})
        xbmcplugin.setResolvedUrl(self.HANDLE, True, item)


if __name__ == '__main__':
    RayStream().run()
