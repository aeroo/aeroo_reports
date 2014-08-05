# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# Copyright (C) 2009  Domsense s.r.l.                                   
# @authors: Simone Orsi																	       
# Copyright (C) 2009-2013  Alistek Ltd                                  
#                                                                       
#This program is free software: you can redistribute it and/or modify   
#it under the terms of the GNU General Public License as published by   
#the Free Software Foundation, either version 3 of the License, or      
#(at your option) any later version.                                    
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#                                                                       
#This program is distributed in the hope that it will be useful,        
#but WITHOUT ANY WARRANTY; without even the implied warranty of         
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          
#GNU General Public License for more details.                           
#                                                                       
#You should have received a copy of the GNU General Public License      
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  
########################################################################

{
    'name': 'Aeroo Reports',
    'version': '1.2.1',
    'category': 'Generic Modules/Aeroo Reporting',
    'description': """
Aeroo Reports for OpenERP is a comprehensive reporting engine based on Aeroo Library.

Report templates can be created directly in of following formats:
=================================================================
* Open Document Format (ODF) - .odt, .ods;
* Other ASCII based formats, like HTML, CSV, etc.

Output formats:
=================================================================
* Open Document Format (ODF) - .odt, .ods;
* Other ASCII based formats, like HTML, CSV, etc. 
* with report_aeroo_ooo [1] module - PDF, DOC, XLS, CSV.

Reporting engine features:
=================================================================
* Add reports from UI "on the fly";
* Install reports from module;
* Dynamic template load/unload;
* Extra Functions - set of functions for rapid template development;
* Use templates stored on filesystem, database or elsewhere;
* Same button - different templates;
* Powerful stylesheet system for ODF templates;
* Global or local stylesheets;
* Template preloading for performance concerns;
* User defined parsers;
* Report deactivation;
* Tunable format fallback;
* Add/Remove print button wizards;
* Test report on particular object ID, directly from Report form;
* Translatable reports;
* Translation export;
* Number of copies;
* Universal Report wizard;
* Override report file extension (for direct printing, etc);
* Separate input/output format selections;

[1] For more information on available template -> output pairs and other features, see description of report_aeroo_ooo module.
""",
    'author': 'Alistek Ltd, Simone Orsi - Domsense',
    'website': 'http://www.alistek.com',
    'complexity': "easy",
    'depends': ['base'],
    'data': ["installer.xml", "report_view.xml", "data/report_aeroo_data.xml", "wizard/add_print_button_view.xml", "wizard/remove_print_button_view.xml", "security/ir.model.access.csv"],
    "license" : "GPL-3 or any later version",
    'installable': True,
    'active': False,
    'application': True,
    'auto_install': False,
}
