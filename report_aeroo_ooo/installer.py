# -*- encoding: utf-8 -*-
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

from openerp.osv import fields, osv
import openerp.tools as tools
from xml.dom import minidom
import os, base64
import urllib2
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from openerp.tools.translate import _

from DocumentConverter import DocumentConversionException
from report import OpenOffice_service
from openerp.addons.report_aeroo.report_aeroo import aeroo_lock

_url = 'http://www.alistek.com/aeroo_banner/v7_0_report_aeroo_ooo.png'

class aeroo_config_installer(osv.osv_memory):
    _name = 'aeroo_config.installer'
    _inherit = 'res.config.installer'
    _rec_name = 'host'
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
        'host':fields.char('Host', size=64, required=True),
        'port':fields.integer('Port', required=True),
        'ooo_restart_cmd': fields.char('OOO restart command', size=256, \
            help='Enter the shell command that will be executed to restart the LibreOffice/OpenOffice background process.'+ \
                'The command will be executed as the user of the OpenERP server process,'+ \
                'so you may need to prefix it with sudo and configure your sudoers file to have this command executed without password.'),
        'state':fields.selection([
            ('init','Init'),
            ('error','Error'),
            ('done','Done'),
            
        ],'State', select=True, readonly=True),
        'msg': fields.text('Message', readonly=True),
        'error_details': fields.text('Error Details', readonly=True),
        'link':fields.char('Installation Manual', size=128, help='Installation (Dependencies and Base system setup)', readonly=True),
        'config_logo': fields.function(_get_image_fn, string='Image', type='binary', method=True),
        
    }

    def default_get(self, cr, uid, fields, context=None):
        config_obj = self.pool.get('oo.config')
        data = super(aeroo_config_installer, self).default_get(cr, uid, fields, context=context)
        ids = config_obj.search(cr, 1, [], context=context)
        if ids:
            res = config_obj.read(cr, 1, ids[0], context=context)
            del res['id']
            data.update(res)
        return data

    def check(self, cr, uid, ids, context=None):
        config_obj = self.pool.get('oo.config')
        data = self.read(cr, uid, ids, ['host','port','ooo_restart_cmd'])[0]
        del data['id']
        config_id = config_obj.search(cr, 1, [], context=context)
        if config_id:
            config_obj.write(cr, 1, config_id, data, context=context)
        else:
            config_id = config_obj.create(cr, 1, data, context=context)

        try:
            fp = tools.file_open('report_aeroo_ooo/test_temp.odt', mode='rb')
            file_data = fp.read()
            oo = self.pool.get('oo.config')
            DC = OpenOffice_service(cr, data['host'], data['port'])
            oo.set(DC)
            with aeroo_lock:
                DC.putDocument(file_data)
                DC.saveByStream()
                fp.close()
                DC.closeDocument()
                del DC
        except DocumentConversionException, e:
            oo.remove()
            error_details = str(e)
            state = 'error'
        except Exception, e:
            error_details = str(e)
            state = 'error'
        else:
            error_details = ''
            state = 'done'

        if state=='error':
            msg = _('Connection to OpenOffice.org instance was not established or convertion to PDF unsuccessful!')
        else:
            msg = _('Connection to the OpenOffice.org instance was successfully established and PDF convertion is working.')
        self.write(cr, uid, ids, {'msg':msg,'error_details':error_details,'state':state})

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'report_aeroo_ooo', 'action_aeroo_config_wizard')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, id, context=context)
        result['res_id'] = ids[0]
        return result

    _defaults = {
        'config_logo': _get_image,
        'host':'localhost',
        'port':8100,
        'ooo_restart_cmd': 'sudo /etc/init.d/libreoffice restart',
        'state':'init',
        'link':'http://www.alistek.com/wiki/index.php/Aeroo_Reports_Linux_server#Installation_.28Dependencies_and_Base_system_setup.29',
    }

