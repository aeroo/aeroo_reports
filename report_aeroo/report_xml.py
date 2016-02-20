
# -*- encoding: utf-8 -*-
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
from openerp.exceptions import except_orm, Warning

from openerp.osv.orm import transfer_modifiers_to_node
import openerp.netsvc as netsvc
from report_aeroo import Aeroo_report
from openerp.report.report_sxw import rml_parse
from openerp.report import interface
from openerp.modules import module
import base64, binascii
import openerp.tools as tools
import encodings

import imp, sys, os
import zipimport
from openerp.tools.config import config
from lxml import etree

import logging
logger = logging.getLogger('report_aeroo')

class report_stylesheets(models.Model):
    '''
    Aeroo Report Stylesheets
    '''
    _name = 'report.stylesheets'
    _description = 'Report Stylesheets'
    
    ### Fields
    name = fields.Char('Name', size=64, required=True)
    report_styles = fields.Binary('Template Stylesheet',
        help='OpenOffice.org stylesheet (.odt)')
    ### ends Fields

class res_company(models.Model):
    _name = 'res.company'
    _inherit = 'res.company'

    ### Fields
    stylesheet_id = fields.Many2one('report.stylesheets', 
        'Aeroo Global Stylesheet')
    ### ends Fields

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

class report_xml(models.Model):
    _name = 'ir.actions.report.xml'
    _inherit = 'ir.actions.report.xml'

    @api.model
    def aeroo_docs_enabled(self):
        '''
        Check if Aeroo DOCS connection is enabled
        '''
        icp = self.env['ir.config_parameter'].sudo()
        enabled = icp.get_param('aeroo.docs_enabled')
        return enabled == 'True' and True or False
    
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
        except SyntaxError, e:
            raise except_orm(_('Syntax Error !'), e)
        except Exception, e:
            logger.error('Error loading report parser: %s'+(filepath and ' "%s"' % filepath or ''), e)
            return None
    
    @api.model
    def load_from_source(self, source):
        source = "from openerp.report import report_sxw\n" + source
        expected_class = 'Parser'
        context = {'Parser':None}
        try:
            exec source.replace('\r','') in context
            return context['Parser']
        except SyntaxError, e:
            raise except_orm(_('Syntax Error !'), e)
        except Exception, e:
            logger.error("Error in 'load_from_source' method",
                __name__, exc_info=True)
            return None
    
    @api.one
    def link_inherit_report(recs, new_replace_report_id=False):
        res = {}
        if new_replace_report_id:
            inherit_report = recs.browse(new_replace_report_id)
        else:
            inherit_report = report.replace_report_id

        if inherit_report:
            ir_values_obj = recs.env['ir.values']
            if inherit_report.report_wizard:
                src_action_type = 'ir.actions.act_window'
                action_id = recs.wizard_id
            else:
                src_action_type = 'ir.actions.report.xml'
                action_id = inherit_report.id
            events = ir_values_obj.search(
                [('value','=',"%s,%s" % (src_action_type,action_id))])
            if events:
                event = events[0]
                if recs.report_wizard:
                    dest_action_type = 'ir.actions.act_window'
                    if recs.wizard_id:
                        action_id = recs.wizard_id
                    else:
                        action_id = inherit_report._set_report_wizard(recs.id, 
                            linked_report_id=recs.id, report_name=recs.name)[0]
                        res['wizard_id'] = action_id
                else:
                    dest_action_type = 'ir.actions.report.xml'
                    action_id = recs.id
                event.write({'value':"%s,%s" % (dest_action_type,action_id)})
        return res
    
    @api.one
    def unlink_inherit_report(recs):
        res = {}
        keep_wizard = recs.env.context.get('keep_wizard') or False
        if recs.replace_report_id:
            irval_obj = recs.env['ir.values']
            if recs.report_wizard:
                src_action_type = 'ir.actions.act_window'
                action_id = recs.wizard_id.id
                if not keep_wizard:
                    res['wizard_id'] = False
            else:
                src_action_type = 'ir.actions.report.xml'
                action_id = recs.id
            event_ids = irval_obj.search(
                [('value','=',"%s,%s" % (src_action_type,action_id))])
            if event_ids:
                event_id = event_ids[0]
                if recs.replace_report_id.report_wizard:
                    dest_action_type = 'ir.actions.act_window'
                    action_id = recs.wizard_id.id
                else:
                    dest_action_type = 'ir.actions.report.xml'
                    action_id = recs.replace_report_id.id
                event_id.write({'value':"%s,%s" % (dest_action_type,action_id)})

            if not keep_wizard and recs.wizard_id and not res.get('wizard_id',True):
                recs.wizard_id.unlink()
        return res

    def delete_report_service(self, name):
        name = 'report.%s' % name
        if interface.report_int._reports.has_key( name ):
            del interface.report_int._reports[name]
    
    @api.model
    def register_report(self, name, model, tmpl_path, parser):
        name = 'report.%s' % name
        if interface.report_int._reports.has_key( name ):
            del interface.report_int._reports[name]
        res = Aeroo_report(self.env.cr, name, model, tmpl_path, parser=parser)
        return res
    
    @api.model
    def unregister_report(self, name):
        service_name = 'report.%s' % name
        if interface.report_int._reports.has_key( service_name ):
            del interface.report_int._reports[service_name]
        self.env.cr.execute("SELECT * FROM ir_act_report_xml WHERE \
                             report_name = %s and active = true \
                             ORDER BY id", (name,))
        report = self.env.cr.dictfetchall()
        if report:
            report = report[-1]
            parser = rml_parse
            if report['parser_state']=='loc' and report['parser_loc']:
                parser = self.load_from_file(report['parser_loc'], report['id']) or parser
            elif report['parser_state']=='def' and report['parser_def']:
                parser = self.load_from_source(report['parser_def']) or parser
            self.register_report(report['report_name'], report['model'], report['report_rml'], parser)
    
    @api.cr
    def _lookup_report(self, cr, name):
        if 'report.' + name in interface.report_int._reports:
            new_report = interface.report_int._reports['report.' + name]
        else:
            cr.execute("SELECT id, active, report_type, parser_state, \
                        parser_loc, parser_def, model, report_rml \
                        FROM ir_act_report_xml \
                        WHERE report_name=%s", (name,))
            record = cr.dictfetchone()
            if record['report_type'] == 'aeroo':
                if record['active'] == True:
                    parser = rml_parse
                    if record['parser_state']=='loc' and record['parser_loc']:
                        parser = self.load_from_file(cr, 1, record['parser_loc'], record['id']) or parser
                    elif record['parser_state']=='def' and record['parser_def']:
                        parser = self.load_from_source(cr, 1, record['parser_def']) or parser
                    new_report = self.register_report(cr, 1, name, record['model'], record['report_rml'], parser)
                else:
                    new_report = False
            else:
                new_report = super(report_xml, self)._lookup_report(cr, name)
        return new_report

    @api.multi
    @api.depends('report_type', 'tml_source', 'report_sxw')
    def _report_content(recs):
        res = {}
        aeroo_ids = recs.search([('report_type','=','aeroo'),('id','in',recs.ids)])
        orig_ids = list(set(recs.ids).difference(aeroo_ids.ids))
        name = 'report_sxw_content'
        ancestor = recs.pool.get('ir.actions.report.xml')
        #TODO v8 how to call original function, where to get 'name' param?
        #res = orig_ids and super(report_xml, recs)._report_content({name=name) or {}
        for report in aeroo_ids:
            data = report[name + '_data']
            if report.report_type == 'aeroo' and report.tml_source == 'file' or not data and report.report_sxw:
                fp = None
                try:
                    #TODO: Probably there's a need to check if path to the report template actually present (???)
                    fp = tools.file_open(report[name[:-8]], mode='rb')
                    data = report.report_type == 'aeroo' and base64.encodestring(fp.read()) or fp.read()
                except IOError, e:
                    if e.errno == 13: # Permission denied on the template file
                        raise osv.except_osv(_(e.strerror), e.filename)
                    else:
                        logger.error("Error in '_report_content' method", exc_info=True)
                except Exception, e:
                    logger.error("Error in '_report_content' method", exc_info=True)
                    fp = False
                    data = False
                finally:
                    if fp:
                        fp.close()
            report.report_sxw_content = data

    def _get_encodings(self, cursor, user, context={}):
        l = list(set(encodings._aliases.values()))
        l.sort()
        return zip(l, l)
    
    @api.one
    def _report_content_inv(recs, name, value, arg):
        if value:
            recs.report_sxw_content = value
    
    def change_input_format(self, cr, uid, ids, in_format):
        out_format = self.pool.get('report.mimetypes').search(cr, uid, [('code','=',in_format)])
        return {
            'value':{'out_format': out_format and out_format[0] or False}
        }
    
    @api.model
    def _get_in_mimetypes(self):
        mime_obj = self.env['report.mimetypes']
        domain = self.env.context.get('allformats') and [] or [('filter_name','=',False)]
        res = mime_obj.search(domain).read(['code', 'name'])
        return [(r['code'], r['name']) for r in res]
    
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
        
    ### Fields
    charset = fields.Selection('_get_encodings', string='Charset',
        required=True)
    content_fname = fields.Char('Override Extension',size=64,
        help='Here you can override output file extension')
    styles_mode = fields.Selection([
        ('default','Not used'),
        ('global','Global'),
        ('specified','Specified'),
        ], string='Stylesheet')
    stylesheet_id = fields.Many2one('report.stylesheets', 'Template Stylesheet')
    preload_mode = fields.Selection([
        ('static',_('Static')),
        ('preload',_('Preload')),
        ], string='Preload Mode')
    tml_source = fields.Selection([
        ('database','Database'),
        ('file','File'),
        ('parser','Parser'),
        ], string='Template source', default='database', select=True)
    parser_def = fields.Text('Parser Definition')
    parser_loc = fields.Char('Parser location', size=128,
        help="Path to the parser location. Beginning of the path must be start \
              with the module name!\n Like this: {module name}/{path to the \
              parser.py file}")
    parser_state = fields.Selection([
        ('default',_('Default')),
        ('def',_('Definition')),
        ('loc',_('Location')),
        ],'State of Parser', select=True)
    report_type = fields.Selection(selection_add=[('aeroo', 'Aeroo Reports')])
    process_sep = fields.Boolean('Process Separately',
        help='Generate the report for each object separately, then merge reports.')
    in_format = fields.Selection(selection='_get_in_mimetypes',
        string='Template Mime-type')
    out_format = fields.Many2one('report.mimetypes', 'Output Mime-type')
    #report_sxw_content = fields.Binary('SXW content', compute='_report_content',
    #    fnct_inv=_report_content_inv, method=True) #TODO v8
    #report_sxw_content = fields.Binary('SXW content', compute='_report_content', inverse="_report_content_inv")
    report_sxw_content = fields.Binary('SXW content', compute='_report_content')
    active = fields.Boolean('Active', help='Disables the report if unchecked.')
    report_wizard = fields.Boolean('Report Wizard',
        help='Adds a standard wizard when the report gets invoked.')
    copies = fields.Integer(string='Number of Copies')
    fallback_false = fields.Boolean('Disable Format Fallback', 
        help='Raises error on format convertion failure. Prevents returning original report file type if no convertion is available.')
    extras = fields.Char('Extra options', compute='_get_extras', method=True,
        size=256)
    deferred = fields.Selection([
        ('off',_('Off')),
        ('adaptive',_('Adaptive')),
        ],'Deferred',
        help='Deferred (aka Batch) reporting, for reporting on large amount of data.')
    deferred_limit = fields.Integer('Deferred Records Limit',
        help='Records limit at which you are invited to start the deferred process.')
    replace_report_id = fields.Many2one('ir.actions.report.xml', 'Replace Report',
        help='Select a report that should be replaced.')
    wizard_id = fields.Many2one('ir.actions.act_window', 'Wizard Action')
    ### ends Fields
    
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False, context=None):
        orig_res = super(report_xml, self).search(args, offset=offset, limit=limit, order=order)
        by_name = len(args) == 1 and [x for x in args if x[0] == 'report_name']
        if by_name and orig_res and 'print_id' not in self.env.context:
            report_name = by_name[0][2]
            replace_rep = super(report_xml, self).search([('replace_report_id','=',orig_res.ids[0])], offset=offset, limit=limit, order=order)
            if len(replace_rep):
                return replace_rep
        return orig_res
    
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if self.env.context.get('default_report_type')=='aeroo':
            mda_mod = self.env['ir.model.data']
            if view_type == 'form':
                view_id = mda_mod.get_object_reference('report_aeroo', 'act_report_xml_view1')[1]
            elif view_type == 'tree':
                view_id = mda_mod.get_object_reference('report_aeroo', 'act_aeroo_report_xml_view_tree')[1]
        res = super(report_xml, self).fields_view_get(view_id, view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type=='form' and self.env.context.get('default_report_type')=='aeroo':
            cr = self.env.cr
            ##### Check deferred_processing module #####
            cr.execute("SELECT id, state FROM ir_module_module WHERE name='deferred_processing'")
            deferred_proc_module = cr.dictfetchone()
            if not (deferred_proc_module and deferred_proc_module['state'] in ('installed', 'to upgrade')):
                doc = etree.XML(res['arch'])
                deferred_node = doc.xpath("//field[@name='deferred']")
                modifiers = {'invisible': True}
                transfer_modifiers_to_node(modifiers, deferred_node[0])
                deferred_limit_node = doc.xpath("//field[@name='deferred_limit']")
                transfer_modifiers_to_node(modifiers, deferred_limit_node[0])
                res['arch'] = etree.tostring(doc)
            ############################################
        return res
    
    # TODO Odoo v8: Remove when issue https://github.com/odoo/odoo/issues/2899 gets
    # really resolved.
    @api.v7
    def read(self, cr, user, ids, fields=None, context=None, load='_classic_read'):
        ##### check new model fields, that while not exist in database #####
        cr.execute("SELECT name FROM ir_model_fields WHERE model = 'ir.actions.report.xml'")
        true_fields = [val[0] for val in cr.fetchall()]
        true_fields.append(self.CONCURRENCY_CHECK_FIELD)
        if fields:
            exclude_fields = set(fields).difference(set(true_fields))
            fields = filter(lambda f: f not in exclude_fields, fields)
        else:
            exclude_fields = []
        ####################################################################
        res = super(report_xml, self).read(cr, user, ids, fields, context)
        ##### set default values for new model fields, that while not exist in database ####
        if exclude_fields:
            defaults = self.default_get(cr, user, exclude_fields, context=context)
            if type(res)==list:
                for r in res:
                    for exf in exclude_fields:
                        if exf!='id':
                            r[exf] = defaults.get(exf, False)
            else:
                for exf in exclude_fields:
                    if exf!='id':
                        res[exf] = defaults.get(exf, False)
        ####################################################################################
        return res    
    
    @api.v8
    @api.multi
    def read(recs, fields=None, load='_classic_read'):
        cr = recs.env.cr
        ##### check new model fields, that while not exist in database #####
        cr.execute("SELECT name FROM ir_model_fields WHERE model = 'ir.actions.report.xml'")
        true_fields = [val[0] for val in cr.fetchall()]
        true_fields.append(recs.CONCURRENCY_CHECK_FIELD)
        if fields:
            exclude_fields = set(fields).difference(set(true_fields))
            fields = filter(lambda f: f not in exclude_fields, fields)
        else:
            exclude_fields = []
        ####################################################################
        res = super(report_xml, recs).read(fields=fields, load=load)
        ##### set default values for new model fields, that while not exist in database ####
        if exclude_fields:
            defaults = recs.default_get(exclude_fields)
            if type(res)==list:
                for r in res:
                    for exf in exclude_fields:
                        if exf!='id':
                            r[exf] = defaults.get(exf, False)
            else:
                for exf in exclude_fields:
                    if exf!='id':
                        res[exf] = defaults.get(exf, False)
        ####################################################################################
        #if len(res) == 1: #TODO v8 fails, ir.values expect dict instead of list- ir_values.py#432
        #    return res[0]
        return res
    
    @api.multi
    def unlink(recs):
        #TODO: process before delete resource
        trans_obj = recs.env['ir.translation']
        act_win_obj = recs.env['ir.actions.act_window']
        irval_obj = recs.env['ir.values']
        mdata_obj = recs.env['ir.model.data']
        trans_ids = trans_obj.search([('type','=','report'),('res_id','in',recs.ids)])
        trans_ids.unlink()
        recs.unlink_inherit_report()
        ####################################
        reports = recs.read(['report_name','model','report_wizard','replace_report_id'])
        for r in reports:
            if r['report_wizard']:
                act_win_ids = act_win_obj.search([('res_model','=','aeroo.print_actions')])
                for act_win in act_win_ids:
                    act_win_context = eval(act_win.context, {})
                    if act_win_context.get('report_action_id') == r['id']:
                        act_win.unlink()
            else:
                ir_value_ids = irval_obj.search([('value','=','ir.actions.report.xml,%s' % r['id'])])
                if ir_value_ids:
                    if not r['replace_report_id']:
                        ir_value_ids.unlink()
                    recs.unregister_report(r['report_name'])
        mdata_obj.unlink()
        ####################################
        res = super(report_xml, recs).unlink()
        return res
    
    @api.model
    def create(self, vals): #TODO convert to v8
        if 'report_type' in vals and vals['report_type'] == 'aeroo':
            parser=rml_parse
            vals['auto'] = False
            if vals['parser_state']=='loc' and vals['parser_loc']:
                parser=self.load_from_file(vals['parser_loc'], vals['name'].lower().replace(' ','_')) or parser
            elif vals['parser_state']=='def' and vals['parser_def']:
                parser=self.load_from_source(vals['parser_def']) or parser
            res_id = super(report_xml, self).create(vals)
            if vals.get('report_wizard'):
                wizard_id = self._set_report_wizard(self.env.cr, self.env.uid, vals['replace_report_id'] or res_id, \
                            res_id, linked_report_id=res_id, report_name=vals['name'], context=self.env.context)
                res_id.write({'wizard_id': wizard_id})
            if vals.get('replace_report_id'):
                self.link_inherit_report(self.env.cr, self.env.uid, res_id, new_replace_report_id=vals['replace_report_id'], context=self.env.context)
            try:
                if vals.get('active', False):
                    self.register_report(vals['report_name'], vals['model'], vals.get('report_rml', False), parser)
            except Exception, e:
                logger.error("Error in report registration", exc_info=True)
                raise except_orm(_('Report registration error !'), _('Report was not registered in system !'))
            return res_id

        res_id = super(report_xml, self).create(vals)
        return res_id
    
    @api.one
    def write(recs, vals):
        if 'report_sxw_content_data' in vals:
            if vals['report_sxw_content_data']:
                try:
                    base64.decodestring(vals['report_sxw_content_data'])
                except binascii.Error:
                    vals['report_sxw_content_data'] = False
        if vals.get('report_type', recs.report_type) != 'aeroo':
            res = super(report_xml, recs).write(vals)
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
        parser=rml_parse
        p_state = vals.get('parser_state', False)
        if p_state == 'loc':
            parser = recs.load_from_file(vals.get('parser_loc', False) or recs.parser_loc, recs.id) or parser
        elif p_state == 'def':
            parser = recs.load_from_source((vals.get('parser_loc', False) or recs.parser_def or '')) or parser
        elif p_state == 'default':
            parser = rml_parse
        elif recs.parser_state=='loc':
            parser = recs.load_from_file(recs.parser_loc, recs.id) or parser
        elif recs.parser_state=='def':
            parser = recs.load_from_source(recs.parser_def) or parser
        elif recs.parser_state=='default':
            parser = rml_parse
        if vals.get('parser_loc', False):
            parser = recs.load_from_file(vals['parser_loc'], recs.id) or parser
        elif vals.get('parser_def', False):
            parser = recs.load_from_source(vals['parser_def']) or parser
        if vals.get('report_name', False) and vals['report_name'] != recs.report_name:
            recs.delete_report_service(recs.report_name)
            report_name = vals['report_name']
        else:
            recs.delete_report_service(recs.report_name)
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
        try:
            if vals.get('active', recs.active):
                recs.register_report(report_name, vals.get('model', recs.model), vals.get('report_rml', recs.report_rml), parser)
                if not recs.active and vals.get('replace_report_id',recs.replace_report_id):
                    link_vals.update(recs.link_inherit_report(new_replace_report_id=vals.get('replace_report_id', False)))
            elif not vals.get('active', recs.active):
                recs.unregister_report(report_name)
                if not now_unlinked:
                    link_vals.update(recs.unlink_inherit_report())
        except Exception, e:
            logger.error("Error in report registration", exc_info=True)
            raise except_orm(_('Report registration error !'), _('Report was not registered in system !'))
        vals.update(link_vals)
        res = super(report_xml, recs).write(vals)
        return res
    
    @api.one
    def copy(recs, default=None):
        default = {
                'name':recs.name+" (copy)",
                'report_name':recs.report_name+"_copy",
        }
        res_id = super(report_xml, recs).copy(default)
        return res_id
    
    @api.one
    def _set_report_wizard(recs, report_action_id, linked_report_id=False, report_name=False):
        ir_values_obj = recs.env['ir.values']
        trans_obj = recs.env['ir.translation']
        if linked_report_id:
            linked_report = recs.browse(linked_report_id)
        else:
            linked_report = recs.replace_report_id
        event_id = ir_values_obj.search([('value','=',"ir.actions.report.xml,%s" % recs.id)])
        if not event_id:
            event_id = ir_values_obj.search([('value','=',"ir.actions.report.xml,%s" % linked_report.id)])
        if event_id:
            event_id = event_id[0]
            action_data = {'name': report_name or recs.name,
                           'view_mode': 'form',
                           'view_type': 'form',
                           'target': 'new',
                           'res_model': 'aeroo.print_actions',
                           'context': {'report_action_id': report_action_id}
                           }
            act_id = recs.env['ir.actions.act_window'].create(action_data)
            event_id.value = "ir.actions.act_window,%s" % act_id.id

            translations = trans_obj.search([('res_id','=',recs.id),
                ('src','=',recs.name),
                ('name','=','ir.actions.report.xml,name')])
            for trans in translations:
                trans.copy(default={'name':'ir.actions.act_window,name','res_id':act_id.id})
            return act_id.id
        return False
    
    @api.one
    def _unset_report_wizard(recs):
        ir_values_obj = recs.env['ir.values']
        trans_obj = recs.env['ir.translation']
        act_win_obj = recs.env['ir.actions.act_window']
        act_win_ids = act_win_obj.search([('res_model','=','aeroo.print_actions'),
            ('context','like',str(recs.id))])
        for act_win in act_win_ids:
            act_win_context = eval(act_win.context, {})
            if recs.id in act_win_context.get('report_action_id'):
                event_id = ir_values_obj.search([('value','=',"ir.actions.act_window,%s" % act_win.id)])
                if event_id:
                    event_id[0].value = "ir.actions.report.xml,%s" % recs.id
                ##### Copy translation from window action #####
                report_xml_trans = trans_obj.search([('res_id','=',recs.id),
                    ('src','=',act_win.name),
                    ('name','=','ir.actions.report.xml,name')])
                trans_langs = map(lambda t: t['lang'], report_xml_trans.read(['lang']))
                act_window_trans = trans_obj.search([('res_id','=',act_win.id),
                    ('src','=',act_win.name),
                    ('name','=','ir.actions.act_window,name'),
                    ('lang','not in',trans_langs)])
                for trans in act_window_trans:
                    trans.copy(default={'name':'ir.actions.report.xml,name','res_id':recs.id})
                ####### Delete wizard name translations #######
                act_window_trans = trans_obj.search([('res_id','=',act_win.id),
                    ('src','=',act_win.name),
                    ('name','=','ir.actions.act_window,name')])
                act_window_trans.unlink()
                ###############################################
                act_win.unlink()
                return True
        return False

    def _set_auto_false(self, cr, uid, ids=[]):
        if not ids:
            ids = self.search(cr, uid, [('report_type','=','aeroo'),('auto','=','True')])
        for id in ids:
            self.write(cr, uid, id, {'auto':False})
        return True
    
    @api.model
    def _get_default_outformat(self):
        res = self.env['report.mimetypes'].search([('code','=','oo-odt')])
        return res and res[0].id or False

    _defaults = {
        'tml_source': 'database',
        'in_format' : 'oo-odt',
        'out_format' : _get_default_outformat,
        'charset': 'utf_8',
        'styles_mode' : 'default',
        'preload_mode': 'static',
        'parser_state': 'default',
        'parser_def': """class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.context = context
        self.localcontext.update({})""",
        'active' : True,
        'copies': 1,
        'deferred': 'off',
        'deferred_limit': 80,
    }

