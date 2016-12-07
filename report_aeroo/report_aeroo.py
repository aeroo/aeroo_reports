# -*- coding: utf-8 -*-
# © 2008-2014 Alistek
# © 2016 Savoir-faire Linux
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl).

import base64
import logging
import os
import subprocess
import threading

from aeroolib.plugins.opendocument import Template, OOSerializer
from cStringIO import StringIO
from genshi.template.eval import StrictLookup
from openerp import api, models, registry
from openerp.osv import osv
from openerp.report.report_sxw import report_sxw
from openerp.tools.translate import _
from openerp.tools import safe_eval
from openerp.exceptions import ValidationError
from tempfile import NamedTemporaryFile

from .extra_functions import ExtraFunctions

logger = logging.getLogger('report_aeroo')


try:
    aeroo_lock = threading.Lock()
    msg = "Aeroo lock instantiated."
    logger.info(msg)
except Exception:
    err_msg = "Could not instantiate Aeroo lock!!!"
    logger.critical(msg)

mime_dict = {
    'oo-odt': 'odt',
    'oo-ods': 'ods',
    'oo-pdf': 'pdf',
    'oo-doc': 'doc',
    'oo-xls': 'xls',
    'oo-csv': 'csv',
}


class DynamicLookup(StrictLookup):
    """
    Dynamically changes language in a context
    according to Parser's current language
    """

    @classmethod
    def lookup_name(cls, data, name):
        orig = super(DynamicLookup, cls).lookup_name(data, name)
        if isinstance(orig, models.Model):
            new_lang = data.get('getLang')()
            if orig.env.context.get('lang') != new_lang:
                orig = orig.with_context(lang=new_lang)
        return orig


class AerooReport(report_sxw):

    def create_aeroo_report(
            self, cr, uid, ids, data, report_xml, context):
        """ Return an aeroo report generated with aeroolib
        """
        if len(ids) > 1:
            raise ValidationError(
                _('Aeroo Reports do not support generating reports in batch. '
                  'You must select one record at a time.'))

        context = context.copy()
        if self.name == 'report.printscreen.list':
            context['model'] = data['model']
            context['ids'] = ids

        assert report_xml.out_format.code in (
            'oo-odt', 'oo-ods', 'oo-doc', 'oo-xls', 'oo-csv', 'oo-dbf',
        )
        assert report_xml.in_format in ('oo-odt', 'oo-ods')

        output_format = report_xml.out_format.code[3:]
        input_format = report_xml.in_format[3:]

        oo_parser = self.parser(cr, uid, self.name2, context=context)

        table_obj = registry(cr.dbname).get(self.table)
        objects = table_obj.browse(cr, uid, ids, context=context) or []
        oo_parser.localcontext.update(context)
        oo_parser.set_context(objects, data, ids, report_xml.report_type)

        oo_parser.localcontext['data'] = data
        oo_parser.localcontext['user_lang'] = context.get('lang', False)
        oo_parser.localcontext['o'] = objects[0]

        xfunc = ExtraFunctions(cr, uid, report_xml.id, oo_parser.localcontext)
        oo_parser.localcontext.update(xfunc.functions)

        if report_xml.tml_source == 'lang':
            lang = safe_eval(report_xml.lang_eval, {'o': objects[0]})
            template = report_xml.template_from_lang(lang)

        else:
            template = report_xml.report_sxw_content
            if not template:
                raise osv.except_osv(_('Error!'), _('No template found!'))
            template = base64.decodestring(template)

        template_io = StringIO()
        template_io.write(template)
        serializer = OOSerializer(template_io)
        basic = Template(
            source=template_io, serializer=serializer, lookup=DynamicLookup)

        data = basic.generate(**oo_parser.localcontext).render().getvalue()

        if input_format != output_format:
            temp_file = NamedTemporaryFile(
                suffix='.%s' % input_format, delete=False)
            temp_file.close()

            with open(temp_file.name, 'w') as f:
                f.write(data)

            filedir, filename = os.path.split(temp_file.name)

            subprocess.call([
                "soffice", "--headless", "--convert-to", output_format,
                "--outdir", filedir, temp_file.name])

            with open(temp_file.name[:-3] + output_format, 'r') as f:
                data = f.read()

        return data, output_format

    def create(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        else:
            context = dict(context)

        env = api.Environment(cr, uid, context)

        if 'tz' not in context:
            context['tz'] = env.user.tz

        data.setdefault('model', context.get('active_model', False))

        name = self.name.startswith('report.') and self.name[7:] or self.name

        report_xml = env['ir.actions.report.xml'].search(
            [('report_name', '=', name)])

        report_type = report_xml.report_type
        assert report_type == 'aeroo'

        res = self.create_aeroo_report(
            cr, uid, ids, data, report_xml, context=context)

        return res
