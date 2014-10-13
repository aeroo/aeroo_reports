#
# Copyright (c) 2008-2014 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

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
        event_id = irval_mod.search(cr, uid, [('value','=','ir.actions.report.xml,%d' % context['active_id'])])[0]
        res = irval_mod.unlink(cr, uid, [event_id])
        this.write({'state':'done'})
        return _reopen(self, this.id, this._model)
    
    _columns = {
        'state':fields.selection([
            ('remove','Remove'),
            ('no_exist','Not Exist'),
            ('done','Done'),
            
        ],'State', select=True, readonly=True),
    }

aeroo_remove_print_button()

