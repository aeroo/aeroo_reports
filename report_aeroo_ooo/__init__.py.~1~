##############################################################################
#
# Copyright (c) 2008-2012 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
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

check_list = [
    'import uno',
    'import unohelper',
    'from com.sun.star.beans import PropertyValue',
    'from com.sun.star.uno import Exception as UnoException',
    'from com.sun.star.connection import NoConnectException, ConnectionSetupException',
    'from com.sun.star.beans import UnknownPropertyException',
    'from com.sun.star.lang import IllegalArgumentException',
    'from com.sun.star.io import XOutputStream',
    'from com.sun.star.io import IOException',
]

DEFAULT_OPENOFFICE_PATH = [
    "C:\Program Files\OpenOffice.org 3\Basis\program",
    "C:\Program Files\OpenOffice.org 3\program",
    "C:\Program Files\OpenOffice.org 3\URE\bin"]

DEFAULT_OPENOFFICE_PATH_AMD64 = [
    "C:\Program Files (x86)\OpenOffice.org 3\Basis\program",
    "C:\Program Files (x86)\OpenOffice.org 3\program",
    "C:\Program Files (x86)\OpenOffice.org 3\URE\bin"]

import sys

if sys.platform=='win32':
    import _winreg
    import platform
    try:
        key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment')
        python_path = _winreg.QueryValueEx(key, "PYTHONPATH")[0].split(';')
        if python_path:
            sys.path.extend(python_path)
        else:
            sys.path.extend(platform.machine()=='x86' and DEFAULT_OPENOFFICE_PATH or DEFAULT_OPENOFFICE_PATH_AMD64)
    except WindowsError, e:
        sys.path.extend(platform.machine()=='x86' and DEFAULT_OPENOFFICE_PATH or DEFAULT_OPENOFFICE_PATH_AMD64)

from check_deps import check_deps
check_deps(check_list)

import installer
import report
try:
    import DocumentConverter
except ImportError, e:
    print e

