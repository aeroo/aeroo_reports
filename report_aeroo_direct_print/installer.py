# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008-2013 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
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

from openerp.osv import fields, osv
import openerp.tools as tools
import os, base64
import cups
import urllib2

_url = 'http://www.alistek.com/aeroo_banner/v6_0_report_aeroo_direct_print.png'

class aeroo_printer_installer(osv.osv_memory):
    _name = 'aeroo_printer.installer'
    _inherit = 'res.config.installer'
    _logo_image = None

    def _get_image(self, cr, uid, context=None):
        if self._logo_image:
            return self._logo_image
        try:
            im = urllib2.urlopen(_url.encode("UTF-8"))
            if im.headers.maintype!='image':
                raise TypeError(im.headers.maintype)
        except Exception, e:
            path = os.path.join('report_aeroo','config_pixmaps','module_banner.png')
            image_file = file_data = tools.file_open(path,'rb')
            try:
                file_data = image_file.read()
                self._logo_image = base64.encodestring(file_data)
                return self._logo_image
            finally:
                image_file.close()
        else:
            self._logo_image = base64.encodestring(im.read())
            return self._logo_image

    def _get_image_fn(self, cr, uid, ids, name, args, context=None):
        image = self._get_image(cr, uid, context)
        return dict.fromkeys(ids, image) # ok to use .fromkeys() as the image is same for all 

    _columns = {
        'printer_ids':fields.one2many('aeroo.printers.temp', 'install_id', 'Printers'),
        'config_logo': fields.function(_get_image_fn, string='Image', type='binary', method=True),
        'state':fields.selection([
            ('init','Init'),
            ('done','Done'),
            
        ],'State', select=True, readonly=True),
    }

    def default_get(self, cr, uid, fields, context=None):
        printers_obj = self.pool.get('aeroo.printers')
        data = super(aeroo_printer_installer, self).default_get(cr, uid, fields, context=context)
        conn = cups.Connection()
        printers = conn.getPrinters()
        installed_ids = printers_obj.search(cr, 1, ['|',('active','=',False),('active','=',True)], context=context)
        printers_installed = printers_obj.read(cr, uid, installed_ids, context=context)
        new_printers = list(set(printers.keys()).difference(set(map(lambda p: p['code'], printers_installed))))

        data['printer_ids'] = []
        for p in printers_installed:
            p_temp = p.copy()
            del p_temp['id']
            del p_temp['group_ids']
            del p_temp['active']
            p_temp['state'] = 'connected'
            data['printer_ids'].append(p_temp)

        for new_p in new_printers:
            note = '\n'.join(map(lambda key: "%s: %s" % (key, printers[new_p][key]), printers[new_p]))
            p_temp = {'name':printers[new_p]['printer-info'],'code':new_p,'state':'new','note':note}
            data['printer_ids'].append(p_temp)

        data.update(data)
        return data

    def process(self, cr, uid, ids, context=None):
        printers_obj = self.pool.get('aeroo.printers')
        this = self.browse(cr, uid, ids[0], context=context)
        conn_printers = []
        for printer in this.printer_ids:
            if printer.state=='new' and not printers_obj.search(cr, uid, [('code','=',printer.code)], context=context):
                printers_obj.create(cr, uid, {'name':printer.name,
                                              'code':printer.code,
                                              'note':printer.note,
                                             }, context=context)
                conn_printers.append((1, printer.id, {'state':'connected'}))

        self.write(cr, uid, ids, {'state':'done','printer_ids':conn_printers}, context=context)

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'report_aeroo_direct_print', 'action_aeroo_printer_installer')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, id, context=context)
        result['res_id'] = ids[0]
        return result

    _defaults = {
        'state':'init',
        'config_logo': _get_image,
    }

aeroo_printer_installer()

class aeroo_printers_temp(osv.osv_memory):
    _name = 'aeroo.printers.temp'

    _columns = {
        'name':fields.char('Description', size=256, required=True),
        'code':fields.char('Name', size=64, required=True),
        'note': fields.text('Details'),
        'install_id':fields.many2one('aeroo_printer.installer', 'Install Id'),
        'state':fields.selection([
            ('connected','Connected'),
            ('new','New'),
            
        ],'State', select=True, readonly=True),
    }
    
aeroo_printers_temp()

