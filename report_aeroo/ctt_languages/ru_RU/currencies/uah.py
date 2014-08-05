#!/usr/bin/python
# -*- coding: utf8 -*-

from openerp.addons.report_aeroo.ctt_objects import ctt_currency

class uah(ctt_currency):
    def _init_currency(self):
        self.language = u'ru_RU'
        self.code = u'UAH'
        self.fractions = 100
        self.cur_singular = u' гривна'
        # default plural form for currency
        self.cur_plural = u' гривен'
        self.cur_plural_2to4 = u' гривны'
        self.frc_singular = u' копeйка'
        # default plural form for fractions
        self.frc_plural = u' копeек'
        self.frc_plural_2to4 = u' копeйки'
        # grammatical genders: f - feminine, m - masculine, n -neuter
        self.cur_gram_gender = 'f'
        self.frc_gram_gender = 'f'

uah()
