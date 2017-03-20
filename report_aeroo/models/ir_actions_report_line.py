# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64

from openerp import api, fields, models, tools


class IrActionsReportLine(models.Model):

    _name = 'ir.actions.report.line'

    report_id = fields.Many2one(
        'ir.actions.report.xml', 'Report', required=True,
        ondelete='cascade')
    lang_id = fields.Many2one('res.lang', 'Language', required=True)

    template_source = fields.Selection([
        ('database', 'Database'),
        ('file', 'File'),
    ], string='Template source', default='database', select=True)

    template_data = fields.Binary('Template')
    template_filename = fields.Binary('File Name')
    template_location = fields.Char('File Location')

    @api.multi
    def get_aeroo_report_template(self, record):
        self.ensure_one()
        if self.template_source == 'file':
            fp = tools.file_open(self.template_location, mode='r')
            data = fp.read()
            fp.close()
        else:
            data = base64.decodestring(self.template_data)
        return data
