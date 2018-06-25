# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file  
#
################################################################################

import encodings
import imp
import sys
import os
import binascii
from base64 import b64decode
import zipimport
from lxml import etree
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import file_open
from odoo.tools.translate import _
from odoo.modules import module

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
class report_stylesheets(models.Model):
    '''
    Aeroo Report Stylesheets
    '''
    _name = 'report.stylesheets'
    _description = 'Report Stylesheets'
    
    ### Fields
    name = fields.Char('Name', size=64, required=True)
    report_styles = fields.Binary('Template Stylesheet',
        help='OpenOffice.org / LibreOffice stylesheet (.odt)')
    ### ends Fields

# ------------------------------------------------------------------------------
class res_company(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    ### Fields
    stylesheet_id = fields.Many2one('report.stylesheets', 
        'Aeroo Reports Global Stylesheet')
    ### ends Fields

# ------------------------------------------------------------------------------
class report_mimetypes(models.Model):
    '''
    Aeroo Report Mime-Type
    '''
    _name = 'report.mimetypes'
    _description = 'Report Mime-Types'

    ### Fields
    name = fields.Char('Name', size=64, required=True, readonly=True)
    code = fields.Char('Code', size=16, required=True, readonly=True)
    compatible_types = fields.Char('Compatible Mime-Types', size=128, 
        readonly=True)
    filter_name = fields.Char('Filter Name', size=128, readonly=True)
    ### ends Fields

# ------------------------------------------------------------------------------
class report_aeroo(models.Model):
    _name = 'ir.actions.report'
    _inherit = 'ir.actions.report'
    
    @api.model
    def render_aeroo(self, docids, data):
        report_model_name = 'report.%s' % self.report_name
        
        report_parser = self.env.get(report_model_name)
        context = dict(self.env.context)
        if report_parser is None:
            report_parser = self.env['report.report_aeroo.abstract']
        
        context.update({
            'active_model': self.model,
            'report_name': self.report_name,
            })
        
        return report_parser.with_context(context).aeroo_report(docids, data)
    
    @api.model
    def _get_report_from_name(self, report_name):
        res = super(report_aeroo, self)._get_report_from_name(report_name)
        if res:
            return res
        report_obj = self.env['ir.actions.report']
        conditions = [('report_type', 'in', ['aeroo']),
                      ('report_name', '=', report_name)]
        context = self.env['res.users'].context_get()
        return report_obj.with_context(context).search(conditions, limit=1)
    
    @api.one
    @api.depends('report_file')
    def _read_template(self):
        fp = None
        data = None
        try:
            fp = file_open(self.report_file, mode='rb')
            data = fp.read()
        except IOError as e:
            if e.errno == 13: # Permission denied on the template file
                raise osv.except_osv(_(e.strerror), e.filename)
            else:
                _logger.exception("Error in '_read_template' method", exc_info=True)
        except Exception as e:
            _logger.exception("Error in '_read_template' method", exc_info=True)
            fp = False
            data = False
        finally:
            if fp is not None:
                fp.close()
        return data
    
    @api.model
    def _get_encodings(self):
        l = list(set(encodings._aliases.values()))
        l.sort()
        return zip(l, l)
    
    @api.model
    def _get_default_outformat(self):
        res = self.env['report.mimetypes'].search([('code','=','oo-odt')])
        return res and res[0].id or False
    
    @api.multi
    def _get_extras(recs):
        result = []
        if recs.aeroo_docs_enabled():
            result.append('aeroo_ooo')
        ##### Check deferred_processing module #####
        recs.env.cr.execute("SELECT id, state FROM ir_module_module WHERE \
                             name='deferred_processing'")
        deferred_proc_module = recs.env.cr.dictfetchone()
        if deferred_proc_module and deferred_proc_module['state'] in ('installed', 'to upgrade'):
            result.append('deferred_processing')
        ############################################
        result = ','.join(result)
        for rec in recs:
            rec.extras = result
    
    @api.model
    def aeroo_docs_enabled(self):
        '''
        Check if Aeroo DOCS connection is enabled
        '''
        icp = self.env['ir.config_parameter'].sudo()
        enabled = icp.get_param('aeroo.docs_enabled')
        return enabled == 'True' and True or False
    
    @api.model
    def _get_in_mimetypes(self):
        mime_obj = self.env['report.mimetypes']
        domain = self.env.context.get('allformats') and [] or [('filter_name','=',False)]
        res = mime_obj.search(domain).read(['code', 'name'])
        return [(r['code'], r['name']) for r in res]
    
    ### Fields
    charset = fields.Selection('_get_encodings', string='Charset',
        required=True, default='utf_8')
    content_fname = fields.Char('Override Extension',size=64,
        help='Here you can override report filename and extension.')
    styles_mode = fields.Selection([
        ('default','Not used'),
        ('global','Global'),
        ('specified','Specified'),
        ], string='Stylesheet', default='default')
    stylesheet_id = fields.Many2one('report.stylesheets', 'Template Stylesheet')
    preload_mode = fields.Selection([
        ('static',_('Static')),
        ('preload',_('Preload')),
        ], string='Preload Mode', default='static')
    tml_source = fields.Selection([
        ('database','Database'),
        ('file','File'),
        ('parser','Parser'),
        ], string='Template source', default='database', index=True)
    parser_def = fields.Text('Parser Definition',
        default="""from odoo import api, models
class Parser(models.AbstractModel):
    _inherit = 'report.report_aeroo.abstract'
    _name = 'report.thisismyparserservicename'"""
        )
    parser_loc = fields.Char('Parser location', size=128,
        help="Path to the parser location. Beginning of the path must be start \
              with the module name!\n Like this: {module name}/{path to the \
              parser.py file}")
    parser_state = fields.Selection([
        ('default',_('Default')),
        ('def',_('Definition')),
        ('loc',_('Location')),
        ],'State of Parser', index=True, default='default')
    report_type = fields.Selection(selection_add=[('aeroo', _('Aeroo Reports'))])
    process_sep = fields.Boolean('Process Separately',
        help='Generate the report for each object separately, \
              then merge reports.')
    in_format = fields.Selection(selection='_get_in_mimetypes',
        string='Template Mime-type', default='oo-odt')
    out_format = fields.Many2one('report.mimetypes', 'Output Mime-type',
        default=_get_default_outformat)
    active = fields.Boolean('Active', help='Disables the report if unchecked.',
        default=True
        )
    report_wizard = fields.Boolean('Report Wizard',
        help='Adds a standard wizard when the report gets invoked.')
    copies = fields.Integer(string='Number of Copies', default=1)
    disable_fallback = fields.Boolean('Disable Format Fallback', 
        help='Raises error on format convertion failure. Prevents returning \
              original report file type if no convertion is available.')
    extras = fields.Char('Extra options', compute='_get_extras', method=True,
        size=256)
    deferred = fields.Selection([
        ('off',_('Off')),
        ('adaptive',_('Adaptive')),
        ],'Deferred',
        help='Deferred (aka Batch) reporting, for reporting on large amount \
              of data.',
        default='off')
    deferred_limit = fields.Integer('Deferred Records Limit',
        help='Records limit at which you are invited to start the deferred \
              process.',
        default=80
        )
    replace_report_id = fields.Many2one('ir.actions.report', 'Replace Report',
        help='Select a report that should be replaced.')
    wizard_id = fields.Many2one('ir.actions.act_window', 'Wizard Action')
    report_data = fields.Binary(string='Template Content', attachment=True)
    ### ends Fields
    
    @api.multi
    def unlink(recs):
        trans_obj = recs.env['ir.translation']
        trans_ids = trans_obj.search([('type','=','report'),('res_id','in',recs.ids)])
        trans_ids.unlink()
        res = super(report_aeroo, recs).unlink()
        return res
        
    @api.model
    def unregister_report(self, report_name):
        report_name = 'report.%s' % self.report_name
        if self.env.get(report_name):
            rep_model = self.env['ir.model'].search([('model','=',report_name)])
            rep_model.with_context(_force_unlink=True).unlink()
    
    @api.model
    def load_from_file(self, path, key):
        class_inst = None
        expected_class = 'Parser'

        try:
            for mod_path in module.ad_paths:
                if os.path.lexists(mod_path+os.path.sep+path.split(os.path.sep)[0]):
                    filepath = mod_path+os.path.sep+path
                    filepath = os.path.normpath(filepath)
                    sys.path.append(os.path.dirname(filepath))
                    mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
                    mod_name = '%s_%s_%s' % (self.env.cr.dbname, mod_name, key)

                    if file_ext.lower() == '.py':
                        py_mod = imp.load_source(mod_name, filepath)

                    elif file_ext.lower() == '.pyc':
                        py_mod = imp.load_compiled(mod_name, filepath)

                    if expected_class in dir(py_mod):
                        class_inst = py_mod.Parser
                    return class_inst
                elif os.path.lexists(mod_path+os.path.sep+path.split(os.path.sep)[0]+'.zip'):
                    zimp = zipimport.zipimporter(mod_path+os.path.sep+path.split(os.path.sep)[0]+'.zip')
                    return zimp.load_module(path.split(os.path.sep)[0]).parser.Parser
        except SyntaxError as e:
            raise except_orm(_('Syntax Error !'), e)
        except Exception as e:
            _logger.error('Error loading report parser: %s'+(filepath and ' "%s"' % filepath or ''), e)
            return None
    
    @api.model
    def create(self, vals):
        if vals.get('report_type') != 'aeroo':
            res_id = super(report_aeroo, self).create(vals)
            return res_id
        
        if 'report_type' in vals and vals.get('report_type') == 'aeroo':
            parser = models.AbstractModel
            ir_model = self.env['ir.model']
            model_data = {'model': vals['report_name'],
                          'name': vals['name'],
                          'parser_def': vals['parser_def'],
                         }
            if vals['parser_state']=='loc' and vals['parser_loc']:
                parser=self.load_from_file(vals['parser_loc'], vals['name'].lower().replace(' ','_')) or parser #TODO Revise
            elif vals['parser_state']=='def' and vals['parser_def']:
                parser = ir_model._custom_aeroo_parser(model_data)
            elif vals['parser_state']=='default':
                parser = ir_model._default_aeroo_parser(model_data)
            model = ir_model._get(vals.get('model'))
            res_id = super(report_aeroo, self).create(vals)
            parser._build_model(self.pool, self.env.cr)
            return res_id
            
    @api.one
    def write(rec, vals):
        orec = rec.read()[0]
        if vals.get('report_type') and orec['report_type'] != vals['report_type']:
            raise UserError(_("Changing report type not allowed!"))
        
        if 'report_data' in vals and vals['report_data']:
            try:
                b64decode(vals['report_data'])
            except binascii.Error:
                vals['report_data'] = False
        
        res = super(report_aeroo, rec).write(vals)
        if orec['report_type'] != 'aeroo':
            return res
        
        try:
            rec.unregister_report(orec['report_name'])
        except Exception as e:
            _logger.exception(_("Error unregistering Aeroo Reports report"))
            raise UserError(_("Error unregistering Aeroo Reports report"))
        
        if rec.active:
            ir_model = rec.env['ir.model']
            model_data = {'model': rec.report_name,
                          'name': rec.name,
                          'parser_def': rec.parser_def,
                         }
            if rec.parser_state == 'default':
                parser = ir_model._default_aeroo_parser(model_data)
            
            elif rec.parser_state == 'loc':
                parser = rec.load_from_file(rec.parser_loc, rec.id) #TODO Revise
            
            elif rec.parser_state == 'def':
                parser = ir_model._custom_aeroo_parser(model_data)
            
            parser._build_model(rec.pool, rec.env.cr)
        
        return res
    
