# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file  
#
################################################################################

from odoo import api, fields, models

special_reports = [
    'printscreen.list'
]

def _reopen(self, res_id, model):
    return {'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': res_id,
            'res_model': self._name,
            'target': 'new',
    }

class aeroo_add_print_button(models.TransientModel):
    '''
    Add Print Button
    '''
    _name = 'aeroo.add_print_button'
    _description = 'Add print button'
    
    @api.model
    def _check(self):
        irval_mod = self.env.get('ir.values')
        report = self.env.get(self._context['active_model']).browse(self._context['active_id'])
        if report.report_name in special_reports:
            return 'exception'
        if report.report_wizard:
            act_win_obj = self.env.get('ir.actions.act_window')
            act_win_ids = act_win_obj.search([('res_model','=','aeroo.print_actions')])
            for act_win in act_win_obj.browse(act_win_ids):
                act_win_context = eval(act_win.context, {})
                if act_win_context.get('report_action_id')==report.id:
                    return 'exist'
            return 'add'
        else:
            ids = irval_mod.search([('value','=',report.type+','+str(report.id))])
            if not ids:
	            return 'add'
            else:
	            return 'exist'
    
    def do_action(self):
        irval_mod = self.env.get('ir.values')
        this = self.browse(cr, uid, ids[0], context=context)
        report = self.pool.get(context['active_model']).browse(cr, uid, context['active_id'], context=context)
        event_id = irval_mod.set_action(cr, uid, report.report_name, 'client_print_multi', report.model, 'ir.actions.report,%d' % context['active_id'])
        if report.report_wizard:
            report._set_report_wizard(report.id)
        this.write({'state':'done'})
        if not this.open_action:
            return _reopen(self, this.id, this._model)

        irmod_mod = self.pool.get('ir.model.data')
        iract_mod = self.pool.get('ir.actions.act_window')

        mod_id = irmod_mod.search(cr, uid, [('name', '=', 'act_values_form_action')])[0]
        res_id = irmod_mod.read(cr, uid, mod_id, ['res_id'])['res_id']
        act_win = iract_mod.read(cr, uid, res_id, [])
        act_win['domain'] = [('id','=',event_id)]
        act_win['name'] = _('Client Events')
        return act_win
    
    
    open_action = fields.Boolean(string='Open added action')
    state = fields.Selection([
            ('add','Add'),
            ('exist','Exist'),
            ('exception','Exception'),
            ('done','Done'),
            ],
            string='State', index=True, readonly=True, default=_check
            )

