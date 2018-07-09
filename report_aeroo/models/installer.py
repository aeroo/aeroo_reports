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

_url = 'xhttp://www.alistek.com/aeroo_banner/v11_1_report_aeroo.png'

class DocsConfigInstaller(models.TransientModel):
    _name = 'docs_config.installer'
    _inherit = 'res.config.installer'
    _rec_name = 'host'
    _logo_image = None
    
    @api.model
    def _get_image(self):
        if self._logo_image:
            return self._logo_image
        try:
            im = urllib2.urlopen(_url.encode("UTF-8"))
            if im.headers.maintype != 'image':
                raise TypeError(im.headers.maintype)
        except Exception as e:
            path = os.path.join('report_aeroo','config_pixmaps',
                    'module_banner_1.png')
            image_file = file_data = file_open(path,'rb')
            try:
                file_data = image_file.read()
                self._logo_image = b64encode(file_data)
                return self._logo_image
            finally:
                image_file.close()
        else:
            self._logo_image = b64encode(im.read())
            return self._logo_image
    
    @api.one
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
    
    @api.model
    def default_get(self, allfields):
        icp = self.env['ir.config_parameter'].sudo()
        defaults = super(DocsConfigInstaller, self).default_get(allfields)
        enabled = icp.get_param('aeroo.docs_enabled')
        defaults['enabled'] = enabled == 'True' and True or False
        defaults['host'] = icp.get_param('aeroo.docs_host') or 'localhost'
        defaults['port'] = int(icp.get_param('aeroo.docs_port')) or 8989
        defaults['auth_type'] = icp.get_param('aeroo.docs_auth_type') or False
        defaults['username'] = icp.get_param('aeroo.docs_username') or 'anonymous'
        defaults['password'] = icp.get_param('aeroo.docs_password') or 'anonymous'
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
                fp = file_open('report_aeroo/test_temp.odt', mode='rb')
                file_data = fp.read()
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
