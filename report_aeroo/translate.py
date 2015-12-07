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
import openerp.tools as tools
from openerp.tools.translate import trans_parse_rml, _extract_translatable_qweb_terms
# from openerp.tools.translate import trans_parse_rml, trans_parse_xsl, trans_parse_view, _extract_translatable_qweb_terms
import fnmatch
from os.path import join
from lxml import etree
from openerp.tools import misc
from openerp.tools import osutil
from babel.messages import extract
import openerp

_logger = logging.getLogger(__name__)

WEB_TRANSLATION_COMMENT = "openerp-web"
ENGLISH_SMALL_WORDS = set("as at by do go if in me no of ok on or to up us we".split())


def extend_trans_generate(lang, modules, cr):
    dbname = cr.dbname

    registry = openerp.registry(dbname)
    trans_obj = registry['ir.translation']
    model_data_obj = registry['ir.model.data']
    uid = 1

    query = 'SELECT name, model, res_id, module' \
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

    _to_translate = set()
    def push_translation(module, type, name, id, source, comments=None):
        # empty and one-letter terms are ignored, they probably are not meant to be
        # translated, and would be very hard to translate anyway.
        if not source or len(source.strip()) <= 1:
            return

        tnx = (module, source, name, id, type, tuple(comments or ()))
        _to_translate.add(tnx)

    def encode(s):
        if isinstance(s, unicode):
            return s.encode('utf8')
        return s

    def push(mod, type, name, res_id, term):
        term = (term or '').strip()
        if len(term) > 2 or term in ENGLISH_SMALL_WORDS:
            push_translation(mod, type, name, res_id, term)

    def get_root_view(xml_id):
        view = model_data_obj.xmlid_to_object(cr, uid, xml_id)
        if view:
            while view.mode != 'primary':
                view = view.inherit_id
        xml_id = view.get_external_id(cr, uid).get(view.id, xml_id)
        return xml_id

    for (xml_name,model,res_id,module) in cr.fetchall():
        module = encode(module)
        model = encode(model)
        xml_name = "%s.%s" % (module, encode(xml_name))

        if model not in registry:
            _logger.error("Unable to find object %r", model)
            continue

        Model = registry[model]
        if not Model._translate:
            # explicitly disabled
            continue

        obj = Model.browse(cr, uid, res_id)
        if not obj.exists():
            _logger.warning("Unable to find object %r with id %d", model, res_id)
            continue

        if model=='ir.ui.view':
            d = etree.XML(encode(obj.arch))
            if obj.type == 'qweb':
                view_id = get_root_view(xml_name)
                push_qweb = lambda t,l: push(module, 'view', 'website', view_id, t)
                _extract_translatable_qweb_terms(d, push_qweb)
#             else:
#                 push_view = lambda t,l: push(module, 'view', obj.model, xml_name, t)
#                 trans_parse_view(d, push_view)
        elif model=='ir.actions.wizard':
            pass # TODO Can model really be 'ir.actions.wizard' ?

        elif model=='ir.model.fields':
            try:
                field_name = encode(obj.name)
            except AttributeError, exc:
                _logger.error("name error in %s: %s", xml_name, str(exc))
                continue
            objmodel = registry.get(obj.model)
            if (objmodel is None or field_name not in objmodel._columns
                    or not objmodel._translate):
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
#                 elif obj.report_xsl:
#                     fname = obj.report_xsl
#                     parse_func = trans_parse_xsl
#                     report_type = "xsl"
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

        for field_name, field_def in obj._columns.items():
            if model == 'ir.model' and field_name == 'name' and obj.name == obj.model:
                # ignore model name if it is the technical one, nothing to translate
                continue
            if field_def.translate:
                name = model + "," + field_name
                try:
                    term = obj[field_name] or ''
                except:
                    term = ''
                push_translation(module, 'model', name, xml_name, encode(term))

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
        if model not in registry:
            _logger.error("Unable to find object %r", model)
            continue

        model_obj = registry[model]

        if model_obj._constraints:
            push_local_constraints(module, model_obj, 'constraints')

        if model_obj._sql_constraints:
            push_local_constraints(module, model_obj, 'sql_constraints')

    installed_modules = map(
        lambda m: m['name'],
        registry['ir.module.module'].search_read(cr, uid, [('state', '=', 'installed')], fields=['name']))

    path_list = list(openerp.modules.module.ad_paths)
    # Also scan these non-addon paths
    for bin_path in ['osv', 'report' ]:
        path_list.append(os.path.join(tools.config['root_path'], bin_path))

    _logger.debug("Scanning modules at paths: %s", path_list)

    def get_module_from_path(path):
        for mp in path_list:
            if path.startswith(mp) and os.path.dirname(path) != mp:
                path = path[len(mp)+1:]
                return path.split(os.path.sep)[0]
        return 'base' # files that are not in a module are considered as being in 'base' module

    def verified_module_filepaths(fname, path, root):
        fabsolutepath = join(root, fname)
        frelativepath = fabsolutepath[len(path):]
        display_path = "addons%s" % frelativepath
        module = get_module_from_path(fabsolutepath)
        if ('all' in modules or module in modules) and module in installed_modules:
            return module, fabsolutepath, frelativepath, display_path
        return None, None, None, None

    def babel_extract_terms(fname, path, root, extract_method="python", trans_type='code',
                               extra_comments=None, extract_keywords={'_': None}):
        module, fabsolutepath, _, display_path = verified_module_filepaths(fname, path, root)
        extra_comments = extra_comments or []
        if not module: return
        src_file = open(fabsolutepath, 'r')
        try:
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
    # translate strings marked as to be translated
    for module, source, name, id, type, comments in sorted(_to_translate):
        trans = '' if not lang else trans_obj._get_source(cr, uid, name, type, lang, source)
        out.append((module, type, name, id, source, encode(trans) or '', comments))
    return out

import sys
sys.modules['openerp.tools.translate'].trans_generate = extend_trans_generate

