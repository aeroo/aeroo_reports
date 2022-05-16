# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file  
#
################################################################################

from openerp.tools.translate import _
from openerp.osv import osv, fields

def _reopen(self, res_id, model):
    return {'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': res_id,
            'res_model': self._name,
            'target': 'new',
    }

class aeroo_remove_print_button(osv.osv_memory):
    '''
    Remove Print Button
    '''
    _name = 'aeroo.remove_print_button'
    _description = 'Remove print button'

    def default_get(self, cr, uid, fields_list, context=None):
        values = {}

        report = self.pool.get(context['active_model']).browse(cr, uid, context['active_id'], context=context)
        if report.report_wizard:
            act_win_obj = self.pool.get('ir.actions.act_window')
            act_win_ids = act_win_obj.search(cr, uid, [('res_model','=','aeroo.print_actions')], context=context)
            for act_win in act_win_obj.browse(cr, uid, act_win_ids, context=context):
                act_win_context = eval(act_win.context, {})
                if act_win_context.get('report_action_id')==report.id:
                    values['state'] = 'remove'
                    break;
            else:
                values['state'] = 'no_exist'
        else:
            irval_mod = self.pool.get('ir.values')
            ids = irval_mod.search(cr, uid, [('value','=',report.type+','+str(report.id))])
            if not ids:
	            values['state'] = 'no_exist'
            else:
	            values['state'] = 'remove'

        return values

    def do_action(self, cr, uid, ids, context):
        this = self.browse(cr, uid, ids[0], context=context)
        report = self.pool.get(context['active_model']).browse(cr, uid, context['active_id'], context=context)
        if report.report_wizard:
            report._unset_report_wizard()
        irval_mod = self.pool.get('ir.values')
        event_id = irval_mod.search(cr, uid, [('value','=','ir.actions.report,%d' % context['active_id'])])[0]
        res = irval_mod.unlink(cr, uid, [event_id])
        this.write({'state':'done'})
        return _reopen(self, this.id, this._model)
    
    _columns = {
        'state':fields.selection([
            ('remove','Remove'),
            ('no_exist','Not Exist'),
            ('done','Done'),
            
        ],'State', index=True, readonly=True),
    }

aeroo_remove_print_button()

