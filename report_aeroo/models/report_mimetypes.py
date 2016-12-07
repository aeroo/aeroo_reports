# -*- coding: utf-8 -*-
# © 2008-2014 Alistek
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import logging

from openerp import fields, models


logger = logging.getLogger('report_aeroo')


class ReportMimetypes(models.Model):
    """
    Aeroo Report Mime-Type
    """

    _name = 'report.mimetypes'
    _description = 'Report Mime-Types'

    name = fields.Char('Name', size=64, required=True, readonly=True)
    code = fields.Char('Code', size=16, required=True, readonly=True)
    compatible_types = fields.Char(
        'Compatible Mime-Types', size=128,
        readonly=True)
    filter_name = fields.Char('Filter Name', size=128, readonly=True)
