# -*- encoding: utf-8 -*-
################################################################################
#
# Copyright (c) 2009-2014 Alistek ( http://www.alistek.com ) All Rights Reserved.
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
################################################################################

from openerp import registry, models, _
from barcode import barcode
from openerp.tools import translate
#from currency_to_text import currency_to_text
from ctt_objects import supported_language
import base64
import StringIO
from PIL import Image
import time
import openerp.osv as osv
from openerp.report import report_sxw
import openerp.netsvc as netsvc
from openerp.tools.safe_eval import safe_eval as eval
from aeroolib.plugins.opendocument import _filter

from openerp.osv.orm import browse_record_list #TODO v8?

import logging
logger = logging.getLogger('report_aeroo')

try:
    from docutils.examples import html_parts # use python-docutils library
except ImportError, e:
    rest_ok = False
else:
    rest_ok = True
try:
    import markdown
    from markdown import Markdown # use python-markdown library
    from markdown.inlinepatterns import AutomailPattern
    
    class AutomailPattern_mod (AutomailPattern, object):
        def __init__(self, *args, **kwargs):
            super(AutomailPattern_mod, self).__init__(*args, **kwargs)

        def handleMatch(self, m):
            el = super(AutomailPattern_mod, self).handleMatch(m)
            href = ''.join([chr(int(a.replace(markdown.AMP_SUBSTITUTE+'#', ''))) for a in el.get('href').split(';') if a])
            el.set('href', href)
            return el
    
    markdown.inlinepatterns.AutomailPattern = AutomailPattern_mod # easy hack for correct displaying in Joomla

except ImportError, e:
    markdown_ok = False
else:
    markdown_ok = True
try:
    from mediawiki import wiki2html # use python-mediawiki library
except ImportError, e:
    wikitext_ok = False
else:
    wikitext_ok = True

def domain2statement(domain):
    statement=''
    operator=False
    for d in domain:
        if not operator:
            if type(d)==str:
                if d=='|':
                    operator=' or'
                continue
            else:
                operator=False
        statement+=' o.'+str(d[0])+' '+(d[1]=='=' and '==' or d[1])+' '+(isinstance(d[2], str) and '\''+d[2]+'\'' or str(d[2]))
        if d!=domain[-1]:
            statement+=operator or ' and'
        operator=False
    return statement

