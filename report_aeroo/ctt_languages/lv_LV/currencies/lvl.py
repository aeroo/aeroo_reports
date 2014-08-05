#!/usr/bin/python
# -*- coding: utf8 -*-

from openerp.addons.report_aeroo.ctt_objects import ctt_currency

class lvl(ctt_currency):
    def _init_currency(self):
        self.language = u'lv_LV'
        self.code = u'LVL'
        self.fractions = 100
        self.cur_singular = u' lats'
        # default plural form for currency
        self.cur_plural = u' latu'
        # betwean 1 and 10 yields different plural form, if defined
        self.cur_plural_2to10 = u' lati'
        self.frc_singular = u' santīms'
        # default plural form for fractions
        self.frc_plural = u' santīmi'
        # betwean 1 and 10 yields different plural form, if defined
        self.frc_plural_2to10 = u' santīmu'
        # grammatical genders: f - feminine, m - masculine, n -neuter
        self.cur_gram_gender = 'm'
        self.frc_gram_gender = 'm'
    
lvl()
