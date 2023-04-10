# -*- coding:utf-8 -*-
import os
import re

from bs4 import Tag

from ..base import *
from datetime import datetime
from aqt.sound import av_player


collins_base_url = u'https://www.collinsdictionary.com/dictionary/italian-english/{}'


@register([u'collins', u'collins'])
class Collins(WebService):

    def __init__(self):
        super().__init__()

    def _get_url(self):
        return collins_base_url.format(self.quote_word)

    def _get_from_api(self):
        data = self.get_response(self._get_url())
        soup = parse_html(data)
        print(str(soup))
        result = {'pronuncia': self.__get_pronunciation(soup), 'sound_url': self.__get_sound(soup)}
        return self.cache_this(result)

    @export('IPA')
    def fld_IPA(self):
        seg = self._get_field('pronuncia')
        return seg

    def __fld_mp3(self):
        audio_url = self._get_field('sound_url')
        if audio_url:
            filename = get_hex_name(self.unique.lower(), audio_url, 'mp3')
            if os.path.exists(filename) or self.net_download(filename, audio_url):
                av_player.play_file(filename)
                return self.get_anki_label(filename, 'audio')
        return ''

    @export('Sound')
    def fld_mp3(self):
        return self.__fld_mp3()


    def __get_pronunciation(self, soup):
        table = soup.find('div', {'class': ['mini_h2', 'form']})
        pronunciation = table.find('span', {'class': ['pron']})
        return pronunciation.text

    def __get_sound(self, soup):
        table = soup.find('div', {'class': ['mini_h2', 'form']})
        span = table.find('span', {'class': ['ptr', 'hwd_sound', 'type-hwd_sound']})
        sound_url = span.find('a', {'class': ['hwd_sound', 'sound audio_play_button', 'icon-volume-up', 'ptr']})
        return sound_url['data-src-mp3'].strip()
