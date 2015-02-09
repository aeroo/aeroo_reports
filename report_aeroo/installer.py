# -*- coding: utf-8 -*-
################################################################################
#
# Copyright (c) 2009-2014 Alistek ( http://www.alistek.com ) All Rights Reserved.
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
################################################################################

from openerp import models, fields, api, _

import openerp.tools as tools
import os, base64
import urllib2
from docs_client_lib import DOCSConnection
from openerp.addons.report_aeroo.report_aeroo import aeroo_lock

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

_url = 'http://www.alistek.com/aeroo_banner/v7_0_report_aeroo.png'

class report_aeroo_installer(models.TransientModel):
    _name = 'report.aeroo.installer'
    _inherit = 'res.config.installer'
    _rec_name = 'link'
    _logo_image = None
    
    @api.model
    def _get_image(self):
        if self._logo_image:
            return self._logo_image
        try:
            im = urllib2.urlopen(_url.encode("UTF-8"))
            if im.headers.maintype!='image':
                raise TypeError(im.headers.maintype)
        except Exception, e:
            path = os.path.join('report_aeroo','config_pixmaps',\
                    'module_banner.png')
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
    
    @api.one
    def _get_image_fn(recs):
        image = recs._get_image()
        for rec in recs:
            rec.config_logo = image
    
    ### Fields
    link = fields.Char('Original developer', size=128, readonly=True)
    config_logo = fields.Binary(compute='_get_image_fn', string='Image')
    ### ends Fields

    _defaults = {
        'config_logo': _get_image,
        'link':'http://www.alistek.com',
    }

class docs_config_installer(models.TransientModel):
    _name = 'docs_config.installer'
    _inherit = 'res.config.installer'
    _rec_name = 'host'
    _logo_image = None
    
    @api.cr_uid_context
    def _get_image(self, cr, uid, context=None):
        if self._logo_image:
            return self._logo_image
        try:
            im = urllib2.urlopen(_url.encode("UTF-8"))
            if im.headers.maintype != 'image':
                raise TypeError(im.headers.maintype)
        except Exception, e:
            path = os.path.join('report_aeroo','config_pixmaps',
                    'module_banner.png')
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
    
    @api.one
    def _get_image_fn(recs):
        recs.config_logo = recs._get_image()
    
    ### Fields
    enabled = fields.Boolean('Enabled')
    host = fields.Char('Host', size=64, required=True)
    port = fields.Integer('Port', required=True)
    auth_type = fields.Selection([
            ('simple','Simple Authentication')
        ],'Authentication')
    username = fields.Char('Username', size=32)
    password = fields.Char('Password', size=32)
    state = fields.Selection([
            ('init','Init'),
            ('error','Error'),
            ('done','Done'),
        ],'State', select=True, readonly=True)
    msg = fields.Text('Message', readonly=True)
    error_details = fields.Text('Error Details', readonly=True)
    config_logo = fields.Binary(compute='_get_image_fn', string='Image')
    ### ends Fields
    
    @api.model
    def default_get(self, allfields):
        icp = self.pool['ir.config_parameter']
        defaults = super(docs_config_installer, self).default_get(allfields)
        enabled = icp.get_param(self.env.cr, self.env.uid, 'aeroo.docs_enabled')
        defaults['enabled'] = enabled == 'True' and True or False
        defaults['host'] = icp.get_param(self.env.cr, self.env.uid, 
                            'aeroo.docs_host') or 'localhost'
        defaults['port'] = int(icp.get_param(self.env.cr, self.env.uid, 
                            'aeroo.docs_port')) or 8989
        defaults['auth_type'] = icp.get_param(self.env.cr, self.env.uid, 
                            'aeroo.docs_auth_type') or False
        defaults['username'] = icp.get_param(self.env.cr, self.env.uid, 
                            'aeroo.docs_username') or 'anonymous'
        defaults['password'] = icp.get_param(self.env.cr, self.env.uid, 
                            'aeroo.docs_password') or 'anonymous'
        return defaults
    
    @api.multi
    def check(self):
        icp = self.env['ir.config_parameter']
        icp.set_param('aeroo.docs_enabled', str(self.enabled))
        icp.set_param('aeroo.docs_host', self.host)
        icp.set_param('aeroo.docs_port', self.port)
        icp.set_param('aeroo.docs_auth_type', self.auth_type or 'simple')
        icp.set_param('aeroo.docs_username', self.username)
        icp.set_param('aeroo.docs_password', self.password)
        error_details = ''
        state = 'done'
        
        if self.enabled:
            try:
                fp =tools.file_open('report_aeroo/test_temp.odt', mode='rb')
                file_data = fp.read()
                with aeroo_lock:
                    docs_client = DOCSConnection(self.host, self.port,
                        username=self.username, password=self.password)
                    token = docs_client.upload(file_data)
                    data = docs_client.convert(identifier=token, out_mime='pdf')
            except Exception as e:
                error_details = str(e)
                state = 'error'
        if state=='error':
            msg = _('Failure! Connection to DOCS service was not established ' +
                    'or convertion to PDF unsuccessful!')
        elif state=='done' and not self.enabled:
            msg = _('Connection to Aeroo DOCS disabled!')
        else:
            msg = _('Success! Connection to the DOCS service was successfully '+
                    'established and PDF convertion is working.')
        self.msg = msg
        self.error_details = error_details
        self.state = state
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        result = mod_obj.get_object_reference('report_aeroo',
                     'action_docs_config_wizard')
        act_id = result and result[1] or False
        result = act_obj.search([('id','=',act_id)]).read()[0]
        result['res_id'] = self.id
        return result

    _defaults = {
        'config_logo': _get_image,
        'host':'localhost',
        'port':8989,
        'auth_type':False,
        'username':'anonymous',
        'password':'anonymous',
        'state':'init',
        'enabled': False,
    }
    
