#!/usr/bin/python
# -*- coding: utf8 -*-
# uk_UA

from openerp.addons.report_aeroo.ctt_objects import ctt_language

class uk_UA(ctt_language):
    def _init_lang(self):
        # language name
        self.name = 'uk_UA'
        # digits - masculine, singular
        self.number_sng_msc = [u'ноль', u'один', u'два', u'три', u'чотири',
                               u'п\'ять', u'шість', u'сім', u'вісім',
                               u'дев\'ять']
        # tens - masculine, singular
        self.number_sng_fem = [u'ноль', u'одна', u'дві', u'три', u'чотири', 
                               u'п\'ять', u'шість', u'сім', u'вісім',
                               u'дев\'ять']
        # tens - masculine, plural
        self.number_plr_msc = [u'', u'один', u'двa', u'три', u'четыре', u'пять',
                               u'шесть', u'семь', u'восемь', u'девять']
        # teens - masculine
        self.number_teens = [u'десять', u'одинадцять', u'дванадцять',
                             u'тринадцять', u'чотирнадцять', u'п\'ятнадцять',
                             u'шістнадцять', u'сімнадцять', u'вісімнадцять',
                             u'дев\'ятнадцять']
        # multiplier - masculine, singular                      
        self.multi_sng_msc = [u'стo', u' тисяча', u' мiллiон', u' мiллiард']
        # multiplier - masculine, plural
        self.multi_plr_msc = [u'сoт', u' тисяч', u' мiллiонiв', u' мiллiардов']
        
        # next line is needed for correct loading of currencies 
        import currencies
        return currencies


    def wordify(self, chunk, chunknr, gender):
        if gender == 'm':
            number = self.number_sng_msc
        elif gender == 'f':
            number = self.number_sng_fem
        elif gender == 'n':
            number = self.number_sng_neu
        words = u''
        digit1 = u''
        digit2 = u''
        digit3 = u''
        chunklength = len(chunk)
        # placing digits in right places
        if chunklength == 1:
            digit3 = chunk[0 : 1]
        if chunklength == 2:
            digit2 = chunk[0 : 1]
            digit3 = chunk[1 : 2]
        if chunklength == 3:
            digit1 = chunk[0 : 1]
            digit2 = chunk[1 : 2]
            digit3 = chunk[-1]
        # processing zero
        if chunklength == 1 and digit3  == '0' :
            return number[0]
        # processing hundreds
        if chunklength == 3 :
            if int(digit1) == 1 :
                words += self.multi_sng_msc[0]
            elif int(digit1) == 2 :
                words += u'двісті'
            elif int(digit1) == 3 :
                words += u'триста'
            elif int(digit1) == 4 :
                words += u'чотириста'
            elif int(digit1) >= 5 :
                words += self.number_sng_msc[int(digit1)] + self.multi_plr_msc[0]
        # processing tens
        if chunklength > 1:
            spacer = ''
            if len(words) > 0 : spacer = ' '
            if digit2 == '1':
                words += spacer + self.number_teens[int(digit3)]
            else:
		        if int(digit2) > 1 and int(digit2) < 4:
		            words += spacer + skaitlix[int(digit2)] + u'дцять'
		        elif digit2 == '4':
		            words += spacer + u'сорок'
		        elif int(digit2) >= 5 and int(digit2) != 9:
		            words += spacer + skaitlix[int(digit2)] + u'десят'
		        elif digit2 == '9':
		            words += spacer + u'дев\'яносто'

        # processing ones
        if chunklength > 0 and digit2 != '1' :
            spacer = ''
            if len(words) > 0: spacer = u' '
            if chunknr == 1:
                if int(digit3) == 1 or int(digit3) == 2:
                    words += spacer + self.number_sng_fem[int(digit3)]
                elif int(digit3) >= 3 and int(digit3) != 0: 
                    words += spacer + self.number_sng_msc[int(digit3)]
            else:
                if int(digit3) > 0: words += spacer + self.number_sng_msc[int(digit3)]
        # end processing
        if len(words) > 0 :
            if digit3 == '1' and chunknr > 0:
                return words + self.multi_sng_msc[chunknr]
            elif digit3 != '1' and chunknr > 0:
                return words + self.multi_plr_msc[chunknr]
            else:
                return words
        else:
            return ''

uk_UA()
