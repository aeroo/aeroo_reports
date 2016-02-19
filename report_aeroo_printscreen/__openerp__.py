##############################################################################
#
# Copyright (c) 2008-2014 Alistek (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

{
    'name': 'Aeroo Reports - Print Screen',
    'version': '9.0.1.0.0',
    'category': 'Generic Modules/Aeroo Reporting',
    'summary': 'Report any model in a spreadsheet report',
    'description': """
Shows "Printscreen List" report on each OpenERP object.

Using aeroo_docs daemon by Alistek, you can convert output to one of these (xls, pdf, csv) formats.
""",
    'author': 'Alistek',
    'website': 'http://www.alistek.com',
    'depends': ['base','report_aeroo'],
    'data': ['data/report_aeroo_printscreen_data.xml',
             'views/views.xml'
            ],
    "license" : "GPL-3 or any later version",
    'installable': True,
    'web': True,
    'application': True,
    'active': False,
}
