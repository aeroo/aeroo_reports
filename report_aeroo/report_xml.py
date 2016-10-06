# -*- coding: utf-8 -*-
# © 2008-2014 Alistek
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

from openerp import models, fields, api

from report_aeroo import AerooReport
from openerp.report.report_sxw import rml_parse
from openerp.report import interface

import logging
logger = logging.getLogger('report_aeroo')


class res_company(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    stylesheet_id = fields.Many2one(
        'report.stylesheets',
        'Aeroo Global Stylesheet')


class report_mimetypes(models.Model):
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


class report_xml(models.Model):
    _name = 'ir.actions.report.xml'
    _inherit = 'ir.actions.report.xml'

    @api.model
    def register_report(self, name, model, tmpl_path, parser):
        name = 'report.%s' % name
        if name in interface.report_int._reports:
            del interface.report_int._reports[name]
        res = AerooReport(self.env.cr, name, model, tmpl_path, parser=parser)
        return res

    @api.cr
    def _lookup_report(self, cr, name):
        if 'report.' + name in interface.report_int._reports:
            new_report = interface.report_int._reports['report.' + name]
        else:
            cr.execute("SELECT id, active, report_type, parser_state, \
                        model, report_rml \
                        FROM ir_act_report_xml \
                        WHERE report_name=%s", (name,))
            record = cr.dictfetchone()
            if record['report_type'] == 'aeroo':
                if record['active'] is True:
                    parser = rml_parse
                    new_report = self.register_report(
                        cr, 1, name, record['model'], record['report_rml'],
                        parser)
                else:
                    new_report = False
            else:
                new_report = super(report_xml, self)._lookup_report(cr, name)
        return new_report

    @api.model
    def _get_default_outformat(self):
        res = self.env['report.mimetypes'].search([('code', '=', 'oo-odt')])
        return res and res[0].id or False

    tml_source = fields.Selection([
        ('database', 'Database'),
        ('file', 'File'),
    ], string='Template source', default='database', select=True)
    report_type = fields.Selection(selection_add=[('aeroo', 'Aeroo Reports')])
    in_format = fields.Selection(
        selection='_get_in_mimetypes',
        string='Template Mime-type',
        default='oo-odt',
    )
    out_format = fields.Many2one(
        'report.mimetypes', 'Output Mime-type',
        default=_get_default_outformat)
    active = fields.Boolean('Active', help='Disables the report if unchecked.')
    extras = fields.Char(
        'Extra options', compute='_compute_extras', method=True, size=256)

    @api.multi
    def _compute_extras(recs):
        result = []
        recs.env.cr.execute("SELECT id, state FROM ir_module_module WHERE \
                             name='deferred_processing'")
        deferred_proc_module = recs.env.cr.dictfetchone()
        if deferred_proc_module and deferred_proc_module['state'] in (
                'installed',
                'to upgrade'):
            result.append('deferred_processing')
        result = ','.join(result)
        for rec in recs:
            rec.extras = result

    @api.model
    def _get_in_mimetypes(self):
        mime_obj = self.env['report.mimetypes']
        domain = self.env.context.get('allformats') and [] or [
            ('filter_name', '=', False)]
        res = mime_obj.search(domain).read(['code', 'name'])
        return [(r['code'], r['name']) for r in res]
