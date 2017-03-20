# -*- coding: utf-8 -*-
# © 2008-2014 Alistek
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
import imp
import logging
import os
import sys

from openerp import models, fields, api, tools, _
from openerp.exceptions import ValidationError
from openerp.report import interface
from openerp.report.report_sxw import rml_parse
from openerp.tools import safe_eval
from openerp.tools.config import config

from ..report_aeroo import AerooReport

logger = logging.getLogger('report_aeroo')


class ReportXml(models.Model):

    _inherit = 'ir.actions.report.xml'

    @api.model
    def _get_default_outformat(self):
        return self.env['report.mimetypes'].search(
            [('code', '=', 'oo-odt')], limit=1)

    tml_source = fields.Selection([
        ('database', 'Database'),
        ('file', 'File'),
        ('lang', 'Different Template per Language'),
    ], string='Template source', default='database', select=True)
    parser_loc = fields.Char(
        'Parser location',
        help="Path to the parser location. Beginning of the path must be start \
              with the module name!\n Like this: {module name}/{path to the \
              parser.py file}")
    report_type = fields.Selection(selection_add=[('aeroo', 'Aeroo Reports')])
    in_format = fields.Selection(
        selection='_get_in_mimetypes',
        string='Template Mime-type',
        default='oo-odt',
    )
    out_format = fields.Many2one(
        'report.mimetypes', 'Output Mime-type',
        default=_get_default_outformat)
    active = fields.Boolean(
        'Active', help='Disables the report if unchecked.', default=True)
    extras = fields.Char(
        'Extra options', compute='_compute_extras', method=True, size=256)

    report_line_ids = fields.One2many(
        'ir.actions.report.line', 'report_id', 'Templates by Language')
    lang_eval = fields.Char(
        'Language Evaluation',
        help="Python expression used to determine the language "
        "of the record being printed in the report.",
        default="o.partner_id.lang")

    @api.multi
    def get_template_from_lang(self, record, lang):
        self.ensure_one()

        if not lang:
            lang = 'en_US'

        line = next(
            (l for l in self.report_line_ids if l.lang_id.code == lang), None)

        if line is None:
            raise ValidationError(
                _('Could not render report %s in lang %s.') %
                (self.name, lang))

        return line.get_aeroo_report_template(record)

    @api.model
    def register_report(self, name, model, tmpl_path, parser):
        name = 'report.%s' % name
        if name in interface.report_int._reports:
            del interface.report_int._reports[name]
        res = AerooReport(name, model, tmpl_path, parser=parser)
        return res

    @api.model
    def load_from_file(self, path, key):
        class_inst = None
        expected_class = 'Parser'
        ad = os.path.abspath(
            os.path.join(tools.ustr(config['root_path']), u'addons'))
        mod_path_list = map(
            lambda m: os.path.abspath(tools.ustr(m.strip())),
            config['addons_path'].split(','))
        mod_path_list.append(ad)
        mod_path_list = list(set(mod_path_list))

        for mod_path in mod_path_list:
            if os.path.lexists(
                mod_path + os.path.sep + path.split(os.path.sep)[0]
            ):
                filepath = mod_path + os.path.sep + path
                filepath = os.path.normpath(filepath)
                sys.path.append(os.path.dirname(filepath))
                mod_name, file_ext = os.path.splitext(
                    os.path.split(filepath)[-1])
                mod_name = '%s_%s_%s' % (self.env.cr.dbname, mod_name, key)

                if file_ext.lower() == '.py':
                    py_mod = imp.load_source(mod_name, filepath)

                if expected_class in dir(py_mod):
                    class_inst = py_mod.Parser
                return class_inst

        raise ValidationError(_('Parser not found at: %s') % path)

    @api.cr
    def _lookup_report(self, cr, name):
        if 'report.' + name in interface.report_int._reports:
            new_report = interface.report_int._reports['report.' + name]
        else:
            env = api.Environment(cr, 1, {})
            action = env['ir.actions.report.xml'].search(
                [('report_name', '=', name)], limit=1)
            if action.report_type == 'aeroo':
                if action.active is True:
                    parser = rml_parse
                    if action.parser_loc:
                        parser = self.load_from_file(
                            cr, 1, action.parser_loc, action.id)
                    new_report = self.register_report(
                        cr, 1, name, action.model, action.report_rml,
                        parser)
                else:
                    new_report = False
            else:
                new_report = super(ReportXml, self)._lookup_report(cr, name)
        return new_report

    @api.multi
    def _compute_extras(recs):
        result = []
        recs.env.cr.execute("SELECT id, state FROM ir_module_module WHERE "
                            "name='deferred_processing'")
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

    @api.multi
    def get_aeroo_report_template(self, record):
        self.ensure_one()
        self = self.sudo()

        if self.tml_source == 'lang':
            lang = safe_eval(self.lang_eval, {'o': record})
            template = self.get_template_from_lang(record, lang)
        else:
            template = self.report_sxw_content
            if not template:
                raise ValidationError(
                    _('No template found for report %s' % self.report_name))
            template = base64.decodestring(template)

        return template
