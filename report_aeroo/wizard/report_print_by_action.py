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


from openerp.osv import osv, fields

class report_print_by_action(osv.osv_memory):
    _name = 'aeroo.print_by_action'

    def to_print(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)
        report_xml = self.pool.get(context['active_model']).browse(cr, uid, context['active_id'], context=context)
        print_ids = eval("[%s]" % this.object_ids, {})
        data = {'model':report_xml.model, 'ids':print_ids, 'id':print_ids[0], 'report_type': 'aeroo'}
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_xml.report_name,
            'datas': data,
            'context':context
        }
    
    _columns = {
        'name':fields.text('Object Model', readonly=True),
        'object_ids':fields.char('Object IDs', size=250, required=True, help="Comma separated records ID"),
                
    }

    def _get_model(self, cr, uid, context):
        return self.pool.get(context['active_model']).read(cr, uid, context['active_id'], ['model'], context=context)['model']

    _defaults = {
        'name': _get_model,
    }

