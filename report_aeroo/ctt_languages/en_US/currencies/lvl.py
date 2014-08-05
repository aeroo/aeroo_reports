#!/usr/bin/python
# -*- coding: utf8 -*-

from openerp.addons.report_aeroo.ctt_objects import ctt_currency

class lvl(ctt_currency):
    def _init_currency(self):
        self.language = u'en_US'
        self.code = u'LVL'
        self.fractions = 100
        self.cur_singular = u' lat'
        self.cur_plural = u' lats'
        self.frc_singular = u' santim'
        self.frc_plural = u' santims'
        # grammatical genders: f - feminine, m - masculine, n -neuter
        self.cur_gram_gender = 'm'
        self.frc_gram_gender = 'm'
    
lvl()
