#!/usr/bin/python
# -*- coding: utf8 -*-

from openerp.addons.report_aeroo.ctt_objects import ctt_currency

class trl(ctt_currency):
    def _init_currency(self):
        self.language = u'lv_LV'
        self.code = u'TRL'
        self.fractions = 100
        self.cur_singular = u' Turku lira'
        # default plural form for currency
        self.cur_plural = u' Turku liru'
        # betwean 1 and 10 yields different plural form, if defined
        self.cur_plural_2to10 = u' Turku liras'
        self.frc_singular = u' kurušs'
        # default plural form for fractions
        self.frc_plural = u' kurušu'
        # betwean 1 and 10 yields different plural form, if defined
        self.frc_plural_2to10 = u' kuruši'
        # grammatical genders: f - feminine, m - masculine, n -neuter
        self.cur_gram_gender = 'f'
        self.frc_gram_gender = 'm'
    
trl()
