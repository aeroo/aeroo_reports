# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file
#
################################################################################

import logging
import json

from odoo.addons.web.controllers import main
from odoo.http import route, request, content_disposition

_logger = logging.getLogger(__name__)


class ReportController(main.ReportController):

    MIMETYPES = {
        'txt': 'text/plain',
        'html': 'text/html',
        'doc': 'application/vnd.ms-word',
        'odt': 'application/vnd.oasis.opendocument.text',
        'ods': 'application/vnd.oasis.opendocument.spreadsheet',
        'pdf': 'application/pdf',
        'sxw': 'application/vnd.sun.xml.writer',
        'xls': 'application/vnd.ms-excel',
    }

    @route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        # if it's not Aeroo Reports fall back to original reporting engine
        if converter != 'aeroo':
            return super(ReportController, self).report_routes(
                reportname, docids, converter, **data
            )

        # Aeroo Reports starts here
        report_obj = request.env['ir.actions.report']
        report = report_obj._get_report_from_name(reportname)
        context = dict(request.env.context)
        # report_data = {}
        if docids:
            docids = [int(i) for i in docids.split(',')]
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            if data['context'].get('lang'):
                del data['context']['lang']
            context.update(data['context'])

        rset = report.with_context(context).render_aeroo(docids, data=data)
        mimetype = self.MIMETYPES.get(rset[1], 'application/octet-stream')
        httpheaders = [
            ('Content-Disposition', content_disposition(rset[2])),
            ('Content-Type', mimetype),
            ('Content-Length', len(rset[0]))
        ]

        return request.make_response(rset[0], headers=httpheaders)
