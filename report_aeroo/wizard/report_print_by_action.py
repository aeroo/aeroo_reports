##############################################################################
#
# Copyright (c) 2008-2012 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning
import re

class report_print_by_action(models.TransientModel):
    _name = 'aeroo.print_by_action'
    
    @api.multi
    def to_print(recs):
        valid_input = re.match('^\s*\[?\s*((\d+)(\s*,\s*\d+)*)\s*\]?\s*$', recs[0].object_ids)
        valid_input = valid_input and valid_input.group(1) or False
        if not valid_input:
            raise Warning(_("Input single record ID or number of comma separated IDs!"))
        print_ids = eval("[%s]" % valid_input, {})
        rep_obj = recs.env['ir.actions.report.xml']
        report = rep_obj.browse(recs.env.context['active_ids'])[0]
        data = {
                'model': report.model,
                'ids': print_ids,
                'id': print_ids[0],
                'report_type': 'aeroo'
                }
        res =  {
                'type': 'ir.actions.report.xml',
                'report_name': report.report_name,
                'datas': data,
                'context': recs.env.context
                }
        return res
    
    ### Fields
    name = fields.Text('Object Model', readonly=True)
    object_ids = fields.Char('Object IDs', size=250, required=True,
        help="Single ID or number of comma separated record IDs")
    ### ends Fields
        
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if self.env.context.get('active_id'):
            report = self.env['ir.actions.report.xml'].browse(self.env.context['active_ids'])
            if report.report_name == 'aeroo.printscreen.list':
                raise Warning(_("Print Screen report does not support this functionality!"))
        res = super(report_print_by_action, self).fields_view_get(view_id, 
            view_type, toolbar=toolbar, submenu=submenu)
        return res
    
    @api.model
    def _get_model(self):
        rep_obj = self.env['ir.actions.report.xml']
        report = rep_obj.browse(self.env.context['active_ids'])
        return report[0].model
    
    @api.model
    def _get_last_ids(self):
        last_call = self.search([('name','=',self._get_model()),('create_uid','=',self.env.uid)])
        return last_call and last_call[-1].object_ids or False

    _defaults = {
       'name': _get_model,
       'object_ids': _get_last_ids,
    }

