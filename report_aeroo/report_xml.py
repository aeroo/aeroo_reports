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

from openerp.osv import osv,fields
from openerp.osv.orm import transfer_modifiers_to_node
import openerp.netsvc as netsvc
from report_aeroo import Aeroo_report, aeroo_ooo_test
from openerp.report.report_sxw import rml_parse
from openerp.report import interface
import base64, binascii
import openerp.tools as tools
import encodings
from openerp.tools.translate import _

import imp, sys, os
import zipimport
from openerp.tools.config import config
from lxml import etree

import logging
logger = logging.getLogger('report_aeroo')

class report_stylesheets(osv.osv):
    '''
    Aeroo Report Stylesheets
    '''
    _name = 'report.stylesheets'
    _description = 'Report Stylesheets'
    
    _columns = {
        'name':fields.char('Name', size=64, required=True),
        'report_styles' : fields.binary('Template Stylesheet', help='OpenOffice.org stylesheet (.odt)'),
        
    }

class res_company(osv.osv):
    _name = 'res.company'
    _inherit = 'res.company'

    _columns = {
        'stylesheet_id':fields.many2one('report.stylesheets', 'Aeroo Global Stylesheet'),
    }

class report_mimetypes(osv.osv):
    '''
    Aeroo Report Mime-Type
    '''
    _name = 'report.mimetypes'
    _description = 'Report Mime-Types'

    _columns = {
        'name':fields.char('Name', size=64, required=True, readonly=True),
        'code':fields.char('Code', size=16, required=True, readonly=True),
        'compatible_types':fields.char('Compatible Mime-Types', size=128, readonly=True),
        'filter_name':fields.char('Filter Name', size=128, readonly=True),
        
    }

