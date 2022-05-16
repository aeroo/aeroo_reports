# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file
#
################################################################################

from odoo import api, fields, models

class IrTranslation(models.Model):
    _name = 'ir.translation'
    _inherit = 'ir.translation'

    ### Fields
    type = fields.Selection(selection_add=[('report','Report')], string='Type',
            index=True, ondelete={'report':'cascade'})
    ### ends Fields
