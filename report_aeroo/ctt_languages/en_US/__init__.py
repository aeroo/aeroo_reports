#!/usr/bin/python
# -*- coding: utf8 -*-
# en_US

from openerp.addons.report_aeroo.ctt_objects import ctt_language

class en_US(ctt_language):
    def _init_lang(self):
        # language name
        self.name = 'en_US'
        # digits - masculine, singular
        self.digits_sng_msc = [u'zero', u'one', u'two', u'three', u'four',
                               u'five', u'six', u'seven', u'eight', u'nine']
        # tens - masculine, singular
        self.tens_sng_msc = [u'', u'one', u'twen', u'thir', u'four', u'fif',
                             u'six', u'seven', u'eigh', u'nine']
        # teens - masculine
        self.teens = [u'ten', u'eleven', u'twelve', u'thirteen', u'fourteen',
                      u'fifteen', u'sixteen', u'seventeen', u'eighteen',
                      u'nineteen']
        # multiplier - masculine, singular
        self.multi_sng_msc = [u' hundred', u' thousand', u' million',
                              u' billion']
        # multiplier - masculine, plural
        self.multi_plr_msc = [u' hundreds', u' thousands', u' millions',
                              u' billions']
        
        # next line is needed for correct loading of currencies 
        import currencies
        return currencies


    def wordify(self, chunk, chunknr, gender):
        if gender == 'm':
            number = self.digits_sng_msc
        elif gender == 'f':
            number = self.digits_sng_fem
        elif gender == 'n':
            number = self.digits_sng_neu
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
                words += self.digits_sng_msc[int(digit1)] + self.multi_sng_msc[0]
            else :
                if int(digit1) >= 1 : words += self.digits_sng_msc[int(digit1)] + self.multi_plr_msc[0]
        # processing tens
        if chunklength > 1:
            spacer = ''
            if len(words) > 0 : spacer = u' '
            if digit2 == '1':
                words += spacer + self.teens[int(digit3)]
            else:
                if int(digit2) > 1 and int(digit2) > 0:
                    words += spacer + self.tens_sng_msc[int(digit2)] + u'ty'

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
                return words + self.multi_sng_msc[chunknr]
            else:
                return words
        else:
            return ''

en_US()
