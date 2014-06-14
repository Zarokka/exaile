# Copyright (C) 2014 Rocco Aliberti
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

try:
    import lxml.html
except ImportError:
    lxml = None

import re
import urllib

from xl.lyrics import (
    LyricSearchMethod,
    LyricsNotFoundException
)
from xl import providers

def enable(exaile):
    """
        Enables the lyrics mania plugin that fetches track lyrics
        from lyricsmania.com
    """
    if lxml:
        providers.register('lyrics', LyricsMania())
    else:
        raise NotImplementedError('LXML is not available.')
        return False

def disable(exaile):
    providers.unregister('lyrics', providers.get_provider('lyrics',
        'lyricsmania'))

class LyricsMania(LyricSearchMethod):

    name= "lyricsmania"
    display_name = "Lyrics Mania"

    def find_lyrics(self, track):
        try:
            (artist, title) = track.get_tag_raw('artist')[0].encode("utf-8"), \
                track.get_tag_raw('title')[0].encode("utf-8")
        except TypeError:
            raise LyricsNotFoundException

        if not artist or not title:
            raise LyricsNotFoundException

        artist = artist.replace(' ','_').replace('\'','')
        title = title.replace(' ','_').replace('\'','')

        url = 'http://www.lyricsmania.com/%s_lyrics_%s.html' % (title, artist)

        try:
            html = urllib.urlopen(url).read()
        except:
            raise LyricsNotFoundException

        try:
            lyrics_html = lxml.html.fromstring(html)
        except lxml.etree.XMLSyntaxError:
            raise LyricsNotFoundException

        try:
            lyrics_body = lyrics_html.find_class('lyrics-body')[0]
            lyrics_body.remove(lyrics_body.get_element_by_id('video-musictory'))
            lyrics = re.sub('^\s+Lyrics to .+', '', lyrics_body.text_content())
        except :
            raise LyricsNotFoundException

        return (lyrics, self.name, url)