#!/usr/bin/python
# -*- coding: utf8 -*-

from openerp.addons.report_aeroo.ctt_objects import ctt_currency

class mxn(ctt_currency):
    def _init_currency(self):
        self.language = u'es_ES'
        self.code = u'MXN'
        self.fractions = 100
        self.cur_singular = u' peso'
        self.cur_plural = u' pesos'
        self.frc_singular = u' centavo'
        self.frc_plural = u' centavos'
        # grammatical genders: f - feminine, m - masculine, n -neuter
        self.cur_gram_gender = 'm'
        self.frc_gram_gender = 'm'
    
mxn()