class report_xml(osv.osv):
    _name = 'ir.actions.report.xml'
    _inherit = 'ir.actions.report.xml'

    def load_from_file(self, path, dbname, key):
        class_inst = None
        expected_class = 'Parser'

        try:
            ad = os.path.abspath(os.path.join(tools.ustr(config['root_path']), u'addons'))
            mod_path_list = map(lambda m: os.path.abspath(tools.ustr(m.strip())), config['addons_path'].split(','))
            mod_path_list.append(ad)
            mod_path_list = list(set(mod_path_list))

            for mod_path in mod_path_list:
                if os.path.lexists(mod_path+os.path.sep+path.split(os.path.sep)[0]):
                    filepath=mod_path+os.path.sep+path
                    filepath = os.path.normpath(filepath)
                    sys.path.append(os.path.dirname(filepath))
                    mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
                    mod_name = '%s_%s_%s' % (dbname,mod_name,key)

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
            raise osv.except_osv(_('Syntax Error !'), e)
        except Exception, e:
            logger.error('Error loading report parser: %s'+(filepath and ' "%s"' % filepath or ''), e)
            return None

    def load_from_source(self, source):
        expected_class = 'Parser'
        context = {'Parser':None}
        try:
            exec source.replace('\r','') in context
            return context['Parser']
        except SyntaxError, e:
            raise osv.except_osv(_('Syntax Error !'), e)
        except Exception, e:
            logger.error("Error in 'load_from_source' method", __name__, exc_info=True)
            return None

    def link_inherit_report(self, cr, uid, report, new_replace_report_id=False, context={}):
        res = {}
        if new_replace_report_id:
            inherit_report = self.browse(cr, uid, new_replace_report_id, context=context)
        else:
            inherit_report = report.replace_report_id

        if inherit_report:
            ir_values_obj = self.pool.get('ir.values')
            if inherit_report.report_wizard:
                src_action_type = 'ir.actions.act_window'
                action_id = report.wizard_id
            else:
                src_action_type = 'ir.actions.report.xml'
                action_id = inherit_report.id
            event_id = ir_values_obj.search(cr, uid, [('value','=',"%s,%s" % (src_action_type,action_id))])
            if event_id:
                event_id = event_id[0]
                if report.report_wizard:
                    dest_action_type = 'ir.actions.act_window'
                    if report.wizard_id:
                        action_id = report.wizard_id
                    else:
                        action_id = self._set_report_wizard(cr, uid, inherit_report.id, report.id, linked_report_id=report.id, report_name=report.name, context=context)
                        res['wizard_id'] = action_id
                else:
                    dest_action_type = 'ir.actions.report.xml'
                    action_id = report.id
                ir_values_obj.write(cr, uid, event_id, {'value':"%s,%s" % (dest_action_type,action_id)}, context=context)
        return res

    def unlink_inherit_report(self, cr, uid, ids, context={}):
        res = {}
        report_id = isinstance(ids, list) and ids[0] or ids
        report = self.browse(cr, uid, report_id, context=context)
        keep_wizard = context and context.get('keep_wizard') or False

        if report.replace_report_id:
            ir_values_obj = self.pool.get('ir.values')
            if report.report_wizard:
                src_action_type = 'ir.actions.act_window'
                action_id = report.wizard_id.id
                if not keep_wizard:
                    res['wizard_id'] = False
            else:
                src_action_type = 'ir.actions.report.xml'
                action_id = report.id
            event_id = ir_values_obj.search(cr, uid, [('value','=',"%s,%s" % (src_action_type,action_id))])
            if event_id:
                event_id = event_id[0]
                if report.replace_report_id.report_wizard:
                    dest_action_type = 'ir.actions.act_window'
                    action_id = report.wizard_id.id
                else:
                    dest_action_type = 'ir.actions.report.xml'
                    action_id = report.replace_report_id.id
                ir_values_obj.write(cr, uid, event_id, {'value':"%s,%s" % (dest_action_type,action_id)}, context=context)

            if not keep_wizard and report.wizard_id and not res.get('wizard_id',True):
                report.wizard_id.unlink(context=context)
        return res

    def delete_report_service(self, name):
        name = 'report.%s' % name
        if interface.report_int._reports.has_key( name ):
            del interface.report_int._reports[name]

    def register_report(self, cr, name, model, tmpl_path, parser):
        name = 'report.%s' % name
        if interface.report_int._reports.has_key( name ):
            del interface.report_int._reports[name]
        return Aeroo_report(cr, name, model, tmpl_path, parser=parser)

    def unregister_report(self, cr, name):
        service_name = 'report.%s' % name
        if interface.report_int._reports.has_key( service_name ):
            del interface.report_int._reports[service_name]
        cr.execute("SELECT * FROM ir_act_report_xml WHERE report_name = %s and active = true ORDER BY id", (name,))
        report = cr.dictfetchall()
        if report:
            report = report[-1]
            parser=rml_parse
            if report['parser_state']=='loc' and report['parser_loc']:
                parser=self.load_from_file(report['parser_loc'], cr.dbname, report['id']) or parser
            elif report['parser_state']=='def' and report['parser_def']:
                parser=self.load_from_source("from report import report_sxw\n"+report['parser_def']) or parser
            self.register_report(cr, report['report_name'], report['model'], report['report_rml'], parser)

    def _lookup_report(self, cr, name):
        if 'report.' + name in interface.report_int._reports:
            new_report = interface.report_int._reports['report.' + name]
        else:
            cr.execute("SELECT * FROM ir_act_report_xml WHERE report_name=%s", (name,))
            record = cr.dictfetchone()
            if record['report_type']=='aeroo':
                if record['active'] == True:
                    parser=rml_parse
                    if record['parser_state']=='loc' and record['parser_loc']:
                        parser=self.load_from_file(record['parser_loc'], cr.dbname, record['id']) or parser
                    elif record['parser_state']=='def' and record['parser_def']:
                        parser=self.load_from_source("from report import report_sxw\n"+record['parser_def']) or parser
                    new_report = self.register_report(cr, record['report_name'], record['model'], record['report_rml'], parser)
                else:
                    new_report = False
            else:
                new_report = super(report_xml, self)._lookup_report(cr, name)
        return new_report

    #def register_all(self, cr):
    #    super(report_xml, self).register_all(cr)
    #    ########### Run OpenOffice service ###########
    #    try:
    #        from report_aeroo_ooo.report import OpenOffice_service
    #    except Exception, e:
    #        OpenOffice_service = False

    #    if OpenOffice_service:
    #        cr.execute("SELECT id, state FROM ir_module_module WHERE name='report_aeroo_ooo'")
    #        helper_module = cr.dictfetchone()
    #        helper_installed = helper_module and helper_module['state']=='installed'

    #    if OpenOffice_service and helper_installed:
    #        cr.execute("SELECT host, port FROM oo_config")
    #        host, port = cr.fetchone()
    #        try:
    #            OpenOffice_service(cr, host, port, allow_raise_errors=False)
    #            netsvc.Logger().notifyChannel('report_aeroo', netsvc.LOG_INFO, "OpenOffice.org connection successfully established")
    #        except Exception, e:
    #            cr.rollback()
    #            netsvc.Logger().notifyChannel('report_aeroo', netsvc.LOG_WARNING, str(e))
    #    ##############################################

    #    cr.execute("SELECT * FROM ir_act_report_xml WHERE report_type = 'aeroo' and active = true ORDER BY id") # change for OpenERP 6.0
    #    records = cr.dictfetchall()
    #    for record in records:
    #        parser=rml_parse
    #        if record['parser_state']=='loc' and record['parser_loc']:
    #            parser=self.load_from_file(record['parser_loc'], cr.dbname, record['id']) or parser
    #        elif record['parser_state']=='def' and record['parser_def']:
    #            parser=self.load_from_source("from report import report_sxw\n"+record['parser_def']) or parser
    #        self.register_report(cr, record['report_name'], record['model'], record['report_rml'], parser)

    def _report_content(self, cursor, user, ids, name, arg, context=None):
        res = {}
        aeroo_ids = self.search(cursor, 1, [('report_type','=','aeroo'),('id','in',ids)], context=context)
        orig_ids = list(set(ids).difference(aeroo_ids))
        res = orig_ids and super(report_xml, self)._report_content(cursor, 1, orig_ids, name, arg, context) or {}
        for report in self.read(cursor, 1, aeroo_ids, ['tml_source','report_type','report_sxw_content_data', 'report_sxw','report_rml','report_file'], context=context):
            data = report[name + '_data']
            #logger.error(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>1..."+str(report), exc_info=True)
            if report['report_type']=='aeroo' and report['tml_source']=='file' or not data and report[name[:-8]]:
                #logger.error(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>2..."+(data and str(len(data)) or ''), exc_info=True)
                fp = None
                try:
                    #TODO: Probably there's a need to check if path to the report template actually present (???)
                    fp = tools.file_open(report[name[:-8]], mode='rb')
                    data = report['report_type']=='aeroo' and base64.encodestring(fp.read()) or fp.read()
                except IOError, e:
                    if e.errno==13: # Permission denied on the template file
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
            res[report['id']] = data
            #logger.error(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>3..."+(data and str(len(data)) or ''), exc_info=True)
        return res

    def _get_encodings(self, cursor, user, context={}):
        l = list(set(encodings._aliases.values()))
        l.sort()
        return zip(l, l)

    def _report_content_inv(self, cursor, user, id, name, value, arg, context=None):
        if value:
            self.write(cursor, user, id, {name+'_data': value}, context=context)

    def change_input_format(self, cr, uid, ids, in_format):
        out_format = self.pool.get('report.mimetypes').search(cr, uid, [('code','=',in_format)])
        return {
            'value':{'out_format': out_format and out_format[0] or False}
        }

    def _get_in_mimetypes(self, cr, uid, context={}):
        obj = self.pool.get('report.mimetypes')
        domain = context.get('allformats') and [] or [('filter_name','=',False)]
        ids = obj.search(cr, uid, domain, context=context)
        res = obj.read(cr, uid, ids, ['code', 'name'], context)
        return [(r['code'], r['name']) for r in res]

    def _get_xml_id(self, cr, uid, ids, *args, **kwargs):
        model_data_obj = self.pool.get('ir.model.data')
        data_ids = model_data_obj.search(cr, uid, [('model', '=', self._name), ('res_id', 'in', ids)])
        data_results = model_data_obj.read(cr, uid, data_ids, ['module', 'name', 'res_id'])
        result = {}
        for id in ids:
            result[id] = False
        for record in data_results:
            result[record['res_id']] = '%(module)s.%(name)s' % record
        return result

    def _get_extras(self, cr, uid, ids, *args, **kwargs):
        result = []
        if aeroo_ooo_test(cr):
            result.append('aeroo_ooo')
        ##### Check deferred_processing module #####
        cr.execute("SELECT id, state FROM ir_module_module WHERE name='deferred_processing'")
        deferred_proc_module = cr.dictfetchone()
        if deferred_proc_module and deferred_proc_module['state'] in ('installed', 'to upgrade'):
            result.append('deferred_processing')
        ############################################
        return dict.fromkeys(ids, ','.join(result))

    _columns = {
        'charset':fields.selection(_get_encodings, string='Charset', required=True),
        'content_fname': fields.char('Override Extension',size=64, help='Here you can override output file extension'),
        'styles_mode': fields.selection([
            ('default','Not used'),
            ('global', 'Global'),
            ('specified', 'Specified'),
            ], string='Stylesheet'),
        'stylesheet_id':fields.many2one('report.stylesheets', 'Template Stylesheet'),
        'preload_mode':fields.selection([
            ('static',_('Static')),
            ('preload',_('Preload')),
        ],'Preload Mode'),
        'tml_source':fields.selection([
            ('database','Database'),
            ('file','File'),
            ('parser','Parser'),
        ],'Template source', select=True),
        'parser_def': fields.text('Parser Definition'),
        'parser_loc':fields.char('Parser location', size=128, help="Path to the parser location. Beginning of the path must be start with the module name!\nLike this: {module name}/{path to the parser.py file}"),
        'parser_state':fields.selection([
            ('default',_('Default')),
            ('def',_('Definition')),
            ('loc',_('Location')),
        ],'State of Parser', select=True),
        'in_format': fields.selection(_get_in_mimetypes, 'Template Mime-type'),
        'out_format':fields.many2one('report.mimetypes', 'Output Mime-type'),
        'report_sxw_content': fields.function(_report_content,
            fnct_inv=_report_content_inv, method=True,
            type='binary', string='SXW content',),
        'active':fields.boolean('Active', help='Disables the report if unchecked.'),
        'report_wizard':fields.boolean('Report Wizard'),
        'copies': fields.integer('Number of Copies'),
        'fallback_false':fields.boolean('Disable Format Fallback'),
        'xml_id': fields.function(_get_xml_id, type='char', size=128, string="XML ID",
                                  method=True, help="ID of the report defined in xml file"),
        'extras': fields.function(_get_extras, method=True, type='char', size='256', string='Extra options'),
        'deferred':fields.selection([
            ('off',_('Off')),
            ('adaptive',_('Adaptive')),
            
        ],'Deferred', help='Deferred (aka Batch) reporting, for reporting on large amount of data.'),
        'deferred_limit': fields.integer('Deferred Records Limit', help='Records limit at which you are invited to start the deferred process.'),
        'replace_report_id':fields.many2one('ir.actions.report.xml', 'Replace Report'),
        'wizard_id':fields.many2one('ir.actions.act_window', 'Wizard Action'),
        
    }

    def fields_view_get(self, cr, user, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        if not context:
            context = {}
        res = super(report_xml, self).fields_view_get(cr, user, view_id, view_type, context, toolbar, submenu)
        if view_type=='form' and context.get('default_report_type')=='aeroo':
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

    def unlink(self, cr, uid, ids, context={}):
        #TODO: process before delete resource
        trans_obj = self.pool.get('ir.translation')
        act_win_obj = self.pool.get('ir.actions.act_window')
        trans_ids = trans_obj.search(cr, uid, [('type','=','report'),('res_id','in',ids)])
        trans_obj.unlink(cr, uid, trans_ids)
        self.unlink_inherit_report(cr, uid, ids, context=context)
        ####################################
        reports = self.read(cr, uid, ids, ['report_name','model','report_wizard','replace_report_id'])
        for r in reports:
            if r['report_wizard']:
                act_win_ids = act_win_obj.search(cr, uid, [('res_model','=','aeroo.print_actions')], context=context)
                for act_win in act_win_obj.browse(cr, uid, act_win_ids, context=context):
                    act_win_context = eval(act_win.context, {})
                    if act_win_context.get('report_action_id')==r['id']:
                        act_win.unlink()
            else:
                ir_value_ids = self.pool.get('ir.values').search(cr, uid, [('value','=','ir.actions.report.xml,%s' % r['id'])])
                if ir_value_ids:
                    if not r['replace_report_id']:
                        self.pool.get('ir.values').unlink(cr, uid, ir_value_ids)
                    self.unregister_report(cr, r['report_name'])
        self.pool.get('ir.model.data').unlink(cr, uid, ids, context=context)
        ####################################
        res = super(report_xml, self).unlink(cr, uid, ids, context)
        return res

    def create(self, cr, user, vals, context={}):
        if 'report_type' in vals and vals['report_type'] == 'aeroo':
            parser=rml_parse
            vals['auto'] = False
            if vals['parser_state']=='loc' and vals['parser_loc']:
                parser=self.load_from_file(vals['parser_loc'], cr.dbname, vals['name'].lower().replace(' ','_')) or parser
            elif vals['parser_state']=='def' and vals['parser_def']:
                parser=self.load_from_source("from report import report_sxw\n"+vals['parser_def']) or parser

            res_id = super(report_xml, self).create(cr, user, vals, context)
            if vals.get('report_wizard'):
                wizard_id = self._set_report_wizard(cr, user, vals['replace_report_id'] or res_id, \
                            res_id, linked_report_id=res_id, report_name=vals['name'], context=context)
                self.write(cr, user, res_id, {'wizard_id': wizard_id}, context)
            if vals.get('replace_report_id'):
                report = self.browse(cr, user, res_id, context=context)
                self.link_inherit_report(cr, user, report, new_replace_report_id=vals['replace_report_id'], context=context)
            try:
                if vals.get('active', False):
                    self.register_report(cr, vals['report_name'], vals['model'], vals.get('report_rml', False), parser)
            except Exception, e:
                logger.error("Error in report registration", exc_info=True)
                raise osv.except_osv(_('Report registration error !'), _('Report was not registered in system !'))
            return res_id

        res_id = super(report_xml, self).create(cr, user, vals, context)
        return res_id

    def write(self, cr, user, ids, vals, context={}):
        #logger.error("=========================================== Values to be written: "+str(vals))
        import traceback
        #logger.error("=========================================== "+str(traceback.format_exc()))
        #print 1/0
        if 'report_sxw_content_data' in vals:
            if vals['report_sxw_content_data']:
                try:
                    base64.decodestring(vals['report_sxw_content_data'])
                except binascii.Error:
                    vals['report_sxw_content_data'] = False
        if type(ids)==list:
            ids = ids[0]
        record = self.browse(cr, user, ids)
        #if context and 'model' in vals and not self.pool.get('ir.model').search(cr, user, [('model','=',vals['model'])]):
        #    raise osv.except_osv(_('Object model is not correct !'),_('Please check "Object" field !') )
        if vals.get('report_type', record.report_type) == 'aeroo':
            if vals.get('report_wizard') and vals.get('active', record.active) and \
                        (record.replace_report_id and vals.get('replace_report_id',True) or not record.replace_report_id):
                vals['wizard_id'] = self._set_report_wizard(cr, user, ids, ids, linked_report_id=vals.get('replace_report_id'), context=context)
                record.report_wizard = True
                record.wizard_id = vals['wizard_id']
            elif 'report_wizard' in vals and not vals['report_wizard'] and record.report_wizard:
                self._unset_report_wizard(cr, user, ids, context)
                vals['wizard_id'] = False
                record.report_wizard = False
                record.wizard_id = False
            parser=rml_parse
            if vals.get('parser_state', False)=='loc':
                parser = self.load_from_file(vals.get('parser_loc', False) or record.parser_loc, cr.dbname, record.id) or parser
            elif vals.get('parser_state', False)=='def':
                parser = self.load_from_source("from report import report_sxw\n"+(vals.get('parser_loc', False) or record.parser_def or '')) or parser
            elif vals.get('parser_state', False)=='default':
                parser = rml_parse
            elif record.parser_state=='loc':
                parser = self.load_from_file(record.parser_loc, cr.dbname, record.id) or parser
            elif record.parser_state=='def':
                parser = self.load_from_source("from report import report_sxw\n"+record.parser_def) or parser
            elif record.parser_state=='default':
                parser = rml_parse

            if vals.get('parser_loc', False):
                parser=self.load_from_file(vals['parser_loc'], cr.dbname, record.id) or parser
            elif vals.get('parser_def', False):
                parser=self.load_from_source("from report import report_sxw\n"+vals['parser_def']) or parser
            if vals.get('report_name', False) and vals['report_name']!=record.report_name:
                self.delete_report_service(record.report_name)
                report_name = vals['report_name']
            else:
                self.delete_report_service(record.report_name)
                report_name = record.report_name
            ##### Link / unlink inherited report #####
            link_vals = {}
            now_unlinked = False
            if 'replace_report_id' in vals and vals.get('active', record.active):
                if vals['replace_report_id']:
                    if record.replace_report_id and vals['replace_report_id']!=record.replace_report_id.id:
                        ctx = context.copy()
                        ctx['keep_wizard'] = True # keep window action for wizard, if only inherit report changed
                        link_vals.update(self.unlink_inherit_report(cr, user, ids, ctx))
                        now_unlinked = True
                    link_vals.update(self.link_inherit_report(cr, user, record, new_replace_report_id=vals['replace_report_id'], context=context))
                    self.register_report(cr, report_name, vals.get('model', record.model), vals.get('report_rml', record.report_rml), parser)
                else:
                    link_vals.update(self.unlink_inherit_report(cr, user, ids, context=context))
                    now_unlinked = True
            ##########################################
            try:
                if vals.get('active', record.active):
                    self.register_report(cr, report_name, vals.get('model', record.model), vals.get('report_rml', record.report_rml), parser)
                    if not record.active and vals.get('replace_report_id',record.replace_report_id):
                        link_vals.update(self.link_inherit_report(cr, user, record, new_replace_report_id=vals.get('replace_report_id',False), context=context))
                elif not vals.get('active', record.active):
                    self.unregister_report(cr, report_name)
                    if not now_unlinked:
                        link_vals.update(self.unlink_inherit_report(cr, user, ids, context=context))
            except Exception, e:
                logger.error("Error in report registration", exc_info=True)
                raise osv.except_osv(_('Report registration error !'), _('Report was not registered in system !'))

            vals.update(link_vals)
            res = super(report_xml, self).write(cr, user, ids, vals, context)
            return res

        res = super(report_xml, self).write(cr, user, ids, vals, context)
        return res

    def copy(self, cr, uid, id, default=None, context=None):
        record = self.pool.get('ir.actions.report.xml').browse(cr, uid, id, context=context)
        default = {
                'name':record.name+" (copy)",
                'report_name':record.report_name+"_copy",
        }
        res_id = super(report_xml, self).copy(cr, uid, id, default, context)
        return res_id

    def _set_report_wizard(self, cr, uid, ids, report_action_id, linked_report_id=False, report_name=False, context=None):
        id = isinstance(ids, list) and ids[0] or ids
        report = self.browse(cr, uid, id, context=context)
        ir_values_obj = self.pool.get('ir.values')
        trans_obj = self.pool.get('ir.translation')
        if linked_report_id:
            linked_report = self.browse(cr, uid, linked_report_id, context=context)
        else:
            linked_report = report.replace_report_id
        event_id = ir_values_obj.search(cr, uid, [('value','=',"ir.actions.report.xml,%s" % report.id)])
        if not event_id:
            event_id = ir_values_obj.search(cr, uid, [('value','=',"ir.actions.report.xml,%s" % linked_report.id)])
        if event_id:
            event_id = event_id[0]
            action_data = {'name':report_name or report.name,
                           'view_mode':'form',
                           'view_type':'form',
                           'target':'new',
                           'res_model':'aeroo.print_actions',
                           'context':{'report_action_id':report_action_id}
                           }
            act_id = self.pool.get('ir.actions.act_window').create(cr, uid, action_data, context)
            ir_values_obj.write(cr, uid, event_id, {'value':"ir.actions.act_window,%s" % act_id}, context=context)

            translations = trans_obj.search(cr, uid, [('res_id','=',report.id),('src','=',report.name),('name','=','ir.actions.report.xml,name')])
            for trans in trans_obj.browse(cr, uid, translations, context):
                trans_obj.copy(cr, uid, trans.id, default={'name':'ir.actions.act_window,name','res_id':act_id})
            return act_id
        return False

    def _unset_report_wizard(self, cr, uid, ids, context=None):
        id = isinstance(ids, list) and ids[0] or ids
        ir_values_obj = self.pool.get('ir.values')
        trans_obj = self.pool.get('ir.translation')
        act_win_obj = self.pool.get('ir.actions.act_window')
        act_win_ids = act_win_obj.search(cr, uid, [('res_model','=','aeroo.print_actions')], context=context)
        for act_win in act_win_obj.browse(cr, uid, act_win_ids, context=context):
            act_win_context = eval(act_win.context, {})
            if act_win_context.get('report_action_id')==id:
                event_id = ir_values_obj.search(cr, uid, [('value','=',"ir.actions.act_window,%s" % act_win.id)])
                if event_id:
                    event_id = event_id[0]
                    ir_values_obj.write(cr, uid, event_id, {'value':"ir.actions.report.xml,%s" % id}, context=context)
                ##### Copy translation from window action #####
                report_xml_trans = trans_obj.search(cr, uid, [('res_id','=',id),('src','=',act_win.name),('name','=','ir.actions.report.xml,name')])
                trans_langs = map(lambda t: t['lang'], trans_obj.read(cr, uid, report_xml_trans, ['lang'], context))
                act_window_trans = trans_obj.search(cr, uid, [('res_id','=',act_win.id),('src','=',act_win.name), \
                                            ('name','=','ir.actions.act_window,name'),('lang','not in',trans_langs)])
                for trans in trans_obj.browse(cr, uid, act_window_trans, context):
                    trans_obj.copy(cr, uid, trans.id, default={'name':'ir.actions.report.xml,name','res_id':id})
                ####### Delete wizard name translations #######
                act_window_trans = trans_obj.search(cr, uid, [('res_id','=',act_win.id),('src','=',act_win.name),('name','=','ir.actions.act_window,name')])
                trans_obj.unlink(cr, uid, act_window_trans, context)
                ###############################################
                act_win.unlink(context=context)
                return True
        return False

    def _set_auto_false(self, cr, uid, ids=[]):
        if not ids:
            ids = self.search(cr, uid, [('report_type','=','aeroo'),('auto','=','True')])
        for id in ids:
            self.write(cr, uid, id, {'auto':False})
        return True

    def _get_default_outformat(self, cr, uid, context):
        obj = self.pool.get('report.mimetypes')
        res = obj.search(cr, uid, [('code','=','oo-odt')])
        return res and res[0] or False

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

