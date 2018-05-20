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
            raise UserError(_('%s report parser not found' % report_model_name))
        
        context.update({
            'active_model': self.model,
            
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
        default="""class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.context = context
        self.localcontext.update({})"""
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
    def create(self, vals):
        if vals.get('report_type') != 'aeroo':
            res_id = super(report_aeroo, self).create(vals)
            return res_id
        
        if 'report_type' in vals and vals['report_type'] == 'aeroo':
            parser = models.AbstractModel
            vals['auto'] = False
            if vals.get('parser_state') =='loc' and vals.get('parser_loc'):
                parser=self.load_from_file(vals['parser_loc'], vals['name'].lower().replace(' ','_')) or parser
            elif vals.get('parser_state') =='def' and vals.get('parser_def'):
                parser=self.load_from_source(vals['parser_def']) or parser
            model = self.env['ir.model']._get(vals.get('model'))
            vals['binding_model_id'] = model.id
            res_id = super(report_aeroo, self).create(vals)
            if vals.get('report_wizard'):
                wizard_id = self._set_report_wizard(self.env.cr, self.env.uid, vals['replace_report_id'] or res_id, \
                            res_id, linked_report_id=res_id, report_name=vals['name'], context=self.env.context)
                res_id.write({'wizard_id': wizard_id})
            if vals.get('replace_report_id'):
                self.link_inherit_report(self.env.cr, self.env.uid, res_id, new_replace_report_id=vals['replace_report_id'], context=self.env.context)
            return res_id
            
    @api.one
    def write(recs, vals):
        if 'report_data' in vals:
            if vals['report_data']:
                try:
                    b64decode(vals['report_data'])
                except binascii.Error:
                    vals['report_data'] = False
        if vals.get('report_type', recs.report_type) != 'aeroo':
            res = super(report_aeroo, recs).write(vals)
            return res
        # Continues if this is Aeroo report
        if vals.get('report_wizard') and vals.get('active', recs.active) and \
                (recs.replace_report_id and vals.get('replace_report_id',True) \
                or not recs.replace_report_id):
            vals['wizard_id'] = recs._set_report_wizard(report_action_id=recs.ids, linked_report_id=vals.get('replace_report_id'))
            vals['wizard_id'] = vals['wizard_id'] and vals['wizard_id'][0]
            #recs.report_wizard = True
            #recs.wizard_id = vals['wizard_id']
        elif 'report_wizard' in vals and not vals['report_wizard'] and recs.report_wizard:
            recs._unset_report_wizard()
            vals['wizard_id'] = False
            #recs.report_wizard = False
            #recs.wizard_id = False
        parser = models.AbstractModel
        p_state = vals.get('parser_state', False)
        if p_state == 'loc':
            parser = recs.load_from_file(vals.get('parser_loc', False) or recs.parser_loc, recs.id) or parser
        elif p_state == 'def':
            parser = recs.load_from_source((vals.get('parser_loc', False) or recs.parser_def or '')) or parser
        elif p_state == 'default':
            parser = models.AbstractModel
        elif recs.parser_state=='loc':
            parser = recs.load_from_file(recs.parser_loc, recs.id) or parser
        elif recs.parser_state=='def':
            parser = recs.load_from_source(recs.parser_def) or parser
        elif recs.parser_state=='default':
            parser = models.AbstractModel
        if vals.get('parser_loc', False):
            parser = recs.load_from_file(vals['parser_loc'], recs.id) or parser
        elif vals.get('parser_def', False):
            parser = recs.load_from_source(vals['parser_def']) or parser
        if vals.get('report_name', False) and vals['report_name'] != recs.report_name:
            report_name = vals['report_name']
        else:
            report_name = recs.report_name
        ##### Link / unlink inherited report #####
        link_vals = {}
        now_unlinked = False
        if 'replace_report_id' in vals and vals.get('active', recs.active):
            if vals['replace_report_id']:
                if recs.replace_report_id and vals['replace_report_id'] != recs.replace_report_id.id:
                    recs_new = recs.with_context(keep_wizard = True)
                    link_vals.update(recs_new.unlink_inherit_report())
                    now_unlinked = True
                link_vals.update(recs.link_inherit_report(new_replace_report_id=vals['replace_report_id'])[0])
                recs.register_report(report_name, vals.get('model', recs.model), vals.get('report_rml', recs.report_rml), parser)
            else:
                link_vals.update(recs.unlink_inherit_report()[0])
                now_unlinked = True
        ##########################################
        #try:
        #    if vals.get('active', recs.active):
        #        recs.register_report(report_name, vals.get('model', recs.model), vals.get('report_rml', recs.report_rml), parser)
        #        if not recs.active and vals.get('replace_report_id',recs.replace_report_id):
        #            link_vals.update(recs.link_inherit_report(new_replace_report_id=vals.get('replace_report_id', False)))
        #    elif not vals.get('active', recs.active):
        #        recs.unregister_report(report_name)
        #        if not now_unlinked:
        #            link_vals.update(recs.unlink_inherit_report())
        #except Exception as e:
        #    logger.error("Error in report registration", exc_info=True)
        #    raise except_orm(_('Report registration error !'), _('Report was not registered in system !'))
        #vals.update(link_vals)
        res = super(report_aeroo, recs).write(vals)
        return res
    