class ExtraFunctions(object):
    """ This class contains some extra functions which
        can be called from the report's template.
    """
    def __init__(self, cr, uid, report_id, context):
        self.cr = cr
        self.uid = uid
        self.registry = registry(self.cr.dbname)
        self.report_id = report_id
        self.context = context
        self.functions = {
            'asarray':self._asarray,
            'asimage':self._asimage,
            'html_embed_image':self._embed_image,
            'get_attachments':self._get_attachments,
            'get_name':self._get_name,
            'get_label':self._get_label,
            'getLang':self._get_lang,
            'get_selection_item':self._get_selection_items('item'),
            'safe':self._get_safe,
            'countif':self._countif,
            'count':self._count,
            'sumif':self._sumif,
            'sum_field':self._sum,
            'max_field':self._max,
            'min_field':self._min,
            'average':self._average,
            'large':self._large,
            'small':self._small,
            'count_blank':self._count_blank,
            '_':self._translate_text,
            'gettext':self._translate_text,
            'currency_to_text':self._currency2text(context['company'].currency_id.name), #self._currency2text(context['company'].currency_id.code),
            'barcode':barcode.make_barcode,
            'debugit':self.debugit,
            'dec_to_time':self._dec2time,
            'chunks':self._chunks,
            'browse':self._browse,
            'search':self._search,
            'search_ids':self._search_ids,
            'field_size':self._field_size,
            'field_accuracy':self._field_accuracy,
            'bool_as_icon':self._bool_as_icon,
            'time':time,
            'report_xml': self._get_report_xml(),
            'get_log': self._perm_read(self.cr, self.uid),
            'get_selection_items': self._get_selection_items(),
            'itemize': self._itemize,
            'html_escape': self._html_escape,
            'http_prettyuri': self._http_prettyuri,
            'http_builduri': self._http_builduri,
            'text_markdown': markdown_ok and self._text_markdown or \
                self._text_plain('"markdown" format is not supported! Need to be installed "python-markdown" package.'),
            'text_restruct': rest_ok and self._text_restruct or \
                self._text_plain('"reStructuredText" format is not supported! Need to be installed "python-docutils" package.'),
            'text_wiki': wikitext_ok and self._text_wiki or \
                self._text_plain('"wikimarkup" format is not supported! Need to be installed "python-mediawiki" package.'),
            'text_markup': self._text_markup,
            'text_remove_markup': self._text_remove_markup,
            '__filter': self.__filter, # Don't use in the report template!
        }

    def __filter(self, val):
        if isinstance(val, osv.orm.browse_null):
            return ''
        elif isinstance(val, osv.orm.browse_record):
            return val.with_context(lang=self._get_lang()).name_get()[0][1]
        return _filter(val)

    def _perm_read(self, cr, uid):
        def get_log(obj, field=None):
            if field:
                return obj.perm_read()[0][field]
            else:
                return obj.perm_read()[0]
        return get_log

    def _get_report_xml(self):
        return self.registry['ir.actions.report.xml'].browse(self.cr, self.uid, self.report_id)

    def _get_lang(self, source='current'):
        if source=='current':
            return self.context['lang'] or self.context['user_lang']
        elif source=='company':
            return self.context['user'].company_id.partner_id.lang
        elif source=='user':
            return self.context['user_lang']

    def _bool_as_icon(self, val, kind=0):
        if isinstance(kind, (list, tuple)):
            if val==True:
                return kind [0]
            elif val==False:
                return kind[1]
            else:
                return kind[2]
        bool_kind = {0:{True:self._translate_text('True'), False:self._translate_text('False'), None:""},
                     1:{True:self._translate_text('T'), False:self._translate_text('F'), None:""},
                     2:{True:self._translate_text('Yes'), False:self._translate_text('No'), None:""},
                     3:{True:self._translate_text('Y'), False:self._translate_text('N'), None:""},
                     4:{True:'+', False:'-', None:""},
                     5:{True:'[ + ]', False:'[ - ]', None:"[ ]"},
                     6:{True:'[ x ]', False:'[ ]', None:"[ ]"},
                    }
        return bool_kind.get(kind, {}).get(val, val)

    def _dec2time(self, dec, h_format, min_format):
        if dec==0.0:
            return None
        elif int(dec)==0:
            return min_format.replace('%M', str(int(round((dec-int(dec))*60))))
        elif dec-int(dec)==0.0:
            return h_format.replace('%H', str(int(dec)))
        else:
            return h_format.replace('%H', str(int(dec)))+min_format.replace('%M', str(int(round((dec-int(dec))*60))))

    def _currency2text(self, currency):
        def c_to_text(sum, currency=currency, language=None):
            #return unicode(currency_to_text(sum, currency, language or self._get_lang()), "UTF-8")
            return unicode(supported_language.get(language or self._get_lang()).currency_to_text(sum, currency), "UTF-8")
        return c_to_text

    def _translate_text(self, source):
        trans_obj = self.registry['ir.translation']
        trans = trans_obj.search(self.cr,self.uid,[('res_id','=',self.report_id),('type','=','report'),('src','=',source),('lang','=',self.context['lang'] or self.context['user_lang'])])
        if not trans:
            #trans_obj.create(self.cr, self.uid, {'src':source,'type':'report','lang':self._get_lang(),'res_id':self.report_id,'name':('ir.actions.report.xml,%s' % source)[:128]})
            trans_obj.create(self.cr, self.uid, {'src':source,'type':'report','lang':self._get_lang(),'res_id':self.report_id,'name':'ir.actions.report.xml'})
        return translate(self.cr, 'ir.actions.report.xml', 'report', self._get_lang(), source) or source

    def _countif(self, attr, domain):
        statement = domain2statement(domain)
        expr = "for o in objects:\n\tif%s:\n\t\tcount+=1" % statement
        localspace = {'objects':attr, 'count':0}
        exec expr in localspace
        return localspace['count']

    def _count_blank(self, attr, field):
        expr = "for o in objects:\n\tif not o.%s:\n\t\tcount+=1" % field
        localspace = {'objects':attr, 'count':0}
        exec expr in localspace
        return localspace['count']

    def _count(self, attr):
        return len(attr)

    def _sumif(self, attr, sum_field, domain):
        statement = domain2statement(domain)
        expr = "for o in objects:\n\tif%s:\n\t\tsumm+=float(o.%s)" % (statement, sum_field)
        localspace = {'objects':attr, 'summ':0}
        exec expr in localspace
        return localspace['summ']

    def _sum(self, attr, sum_field):
        expr = "for o in objects:\n\tsumm+=float(o.%s)" % sum_field
        localspace = {'objects':attr, 'summ':0}
        exec expr in localspace
        return localspace['summ']

    def _max(self, attr, field):
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects':attr, 'value_list':[]}
        exec expr in localspace
        return max(localspace['value_list'])

    def _min(self, attr, field):
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects':attr, 'value_list':[]}
        exec expr in localspace
        return min(localspace['value_list'])

    def _average(self, attr, field):
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects':attr, 'value_list':[]}
        exec expr in localspace
        return float(sum(localspace['value_list']))/float(len(localspace['value_list']))

    def _asarray(self, attr, field):
        expr = "for o in objects:\n\tvalue_list.append(o.%s)" % field
        localspace = {'objects':attr, 'value_list':[]}
        exec expr in localspace
        return localspace['value_list']

    def _get_name(self, obj, context=None):
        if isinstance(obj, models.Model):
            if context and isinstance(context, dict):
                new_context = obj._context.copy()
                new_context.update(context)
                return obj.with_context(new_context).name_get()[0][1]
            else:
                return obj.name_get()[0][1]
        return ''

    def _get_label(self, obj, field):
        if not obj:
            return ''
        try:
            if isinstance(obj, browse_record_list):
                obj = obj[0]
            if isinstance(obj, (str,unicode)):
                model = obj
            else:
                model = obj._name
            if isinstance(obj, (str,unicode)) or hasattr(obj, field):
                labels = self.registry[model].fields_get(self.cr, self.uid, allfields=[field], context=self.context)
                return labels[field]['string']
        except Exception, e:
            raise e

    def _field_size(self, obj, field):
        try:
            if isinstance(obj, browse_record_list):
                obj = obj[0]
            if isinstance(obj, (str,unicode)):
                model = obj
            else:
                model = obj._name
            if isinstance(obj, (str,unicode)) or hasattr(obj, field):
                size = self.registry[model]._columns[field].size
                return size
        except Exception, e:
            return ''

    def _field_accuracy(self, obj, field):
        try:
            if isinstance(obj, browse_record_list):
                obj = obj[0]
            if isinstance(obj, (str,unicode)):
                model = obj
            else:
                model = obj._name
            if isinstance(obj, (str,unicode)) or hasattr(obj, field):
                digits = self.registry[model]._columns[field].digits
                return digits or [16,2]
        except Exception:
            return []

    def _get_selection_items(self, kind='items'):
        def get_selection_item(obj, field, value=None):
            try:
                if isinstance(obj, browse_record_list):
                    obj = obj[0]
                if isinstance(obj, (str,unicode)):
                    model = obj
                    field_val = value
                else:
                    model = obj._name
                    field_val = getattr(obj, field)
                if kind=='item':
                    if field_val:
                        return dict(self.registry[model].fields_get(self.cr, self.uid, allfields=[field], context=self.context)[field]['selection'])[field_val]
                elif kind=='items':
                    return self.registry[model].fields_get(self.cr, self.uid, allfields=[field], context=self.context)[field]['selection']
                return ''
            except Exception:
                return ''
        return get_selection_item

    def _get_attachments(self, o, index=None, raw=False):
        attach_obj = self.registry['ir.attachment']
        srch_param = [('res_model','=',o._name),('res_id','=',o.id)]
        if type(index)==str:
            srch_param.append(('name','=',index))
        attachments = attach_obj.search(self.cr,self.uid,srch_param)
        res = [x['datas'] for x in attach_obj.read(self.cr,self.uid,attachments,['datas']) if x['datas']]
        convert = raw and base64.decodestring or (lambda a: a)
        if type(index)==int:
            return convert(res[index])
        return convert(len(res)==1 and res[0] or res)

    def _asimage(self, field_value, rotate=None, size_x=None, size_y=None, uom='px', hold_ratio=False):
        def size_by_uom(val, uom, dpi):
            if uom=='px':
                result=str(val/dpi)+'in'
            elif uom=='cm':
                result=str(val/2.54)+'in'
            elif uom=='in':
                result=str(val)+'in'
            return result
        ##############################################
        if not field_value:
            return StringIO.StringIO(), 'image/png'
        field_value = base64.decodestring(field_value)
        tf = StringIO.StringIO(field_value)
        tf.seek(0)
        im=Image.open(tf)
        format = im.format.lower()
        dpi_x, dpi_y = map(float, im.info.get('dpi', (96, 96)))
        try:
            if rotate!=None:
                im=im.rotate(int(rotate))
                tf.seek(0)
                im.save(tf, format)
        except Exception, e:
            logger.error("Error in '_asimage' method", exc_info=True)

        if hold_ratio:
            img_ratio = im.size[0] / float(im.size[1]) # width / height
            if size_x and not size_y:
                size_y = size_x / img_ratio
            elif not size_x and size_y:
                size_x = size_y * img_ratio
            elif size_x and size_y:
                size_y2 = size_x / img_ratio
                size_x2 = size_y * img_ratio
                if size_y2 > size_y:
                    size_x = size_x2
                elif size_x2 > size_x:
                    size_y = size_y2

        size_x = size_x and size_by_uom(size_x, uom, dpi_x) or str(im.size[0]/dpi_x)+'in'
        size_y = size_y and size_by_uom(size_y, uom, dpi_y) or str(im.size[1]/dpi_y)+'in'
        return tf, 'image/%s' % format, size_x, size_y

    def _embed_image(self, extention, img, width=0, height=0, raw=False) :
        "Transform a DB image into an embeded HTML image"
        if not img:
            return ''
        try:
            if width :
                width = ' width="%spx"'%(width)
            else :
                width = ''
            if height :
                height = 'height="%spx" '%(height)
            else :
                height = ''
            if raw:
                toreturn = 'data:image/%s;base64,%s' % (extention, ''.join(str(img).splitlines()))
            else:
                toreturn = '<img%s %ssrc="data:image/%s;base64,%s">' % (width, height, extention, str(img))
            return toreturn
        except Exception, exp:
            logger.error("Error in '_embed_image' method", exc_info=True)
            return 'No image'

    def _large(self, attr, field, n):
        array=self._asarray(attr, field)
        try:
            n-=1
            while(n):
                array.remove(max(array))
                n-=1
            return max(array)
        except ValueError, e:
            return None

    def _small(self, attr, field, n):
        array=self._asarray(attr, field)
        try:
            n-=1
            while(n):
                array.remove(min(array))
                n-=1
            return min(array)
        except ValueError, e:
            return None

    def _chunks(self, l, n):
        """ Yield successive n-sized chunks from l.
        """
        for i in xrange(0, len(l), n):
            yield l[i:i+n]

    def _search_ids(self, model, domain):
        obj = self.registry[model]
        return obj.search(self.cr, self.uid, domain)

    def _search(self, model, domain):
        obj = self.registry[model]
        ids = obj.search(self.cr, self.uid, domain)
        return obj.browse(self.cr, self.uid, ids, {'lang':self._get_lang()})

    def _browse(self, *args):
        if not args or (args and not args[0]):
            return None
        if len(args)==1:
            model, id = args[0].split(',')
            id = int(id)
        elif len(args)==2:
            model, id = args
        else:
            raise None
        return self.registry[model].browse(self.cr, self.uid, id)

    def _get_safe(self, expression, obj):
        try:
            return eval(expression, {'o':obj})
        except Exception, e:
            return None

    def debugit(self, object):
        """ Run the server from command line and 
            call 'debugit' from the template to inspect variables.
        """
        import pdb;pdb.set_trace()
        return

    def _itemize(self, array, purefalse = False, base_num = 1):
        it = iter(array)
        falseval = purefalse and False or ''
        e = it.next()
        lind = 0
        while True:
            lind += 1
            is_even = lind%2 == 0 or falseval
            is_odd = not is_even or falseval
            is_first = lind == 1 or falseval
            try:
                nxt = it.next()
                yield (lind-1, lind+base_num-1, e, is_even, is_odd, is_first, falseval)
                e = nxt
            except StopIteration:
                yield (lind-1, lind+base_num-1, e, is_even, is_odd, is_first, True)
                break

    def _html_escape(self, s):
        toesc={ '<': '&lt;',
                '>': '&gt;',
                '&': '&amp;',
                '"': '&quot;',
                "'": '&apos;' }
        
        if type(s) is str:
            s.decode()
        try:
            return ''.join(map(lambda a: toesc.get(a, a), s))
        except TypeError:
            return s

    def _http_prettyuri(self, s):
        def do_filter(c):
            # filter out reserved and "unsafe" characters
            pos = '''<>$&+,/\:;=?@'"#%{}|^~[]()`'''.find(c)
            if pos >= 0: return False
            
            # filter out ASCII Control characters and unhandled Non-ASCII characters
            ordc = ord(c)
            if (ordc >= 0 and ordc <= 31) or (ordc >= 127 and ordc <= 255): return False
            return c

        if type(s) is str: s.decode()
        # tranlate specific latvian characters into latin and whitespace into dash
        tt = dict(zip(map(ord, 'āčēģīķļņōŗšūžĀČĒĢĪĶĻŅŌŖŠŪŽ '.decode()), 'acegiklnorsuzACEGIKLNORSUZ-'.decode()))
        try:
            s = s.translate(tt)
            return (filter(do_filter, s)).lower()
        except TypeError:
            return s

    def _http_builduri(self, *dicts):
        d = {}
        for ind in dicts:
            d.update(ind)
        result = ''
        for pair in d.iteritems():
            result += '&%s=%s' % pair
        return result

    def _text_restruct(self, text):
        output = html_parts(unicode(text), doctitle=False)
        return output['body']

    def _text_markdown(self, text):
        md = Markdown()
        return md.convert(text)

    def _text_wiki(self, text):
        return wiki2html(text, True)

    def _text_plain(self, msg):
        def text_plain(text):
            logger.info(msg)
            return text
        return text_plain

    def _text_markup(self, text):
        lines = text.splitlines()
        first_line = lines.pop(0)
        if first_line=='text/x-markdown':
            return self._text_markdown('\n'.join(lines))
        elif first_line=='text/x-wiki':
            return self._text_wiki('\n'.join(lines))
        elif first_line=='text/x-rst':
            return self._text_rest('\n'.join(lines))
        return text

    def _text_remove_markup(self, text):
        lines = text.splitlines()
        first_line = lines.pop(0)
        if first_line in ['text/x-markdown', 'text/x-wiki', 'text/x-rst']:
            return '\n'.join(lines)
        return text
