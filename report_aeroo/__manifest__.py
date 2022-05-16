# -*- encoding: utf-8 -*-
################################################################################
#
#  This file is part of Aeroo Reports software - for license refer LICENSE file  
#
################################################################################

{
    'name': 'Aeroo Reports',
    'version': '15.2.1',
    'category': 'Generic Modules/Aeroo Reports',
    'summary': 'Enterprise grade reporting solution (odoo v15)',
    'author': 'Alistek',
    'website': 'http://www.alistek.com',
    'complexity': "easy",
    'depends': ['base', 'web'],
    'data': [
             "data/report_aeroo_data.xml", 
             "views/report_view.xml",
             #"views/webclient_report_action.xml",
             "views/report_print_by_action.xml",
             #"wizard/add_print_button_view.xml",
             #"wizard/remove_print_button_view.xml",
             "views/installer.xml",
             "security/ir.model.access.csv"
             ],
    'assets':{
              'web.assets_backend':['report_aeroo/static/src/js/action_manager_report.js',],
             },
    'license' : "GPL-3 or any later version",
    'installable': True,
    'active': False,
    'application': True,
    'auto_install': False,
}
