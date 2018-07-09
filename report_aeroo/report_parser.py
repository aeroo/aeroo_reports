# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file
#
################################################################################

import logging
from io import BytesIO
from PIL import Image
from base64 import b64decode
import time

from aeroolib.plugins.opendocument import Template, OOSerializer, _filter
from aeroolib import __version__ as aeroolib_version
from currency2text import supported_language, currency_to_text
from .docs_client_lib import DOCSConnection
from .exceptions import ConnectionError

from genshi.template.eval import StrictLookup

from odoo import release as odoo_release
from odoo import api, models, fields
from odoo.tools import file_open, frozendict
from odoo.tools.translate import _, translate
from odoo.tools.misc import formatLang as odoo_fl
from odoo.tools.misc import format_date as odoo_fd
from odoo.tools.safe_eval import safe_eval
from odoo.modules import load_information_from_description_file
from odoo.exceptions import MissingError


_logger = logging.getLogger(__name__)

mime_dict = {'oo-odt': 'odt',
             'oo-ods': 'ods',
             'oo-pdf': 'pdf',
             'oo-doc': 'doc',
             'oo-xls': 'xls',
             'oo-csv': 'csv',
             }


class ReportAerooAbstract(models.AbstractModel):
    _name = 'report.report_aeroo.abstract'
    docs_client = None

    def __filter(self, val):
        if isinstance(val, models.BaseModel):
            return val.name_get()[0][1]
        return _filter(val)

    # Extra Functions ==========================================================
    def _asarray(self, attr, field):
        """
        Returns named field from all objects as a list.
        """
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects': attr, 'value_list': []}
        exec(expr, localspace)
        return localspace['value_list']

    def _average(self, attr, field):
        """
        Returns average (arithmetic mean) of fields from all objects in a list.
        """
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects': attr, 'value_list': []}
        exec(expr, localspace)
        x = sum(localspace['value_list'])
        y = len(localspace['value_list'])
        return float(x)/float(y)

    def _asimage(self, field_value, rotate=None, size_x=None, size_y=None,
                 uom='px', hold_ratio=False):
        """
        Prepare image for inserting into OpenOffice.org document
        """
        def size_by_uom(val, uom, dpi):
            if uom == 'px':
                result = str(val/dpi)+'in'
            elif uom == 'cm':
                result = str(val/2.54)+'in'
            elif uom == 'in':
                result = str(val)+'in'
            return result
        ##############################################
        if not field_value:
            return BytesIO(), 'image/png'
        field_value = b64decode(field_value)
        tf = BytesIO(field_value)
        tf.seek(0)
        im = Image.open(tf)
        format = im.format.lower()
        dpi_x, dpi_y = map(float, im.info.get('dpi', (96, 96)))
        try:
            if rotate != None:
                im = im.rotate(int(rotate))
                tf.seek(0)
                im.save(tf, format)
        except Exception as e:
            _logger.exception("Error in '_asimage' method")

        if hold_ratio:
            img_ratio = im.size[0] / float(im.size[1])
            if size_x and not size_y:
                size_y = size_x / img_ratio
            elif not size_x and size_y:
                size_x = size_y * img_ratio
            elif size_x and size_y:
                size_y2 = size_x / img_ratio
                size_x2 = size_y * img_ratio
                if size_y2 > size_y:
                    size_x = size_x2
                elif size_x2 > size_x:
                    size_y = size_y2

        size_x = size_x and size_by_uom(size_x, uom, dpi_x) \
            or str(im.size[0]/dpi_x)+'in'
        size_y = size_y and size_by_uom(size_y, uom, dpi_y) \
            or str(im.size[1]/dpi_y)+'in'
        return tf, 'image/%s' % format, size_x, size_y

    def _currency_to_text(self, currency):
        def c_to_text(sum, currency=currency, language=None):
            lang = supported_language.get(language or self._get_lang())
            return str(lang.currency_to_text(sum, currency), "UTF-8")
        return c_to_text

    def _get_selection_items(self, kind='items'):
        def get_selection_item(obj, field, value=None):
            try:
                # TODO how to check for list of objects in new API?
                if isinstance(obj, models.AbstractModel):
                    obj = obj[0]
                if isinstance(obj, str):
                    model = obj
                    field_val = value
                else:
                    model = obj._name
                    field_val = getattr(obj, field)
                val = self.env[model].fields_get(allfields=[field]
                                                 )[field]['selection']
                if kind == 'item':
                    if field_val:
                        return dict(val)[field_val]
                elif kind == 'items':
                    return val
                return ''
            except Exception as e:
                _logger.exception(
                    "Error in '_get_selection_item' method", exc_info=True)
                return ''
        return get_selection_item

    def _get_log(self, obj, field=None):
        if field:
            return obj.get_metadata()[0][field]
        else:
            return obj.get_metadata()[0]

    def _translate_text(self, source):
        trans_obj = self.env['ir.translation']
        lang = self._get_lang()
        name = 'ir.actions.report'
        conds = [('res_id', '=', self.report.id),
                 ('type', '=', 'report'),
                 ('src', '=', source),
                 ('lang', '=', lang)
                 ]
        trans = trans_obj.search(conds)
        if not trans:
            vals = {
                'src': source,
                'type': 'report',
                'lang': self._get_lang(),
                'res_id': self.report.id,
                'name': name,
            }
            trans_obj.create(vals)
        return translate(self.env.cr, name, 'report', lang, source) or source

    def _asarray(self, attr, field):
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects': attr, 'value_list': []}
        exec(expr, localspace)
        return localspace['value_list']

    # / Extra Functions ========================================================

    def get_docs_conn(self):
        if self.docs_client:
            return
        icp = self.env.get('ir.config_parameter')
        icpgp = icp.get_param
        docs_host = icpgp('aeroo.docs_host') or 'localhost'
        docs_port = icpgp('aeroo.docs_port') or '8989'
        # docs_auth_type = icpgp('aeroo.docs_auth_type') or False
        docs_username = icpgp('aeroo.docs_username') or 'anonymous'
        docs_password = icpgp('aeroo.docs_password') or 'anonymous'
        docs_client = DOCSConnection(
            docs_host, docs_port, username=docs_username,
            password=docs_password)
        self.docs_client = docs_client

    def _generate_doc(self, data, report):
        docs = self.docs_client
        token = docs.upload(data)
        if report.out_format.code == 'oo-dbf':
            data = docs.convert(identifier=token)  # TODO What format?
        else:
            data = docs.convert(identifier=token,
                                out_mime=mime_dict[report.out_format.code],
                                in_mime=mime_dict[report.in_format]
                                )
        return data

    def _get_lang(self, source='current'):
        if source == 'current':
            return self.env.context['lang'] or self.env.context['user_lang']
        elif source == 'company':
            return self.env.user.company_id.partner_id.lang
        elif source == 'user':
            return self.env.context['user_lang']

    def _set_lang(self, lang, obj=None):
        self.localcontext.update(lang=lang)
        if obj is None and 'objects' in self.localcontext:
            obj = self.localcontext['objects']
        if obj and obj.env.context['lang'] != lang:
            ctx_copy = dict(self.env.context)
            ctx_copy.update(lang=lang)
            obj.env.context = frozendict(ctx_copy)
            obj.invalidate_cache()

    def _format_lang(
            self, value, digits=None, grouping=True, monetary=False, dp=False,
            currency_obj=False, date=False, date_time=False):
        """ We add date and date_time for backwards compatibility. Odoo has
        split the method in two (formatlang and format_date)
        """
        if date or date_time:
            return odoo_fd(self.env, value)
        return odoo_fl(
            self.env, value, digits, grouping, monetary, dp, currency_obj)

    def _set_objects(self, model, docids):
        _logger.exception(
            'AEROO setobjects======================= %s - %s' % (model, docids))
        lctx = self.localcontext
        lang = lctx['lang']
        objects = None
        if self.env.context['lang'] != lang:
            ctx_copy = dict(self.env.context)
            ctx_copy.update(lang=lang)
            objects = self.env.get(model).with_context(**ctx_copy).browse(docids)
        else:
            objects = self.env.get(model).browse(docids)
        lctx['objects'] = objects
        lctx['o'] = objects and objects[0] or None
        _logger.exception(
            'AEROO setobjects======================= %s' % (lang,))

    def test(self, obj):
        _logger.exception(
            'AEROO TEST1======================= %s - %s' %
            (type(obj),
             id(obj)))
        _logger.exception('AEROO TEST2======================= %s' % (obj,))

    def get_other_template(self, model, rec_id):
        if not hasattr(self, 'get_template'):
            return False
        record = self.env.get(model).browse(rec_id)
        template = self.get_template(record)
        return template

    def get_stylesheet(self, report):
        style_io = None
        if report.styles_mode != 'default':
            if report.styles_mode == 'global':
                styles = self.company.stylesheet_id
            elif report.styles_mode == 'specified':
                styles = report.stylesheet_id
            if styles:
                style_io = b64decode(styles.report_styles or False)
        return style_io

    def complex_report(self, docids, data, report, ctx):
        """ Returns an aeroo report generated by aeroolib
        """
        self.model = ctx.get('active_model', False)
        # tmpl_type = 'odt'
        self.record_ids = docids
        self.ctx = ctx
        self.company = self.env.user.company_id
        self.report = report

        #=======================================================================
        self.localcontext = {
            'user':     self.env.user,
            'user_lang': ctx.get('lang', False),
            'data':     data,

            'time':     time,
            'asarray':  self._asarray,
            'average':  self._average,
            'currency_to_text': self._currency_to_text,
            'asimage': self._asimage,
            'get_selection_item': self._get_selection_items('item'),
            'get_selection_items': self._get_selection_items(),
            'get_log': self._get_log,
            'asarray': self._asarray,

            '__filter': self.__filter,  # Don't use in the report template!
            'getLang':  self._get_lang,
            'setLang':  self._set_lang,
            'formatLang': self._format_lang,
            '_': self._translate_text,
            'gettext': self._translate_text,
            'test':     self.test,
            'fields':     fields,
            'company':     self.env.user.company_id,
        }
        self.localcontext.update(ctx)
        self._set_lang(self.company.partner_id.lang)
        self._set_objects(self.model, docids)

        file_data = None
        if report.tml_source == 'database':
            if not report.report_data or report.report_data == 'False':
                # TODO log report ID etc.
                raise MissingError(
                    _("Aeroo Reports could'nt find report template"))
            file_data = b64decode(report.report_data)
        elif report.tml_source == 'file':
            if not report.report_file or report.report_file == 'False':
                # TODO log report ID etc.
                raise MissingError(
                    _("No Aeroo Reports template filename provided"))
            file_data = report._read_template()
        else:
            rec_id = ctx.get('active_id', data.get('id')) or data.get('id')
            file_data = self.get_other_template(self.model, rec_id)

        if not file_data:
            # TODO log report ID etc.
            raise MissingError(_("Aeroo Reports could'nt find report template"))

        template_io = BytesIO(file_data)
        if report.styles_mode == 'default':
            serializer = OOSerializer(template_io)
        else:
            style_io = BytesIO(self.get_stylesheet(report))
            serializer = OOSerializer(template_io, oo_styles=style_io)

        basic = Template(source=template_io,
                         serializer=serializer,
                         lookup=StrictLookup
                         )

        # Add metadata
        ser = basic.Serializer
        model_obj = self.env.get('ir.model')
        model_name = model_obj.search([('model', '=', self.model)])[0].name
        ser.add_title(model_name)

        user_name = self.env.user.name
        ser.add_creation_user(user_name)

        module_info = load_information_from_description_file('report_aeroo')
        version = module_info['version']
        ser.add_generator_info('Aeroo Lib/%s Aeroo Reports/%s'
                               % (aeroolib_version, version))
        ser.add_custom_property('Aeroo Reports %s' % version, 'Generator')
        ser.add_custom_property('Odoo %s' % odoo_release.version, 'Software')
        ser.add_custom_property(module_info['website'], 'URL')
        ser.add_creation_date(time.strftime('%Y-%m-%dT%H:%M:%S'))

        file_data = basic.generate(**self.localcontext).render().getvalue()
        #=======================================================================
        code = mime_dict[report.in_format]
        #_logger.info("End process %s (%s), elapsed time: %s" % (self.name, self.model, time.time() - aeroo_print.start_time), logging.INFO) # debug mode

        return file_data, code

    def simple_report(self, docids, data, report, ctx, output='raw'):
        pass

    def single_report(self, docids, data, report, ctx):
        code = report.out_format.code
        ext = mime_dict[code]
        if code.startswith('oo-'):
            return self.complex_report(docids, data, report, ctx)
        elif code == 'genshi-raw':
            return self.simple_report(docids, data, report, ctx, output='raw')

    def assemble_tasks(self, docids, data, report, ctx):
        code = report.out_format.code
        result = self.single_report(docids, data, report, ctx)

        print_report_name = 'report'
        if report.print_report_name and not len(docids) > 1:
            obj = self.env[report.model].browse(docids)
            print_report_name = safe_eval(
                report.print_report_name, {'object': obj, 'time': time})

        if report.in_format == code:
            filename = '%s.%s' % (
                print_report_name, mime_dict[report.in_format])
            return result[0], result[1], filename
        else:
            try:
                self.get_docs_conn()
                result = self._generate_doc(result[0], report)
                filename = '%s.%s' % (
                    print_report_name, mime_dict[report.out_format.code])
                return result, mime_dict[code], filename
            except Exception as e:
                _logger.exception(_("Aeroo DOCS error!\n%s") % str(e))
                if report.disable_fallback:
                    result = None
                    _logger.exception(e[0])
                    raise ConnectionError(_('Could not connect Aeroo DOCS!'))
        # only if fallback
        filename = '%s.%s' % (print_report_name, mime_dict[report.in_format])
        return result[0], result[1], filename

    @api.model
    def aeroo_report(self, docids, data):

        self.name = self._context.get('report_name')
        report = self.env['ir.actions.report']._get_report_from_name(self.name)
        # TODO
        #_logger.info("Start Aeroo Reports %s (%s)" % (name, ctx.get('active_model')), logging.INFO) # debug mode

        if 'tz' not in self._context:
            self = self.with_context(tz=self.env.user.tz)

        # TODO fix and implement, it raise an error if no records selected
        # (docids=None)
        # copies_ids = []
        # if not report.report_wizard and report.id > 1:
        #     copies = report.copies
        #     while(copies):
        #         copies_ids.extend(docids)
        #         copies -= 1
        # docids = copies_ids or docids

        # TODO we should propagate context in the proper way, just with self
        res = self.assemble_tasks(docids, data, report, self._context)
        # TODO
        #_logger.info("End Aeroo Reports %s (%s), total elapsed time: %s" % (name, model), time() - aeroo_print.start_total_time), logging.INFO) # debug mode

        return res
