#!/usr/bin/python
# -*- coding: utf8 -*-
# lv_LV

from openerp.addons.report_aeroo.ctt_objects import ctt_language

class lv_LV(ctt_language):
    def _init_lang(self):
        self.name = 'lv_LV'
        # digits - masculine, singular
        self.number_sng_msc = [u'nulle', u'viens', u'divi',
                               u'trīs', u'četri', u'pieci',
                               u'seši', u'septiņi', u'astoņi',
                               u'deviņi']
        # digits - feminine, singular
        self.number_sng_fem = [u'nulle', u'viena', u'divas',
                               u'trīs', u'četras', u'piecas',
                               u'sešas', u'septiņas', u'astoņas',
                               u'deviņas']
        # tens - masculine, singular
        self.tens_sng_msc = [u'nulle', u'vien', u'div',
                             u'trīs', u'četr', u'piec',
                             u'seš', u'septiņ', u'astoņ',
                             u'deviņ']
        # teens - masculine
        self.teens = [u'desmit', u'vienpadsmit', u'divpadsmit',
                      u'trīspadsmit', u'četrpadsmit', u'piecpadsmit',
                      u'sešpadsmit', u'septiņpadsmit', u'astoņpadsmit',
                      u'deviņpadsmit']
        # multiplier - masculine, singular                      
        self.multi_sng_msc = [u'simts', u' tūkstotis', u' miljons',
                              u' miljards']
        # multiplier - masculine, plural
        self.multi_plr_msc = [u' simti', u' tūkstoši', u' miljoni',
                              u' miljardi']
        
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
            if digit1 == '1' :
                words += self.multi_sng_msc[0]
            else :
                if int(digit1) > 1 : words += number[int(digit1)] + \
                                                self.multi_plr_msc[0]
        # processing tens
        if chunklength > 1:
            spacer = ''
            if len(words) > 0 : spacer = ' '
            if digit2 == '1':
                words += spacer + self.teens[int(digit3)]
            else:
                if int(digit2) > 1 and int(digit2) > 0:
                    words += spacer + self.tens_sng_msc[int(digit2)] + u'desmit'

        # processing ones
        if chunklength > 0 and digit2 != '1' :
            spacer = ''
            if len(words) > 0: spacer = u' '
            if int(digit3) > 0:
                words += spacer + number[int(digit3)]
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

lv_LV()
