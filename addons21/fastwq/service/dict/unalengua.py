# -*- coding:utf-8 -*-
import requests
from urllib import request, parse
import urllib
import json
from ..base import *


base_url = u'https://api2.unalengua.com/ipav3'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36 Edge/15.15063',
    'Content-Type': 'application/json'
}

@register([u'unalengua-ipa-it', u'unalengua-ipa-it'])
class Unalengua(WebService):


    def __init__(self):
        super().__init__()

    def _get_from_api(self):
        payload = {'text': self.word, # do not use quote_word it will cause encoding problems in this api
                   'lang': 'it-IT',
                   'mode': False}

        try:
            response = requests.post(
                base_url, json=payload, headers=headers)
            
            result = response.json() 
        except Exception as e:
            print('exception is ', e)

            result = self._empty_response()
        return self.cache_this(result)

    def _empty_response(self):
        return {'detected': '', 'ipa': '',
                'lang': '', 'spelling': False}

    @export('IPA')
    def fld_IPA(self):
        seg = self._get_field('ipa')
        return seg 
