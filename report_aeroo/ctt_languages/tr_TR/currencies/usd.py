#!/usr/bin/python
# -*- coding: utf8 -*-

from openerp.addons.report_aeroo.ctt_objects import ctt_currency

class usd(ctt_currency):
    def _init_currency(self):
        self.language = u'tr_TR'
        self.code = u'USD'
        self.fractions = 100
        self.cur_singular = u' USD'
        # default plural form for currency
        self.cur_plural = u' USD'
        self.frc_singular = u' sent'
        # default plural form for fractions
        self.frc_plural = u' sent'
        # grammatical genders: f - feminine, m - masculine, n -neuter
        self.cur_gram_gender = 'm'
        self.frc_gram_gender = 'm'
    
usd()
