#!/usr/bin/python
# -*- coding: utf8 -*-

from openerp.addons.report_aeroo.ctt_objects import ctt_currency

class lvl(ctt_currency):
    def _init_currency(self):
        self.language = u'ru_RU'
        self.code = u'LVL'
        self.fractions = 100
        self.cur_singular = u' лат'
        # default plural form for currency
        self.cur_plural = u' латов'
        self.cur_plural_2to4 = u' лата'
        self.frc_singular = u' сантим'
        # default plural form for fractions
        self.frc_plural = u' сантимов'
        self.frc_plural_2to4 = u' сантима'
        # grammatical genders: f - feminine, m - masculine, n -neuter
        self.cur_gram_gender = 'm'
        self.frc_gram_gender = 'm'
    
lvl()
