# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file  
#
################################################################################

import os
from base64 import b64encode

from odoo.addons.report_aeroo.docs_client_lib import DOCSConnection

from odoo import api, fields, models
from odoo.tools import file_open
from odoo.tools.translate import _
from urllib.request import urlopen, Request

_url = 'http://www.alistek.com/aeroo_banner/v11_1_report_aeroo.png'

class DocsConfigInstaller(models.TransientModel):
    _name = 'docs_config.installer'
    _description = 'Wizard for configuration of Aeroo DOCS connection parameters'
    _inherit = 'res.config.installer'
    _rec_name = 'host'
    
    @api.model
    def _get_image(self):
        try:
            im = urlopen(Request(_url))
            if im.getheader('Content-Type') != 'image/png;':
                raise TypeError(im.getheader('Content-Type'))
        except Exception as e:
            path = os.path.join('report_aeroo','config_pixmaps',
                    'module_banner_1.png')
            image_file = file_data = file_open(path,'rb')
            try:
                file_data = image_file.read()
                _logo_image = b64encode(file_data)
                return _logo_image
            finally:
                image_file.close()
        else:
            _logo_image = b64encode(im.read())
            return _logo_image
    
    
    def _get_image_fn(recs):
        recs.config_logo = recs._get_image()
    
    ### Fields
    enabled = fields.Boolean('Enabled', default=False)
    host = fields.Char('Host', size=64, required=True, default='localhost')
    port = fields.Integer('Port', required=True, default=8989)
    auth_type = fields.Selection([
            ('simple','Simple Authentication')
        ],'Authentication', default=False)
    username = fields.Char('Username', size=32, default='anonymous')
    password = fields.Char('Password', size=32, default='anonymous')
    state = fields.Selection([
            ('init','Init'),
            ('error','Error'),
            ('done','Done'),
            ],'State', index=True, readonly=True, default='init')
    msg = fields.Text('Message', readonly=True)
    error_details = fields.Text('Error Details', readonly=True)
    config_logo = fields.Binary(compute='_get_image_fn', string='Image',
            default=_get_image)
    ### ends Fields
    
    def read(self, fields=None, load='_classic_read'):
        res = super(DocsConfigInstaller, self).read(fields=fields, load=load)
        res = res and res[0] or {}
        icp = self.env['ir.config_parameter'].sudo()
        res['enabled'] = icp.get_param('aeroo.docs_enabled') and True or False
        res['host'] = icp.get_param('aeroo.docs_host') or 'localhost'
        res['port'] = int(icp.get_param('aeroo.docs_port')) or 8989
        res['auth_type'] = icp.get_param('aeroo.docs_auth_type') == 'simple' and 'simple' or False
        res['username'] = icp.get_param('aeroo.docs_username') or 'anonymous'
        res['password'] = icp.get_param('aeroo.docs_password') or 'anonymous'
        return [res]

    @api.model
    def default_get(self, allfields):
        icp = self.env['ir.config_parameter'].sudo()
        defaults = super(DocsConfigInstaller, self).default_get(allfields)
        enabled = icp.get_param('aeroo.docs_enabled')
        defaults['enabled'] = enabled == 'True' and True or False
        defaults['host'] = icp.get_param('aeroo.docs_host') or 'localhost'
        defaults['port'] = int(icp.get_param('aeroo.docs_port')) or 8989
        defaults['auth_type'] = icp.get_param('aeroo.docs_auth_type')  == 'simple' and 'simple' or False
        defaults['username'] = icp.get_param('aeroo.docs_username') or 'anonymous'
        defaults['password'] = icp.get_param('aeroo.docs_password') or 'anonymous'
        return defaults
    
    def check(self):
        icp = self.env['ir.config_parameter']
        icp.set_param('aeroo.docs_enabled', str(self.enabled))
        icp.set_param('aeroo.docs_host', self.host)
        icp.set_param('aeroo.docs_port', self.port)
        icp.set_param('aeroo.docs_auth_type', self.auth_type == 'simple' and 'simple' or False)
        icp.set_param('aeroo.docs_username', self.username)
        icp.set_param('aeroo.docs_password', self.password)
        error_details = ''
        state = 'done'
        
        if self.enabled:
            try:
                fp = file_open('report_aeroo/test_temp.odt', mode='rb')
                file_data = fp.read()
                docs_client = DOCSConnection(self.host, self.port,
                    username=self.auth_type == 'simple' and self.username or None,
                    password=self.auth_type == 'simple' and self.password or None)
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
        result = mod_obj.check_object_reference('report_aeroo',
                     'action_docs_config_wizard')
        act_id = result and result[1] or False
        result = act_obj.search([('id','=',act_id)]).read()[0]
        result['res_id'] = self.id
        return result
