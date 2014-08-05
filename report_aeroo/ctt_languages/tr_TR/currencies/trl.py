#!/usr/bin/python
# -*- coding: utf8 -*-

from openerp.addons.report_aeroo.ctt_objects import ctt_currency

class trl(ctt_currency):
    def _init_currency(self):
        self.language = u'tr_TR'
        self.code = u'TRL'
        self.fractions = 100
        self.cur_singular = u' Lira'
        # default plural form for currency
        self.cur_plural = u' Lira'
        self.frc_singular = u' kuruş'
        # default plural form for fractions
        self.frc_plural = u' kuruş'
        # grammatical genders: f - feminine, m - masculine, n -neuter
        self.cur_gram_gender = 'm'
        self.frc_gram_gender = 'm'
    
trl()
