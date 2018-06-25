# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file  
#
################################################################################

import logging
from odoo import api, models
from odoo.tools import pycompat
from odoo.addons.report_aeroo.exceptions import ProgrammingError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class IrModel(models.Model):
    _name = 'ir.model'
    _inherit = 'ir.model'

    def _add_manual_models(self):
        """
        Calls original function + loads Aeroo Reports 'dynamic' reports
        """
        super(IrModel, self)._add_manual_models()
        if 'report_aeroo' in self.pool._init_modules:
            _logger.info('Adding aeroo reports dynamic models')
            cr = self.env.cr
            sql_stmt = """SELECT report_name, name, parser_def, parser_state
                    FROM ir_act_report_xml WHERE
                    report_type = 'aeroo'
                    AND parser_state in ('default', 'def')
                    ORDER BY id
                    """
            cr.execute(sql_stmt)
            for report in cr.dictfetchall():
                model_data = {
                    'model': report['report_name'],
                    'name': report['name'],
                    'parser_def': report['parser_def'],
                }
                if report['parser_state'] == 'default':
                    parser = self._default_aeroo_parser(model_data)
                else:
                    parser = self._custom_aeroo_parser(model_data)
                parser._build_model(self.pool, cr)

    @api.model
    def _default_aeroo_parser(self, model_data):
        """
        Instantiates default parsers for Aeroo Reports "dynamic" reports
        """
        class DefaultAerooParser(models.AbstractModel):
            _inherit = 'report.report_aeroo.abstract'
            _name = 'report.%s' % pycompat.to_native(model_data['model'])
            _description = model_data['name'],
            _module = False
            _custom = True
            __doc__ = ''
            _transient = False
        return DefaultAerooParser

    @api.model
    def _custom_aeroo_parser(self, model_data):
        """
        Instantiates custom parsers for Aeroo Reports "dynamic" reports
        """
        context = {'Parser': None}
        try:
            exec(model_data['parser_def'].replace('\r',''), context)
            return context['Parser']
        except SyntaxError as e:
            raise ProgrammingError(_('Aeroo Reports Parser Syntax Error !'))
        except Exception as e:
            _logger.exception(
                _("Error in Aeroo Reports '_custom_aeroo_parser' method"))
        return None
