##############################################################################
#
# Copyright (c) 2008-2011 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
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

from code128 import get_code
from code39 import create_c39
from EANBarCode import EanBarCode
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def make_barcode(code, code_type='ean13', rotate=None, height=50, xw=1):
    if code:
        if code_type.lower()=='ean13':
            bar=EanBarCode()
            im = bar.getImage(code,height)
        elif code_type.lower()=='code128':
            im = get_code(code, xw, height)
        elif code_type.lower()=='code39':
            im = create_c39(height, xw, code)
    else:
        return StringIO(), 'image/png'

    tf = StringIO()
    try:
        if rotate!=None:
            im=im.rotate(int(rotate))
    except Exception, e:
        pass
    im.save(tf, 'png')
    size_x = str(im.size[0]/96.0)+'in'
    size_y = str(im.size[1]/96.0)+'in'
    return tf, 'image/png', size_x, size_y

