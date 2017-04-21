# -*- coding: utf-8 -*-
#########################################################################
# Copyright (C) 2009  Eric.Chen, HuaGuoShan ERP Solution    #
# Copyright (C) 2014-Today  ShenZhen www.huaguoshan.com                   #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
{
    "name" : "odoo HuaGuoXian Logistics Support",
    "version" : "1.0",
    "author" : "huaguoshan OpenERP team",
    "website" : "http://www.huaguoshan.com",
    "depends" : [
        'base',
        'odoo_hgs_erp',
        'odoo_logistics_base',
        ],
    'data': [
              "hgx_view.xml",
              "res_country_address_view.xml",
              "hgx_config_settings_view.xml",
              "wizard/init_address_records_view.xml",
    ],
    "installable" : True,
    "active": True,
    "category":'Generic Modules/Others' ,
    'description' : """
Connecting to HGX Logistics
==================================================

""",
}
