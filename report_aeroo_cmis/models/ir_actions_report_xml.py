# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import traceback

from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class ReportXml(models.Model):

    _inherit = 'ir.actions.report.xml'

    tml_source = fields.Selection(
        selection_add=[('dms', 'Import From DMS')])

    dms_repository_id = fields.Many2one(
        'aeroo.dms.backend.repository', 'DMS Repository')

    dms_path = fields.Char('DMS Path')

    dms_document_version = fields.Char(
        'Template Version', readonly=True)

    @api.constrains('tml_source', 'dms_repository_id')
    def _check_dms_repository_id(self):
        for report in self:
            if report.tml_source == 'dms':
                if not report.dms_repository_id:
                    raise ValidationError(_(
                        "The DMS repository is mandatory "
                        "if the template source is set to "
                        "Import from DMS."
                    ))

    @api.constrains('tml_source', 'dms_path')
    def _check_dms_path(self):
        for report in self:
            if report.tml_source == 'dms':
                if not report.dms_path:
                    raise ValidationError(_(
                        "The document DMS path is mandatory "
                        "if the template source is set to "
                        "Import from DMS."
                    ))

    def log_dms_exception_message(self, record):
        self.ensure_one()
        if hasattr(record, 'message_post'):
            repo_name = self.dms_repository_id.name_get()[0][1]
            message = _(
                "Could not load the report template "
                "from the DMS repository %s."
                "Using last version of the template stored in database."
                "<br/><br/>%s"
            ) % (repo_name, traceback.format_exc())

            record.message_post(message)

    @api.multi
    def get_template_from_dms(self, record):
        self.ensure_one()
        assert self.tml_source == 'dms'

        try:
            data, version = self.dms_repository_id.read_document_from_path(
                self.dms_path)
        except:
            if self.report_rml_content:
                self.log_dms_exception_message(record)
                return base64.decodestring(self.report_rml_content)
            else:
                raise

        if self.dms_document_version != version:
            self.report_rml_content = base64.encodestring(data)
            self.dms_document_version = version

        return data

    @api.multi
    def get_aeroo_report_template(self, record):
        """
        Attempt to load the report template from the DMS.

        If an exception is raised, it is logged in the record's chatter
        and the most recent version of the template stored in the Odoo database
        is used instead.
        """
        if self.tml_source == 'dms':
            return self.get_template_from_dms(record)
        return super(ReportXml, self).get_aeroo_report_template(record)
