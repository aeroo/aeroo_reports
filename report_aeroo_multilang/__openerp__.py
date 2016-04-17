# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': "Multilingual support for Aeroo Report",
    'summary': """
        One template by lang""",
    'author': 'ACSONE SA/NV',
    'website': "http://acsone.eu",
    'category': 'Uncategorized',
    'version': '9.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'report_aeroo',
    ],

    # always loaded
    'data': [
        'views/report_aeroo_multilang.xml'
    ],
}
