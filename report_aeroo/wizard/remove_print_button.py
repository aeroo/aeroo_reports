# -*- coding: utf-8 -*-
# © 2008-2014 Alistek
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).


from openerp import api, fields, models


class AerooRemovePrintButton(models.TransientModel):
    """
    Remove Print Button
    """

    _name = 'aeroo.remove_print_button'
    _description = 'Remove print button'

    state = fields.Selection([
        ('remove', 'Remove'),
        ('no_exist', 'Not Exist'),
        ('done', 'Done'),
    ], 'State', select=True, readonly=True)

    @api.model
    def default_get(self, fields_list):
        values = {}

        ctx = self.env.context
        if 'active_model' not in ctx or 'active_id' not in ctx:
            return None

        report = self.env[ctx['active_model']].browse(ctx['active_id'])
        ir_values = self.env['ir.values'].search(
            [('value', '=', report.type + ',' + str(report.id))]
        )
        if not ir_values:
            values['state'] = 'no_exist'
        else:
            values['state'] = 'remove'

        return values

    @api.multi
    def do_action(self):
        ctx = self.env.context
        assert 'active_id' in ctx

        self.env['ir.values'].search([
            ('value', '=', 'ir.actions.report.xml,%d' % ctx['active_id'])
        ]).unlink()
        self.write({'state': 'done'})
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'res_model': self._name,
            'target': 'new',
        }
