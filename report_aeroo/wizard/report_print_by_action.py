# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file  
#
################################################################################

from odoo import api, models, fields
from odoo.tools.translate import _
from odoo.exceptions import Warning
import re
import logging
_logger = logging.getLogger(__name__)

class report_print_by_action(models.TransientModel):
    _name = 'aeroo.print_by_action'
    
    @api.multi
    def to_print(recs):
        valid_input = re.match('^\s*\[?\s*((\d+)(\s*,\s*\d+)*)\s*\]?\s*$',
                                                            recs[0].object_ids)
        valid_input = valid_input and valid_input.group(1) or False
        if not valid_input:
            raise Warning(
                _("Input single record ID or number of comma separated IDs!"))
        print_ids = eval("[%s]" % valid_input, {})
        rep_obj = recs.env['ir.actions.report']
        report = rep_obj.browse(recs.env.context['active_id'])[0]
        ctx = dict(recs.env.context)
        ctx.update({'active_id': print_ids[0],
                    'active_ids': print_ids,
                    'active_model': report.model,
                   })
        data = {
                'model': report.model,
                'ids': print_ids,
                'id': print_ids[0],
                'report_type': 'aeroo',
                }
        res =  {
                'type': 'ir.actions.report',
                'report_name': report.report_name,
                'report_type': report.report_type,
                'datas': data,
                'context': ctx,
                'target': 'current',
                }
        _logger.exception('AEROO by_action======================= %s' % (res,))
        return res
    
    @api.model
    def _get_model(self):
        rep_obj = self.env['ir.actions.report']
        report = rep_obj.browse(self.env.context['active_ids'])
        return report[0].model
    
    @api.model
    def _get_last_ids(self):
        conds = [('name','=',self._get_model()),('create_uid','=',self.env.uid)]
        last_call = self.search(conds)
        return last_call and last_call[-1].object_ids or False
        
    ### Fields
    name = fields.Text('Object Model', default=_get_model, readonly=True)
    object_ids = fields.Char('Object IDs', size=250, default=_get_last_ids,
        required=True, help="Single ID or number of comma separated record IDs")
    ### ends Fields
        
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                                                                submenu=False):
        if self.env.context.get('active_id'):
            rep_obj = self.env['ir.actions.report']
            report = rep_obj.browse(self.env.context['active_id'])
            if report.report_name == 'aeroo.printscreen.list':
                raise Warning(
                  _("Print Screen report does not support this functionality!"))
        res = super(report_print_by_action, self).fields_view_get(view_id, 
                                    view_type, toolbar=toolbar, submenu=submenu)
        return res

