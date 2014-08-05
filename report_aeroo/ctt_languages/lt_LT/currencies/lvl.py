#!/usr/bin/python
# -*- coding: utf8 -*-

from openerp.addons.report_aeroo.ctt_objects import ctt_currency

class lvl(ctt_currency):
    def _init_currency(self):
        self.language = u'lt_LT'
        self.code = u'LVL'
        self.fractions = 100
        self.cur_singular = u' latas'
        # default plural form for currency
        self.cur_plural = u' latų'
        # betwean 1 and 10 yields different plural form, if defined
        self.cur_plural_2to10 = u' latai'
        self.frc_singular = u' santimas'
        # default plural form for fractions
        self.frc_plural = u' santimų'
        # betwean 1 and 10 yields different plural form, if defined
        self.frc_plural_2to10 = u' santimai'
        # grammatical genders: f - feminine, m - masculine, n -neuter
        self.cur_gram_gender = 'm'
        self.frc_gram_gender = 'm'
    
lvl()
