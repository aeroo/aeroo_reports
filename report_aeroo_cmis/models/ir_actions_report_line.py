# -*- coding: utf-8 -*-
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64

from openerp import api, fields, models
from openerp.exceptions import ValidationError


class IrActionsReportLine(models.Model):

    _inherit = 'ir.actions.report.line'

    template_source = fields.Selection(
        selection_add=[('dms', 'Import From DMS')])

    dms_document_version = fields.Char(
        'Version', readonly=True)

    @api.constrains('template_source')
    def _check_dms_repository_id(self):
        for line in self:
            if line.template_source == 'dms':
                if not line.report_id.dms_repository_id:
                    raise ValidationError(
                        "The DMS repository is mandatory "
                        "if the template source is set to "
                        "Import from DMS."
                    )

                if not line.template_location:
                    raise ValidationError(
                        "The DMS path for each language "
                        "must be defined in the field File Location."
                    )

    @api.multi
    def get_template_from_dms(self, record):
        self.ensure_one()
        assert self.template_source == 'dms'

        try:
            repository = self.report_id.dms_repository_id
            data, version = repository.read_document_from_path(
                self.template_location)
        except:
            if self.template_data:
                self.report_id.log_dms_exception_message(
                    record, self.dms_document_version)
                return base64.decodestring(self.template_data)
            else:
                raise

        if self.dms_document_version != version:
            self.template_data = base64.encodestring(data)
            self.dms_document_version = version

        return data

    @api.multi
    def get_aeroo_report_template(self, record):
        self.ensure_one()
        if self.template_source == 'dms':
            return self.get_template_from_dms(record)
        return super(IrActionsReportLine, self).get_aeroo_report_template(
            record)
