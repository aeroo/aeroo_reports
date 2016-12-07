# -*- coding: utf-8 -*-
# © 2008-2014 Alistek
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

from openerp.tools.translate import _
from openerp import api, fields, models


class AerooAddPrintButton(models.TransientModel):
    """
    Add Print Button
    """

    _name = 'aeroo.add_print_button'
    _description = __doc__

    @api.model
    def _default_state(self):
        ctx = self.env.context
        if 'active_model' not in ctx or 'active_id' not in ctx:
            return None

        report = self.env[ctx['active_model']].browse(ctx['active_id'])
        vals = self.env['ir.values'].search([
            ('value', '=', report.type + ',' + str(report.id))
        ])
        if not vals:
            return 'add'
        else:
            return 'exist'

    open_action = fields.Boolean('Open added action')
    state = fields.Selection([
        ('add', 'Add'),
        ('exist', 'Exist'),
        ('done', 'Done'),
    ], 'State', select=True, readonly=True, default=_default_state)

    @api.multi
    def do_action(self):
        self.ensure_one()
        ctx = self.env.context
        assert 'active_model' in ctx and 'active_id' in ctx
        report = self.env[ctx['active_model']].browse(ctx['active_id'])
        event_id = self.env['ir.values'].set_action(
            report.report_name, 'client_print_multi',
            report.model, 'ir.actions.report.xml,%d' % ctx['active_id'])
        self.write({'state': 'done'})
        if not self.open_action:
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'res_model': self._name,
                'target': 'new',
            }

        action = self.env.ref('base.act_values_form_action')

        return {
            'name': _('Client Events'),
            'type': action.type,
            'res_model': action.res_model,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'search_view_id': action.search_view_id.id,
            'domain': [('id', '=', event_id)],
            'context': action.context,
        }
