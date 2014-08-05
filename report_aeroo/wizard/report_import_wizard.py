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

from openerp.osv import osv, fields
from openerp.tools import convert_xml_import
from openerp.tools.translate import _
import base64
import lxml.etree
import zipfile
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class report_aeroo_import(osv.osv_memory):
    _name = 'aeroo.report_import'
    _description = 'Aeroo report import wizard'
    
    _columns = {
        'name':fields.char('Name', size=64),
        'file':fields.binary('Aeroo report file', filters='*.aeroo', required=True),
        'info': fields.text('Info', readonly=True),
        'state':fields.selection([
            ('draft','Draft'),
            ('info','Info'),
            ('done','Done'),
            
        ],'State', select=True, readonly=True),
                        
    }

    def default_get(self, cr, uid, fields_list, context=None):
        values = {'state': 'draft'}
        default_ids = context.get('default_ids')
        if default_ids:
            this = self.read(cr, uid, default_ids, ['name','state','file','info'], context=context)[0]
            del this['id']
            values.update(this)
        return values

    def install_report(self, cr, uid, ids, context=None):
        report_obj = self.pool.get('ir.actions.report.xml')
        this = self.browse(cr, uid, ids[0], context=context)
        if report_obj.search(cr, uid, [('report_name','=',this.name)], context=context):
            raise osv.except_osv(_('Warning!'), _('Report with service name "%s" already exist in system!') % this.name)
        fd = StringIO()
        fd.write(base64.decodestring(this.file))
        fd.seek(0)
        convert_xml_import(cr, 'report_aeroo', fd, {}, 'init', noupdate=True)
        fd.close()
        self.write(cr, uid, ids, {'state':'done'}, context=context)
        report_id = report_obj.search(cr, uid, [('report_name','=',this.name)], context=context)[-1]
        report = report_obj.browse(cr, uid, report_id, context=context)
        event_id = self.pool.get('ir.values').set_action(cr, uid, report.report_name, 'client_print_multi', report.model, 'ir.actions.report.xml,%d' % report_id)
        if report.report_wizard:
            report._set_report_wizard(report.id)

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        mod_id = mod_obj.search(cr, uid, [('name', '=', 'action_aeroo_report_xml_tree')])[0]
        res_id = mod_obj.read(cr, uid, mod_id, ['res_id'])['res_id']
        act_win = act_obj.read(cr, uid, res_id, [])
        act_win['domain'] = [('id','=',report_id)]
        return act_win

    def next(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids[0], context=context)
        file_data = base64.decodestring(this.file)
        zip_stream = StringIO()
        zip_stream.write(file_data)
        zip_obj = zipfile.ZipFile(zip_stream, mode='r', compression=zipfile.ZIP_DEFLATED)
        if zipfile.is_zipfile(zip_stream):
            report_obj = self.pool.get('ir.actions.report.xml')
            context['allformats'] = True
            mimetypes = dict(report_obj._get_in_mimetypes(cr, uid, context=context))
            styles_select = dict(report_obj._columns['styles_mode'].selection)
            if 'data.xml' in zip_obj.namelist():
                data = zip_obj.read('data.xml')
            else:
                raise osv.except_osv(_('Error!'), _('Aeroo report file is invalid!'))
            tree = lxml.etree.parse(StringIO(data))
            root = tree.getroot()
            info = ''
            report = root.xpath("//data/record[@model='ir.actions.report.xml']")[0]
            style = root.xpath("//data/record[@model='report.stylesheets']")[0]
            rep_name = report.find("field[@name='name']").text
            rep_service = report.find("field[@name='report_name']").text
            rep_model = report.find("field[@name='model']").text
            rep_format = eval(report.find("field[@name='out_format']").attrib['search'], {})[0][2]
            rep_charset = report.find("field[@name='charset']").text
            parser_state = report.find("field[@name='parser_state']").text
            styles_mode = report.find("field[@name='styles_mode']").text
            tml_source = report.find("field[@name='tml_source']").text

            info += "Name: %s\n" % rep_name
            info += "Object: %s\n" % rep_model
            info += "Service Name: %s\n" % rep_service
            info += "Format: %s\n" % mimetypes.get(rep_format,'oo-odt')
            info += "Template: %s\n" % (tml_source=='parser' and 'defined by parser' or 'static')
            if rep_format=='genshi-raw':
                info += "Charset: %s\n" % rep_charset
            info += "Parser: %s\n" % (parser_state in ('def','loc') and 'customized' or 'default')
            info += "Stylesheet: %s%s\n" % (styles_select[styles_mode].lower(), style is not None and " (%s)" % style.find("field[@name='name']").text)
            self.write(cr, uid, ids, {'name':rep_service,'info':info,'state':'info','file':base64.encodestring(data)}, context=context)
        else:
            raise osv.except_osv(_('Error!'), _('Is not Aeroo report file.'))

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        mod_id = mod_obj.search(cr, uid, [('name', '=', 'action_aeroo_report_import_wizard')])[0]
        res_id = mod_obj.read(cr, uid, mod_id, ['res_id'])['res_id']
        act_win = act_obj.read(cr, uid, res_id, [])
        act_win['domain'] = [('id','in',ids)]
        act_win['context'] = {'default_ids':ids}
        return act_win
        
    _defaults = {
        'state': 'draft',
    }

