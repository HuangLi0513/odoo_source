# -*- coding: utf-8 -*-
import openerp
from openerp import models
from openerp.models import BaseModel, fix_import_export_id_paths
from openerp import api

def __new_export_rows(self, fields):
     
    def to_unicode(value):
        if not isinstance(value, basestring):
            value = str(value)
        return isinstance(value, unicode) and value or unicode(value, encoding='utf-8')
    
    lines = []
    for record in self:
        current = [''] * len(fields)
        lines.append(current)
         
        # list of primary fields followed by secondary field(s)
        primary_done = []

        # process column by column
        for i, path in enumerate(fields):
            if not path:
                continue

            name = path[0]
            if name in primary_done:
                continue

            if name == 'id':
                current[i] = to_unicode(getattr(record, 'name', record.id))
            else:
                field = record._fields[name]
                value = record[name]

                # this part could be simpler, but it has to be done this way
                # in order to reproduce the former behavior
                if not isinstance(value, BaseModel):
                    value = field.convert_to_export(value, self.env) or ''
                    current[i] = to_unicode(value)
                else:   #one2many/many2one/many2many
                    primary_done.append(name)

                    # This is a special case, its strange behavior is intended!
                    if field.type == 'many2many' and len(path) > 1 and path[1] == 'id':
                        m2m_field = [str(getattr(r, 'name', r.id)) for r in value]
                        current[i] = to_unicode(','.join(m2m_field) or '')
                        continue

                    # recursively export the fields that follow name
                    fields2 = [(p[1:] if p and p[0] == name else []) for p in fields]
                    lines2 = value.__new_export_rows(fields2)
                    if lines2:
                        # merge first line with record's main line
                        for j, val in enumerate(lines2[0]):
                            if val:
                                current[j] = val
#                             # check value of current field
                        lines += lines2[1:]
                    else:
                        current[i] = ''

    return lines
 
@api.multi
def new_export_data(self, fields_to_export, raw_data=False):
    fields_to_export = map(fix_import_export_id_paths, fields_to_export)
    print fields_to_export
    if raw_data:
        self = self.with_context(export_raw_data=True)

    return {'datas': self.__new_export_rows(fields_to_export)}
    
    
BaseModel.new_export_data = new_export_data
BaseModel.__new_export_rows = __new_export_rows


    
    
    
    
    
    



