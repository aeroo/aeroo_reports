# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file  
#
################################################################################

import encodings
import importlib
import sys
import os
import binascii
from base64 import b64decode
import zipimport
from lxml import etree
import logging
import time

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import file_open
from odoo.tools.translate import _
from odoo.modules import module
from odoo.tools.safe_eval import safe_eval
from odoo.tools.safe_eval import time as eval_time

_logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
class ReportStylesheets(models.Model):
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
class ResCompany(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    ### Fields
    stylesheet_id = fields.Many2one('report.stylesheets',
        'Aeroo Reports Global Stylesheet')
    ### ends Fields

# ------------------------------------------------------------------------------
class ReportMimetypes(models.Model):
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
class ReportAeroo(models.Model):
    _name = 'ir.actions.report'
    _inherit = 'ir.actions.report'
    
    @api.model
    def render_aeroo(self, docids=None, data=None, get_filename=False):
        if not data:
            data = {}
        report_model_name = 'report.%s' % self.report_name
        report_parser = self.env.get(report_model_name)
        context = dict(self.env.context)
        if report_parser is None:
            report_parser = self.env['report.report_aeroo.abstract']
        context.update({
            'active_model': self.model,
            'report_name': self.report_name,
            })
        record = self.env.get(self.model).browse(docids)
        variables = {}
        variables['object'] = record
        variables['o'] = record
        variables['time'] = eval_time
        
        report_name = safe_eval(report.print_report_name, variables)

        attachment_name = safe_eval(self.attachment, variables) if self.attachment else ''
        res = report_parser.with_context(context).aeroo_report(docids, data)
        return res[:2] if not get_filename else res[:]
    
    #===========================================================================
    @api.model
    def _get_report_from_name(self, report_name):
        res = super(ReportAeroo, self)._get_report_from_name(report_name)
        if res:
            return res
        report_obj = self.env['ir.actions.report']
        conditions = [('report_type', 'in', ['aeroo']),
                      ('report_name', '=', report_name)]
        context = self.env['res.users'].context_get()
        return report_obj.with_context(context).search(conditions, limit=1)
    
    #===========================================================================
    def _read_template(self):
        self.ensure_one()
        fp = None
        data = None
        try:
            fp = file_open(self.report_file, mode='rb')
            data = fp.read()
        except IOError as e:
            if e.errno == 13:  # Permission denied on the template file
                raise UserError(_(e.strerror), e.filename)
            else:
                _logger.exception(
                    "Error in '_read_template' method", exc_info=True)
        except Exception as e:
            _logger.exception(
                "Error in '_read_template' method", exc_info=True)
            fp = False
            data = False
        finally:
            if fp is not None:
                fp.close()
        return data
    
    #===========================================================================
    @api.model
    def _get_encodings(self):
        l = list(set(encodings._aliases.values()))
        l.sort()
        return zip(l, l)
    
    #===========================================================================
    @api.model
    def _get_default_outformat(self):
        res = self.env['report.mimetypes'].search([('code','=','oo-odt')])
        return res and res[0].id or False
    
    #===========================================================================
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
    
    #===========================================================================
    @api.model
    def aeroo_docs_enabled(self):
        '''
        Check if Aeroo DOCS connection is enabled
        '''
        icp = self.env['ir.config_parameter'].sudo()
        enabled = icp.get_param('aeroo.docs_enabled')
        return enabled == 'True' and True or False
    
    #===========================================================================
    @api.model
    def _get_in_mimetypes(self):
        mime_obj = self.env['report.mimetypes']
        domain = self.env.context.get('allformats') and [] or [('filter_name','=',False)]
        res = mime_obj.search(domain).read(['code', 'name'])
        if not res: # TODO: remove. Installing on clean DB, no data not initialized in v12
                    # ValueError: Wrong value for ir.actions.report.in_format: 'oo-odt'
            return [('oo-odt', 'oo-odt')]
        else:
            return [(r['code'], r['name']) for r in res]
    
    #===========================================================================
    ### Fields
    charset = fields.Selection('_get_encodings', string='Charset',
        required=True, default='utf_8')
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
    report_type = fields.Selection(selection_add=[('aeroo', _('Aeroo Reports'))], ondelete={'aeroo':'cascade'})
    process_sep = fields.Boolean('Process Separately',
        help='Generate the report for each object separately, \
              then merge reports.')
    in_format = fields.Selection(selection='_get_in_mimetypes',
        string='Template Mime-type', default='oo-odt')
    out_format = fields.Many2one('report.mimetypes', 'Output Mime-type',
        default=_get_default_outformat)
    report_wizard = fields.Boolean('Report Wizard',
        help='Adds a standard wizard when the report gets invoked.')
    copies = fields.Integer(string='Number of Copies', default=1)
    disable_fallback = fields.Boolean('Disable Format Fallback', 
        help='Raises error on format convertion failure. Prevents returning \
              original report file type if no convertion is available.')
    extras = fields.Char('Extra options', compute='_get_extras', size=256)
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
    
    #===========================================================================
    @api.onchange('in_format')
    def onchange_in_format(self):
        # TODO get first available format
        self.out_format = False
    
    #===========================================================================
    def unlink(recs):
        trans_obj = recs.env['ir.translation']
        trans_ids = trans_obj.search([('type','=','report'),('res_id','in',recs.ids)])
        trans_ids.unlink()
        res = super(ReportAeroo, recs).unlink()
        return res
    #===========================================================================
    def register_report(self, parser_state=None, model_data=None):
        ir_model = self.env['ir.model']
        model_data = {
            'model': self.report_name,
            'name': self.name,
            'parser_def': self.parser_def,
            } or model_data
        parser_state = self.parser_state or parser_state
        
        if parser_state == 'default':
            parser = ir_model._default_aeroo_parser(model_data)
        elif parser_state == 'loc':
            # TODO Revise
            parser = self.load_from_file(self.parser_loc, self.id)
        elif parser_state == 'def':
            parser = ir_model._custom_aeroo_parser(model_data)
        parser._build_model(self.pool, self.env.cr)
    #===========================================================================
    def unregister_report(self):
        report_name = 'report.%s' % self.report_name
        _logger.exception("++++++++++++++++ 1: %s" % self.pool.get(report_name))
        _logger.exception("++++++++++++++++ 1a: %s" % self.env.get(report_name))
        if self.pool.get(report_name):
            self.clear_caches()
            rep_model = self.env['ir.model'].search(
                [('model', '=', report_name)])
            _logger.exception("++++++++++++++++ x: %s" % type(self.env))
            _logger.exception("++++++++++++++++ x: %s" % rep_model)
            rep_model.with_context(_force_unlink=True).unlink()
            
            self.pool.setup_models(self.env.cr)
        _logger.exception("++++++++++++++++ 2: %s" % self.pool.get(report_name))
        _logger.exception("++++++++++++++++ 2a: %s" % self.env.get(report_name))
            
    
    #===========================================================================
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
                    mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
                    mod_name = '%s_%s_%s' % (self.env.cr.dbname, mod_name, key)

                    if file_ext.lower() == '.py':
                        py_mod = importlib.load_source(mod_name, filepath)

                    elif file_ext.lower() == '.pyc':
                        py_mod = importlib.load_compiled(mod_name, filepath)

                    if expected_class in dir(py_mod):
                        class_inst = py_mod.Parser
                    return class_inst
                elif os.path.lexists(mod_path+os.path.sep+path.split(os.path.sep)[0]+'.zip'):
                    zimp = zipimport.zipimporter(mod_path+os.path.sep+path.split(os.path.sep)[0]+'.zip')
                    return zimp.load_module(path.split(os.path.sep)[0]).parser.Parser
        except SyntaxError as e:
            raise UserError(_('Syntax Error !'), e)
        except Exception as e:
            _logger.error('Error loading report parser: %s'+(filepath and ' "%s"' % filepath or ''), e)
            return None
    
    #===========================================================================
    @api.model
    def create(self, vals):
        rec = super(ReportAeroo, self).create(vals)
        if rec.report_type != 'aeroo':
            return rec
        model_data = {
            'model': vals['report_name'],
            'name': vals['name'],
            'parser_def': vals['parser_def'],
            }
        self.register_report(parser_state=vals['parser_state'], model_data=model_data)
        #parser = models.AbstractModel
        #ir_model = self.env['ir.model']
        #model_data = {
        #    'model': rec.report_name,
        #    'name': rec.name,
        #    'parser_def': rec.parser_def,
        #}
        #if rec.parser_state == 'loc' and rec.parser_loc:
        #    # TODO Revise
        #    parser = self.load_from_file(
        #        rec.parser_loc, rec.name.lower().replace(' ', '_')) or parser
        #elif rec.parser_state == 'def' and rec.parser_def:
        #    parser = ir_model._custom_aeroo_parser(model_data)
        #elif rec.parser_state == 'default':
        #    parser = ir_model._default_aeroo_parser(model_data)
        #parser._build_model(self.pool, self.env.cr)
        return rec
    
    #===========================================================================
    def write(self, vals):
        # TODO remove or adapt, it shouldn't be necessary
        # if vals.get('report_type') and \
        #         orec['report_type'] != vals['report_type']:
        #     raise UserError(_("Changing report type not allowed!"))
        if 'report_data' in vals and vals['report_data']:
            try:
                b64decode(vals['report_data'])
            except binascii.Error:
                vals['report_data'] = False

        res = super(ReportAeroo, self).write(vals)
        
        #for rec in self.filtered(lambda x: x.report_type == 'aeroo'):
        #    try:
        #        rec.unregister_report()
        #    except Exception:
        #        _logger.exception(_("Error unregistering Aeroo Reports report"))
        #        raise UserError(_("Error unregistering Aeroo Reports report"))
        #
        #    #self.register_report()

        return res
