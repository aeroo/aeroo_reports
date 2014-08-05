#!/usr/bin/python
# -*- coding: utf8 -*-
# lt_LT
################################################################################
#
# Lithuanian language support assembled from contributions provided by:
# Paulius Sladkevičius
#
################################################################################

from openerp.addons.report_aeroo.ctt_objects import ctt_language

class lt_LT(ctt_language):
    def _init_lang(self):
        self.name = 'lt_LT'
        # digits - masculine, singular
        self.number_sng_msc = [u'nulis', u'vienas', u'du', u'trys', u'keturi',
                               u'penkti', u'šeši', u'septyni', u'aštuoni',
                               u'devyni']
        # tens - masculine, singular
        self.tens_sng_msc = [u'nulis', u'vienas', u'dvi', u'tris',
                               u'keturias', u'penkias', u'šešias', u'septynias',
                               u'aštuonias', u'devynias']
        # teens - masculine
        self.teens = [u'dešimt', u'vienuolika', u'dvylika', u'trylika',
                      u'keturiolika', u'penkiolika', u'šešiolika',
                      u'septyniolika', u'aštuonolika', u'devyniolika']
        # multiplier - masculine, singular
        self.multi_sng_msc = [u' šimtas', u' tūkstantis', u' milijonas',
                              u' milijardas']
        # multiplier - masculine, plural
        self.multi_plr_msc = [u' šimtai', u' tūkstančiai', u' milijonai',
                              u' milijardai']
        # multiplier - masculine, plural (other form)
        self.multi_plr_msc_2 = [u' šimtų', u' tūkstančių', u' milijonų',
                              u' milijardų']
        
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
                words += spacer + self.number_teens[int(digit3)]
            else:
                if int(digit2) > 1 and int(digit2) > 0:
                    words += spacer + self.tens_sng_msc[int(digit2)] + u'dešimt'

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
                if chunklength >= 2 and ((int(chunk) % 10) == 0 or (digit2 == \
                                                     '1' and int(digit3) > 0)):
                    return words + multi_plr_msc_2[chunknr]
                else:
                    return words + multi_plr_msc[chunknr]

            else:
                return words
        else:
            return ''

lt_LT()
