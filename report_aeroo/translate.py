# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (c) 2009-2011 Alistek (http://www.alistek.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import os
import logging
import openerp.pooler as pooler
import openerp.tools as tools
from openerp.tools.translate import trans_parse_rml, trans_parse_xsl, trans_parse_view
import fnmatch
from os.path import join
from lxml import etree
from openerp.tools import misc
from openerp.tools.misc import UpdateableStr
from openerp.tools import osutil
from babel.messages import extract

_logger = logging.getLogger(__name__)

WEB_TRANSLATION_COMMENT = "openerp-web"

def extend_trans_generate(lang, modules, cr):
    dbname = cr.dbname

    pool = pooler.get_pool(dbname)
    trans_obj = pool.get('ir.translation')
    model_data_obj = pool.get('ir.model.data')
    uid = 1
    l = pool.models.items()
    l.sort()

    query = 'SELECT name, model, res_id, module'    \
            '  FROM ir_model_data'

    query_models = """SELECT m.id, m.model, imd.module
            FROM ir_model AS m, ir_model_data AS imd
            WHERE m.id = imd.res_id AND imd.model = 'ir.model' """

    if 'all_installed' in modules:
        query += ' WHERE module IN ( SELECT name FROM ir_module_module WHERE state = \'installed\') '
        query_models += " AND imd.module in ( SELECT name FROM ir_module_module WHERE state = 'installed') "
    query_param = None
    if 'all' not in modules:
        query += ' WHERE module IN %s'
        query_models += ' AND imd.module in %s'
        query_param = (tuple(modules),)
    query += ' ORDER BY module, model, name'
    query_models += ' ORDER BY module, model'

    cr.execute(query, query_param)

    _to_translate = []
    def push_translation(module, type, name, id, source, comments=None):
        tuple = (module, source, name, id, type, comments or [])
        # empty and one-letter terms are ignored, they probably are not meant to be
        # translated, and would be very hard to translate anyway.
        if not source or len(source.strip()) <= 1:
            _logger.debug("Ignoring empty or 1-letter source term: %r", tuple)
            return
        if tuple not in _to_translate:
            _to_translate.append(tuple)

    def encode(s):
        if isinstance(s, unicode):
            return s.encode('utf8')
        return s

    for (xml_name,model,res_id,module) in cr.fetchall():
        module = encode(module)
        model = encode(model)
        xml_name = "%s.%s" % (module, encode(xml_name))

        if not pool.get(model):
            _logger.error("Unable to find object %r", model)
            continue

        exists = pool.get(model).exists(cr, uid, res_id)
        if not exists:
            _logger.warning("Unable to find object %r with id %d", model, res_id)
            continue
        obj = pool.get(model).browse(cr, uid, res_id)

        if model=='ir.ui.view':
            d = etree.XML(encode(obj.arch))
            for t in trans_parse_view(d):
                push_translation(module, 'view', encode(obj.model), 0, t)

        elif model=='ir.model.fields':
            try:
                field_name = encode(obj.name)
            except AttributeError, exc:
                _logger.error("name error in %s: %s", xml_name, str(exc))
                continue
            objmodel = pool.get(obj.model)
            if not objmodel or not field_name in objmodel._columns:
                continue
            field_def = objmodel._columns[field_name]

            name = "%s,%s" % (encode(obj.model), field_name)
            push_translation(module, 'field', name, 0, encode(field_def.string))

            if field_def.help:
                push_translation(module, 'help', name, 0, encode(field_def.help))

            if field_def.translate:
                ids = objmodel.search(cr, uid, [])
                obj_values = objmodel.read(cr, uid, ids, [field_name])
                for obj_value in obj_values:
                    res_id = obj_value['id']
                    if obj.name in ('ir.model', 'ir.ui.menu'):
                        res_id = 0
                    model_data_ids = model_data_obj.search(cr, uid, [
                        ('model', '=', model),
                        ('res_id', '=', res_id),
                        ])
                    if not model_data_ids:
                        push_translation(module, 'model', name, 0, encode(obj_value[field_name]))

            if hasattr(field_def, 'selection') and isinstance(field_def.selection, (list, tuple)):
                for dummy, val in field_def.selection:
                    push_translation(module, 'selection', name, 0, encode(val))

        elif model=='ir.actions.report.xml':
            name = encode(obj.report_name)
            fname = ""
            ##### Changes for Aeroo ######
            if obj.report_type == 'aeroo':
                trans_ids = trans_obj.search(cr, uid, [('type', '=', 'report'),('res_id', '=', obj.id)])
                for t in trans_obj.read(cr, uid, trans_ids, ['name','src']):
                    push_translation(module, "report", t['name'], xml_name, t['src'].encode('UTF-8'))
            ##############################
            else:
                if obj.report_rml:
                    fname = obj.report_rml
                    parse_func = trans_parse_rml
                    report_type = "report"
                elif obj.report_xsl:
                    fname = obj.report_xsl
                    parse_func = trans_parse_xsl
                    report_type = "xsl"
                if fname and obj.report_type in ('pdf', 'xsl'):
                    try:
                        report_file = misc.file_open(fname)
                        try:
                            d = etree.parse(report_file)
                            for t in parse_func(d.iter()):
                                push_translation(module, report_type, name, 0, t)
                        finally:
                            report_file.close()
                    except (IOError, etree.XMLSyntaxError):
                        _logger.exception("couldn't export translation for report %s %s %s", name, report_type, fname)

        for field_name,field_def in obj._table._columns.items():
            if field_def.translate:
                name = model + "," + field_name
                try:
                    trad = getattr(obj, field_name) or ''
                except:
                    trad = ''
                push_translation(module, 'model', name, xml_name, encode(trad))

        # End of data for ir.model.data query results

    cr.execute(query_models, query_param)

    def push_constraint_msg(module, term_type, model, msg):
        if not hasattr(msg, '__call__'):
            push_translation(encode(module), term_type, encode(model), 0, encode(msg))

    def push_local_constraints(module, model, cons_type='sql_constraints'):
        """Climb up the class hierarchy and ignore inherited constraints
           from other modules"""
        term_type = 'sql_constraint' if cons_type == 'sql_constraints' else 'constraint'
        msg_pos = 2 if cons_type == 'sql_constraints' else 1
        for cls in model.__class__.__mro__:
            if getattr(cls, '_module', None) != module:
                continue
            constraints = getattr(cls, '_local_' + cons_type, [])
            for constraint in constraints:
                push_constraint_msg(module, term_type, model._name, constraint[msg_pos])
            
    for (_, model, module) in cr.fetchall():
        model_obj = pool.get(model)

        if not model_obj:
            _logger.error("Unable to find object %r", model)
            continue

        if model_obj._constraints:
            push_local_constraints(module, model_obj, 'constraints')

        if model_obj._sql_constraints:
            push_local_constraints(module, model_obj, 'sql_constraints')

    def get_module_from_path(path, mod_paths=None):
        if not mod_paths:
            # First, construct a list of possible paths
            def_path = os.path.abspath(os.path.join(tools.config['root_path'], 'addons'))     # default addons path (base)
            ad_paths= map(lambda m: os.path.abspath(m.strip()),tools.config['addons_path'].split(','))
            mod_paths=[def_path]
            for adp in ad_paths:
                mod_paths.append(adp)
                if not os.path.isabs(adp):
                    mod_paths.append(adp)
                elif adp.startswith(def_path):
                    mod_paths.append(adp[len(def_path)+1:])
        for mp in mod_paths:
            if path.startswith(mp) and (os.path.dirname(path) != mp):
                path = path[len(mp)+1:]
                return path.split(os.path.sep)[0]
        return 'base'   # files that are not in a module are considered as being in 'base' module

    modobj = pool.get('ir.module.module')
    installed_modids = modobj.search(cr, uid, [('state', '=', 'installed')])
    installed_modules = map(lambda m: m['name'], modobj.read(cr, uid, installed_modids, ['name']))

    root_path = os.path.join(tools.config['root_path'], 'addons')

    apaths = map(os.path.abspath, map(str.strip, tools.config['addons_path'].split(',')))
    if root_path in apaths:
        path_list = apaths
    else :
        path_list = [root_path,] + apaths

    # Also scan these non-addon paths
    for bin_path in ['osv', 'report' ]:
        path_list.append(os.path.join(tools.config['root_path'], bin_path))

    _logger.debug("Scanning modules at paths: ", path_list)

    mod_paths = []

    def verified_module_filepaths(fname, path, root):
        fabsolutepath = join(root, fname)
        frelativepath = fabsolutepath[len(path):]
        display_path = "addons%s" % frelativepath
        module = get_module_from_path(fabsolutepath, mod_paths=mod_paths)
        if ('all' in modules or module in modules) and module in installed_modules:
            return module, fabsolutepath, frelativepath, display_path
        return None, None, None, None

    def babel_extract_terms(fname, path, root, extract_method="python", trans_type='code',
                               extra_comments=None, extract_keywords={'_': None}):
        module, fabsolutepath, _, display_path = verified_module_filepaths(fname, path, root)
        extra_comments = extra_comments or []
        if module:
            src_file = open(fabsolutepath, 'r')
            try:
                #for lineno, message, comments in extract.extract(extract_method, src_file,
                #                                                 keywords=extract_keywords):
                for extracted in extract.extract(extract_method, src_file,
                                                 keywords=extract_keywords):
                    # Babel 0.9.6 yields lineno, message, comments
                    # Babel 1.3 yields lineno, message, comments, context
                    lineno, message, comments = extracted[:3]
                    push_translation(module, trans_type, display_path, lineno,
                                     encode(message), comments + extra_comments)
            except Exception:
                _logger.exception("Failed to extract terms from %s", fabsolutepath)
            finally:
                src_file.close()

    for path in path_list:
        _logger.debug("Scanning files of modules at %s", path)
        for root, dummy, files in osutil.walksymlinks(path):
            for fname in fnmatch.filter(files, '*.py'):
                babel_extract_terms(fname, path, root)
            # mako provides a babel extractor: http://docs.makotemplates.org/en/latest/usage.html#babel
            for fname in fnmatch.filter(files, '*.mako'):
                babel_extract_terms(fname, path, root, 'mako', trans_type='report')
            # Javascript source files in the static/src/js directory, rest is ignored (libs)
            if fnmatch.fnmatch(root, '*/static/src/js*'):
                for fname in fnmatch.filter(files, '*.js'):
                    babel_extract_terms(fname, path, root, 'javascript',
                                        extra_comments=[WEB_TRANSLATION_COMMENT],
                                        extract_keywords={'_t': None, '_lt': None})
            # QWeb template files
            if fnmatch.fnmatch(root, '*/static/src/xml*'):
                for fname in fnmatch.filter(files, '*.xml'):
                    babel_extract_terms(fname, path, root, 'openerp.tools.translate:babel_extract_qweb',
                                        extra_comments=[WEB_TRANSLATION_COMMENT])

    out = []
    _to_translate.sort()
    # translate strings marked as to be translated
    for module, source, name, id, type, comments in _to_translate:
        trans = '' if not lang else trans_obj._get_source(cr, uid, name, type, lang, source)
        out.append([module, type, name, id, source, encode(trans) or '', comments])
    return out

import sys
sys.modules['openerp.tools.translate'].trans_generate = extend_trans_generate

