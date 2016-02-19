# -*- encoding: utf-8 -*-
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
    'name': 'Aeroo Reports - Direct printing to printer',
    'summary': 'Print Aeroo Reports directly to a printer',
    'version': '9.0.1.0.0',
    'category': 'Generic Modules/Aeroo Reports',
    'description': """
Direct Print module for Aeroo Reports enables printing a report directly to
server configured printer without opening the report on the user's screen.

Module supports network printing.

Common Applications
--------------------------------------------------------------------------------
* POS receipts;
* Shipping/mailing labels;
* Barcode labels;
* Admission tickets;
* Shipment documents;
* Pick-lists;
* Invoices;

Features
--------------------------------------------------------------------------------
* Set default general purpose and label printers for a user;
* Directly print the report to the printer from UI button or code;
* Configure a "pseudo" printer for a report to print to user's desktop;
* Use system pre-configured (CUPS) printers;
* Printer discovery wizard;
* UI user preferences integration;
* Per group user rights on printers;
    
System Dependencies
--------------------------------------------------------------------------------
Direct print module requires Aeroo Reports core module and pycups Python library
For more reference visit - https://pypi.python.org/pypi/pycups
""",
    'author': 'Alistek',
    'website': 'http://www.alistek.com',
    'depends': ['report_aeroo'],
    'data': ["data/report_aeroo_direct_data.xml",
                   "installer.xml",
                   "report_aeroo_direct_print_view.xml",
                   "security/security_rules.xml",
                   "security/ir.model.access.csv"],
    "license" : "GPL-3 or any later version",
    'installable': True,
    'application': True,
    'active': False,
}
