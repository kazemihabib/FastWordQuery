# -*- coding:utf-8 -*-
import os
import re

from bs4 import Tag

from ..base import *
from datetime import datetime
from aqt.sound import av_player


dizionario_italiano_base_url = u'https://www.dizionario-italiano.it/dizionario-italiano.php?parola={}100'
collins_base_url = u'https://www.collinsdictionary.com/dictionary/italian-english/{}'


@register([u'italian_pack', u'italian_pack'])
class ItalianPack(WebService):

    def __init__(self):
        super().__init__()

    def _dizionario_italiano_get_url(self):
        return dizionario_italiano_base_url.format(self.quote_word)

    def _collins_get_url(self):
        return collins_base_url.format(self.quote_word)

    def _get_from_api(self):
        dizionario_italiano_data = self.get_response(self._dizionario_italiano_get_url())
        collins_data = self.get_response(self._collins_get_url())
        DI_soup = parse_html(dizionario_italiano_data)
        collins_soup = parse_html(collins_data)
        try:
            result = {'DI_definizione': self.__ID_get_defs(DI_soup),
                      'DI_sillabe': self.__ID_get_sillabe(DI_soup, self.word),
                      'DI_lemma': self.__ID_get_lemma(DI_soup),
                      'DI_IPA': self.__ID_get_pronuncia(DI_soup),
                      'DI_grammatica': self.__ID_get_grammatica(DI_soup),
                      'DI_sound_url': self.__ID_get_sound_url(DI_soup),
                      'DI_table': self.__ID_get_table(DI_soup),
                      'DI_url': self._dizionario_italiano_get_url(),
                      'collins_url': self._collins_get_url(),
                      'collins_sound_url': self.__collins_get_sound_url(collins_soup),
                      'collins_IPA': self.__collins_get_IPA(collins_soup),
                      }
        except Exception as e:
            print('exception is ', e)
            result = {'DI_definizione': '',
                      'DI_sillabe': '',
                      'DI_lemma': '',
                      'DI_IPA': '',
                      'DI_grammatica': '',
                      'DI_sound_url': '',
                      'DI_table': '',
                      'DI_url': '',
                      'collins_url': '',
                      'collins_sound_url': '',
                      'collins_IPA': '',
                      }
        return self.cache_this(result)

    @export('IPA')
    def fld_IPA(self):
        seg = self._get_field('collins_IPA')
        if (not seg):
            seg = self._get_field('DI_IPA')
        return seg

    def __fld_mp3(self):
        audio_url = self._get_field('collins_sound_url')

        if(not audio_url):
            audio_url = self._get_field('DI_sound_url')
        if audio_url:
            filename = get_hex_name(self.unique.lower(), audio_url, 'mp3')
            if os.path.exists(filename) or self.net_download(filename, audio_url):
                av_player.play_file(filename)
                return self.get_anki_label(filename, 'audio')
        return ''

    @export('Sound')
    def fld_mp3(self):
        return self.__fld_mp3()

    @export('Italian Definition')
    def fld_definition(self):
        try:
            return '\n'.join(self._get_field('DI_definizione'))
        except Exception as e:
            return ""

    @export('Sillabe')
    def fld_sillabe(self):
        return str(self._get_field('DI_sillabe'))

    @export('Grammatica')
    def fld_grammatica(self):
        return ' '.join(self._get_field('DI_grammatica'))

    @export('table')
    def fld_table(self):
        return self._get_field('DI_table')

    def __ID_get_lemma(self, soup):
        try:
            lemma = soup.find('span', class_='lemma')
            if lemma is not None:
                # Getting only span text + removing white spaces at the end
                return lemma.find(text=True, recursive=False).rstrip()
        except Exception as e:
            return ""

    def __ID_get_sillabe(self, soup, word):
        try:
            lemma = soup.find(class_='lemma')
            small_list = lemma.find_all_next('small')
            for el in small_list:
                if el.parent not in lemma.children:
                    try:
                        sillabe = el.span.find(text=True, recursive=False)
                    except AttributeError:  # Word has no syllable division
                        return [word]
                    break

            split_indexes = [pos for pos,
                            char in enumerate(sillabe) if char == "|"]
            # necessario perchè le sillabazioni contengono gli accenti di pronuncia
            tmp = list(word)
            for i in split_indexes:
                tmp = tmp[0:i] + ["|"] + tmp[i:]
                sillabe = ''.join(tmp).split("|")
            return sillabe
        except Exception as e:
            return []

    def __ID_get_pronuncia(self, soup):
        try:
            pronuncia = soup.find('span', class_="paradigma")
            return pronuncia.text[10:]
        except Exception as e:
            return ""

    def __ID_get_grammatica(self, soup):
        try:
            gram = soup.find_all('span', class_="grammatica")
            return [x.text for x in gram]
        except:
            return []

    def __ID_generate_current_date(self):
        today = datetime.now()
        date = str(today.year) + str(today.month) + str(today.day)
        time = str(today.hour) + str(today.minute) + str(today.second)
        dateTime = date + time
        return dateTime

    def __ID_get_sound_url(self, soup):
        try:
            mp3_path = soup.find('span', class_="psPlay")['data-audio'].strip()
            sound_url = "https://www.dizionario-italiano.it/{0}&sc=1&d={1}".format(
                mp3_path, self.__ID_generate_current_date())
            print('data_audio', sound_url)
            return sound_url
        except Exception as e:
            return ""

    def __ID_get_table(self, soup):
        try:
            table = soup.find('div', {'class': ['section', 'group', 'sec-top']})
            return self._css(str(table))
        except Exception as e:
            return ""

    def __ID_get_defs(self, soup):
        try:
            defs = []
            for definitions in soup.find_all('span', class_='italiano'):
                children_content = ''
                for children in definitions.findChildren():
                    if children.string is None:
                        continue
                    try:
                        if children.attrs['class'][0] in ('esempi', 'autore'):
                            continue
                        else:
                            children_content += children.text
                            children_content += ' '
                            children.decompose()
                    except KeyError:
                        continue
                if children_content != '':
                    defs.append(
                        f"{children_content.upper()} -- {definitions.text.replace('()', '')}")
                else:
                    defs.append(definitions.text)
            if len(defs) == 0:
                raise exceptions.WordNotFoundError()
            return defs
        except Exception as e:
            return []
    
    def __collins_get_IPA(self, soup):
        try:
            table = soup.find('div', {'class': ['mini_h2', 'form']})
            pronunciation = table.find('span', {'class': ['pron']})
            return pronunciation.text
        except Exception as e:
            return ""

    def __collins_get_sound_url(self, soup):
        try:
            table = soup.find('div', {'class': ['mini_h2', 'form']})
            span = table.find('span', {'class': ['ptr', 'hwd_sound', 'type-hwd_sound']})
            sound_url = span.find('a', {'class': ['hwd_sound', 'sound audio_play_button', 'icon-volume-up', 'ptr']})
            return sound_url['data-src-mp3'].strip()
        except Exception as e:
            return ""

    # @with_styles(need_wrap_css=True, cssfile='_dizionario_italiano.css') //adding cssfile didn't work so I added the css for tables manually
    def _css(self, val):
        return ''' <style> 
/* Responsive tables */
.section {              /*  SECTIONS  */
	clear: both;
	padding: 0px;
	margin: 0px;
   padding-bottom:10px;
}

.col {                  /*  COLUMN SETUP  */
	display: block;
	float:left;
	margin: 1% 0 .5% .5%;
   padding: 0px;
}

.col2 {                  /*  COLUMN SETUP  */
	display: block;
	float:left;
	margin: 0px;
   padding: 0px;
}

.fir{
   display:none !important;
}

.sec{
   width:100%;
}

.col:first-child { margin-left: 0; }
.group:before,          /*  GROUPING  */
.group:after { content:""; display:table; }
.group:after { clear:both;}
.group { zoom:1; /* For IE 6/7 */ }

.span_title{width:20%;}
.span_2_of_2 {          /*  GRID OF TWO  */
	width: 30%;
}

.span_3_of_3 {          /*  GRID OF THREE  */
	width: 33.3%;
}

.span_1_of_2 {
	width: 49.2%;
}



.tb{
	width: 103.5%;
}

.bord-top{
   border-left: 1px solid #000099;
   border-bottom: 1px solid #000099;
   border-top: 1px solid #000099;
   border-top-left-radius: 6px !important;
}

.bord-masc{
   border-bottom: 1px solid #000099;
   border-top: 1px solid #000099;
}

.bord-femm{
   border-right: 1px solid #000099;
   border-bottom: 1px solid #000099;
   border-top: 1px solid #000099;
   border-top-right-radius: 6px !important;
   width:100% !important;
}

@media only screen and (max-width: 700px) {
	.col {
		margin: 1% 0 1% 0%;
	}

	.span_2_of_2, .span_1_of_2 , .span_3_of_3 { width: 100%; }
   .blocklist{
      width:90%;
      margin: 10px !important;
   }
   .fir{
      display:block !important;
      width:40%;
   }
   
   .sec{
      width:60%;
   }
   
   .sec-top{
      padding-top:20px;
   }
   
   .span_title{display:none;}
   
   .tb{
		width: 100%;
   }
	
   .bord-top{
      border-left: 1px solid #000099;
      border-top: 1px solid #000099;
      border-top-left-radius: 0px !important;
   }
   
   .bord-masc{
      border-top: 1px solid #000099;
      border-bottom: 0px;
      border-right: 1px solid #000099;
      border-left: 1px solid #000099;
      border-top-right-radius: 7px !important;
      border-top-left-radius: 7px !important;
      width:98% !important;
   }
   
   .bord-femm{
      border-right: 1px solid #000099;
      border-bottom: 1px solid #000099;
      border-top: 1px solid #000099;
      border-left: 1px solid #000099;
      border-top-right-radius: 0px !important;
      width:98% !important;
   }
}
</style>''' + val
