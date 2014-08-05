# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008-2013 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
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
    'name': 'Aeroo Reports - OpenOffice Helper Addon',
    'version': '1.2',
    'category': 'Generic Modules/Aeroo Reporting',
    'description': """
Aeroo Reports OpenOffice.org helper adds following features:

* Additional output formats for ODF reports;
* ODF subreport feature;
* Include external ODF documents feature;
* Process each object separately or in group;

Supported output format combinations (Template -> Output):
=================================================================
odt -> pdf
odt -> doc
ods -> pdf
ods -> xls
ods -> csv
""",
    'author': 'Alistek Ltd',
    'website': 'http://www.alistek.com',
    'complexity': "easy",
    'depends': ['base','report_aeroo'],
    'data': ["data/report_aeroo_data.xml", "installer.xml", "report_view.xml"],
    "license" : "GPL-3 or any later version",
    'installable': True,
    'active': False,
    'auto_install': False,
}
