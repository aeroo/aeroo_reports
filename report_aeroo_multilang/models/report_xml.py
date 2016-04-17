# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import api, fields, models
from openerp import tools
from openerp.tools import translate as _
from openerp.exceptions import ValidationError


logger = logging.getLogger(__name__)


class ReportXml(models.Model):
    _inherit = 'ir.actions.report.xml'

    lang = fields.Char(
        'Language',
        help="Optional translation language (ISO code) to use to resolve the "
             "expression provided in the 'Alternate report file path field'"
             "This should usually be a placeholder expression "
             "that provides the appropriate language, e.g. "
             "${object.partner_id.lang}.",
        placeholder="${object.partner_id.lang}")

    alt_report_rml = fields.Char(
        'Alternate report file path',
        help="This should be a string expression that provides the path "
             "to an alternate report file to use. The string is formatted "
             "with '{lang}' as relacement string in the path, e.g. "
             "'folder/my_template_{lang}.odt'. If the expression is not "
             "provided or can be resolved, the report falls back on the main "
             "report file path/controller.\n The expression is resolved a "
             "first time by providing the iso code as as lang e.g. fr_BE. "
             "If no file is found at the resolved path, The expression is "
             "resolved and second time by using the lang part of the ISO code "
             "e.g. 'fr'."
        )

    @api.constrains('lang', 'alt_report_rml')
    def _check_lant_alt_report_rml(self):
        for this in self:
            if not(this.lang and this.alt_report_rml):
                raise ValidationError(
                    _("If a value is provided for the language or an the "
                      "alternate report file path, you must also provide a "
                      "value for the other one"))

    @api.multi
    def get_template_for_lang(self, model, res_id, parser):
        self.ensure_one()
        lang = self.env['mail.template'].render_template(
            self.lang, self.model, res_id)
        if lang:
            tmpl_path = self.alt_report_rml.format(lang=lang)
            tmpl_file = None
            try:
                tmpl_file = tools.file_open(tmpl_path, mode='rb')
            except IOError:
                logger.debug('Template not found at %s', tmpl_path)
            if not tmpl_file:
                lang = '_' in lang and lang.split('_')[0] or ''
                tmpl_path = self.alt_report_rml.format(lang=lang)
            try:
                tmpl_file = tools.file_open(tmpl_path, mode='rb')
            except IOError:
                logger.debug('Template not found at %s', tmpl_path)
            if tmpl_file:
                return tmpl_file.read()
        return super(ReportXml, self).get_template(model, res_id, parser)

    @api.multi
    def get_template(self, model, res_id, parser):
        self.ensure_one()
        if self.lang:
            return self.get_template_for_lang(model, res_id, parser)
        return super(ReportXml, self).get_template(model, res_id, parser)
