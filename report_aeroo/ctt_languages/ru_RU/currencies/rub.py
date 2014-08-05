#!/usr/bin/python
# -*- coding: utf8 -*-

from openerp.addons.report_aeroo.ctt_objects import ctt_currency

class rub(ctt_currency):
    def _init_currency(self):
        self.language = u'ru_RU'
        self.code = u'RUB'
        self.fractions = 100
        self.cur_singular = u' рубль'
        # default plural form for currency        
        self.cur_plural = u' рублей' 
        self.cur_plural_2to4 = u' рубля' 
        self.frc_singular = u' копейка'
        # default plural form for fractions
        self.frc_plural = u' копеек'
        self.frc_plural_2to4 = u' копейки'
        # grammatical genders: f - feminine, m - masculine, n -neuter
        self.cur_gram_gender = 'm'
        self.frc_gram_gender = 'f'

rub()
