{
    'name': 'odoo_hgs_extra',
    'version': '1.0',
    "author" : "HuaGuoShan OpenERP team",
    'description':
        """
This module provides some extra operations of ERP.
        """,
    'depends': ['base','web'],
    'installable' : True,
    'data': [
        'views/hgs_export_view.xml',
        'views/export_by_sql_view.xml',
    ],
    'qweb' : [
        "static/src/xml/*.xml",
    ],
}
