##############################################################################
#
# Copyright (c) 2008-2013 Alistek (http://www.alistek.com) All Rights Reserved.
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

from openerp import api, models, fields, _
from openerp.exceptions import except_orm, Warning

from openerp.report import interface
import re

class report_print_actions(models.TransientModel):
    _name = 'aeroo.print_actions'
    _description = 'Aeroo reports print wizard'

    def _reopen(self, res_id, model):
        return {'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': res_id,
                'res_model': self._name,
                'target': 'new',
            }

    def check_if_deferred(self, report_xml, print_ids):
        extras = report_xml.extras.split(',')
        if 'deferred_processing' in extras and report_xml.deferred!='off' and len(print_ids)>=report_xml.deferred_limit:
            return True
        return False

    def start_deferred(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)
        report_xml = self.pool.get('ir.actions.report.xml').browse(cr, uid, context['report_action_id'])
        deferred_proc_obj = self.pool.get('deferred_processing.task')
        process_id = deferred_proc_obj.create(cr, uid, {'name':report_xml.name}, context=context)
        deferred_proc_obj.new_process(cr, uid, process_id, context=context)
        deferred_proc_obj.start_process_report(cr, uid, process_id, this.print_ids, context['report_action_id'], context=context)

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        mod_id = mod_obj.search(cr, uid, [('name', '=', 'action_deferred_processing_task_deferred_processing')])[0]
        res_id = mod_obj.read(cr, uid, mod_id, ['res_id'])['res_id']
        act_win = act_obj.read(cr, uid, res_id, ['name','type','view_id','res_model','view_type',
                                                'search_view_id','view_mode','target','context'])
        act_win['res_id'] = process_id
        act_win['view_type'] = 'form'
        act_win['view_mode'] = 'form,tree'
        return act_win
    
    @api.multi
    def simple_print(recs):
        report_xml = recs._get_report()
        data = {
                'model':report_xml.model, 
                'ids':this.print_ids,
                'id':context['active_id'],
                'report_type': 'aeroo'
                }
        return {
                'type': 'ir.actions.report.xml',
                'report_name': report_xml.report_name,
                'datas': data,
                'context': context
                }
    
    @api.multi
    def get_strids(recs):
        valid_input = re.match('^\[\s*((\d+)(\s*,\s*\d+)*)\s*\]$',
            recs.print_ids)
        if not valid_input:
            raise Warning(_("Wrong or not ids!"))
        return eval(recs.print_ids, {})
    
    @api.multi
    def to_print(recs=None):
        report_xml = recs._get_report()
        obj_print_ids = recs.get_strids()
        print_ids = []
        if recs.copies <= 1:
            print_ids = obj_print_ids
        else:
            copies = recs.copies
            while(copies):
                print_ids.extend(obj_print_ids)
                copies -= 1
        if recs.check_if_deferred(report_xml, print_ids):
            recs.write({
                'state': 'confirm',
                'message': _("This process may take too long for interactive \
                    processing. It is advisable to defer the process as a \
                    background process. Do you want to start a deferred \
                    process?"),
                'print_ids': str(print_ids)
                })
            return self._reopen(recs.id, recs._model)
        ##### Simple print #####
        data = {
                'model': report_xml.model,
                'ids': print_ids,
                'id': print_ids[0],
                'report_type': 'aeroo'
                }
        res = {
               'type': 'ir.actions.report.xml',
               'report_name': report_xml.report_name,
               'datas': data,
               'context': recs.env.context
               }
        return res

    @api.model
    def _out_formats_get(self):
        report_xml = self._get_report()
        if report_xml:
            mtyp_obj = self.env['report.mimetypes']
            mtyp_ids = mtyp_obj.search([('compatible_types','=',report_xml.in_format)])
            return [(str(r.id), r.name) for r in mtyp_ids]
        else:
            return []
    
    ### Fields
    
    out_format = fields.Selection(selection=_out_formats_get,
        string='Output format', required=True)
    out_format_code = fields.Char(string='Output format code', 
        size=16, required=False, readonly=True)
    copies = fields.Integer(string='Number of copies', required=True)
    message = fields.Text('Message')
    state = fields.Selection([('draft','Draft'),('confirm','Confirm'),
        ('done','Done'),],'State', select=True, readonly=True)
    print_ids = fields.Text()
    report_id = fields.Many2one('ir.actions.report.xml', 'Report')
    
    ### ends Fields

    def onchange_out_format(self, cr, uid, ids, out_format_id):
        if not out_format_id:
            return {}
        out_format = self.pool.get('report.mimetypes').read(cr, uid, int(out_format_id), ['code'])
        return { 'value':
            {'out_format_code': out_format['code']}
        }

    @api.model
    def _get_report(self):
        report_id = self.env.context.get('report_action_id')
        return report_id and self.env['ir.actions.report.xml'].browse(report_id)
    
    @api.model
    def default_get(self, allfields):
        res = super(report_print_actions, self).default_get(allfields)
        report_xml = self._get_report()
        lcall = self.search([('report_id','=',report_xml.id),('create_uid','=',self.env.uid)])
        lcall = lcall and lcall[-1] or False
        if 'copies' in allfields:
            res['copies'] = (lcall or report_xml).copies
        if 'out_format' in allfields:
            res['out_format'] = lcall and lcall.out_format or str(report_xml.out_format.id)
        if 'out_format_code' in allfields:
            res['out_format_code'] = lcall and lcall.out_format_code or report_xml.out_format.code
        if 'print_ids' in allfields:
            res['print_ids'] = self.env.context.get('active_ids')
        if 'report_id' in allfields:
            res['report_id'] = report_xml.id
        return res
    
    _defaults = {
        'state': 'draft',
    }

