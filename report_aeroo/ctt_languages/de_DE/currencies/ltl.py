#!/usr/bin/python
# -*- coding: utf8 -*-

from openerp.addons.report_aeroo.ctt_objects import ctt_currency

class ltl(ctt_currency):
    def _init_currency(self):
        self.language = u'de_DE'
        self.code = u'LTL'
        self.fractions = 100
        self.cur_singular = u' Lithuanian litas'
        self.cur_plural = u' Lithuanian litas'
        self.frc_singular = u' cent'
        self.frc_plural = u' cents'
        # grammatical genders: f - feminine, m - masculine, n -neuter
        self.cur_gram_gender = 'm'
        self.frc_gram_gender = 'm'
    
ltl()
