# -*- encoding: utf-8 -*-
from openerp.osv import osv,fields

class report_xml(osv.osv):
    _name = 'ir.actions.report.xml'
    _inherit = 'ir.actions.report.xml'
    
    _columns = {
        'report_type': fields.selection([
                ('aeroo','Aeroo Reports'),
                ('qweb-pdf', 'PDF'),
                ('qweb-html', 'HTML'),
                ('controller', 'Controller'),
                ('pdf', 'RML pdf (deprecated)'),
                ('sxw', 'RML sxw (deprecated)'),
                ('webkit', 'Webkit (deprecated)'),
                ], 'Report Type', required=True, 
                help="HTML will open the report directly in your browser, PDF will use wkhtmltopdf to render the HTML into a PDF file and let you download it, Controller allows you to define the url of a custom controller outputting any kind of report.")
     }           
                

