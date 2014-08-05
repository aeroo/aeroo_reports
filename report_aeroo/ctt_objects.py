#!/usr/bin/python
# -*- coding: utf8 -*-
################################################################################
# Developed by Kaspars Vilkens - Alistek Ltd (c) 2011
#
# Supported sum: 0 ... 999999999999.99
# Supported languages: for more reference see languages forlder
# Supported currencies: see particular language for reference
################################################################################

import os
supported_language = {}

if __name__ == '__main__':
    from sys import exit
    error = '''This code is part of Report Aeroo package!
    Not to be used separately...'''
    exit(error)
    
def currency_to_text(sum, currency_code, language_code):
    if language_code not in supported_language:
        raise Exception('Not supported or no language: %s' % language_code)
    else:
        suppl = supported_language[language_code]
        return suppl.currency_to_text(sum, currency_code)

class ctt_language(object):
    def _init_lang(self):
        pass

    def __repr__(self):
        return self.name

    def __init__(self):
        self.supported_currency = {}
        self.minbound = 0
        self.maxbound = 999999999999.99
        currencies = self._init_lang()
        supported_language.update({self.name : self})
        import_submodules('currency', currencies, 0)

    def check_sum(self):
        if sum < self.minbound or sum > self.maxbound : 
            raise Exception(\
                """Sum out of bounds: must be from %s to %s""" % \
                (str(self.minbound), str(self.maxbound)))

    def check_currency(self):
        if currency not in supported_currency: 
            raise Exception(\
                """Unsupported or no currency: must be one of (%s)""" % \
                ', '.join(self.supported_currency))

    def dtowords(self, sum_integers, gender):
        diginwords = u''
        if sum_integers == 0:
            return self.wordify('0', 0, gender)
        elif sum_integers > 0:
            lengthx = len(str(sum_integers))
            nrchunks = (lengthx / 3)
        if nrchunks < (float(lengthx) / 3) :
            nrchunks+=1
        inc = 1
        while inc <= nrchunks:
            startpos = (lengthx - inc * 3)
            chunklength = 3
            if startpos < 0:
                chunklength += startpos
                startpos = 0
            chunk = str(sum_integers)[startpos : startpos + chunklength]
            #print str(startpos)+' '+str(chunklength)+' '+ chunk
            if inc == 1:
                wordified = self.wordify(chunk, inc-1, gender)
            else:
                wordified = self.wordify(chunk, inc-1, 'm')
            inc += 1
            spacer = ''
            if len(diginwords) > 0 and wordified:
                spacer = ' '
            diginwords = wordified + spacer + diginwords
        return diginwords


    def currency_to_text(self, sum, currency):
        #--------------for currencies with 100 fractions
        sum = float(sum)
        sum = round(sum, 2)
        # find out digits before floating point - currency
        sum_cur = int(sum)
        # find out digits after floating point - fractions
        sum_frc = int(round((sum - sum_cur) * 100,0))
        curr = self.supported_currency.get(currency)
        cur_in_words = self.dtowords(sum_cur, curr.cur_gram_gender)
        frc_in_words = self.dtowords(sum_frc, curr.frc_gram_gender)
        #------------------------------------

        return (cur_in_words + curr.cur_to_text(sum_cur) + ' ' + frc_in_words +\
                             curr.frc_to_text(sum_frc)).strip().encode('utf-8')


class ctt_currency(object):
    def _init_currency(self):
        pass

    def __repr__(self):
        return self.code

    def __init__(self):
        self._init_currency()
        suppl = supported_language.get(self.language)
        suppl.supported_currency.update({self.code : self})

    def cur_to_text(self, sum_cur):
        # is the currency sum one
        if sum_cur == 1 or (str(sum_cur)[-1] == '1' and str(sum_cur)[-2] !='1'):
            return self.cur_singular
        # 2,3 and 4 yields different plural form, if defined
        elif ((sum_cur in [2, 3, 4]) or (str(sum_cur)[-1] in ['2', '3', '4'] \
              and str(sum_cur)[-2] != '1')) and hasattr(self, 'cur_plural_2to4'):
            return self.cur_plural_2to4
        # betwean 1 and 10 yields different plural form, if defined
        elif (sum_cur > 1 and sum_cur < 10 or (int(str(sum_cur)[-1]) > 1 \
             and str(sum_cur)[-2] != '1')) and hasattr(self, 'cur_plural_2to10'):
            return self.cur_plural_2to10
        # starting from 10 yields uses default plural form
        else:
            return self.cur_plural

    def frc_to_text(self, sum_frc):
        # is the fraction sum one
        if sum_frc == 1 or (str(sum_frc)[-1] == '1' and str(sum_frc)[-2] !='1'):
            return self.frc_singular
        # 2,3 and 4 yields different plural form, if defined
        elif ((sum_frc in [2, 3, 4]) or (str(sum_frc)[-1] in ['2', '3', '4'] \
              and str(sum_frc)[-2] != '1')) and hasattr(self, 'frc_plural_2to4'):
            return self.frc_plural_2to4
        # betwean 1 and 10 yields different plural form, if defined
        elif (sum_frc > 1 and sum_frc < 10 or (int(str(sum_frc)[-1]) > 1 \
             and str(sum_frc)[-2] != '1')) and hasattr(self, 'frc_plural_2to10'):
            return self.frc_plural_2to10
        # starting from 10 yields uses default plural form
        else:
            return self.frc_plural

def __filter_names(to_import, package):
    folder = os.path.split(package.__file__)[0]
    for name in os.listdir(folder):
        if to_import == 'currency':
            if name.endswith(".py") and not name.startswith("__"):
                yield name[:-3]
        if to_import == 'language':
            if len(name) == 5 and not name.startswith("__"):
                yield name

def import_submodules(to_import, package, level=-1):
    names = list(__filter_names(to_import, package))
    m = __import__(package.__name__, globals(), locals(), names, level)
    return dict((name, getattr(m, name)) for name in names)

import ctt_languages
import_submodules('language', ctt_languages, 0)
