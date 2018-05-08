# -*- coding: utf-8 -*-

from odoo import api, models


class TestAerooReport(models.AbstractModel):
    _inherit = 'report.report_aeroo.abstract'
    
    _name = 'report.product_template_printer'
    

#===============================================================================
    @api.model
    def get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(self._name)
        selected_companies = self.env['res.company'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': selected_companies,
        }
