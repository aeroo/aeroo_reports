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

from werkzeug.urls import url_decode, iri_to_uri

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
        # if it's not Aeroo Reports, fall back to built-in reporting engine
        if converter != 'aeroo':
            return super(ReportController, self).report_routes(
                reportname, docids=docids, converter=converter, **data
            )
        # Aeroo Reports starts here
        report_obj = request.env['ir.actions.report']
        report = report_obj._get_report_from_name(reportname)
        context = dict(request.env.context)
        # report_data = {}
        if docids:
            docids = [int(i) for i in docids.split(',')]
        else:
            opt = json.loads(data.get('options'))
            docids = opt and opt.get('ids') or opt.get('id')
        
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            if data['context'].get('lang'):
                del data['context']['lang']
            context.update(data['context'])
        rset = report.with_context(context).render_aeroo(docids, data=data, get_filename=True)
        mimetype = self.MIMETYPES.get(rset[1], 'application/octet-stream')
        httpheaders = [
            ('Content-Type', mimetype),
            ('Content-Length', len(rset[0])),
            ('Content-Disposition', content_disposition(rset[2])),
        ]
        return request.make_response(rset[0], headers=httpheaders)
    
    @route(['/report/download'], type='http', auth="user")
    def report_download(self, data, context=None):
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        if type != 'aeroo':
            return super(ReportController, self).report_download(
                data, context=context
            )
        pattern = '/report/aeroo/'
        reportname = url.split(pattern)[1].split('?')[0]
        docids = None
        if '/' in reportname:
            reportname, docids = reportname.split('/')
        if docids:
            # Generic report:
            response = self.report_routes(reportname, docids=docids, converter='aeroo')
        else:
            # Particular report:
            data = url_decode(url.split('?')[1]).items()  # decoding the args represented in JSON
            response = self.report_routes(reportname, converter='aeroo', **dict(data))
        report = request.env['ir.actions.report']._get_report_from_name(reportname)
        
        if docids:
            ids = [int(x) for x in docids.split(",")]
            obj = request.env[report.model].browse(ids)
        token = "token=dummy-because-api-expects-one"
        response.set_cookie('fileToken', token)
        return response
        
