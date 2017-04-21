# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)
import operator
import datetime
import re
import simplejson
import sys
import time
from xml.etree import ElementTree
from cStringIO import StringIO

try:
    import xlwt
except ImportError:
    xlwt = None

import openerp
from openerp import http

from openerp.http import request, serialize_exception as _serialize_exception
from openerp.addons.web.controllers.main import Export, ExportFormat, content_disposition, serialize_exception

class HgsExport(Export):
    
    @http.route('/hgs/export/formats', type='json', auth="user")
    def formats(self):
        """ Returns all valid export formats
        :returns: for each export format, a pair of identifier and printable name
        :rtype: [(str, str)]
        """
        return [
            {'tag': 'xls', 'label': 'Excel', 'error': None if xlwt else "XLWT required"},
#             {'tag': 'csv', 'label': 'CSV'},
        ]

class HgsExcelExport(ExportFormat, http.Controller):
    # Excel needs raw data to correctly handle numbers and date values
    raw_data = True

    @http.route('/hgs/extra/export/xls', type='http', auth="user")
    @serialize_exception
    def index(self, data, token):
        return self.base(data, token)

    @property
    def content_type(self):
        return 'application/vnd.ms-excel'

    def filename(self, base):
        return base + '.xls'
    
    def base(self, data, token):
        params = simplejson.loads(data)
        model, fields, ids, domain, import_compat = \
            operator.itemgetter('model', 'fields', 'ids', 'domain',
                                'import_compat')(
                params)
        Model = request.session.model(model)
        
        context = dict(request.context or {}, **params.get('context', {}))
        ids = ids or Model.search(domain, 0, False, False, context)

        field_names = map(operator.itemgetter('name'), fields)
        
        import_data = Model.new_export_data(ids, field_names, self.raw_data, context=context).get('datas',[])
        
        columns_headers = [val['label'].strip() for val in fields]

        return request.make_response(self.from_data(columns_headers, import_data),
            headers=[('Content-Disposition', content_disposition(self.filename(model))),
                     ('Content-Type', self.content_type)],
            cookies={'fileToken': token})

    def from_data(self, fields, rows):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Sheet 1')

        for i, fieldname in enumerate(fields):
            worksheet.write(0, i, fieldname)
            worksheet.col(i).width = 8000 # around 220 pixels

        base_style = xlwt.easyxf('align: wrap yes')
        date_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD')
        datetime_style = xlwt.easyxf('align: wrap yes', num_format_str='YYYY-MM-DD HH:mm:SS')

        for row_index, row in enumerate(rows):
            for cell_index, cell_value in enumerate(row):
                cell_style = base_style
                if isinstance(cell_value, basestring):
                    cell_value = re.sub("\r", " ", cell_value)
                elif isinstance(cell_value, datetime.datetime):
                    cell_style = datetime_style
                elif isinstance(cell_value, datetime.date):
                    cell_style = date_style
                worksheet.write(row_index + 1, cell_index, cell_value, cell_style)

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        return data
    
    
    
    
    
    
    
    