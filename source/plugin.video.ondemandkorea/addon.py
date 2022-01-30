# -*- coding: utf-8 -*-
"""
    Ondemand Korea
"""
from xbmcswift2 import Plugin
import os

plugin = Plugin()
_L = plugin.get_string

plugin_path = plugin.addon.getAddonInfo('path')
lib_path = os.path.join(plugin_path, 'resources', 'lib')
sys.path.append(lib_path)

import ondemandkorea as scraper

tPrevPage = u"[B]<<이전 페이지[/B]"
tNextPage = u"[B]다음 페이지>>[/B]"

root_url = "http://www.ondemandkorea.com"

quality_tbl = ['180p', '240p', '300p', '360p', '480p', '720p', '1080p']

@plugin.route('/')
def main_menu():
    items = [
        {'label':u'드라마', 'path':plugin.url_for('genre_view', genre='drama')},
        {'label':u'예능/오락', 'path':plugin.url_for('genre_view', genre='variety')},
        {'label':u'시사/다큐', 'path':plugin.url_for('genre_view', genre='documentary')},
        {'label':u'뉴스', 'path':plugin.url_for('genre_view', genre='korean-news')},
        {'label':u'라이프', 'path':plugin.url_for('genre_view', genre='life')},
        {'label':u'키즈', 'path':plugin.url_for('genre_view', genre='kids')},
        {'label':u'스포츠', 'path':plugin.url_for('genre_view', genre='sports')},
        {'label':u'홈쇼핑', 'path':plugin.url_for('genre_view', genre='home-shopping')},
        {'label':u'교육', 'path':plugin.url_for('genre_view', genre='education')},
        {'label':u'종교', 'path':plugin.url_for('genre_view', genre='religion')},
    ]
    return items

@plugin.route('/genre/<genre>/')
def genre_view(genre):
    plugin.log.debug(genre)
    koPage = plugin.get_setting('koPage', bool)
    info = scraper.parseGenre(genre, koPage=koPage)
    items = [{'label':item['title'], 'path':plugin.url_for('episode_view', url=item['url'], page=1, genre=genre), 'thumbnail':item['thumbnail']} for item in info]
    return plugin.finish(items, view_mode='thumbnail')

@plugin.route('/episode/<genre>/<page>/<url>')
def episode_view(url, page, genre):
    plugin.log.debug(url)
    koPage = plugin.get_setting('koPage', bool)
    info = scraper.parseEpisodePage2(url, page=int(page), koPage=koPage)
    items = [{'label':item['title'], 'label2':item['broad_date'], 'path':plugin.url_for('play_episode', root=item['root'], url=item['url'], videoid=item['videoid'], genre=genre, airdate=item['broad_date']), 'thumbnail':item['thumbnail']} for item in info['episode']]
    # navigation
    if 'prevpage' in info:
        items.append({'label':tPrevPage, 'path':plugin.url_for('episode_view', url=url, page=info['prevpage'], genre=genre)})
    if 'nextpage' in info:
        items.append({'label':tNextPage, 'path':plugin.url_for('episode_view', url=url, page=info['nextpage'], genre=genre)})
    return plugin.finish(items, update_listing=False)

@plugin.route('/play/<genre>/<root>/<url>/<videoid>/<airdate>/')
def play_episode(root, url, videoid, genre, airdate):
    global quality_tbl
    plugin.log.debug(url)
    resolution = quality_tbl[ plugin.get_setting('quality', int) ]
    use_mp4_url = plugin.get_setting('mp4_url', bool)

    if use_mp4_url:
        info = scraper.guessVideoUrl(url, genre=genre)
        plugin.log.info("use guessed url")
    else:
        info = scraper.extractStreamUrl(root, url, videoid, airdate, referer=root_url+"/"+url)

    plugin.log.debug("resolution: "+resolution)
    avail_resolutions = info['videos'].keys()
    if not resolution in avail_resolutions:
        resolution = avail_resolutions[0]
    video = info['videos'][resolution]

    plugin.play_video( {'label':info['title'], 'path':video['url']} )

    return plugin.finish(None, succeeded=False)

if __name__ == "__main__":
    plugin.run()

# vim:sw=4:sts=4:et
