# -*- coding: utf-8 -*-
'''
Created on 2016-03-13

@author: HuangLi
'''

from openerp.osv import osv, fields
from openerp import SUPERUSER_ID
import time
import re
from ..odoo_hgs_erp import hgs_common
from amap import AMAP, Amap_request_sdk
from hgx_config_settings import AMAP_WEB_API_ADDRESS, AMAP_WEB_SERVICE_KEY, AMAP_WEB_SERVICE_SECRET, AMAP_YUNTU_API_ADDRESS

def check_amap_settings(func):
    #装饰器函数（检查高德设置）
    def check_settings(self, cr, uid, *args, **kwargs):
        global AMAP_WEB_API_ADDRESS, AMAP_WEB_SERVICE_KEY, AMAP_WEB_SERVICE_SECRET, AMAP_YUNTU_API_ADDRESS
        if not (AMAP_WEB_API_ADDRESS and AMAP_WEB_SERVICE_KEY and AMAP_WEB_SERVICE_SECRET and AMAP_YUNTU_API_ADDRESS):
            print '1'
            #获取高德账号数据
            hgx_configuration_obj = self.pool.get('logistics.hgx.configuration')
            hgx_configuration_ids = hgx_configuration_obj.search(cr,uid,[])
            if not hgx_configuration_ids:
                raise osv.except_orm('提示', '未找到高德账号信息，请ERP人员设置')
            hgx_configuration = hgx_configuration_obj.browse(cr, uid, hgx_configuration_ids[0])
            AMAP_WEB_API_ADDRESS = hgx_configuration.amap_web_api_address
            AMAP_WEB_SERVICE_KEY = hgx_configuration.amap_web_service_key
            AMAP_WEB_SERVICE_SECRET = hgx_configuration.amap_web_service_secret
            AMAP_YUNTU_API_ADDRESS = hgx_configuration.amap_yuntu_api_address
            if not (AMAP_WEB_API_ADDRESS and AMAP_WEB_SERVICE_KEY and AMAP_WEB_SERVICE_SECRET and AMAP_YUNTU_API_ADDRESS):
                raise osv.except_orm('提示', '高德账号信息设置不全，请ERP人员检查设置')
        func(self, cr, uid, *args, **kwargs)
    return check_settings

class res_country_address(osv.osv, hgs_common.HuaguoshanMixin):
    _name = "res.country.address"
    
    _columns = {
        'name': fields.char(u'名称', size=128),
        'province': fields.many2one('res.country.state', u'省'),
        'city': fields.many2one('res.country.state.city', u'市', domain="[('province','=',province)]"),
        'district': fields.many2one('res.country.state.city.district', u'区', domain="[('city','=',city)]"),
        'town': fields.char(u'乡镇', size=64),
        'street': fields.char(u'街道', size=64),
        'detail_address': fields.text(u'详细地址', require=True),
        'formatted_address': fields.char(u'结构化地址', size=256),
        'key_words': fields.text(u'关键字'),
        'amap_location': fields.char(u'高德坐标', readonly=True),
        'amap_location_level': fields.char(u'高德定位级别', size=64),
        
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        write_result = super(res_country_address, self).write(cr, uid, ids, vals, context=context)
        if vals.has_key('detail_address'):
            self.get_amap_location_4_address(cr, uid, ids, context)
        return write_result

    def batch_create_by_address_info(self, cr, uid, address_info_list=None):
        '''address_info_list = [{'province':province_name, 'city':city_name, 'district':district_name, 'street':street_name, 'detail_address':detail_address},...]'''
        if not address_info_list:
            return
        for address_info in address_info_list:
            province = address_info.get('province', None)
            city = address_info.get('city', None)
            district = address_info.get('distict', None)
            street = address_info.get('street', None)
            #将省市区转化系统中对应的记录id
            province, city, district = self.pool.get('hgs.shop').get_province_city_district_ids(cr, uid, province, city, district)
            address_info['province'] = province
            address_info['city'] = city
            address_info['district'] = district
        try:
            self.batch_create_address_record(cr, uid, address_info_list)
            return True
        except Exception, e:
            if getattr(e, 'name', None) and getattr(e, 'value', None):
                raise osv.except_orm(e.name, e.value)
            else:
                raise osv.except_orm('提示', str(e))
    
    def batch_create_address_record(self, cr, uid, address_list):
        '''address_list = [{'province':province_id, 'city':city_id, 'district':district_id, 'street':street_name, 'detail_address':detail_address},...]'''
        create_data_list = []   #用于批量插入的数据列表
        mark_obj = self.pool.get('hgs.block_special_mark')  #特殊字符替换对象
        for address_info in address_list:
            create_data = address_info.copy()
            detail_address = address_info.get('detail_address', None)
            if not detail_address:
                continue
            result, error = mark_obj.refresh_content_with_handling_block_special_mark(cr, uid, detail_address)
            create_data['detail_address'] = result or detail_address
            #检查在数据库中是否已存在该地址
            address_ids = self.search(cr, uid, args=[('detail_address', '=', create_data['detail_address'])])
            if address_ids:
                continue
            print create_data
            create_data_list.append(create_data)
        if not create_data_list:
            return
        #批量写入
        try:
            self.speed_save_by_sql(cr, uid, 'res.country.address', create_data_list)
            return
        except Exception, e:
            raise e
            
    @check_amap_settings
    def get_amap_location_4_address(self, cr, uid, ids, context=None):
        '''批量获取地址的高德地址坐标'''
        if not ids:
            return
        address_info_list = self.browse(cr, uid, ids)
        print AMAP_WEB_SERVICE_KEY
        print AMAP_WEB_SERVICE_SECRET
        print AMAP_WEB_API_ADDRESS
        address_index_geocode_map, error_info = Amap_request_sdk.batch_get_geocode(key=AMAP_WEB_SERVICE_KEY, secret=AMAP_WEB_SERVICE_SECRET, api_address=AMAP_WEB_API_ADDRESS,\
                                                                                   address_list = map(lambda x: x.detail_address or '', address_info_list))
        update_data_list = []
        for index, geocode in address_index_geocode_map.iteritems():
            address = address_info_list[index]
            update_info = {}
            update_info['formatted_address'] = geocode.get('formatted_address', '')
            key_words = re.split(u'(省|市|区)', update_info['formatted_address'], maxsplit=3)
            for index, key_word in enumerate(key_words):
                if key_word in [u'省', u'市', u'区']:
                    key_words[index - 1] += key_word
                
            update_info['key_words'] = ','.join(filter(lambda x: x not in [u'省', u'市', u'区'], key_words))
            update_info['name'] = key_words[-1]
            
            update_info['amap_location'] = geocode.get('location', '')
            update_info['amap_location_level'] = geocode.get('level', '')
            update_data = ([address.id], update_info)
            update_data_list.append(update_data)
        #批量更新地址数据
        try:
            self.speed_update_by_sql(cr, uid, 'res.country.address', update_data_list)
            cr.commit()
            if error_info:
                raise osv.except_orm('提示', error_info)
            return
        except Exception, e:
            if getattr(e, 'name', None) and getattr(e, 'value', None):
                raise osv.except_orm(e.name, e.value)
            else:
                raise osv.except_orm('提示', str(e))
     
        
        
        
        
        
        
        
        
        
        
        
            
        
            