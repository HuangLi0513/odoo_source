# -*- coding: utf-8 -*-
'''
Created on 2016-03-13

@author: HuangLi
'''

from openerp.osv import osv, fields
from openerp import SUPERUSER_ID
import time
from ..odoo_hgs_erp import hgs_common
from amap import Amap_request_sdk
from hgx_config_settings import AMAP_WEB_API_ADDRESS, AMAP_WEB_SERVICE_KEY, AMAP_WEB_SERVICE_SECRET, AMAP_YUNTU_API_ADDRESS

def check_amap_settings(func):
    #装饰器函数（检查高德设置）
    def check_settings(self, cr, uid, *args, **kwargs):
        global AMAP_WEB_API_ADDRESS, AMAP_WEB_SERVICE_KEY, AMAP_WEB_SERVICE_SECRET, AMAP_YUNTU_API_ADDRESS
        if not (AMAP_WEB_API_ADDRESS and AMAP_WEB_SERVICE_KEY and AMAP_WEB_SERVICE_SECRET and AMAP_YUNTU_API_ADDRESS):
            print '2'
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
        return func(self, cr, uid, *args, **kwargs)
    return check_settings

class logistics_company(hgs_common.HuaguoshanMixin):
    pass

class logistics_hgx(osv.osv, logistics_company):
    _name = "logistics.hgx"
    
    _columns = {
        'name': fields.char(u'名称', size=64, required=True),
        'partner_white_list': fields.many2many('res.partner', 'logistics_hgx_2_valid_partner', 'logistics_hgx_id', 'partner_id', u'客户白名单'),
        'partner_black_list': fields.many2many('res.partner', 'logistics_hgx_2_invalid_partner', 'logistics_hgx_id', 'partner_id', u'客户黑名单'),
        #可达区域
        'available_areas':fields.one2many('logistics.hgx.area.line', 'company_available_area', u'可达区域'),
#         'available_areas':fields.many2many('logistics.hgx.area.line', 'available_areas_4_logistics_hgx', 'company_id', 'area_line_id', u'可达区域'),
        #不可达区域
#         'unavailable_areas':fields.many2many('logistics.hgx.area.line', 'unavailable_areas_4_logistics_hgx', 'company_id', 'area_line_id', u'不可达区域'),
        'unavailable_areas':fields.one2many('logistics.hgx.area.line', 'company_unavailable_area', u'不可达区域'),
        
        'delivery_terminal':fields.one2many('logistics.hgx.delivery_terminal', 'company_id', u'配送站'),
        'cloud_map': fields.char(u'云图表ID', readonly=True),
    }

    @check_amap_settings
    def create_cloud_map(self, cr, uid, ids, context=None):
        if not ids:
            return
        
        logistics_hgx_list = self.browse(cr, uid, ids)
        error_info = ''
        for logistics_hgx in logistics_hgx_list:
            if logistics_hgx.cloud_map:
                continue
            rsp, error_msg = Amap_request_sdk.create_a_cloud_map(AMAP_WEB_SERVICE_KEY, AMAP_WEB_SERVICE_SECRET, AMAP_WEB_API_ADDRESS, \
                                                                 map_name=logistics_hgx.name)
            if error_msg:
                error_info += '[%s]%s\n' %(logistics_hgx.name, error_msg)
                continue
            if not rsp.has_key('status'):
                error_info += '[%s]%s\n' %(logistics_hgx.name, rsp)
                continue
            elif int(rsp.get('status', 0)) != 1:
                error_info += '[%s]%s(%s)\n' %(logistics_hgx.name, rsp.get('info', None), rsp)
                continue
            else:
                table_id = rsp.get('tableid', None)
                self.write(cr, uid, logistics_hgx.id, {'cloud_map': table_id})
        if error_info:
            cr.commit()
            raise osv.except_orm('提示', error_info)
        return
    
    @check_amap_settings
    def update_cloud_map(self, cr, uid, ids, context=None):
        '''更新云图：更新已有的元素，创建新的元素'''
        if not ids:
            return
        
        logistics_hgx_list = self.browse(cr, uid, ids)
        error_info = ''
        for logistics_hgx in logistics_hgx_list:
            if not logistics_hgx.cloud_map:
                error_info += '[%s]请先创建云图数据表\n' %logistics_hgx.name
                continue
            terminal_ids = map(lambda x: x.id, logistics_hgx.delivery_terminal)
            try:
                self.pool.get('logistics.hgx.delivery_terminal').update_cloud_map_point_info(cr, uid, terminal_ids)
            except Exception, e:
                error_info += '%s\n' %getattr(e, 'value', None) or str(e)
                continue
        if error_info:
            cr.commit()
            raise osv.except_orm('提示', error_info)
                
        return
    
    def divide_address_4_hgx(self, cr, uid, ids, context=None):
        ''''''
        if not ids:
            return
        if len(ids) > 1:
            raise osv.except_orm('提示', '暂不支持批量')
        logistics_hgx = self.browse(cr, uid, ids)[0]
        map_id = logistics_hgx.cloud_map
        if not map_id:
            raise osv.except_orm('提示', '请先创建云图数据表')
        
        address_select_sql = 'SELECT id, name, formatted_address, amap_location FROM res_country_address '
        #可达区域
        available_list = []
        for available_area in logistics_hgx.available_areas:
            province_id = available_area.province_id.id
            city_id = available_area.city_id.id
            district_id = available_area.district_id.id
            where_sql = '(%s %s %s)' %(province_id and 'province=%s' %province_id or '', \
                                       city_id and 'AND city=%s' %city_id or '', \
                                       district_id and 'AND district=%s' %district_id or '')
            available_list.append(where_sql)
        #不可达区域
        unavailable_list = []
        for unavailable_area in logistics_hgx.unavailable_areas:
            province_id = unavailable_area.province_id.id
            city_id = unavailable_area.city_id.id
            district_id = unavailable_area.district_id.id
            where_sql = '(%s %s %s)' %(province_id and 'province!=%s' %province_id or '', \
                                       city_id and 'AND city!=%s' %city_id or '', \
                                       district_id and 'AND district!=%s' %district_id or '')
            unavailable_list.append(where_sql)
        #拼接地址查询语句
        if available_list and unavailable_list:
            address_select_sql += 'WHERE %s AND %s' %(' OR '.join(available_list), ' AND '.join(unavailable_list))
        elif not available_list and unavailable_list:
            address_select_sql += 'WHERE %s' %' AND '.join(unavailable_list)
        elif available_list and not unavailable_list:
            address_select_sql += 'WHERE %s' %' OR '.join(available_list)
        cr.execute(address_select_sql)
        result = cr.dictfetchall()
        terminals = logistics_hgx.delivery_terminal
        terminal_map_ids = map(lambda x: x.cloud_map_point, terminals)
        relation_data_list = []
        for address_info in result:
            if not address_info['amap_location']:
                continue
            terminal_datas = self.get_optimal_terminal_4_address(cr, uid, map_id, address_info['amap_location'], 5000, context=context)
            if not terminal_datas:
                continue
            terminal_map_id = None
            for terminal_data in terminal_datas:
                if str(terminal_data['_id']) in terminal_map_ids:
                    terminal_map_id = str(terminal_data['_id'])
                    break
            if not terminal_map_id:
                continue
            terminal = filter(lambda x: x.cloud_map_point == terminal_map_id, terminals)
            if terminal:
                relation_data = {}
                relation_data['terminal_id'] = terminal[0].id
                relation_data['address_id'] = address_info['id']
                relation_data_list.append(relation_data)
        if relation_data_list:
            insert_sql = ''
            relation_table_name = 'available_address_4_delivery_terminal'
            for data in relation_data_list:
#                 search_sql = 'SELECT terminal_id, address_id FROM %s WHERE terminal_id in (%s) AND address_id=%s' %(relation_table_name, ','.join([str(t.id) for t in terminals]), data['address_id'])
#                 cr.execute(search_sql)
#                 rel = cr.dictfetchall()
                
                
                delete_sql = 'DELETE FROM %s WHERE terminal_id in (%s) AND address_id=%s' %(relation_table_name, ','.join([str(t.id) for t in terminals]), data['address_id'])
                cr.execute(delete_sql)
                insert_sql += 'INSERT INTO %s (terminal_id, address_id) VALUES (%s, %s);' %(relation_table_name, data['terminal_id'], data['address_id'])
            if not insert_sql:
                return True
            try:
                cr.execute(insert_sql)
            except Exception, e:
                raise osv.except_orm('关系数据写入异常', str(e))
        return True
            
    @check_amap_settings       
    def get_optimal_terminal_4_address(self, cr, uid, map_id=None, address_location=None, radius=5000, context=None):
        rsp, error_msg = Amap_request_sdk.yuntu_search_around(AMAP_WEB_SERVICE_KEY, AMAP_WEB_SERVICE_SECRET, AMAP_YUNTU_API_ADDRESS, \
                                                              map_id=map_id, center_location=address_location, radius=radius)
        if int(rsp.get('status', 0)) != 1:
            return None
        elif int(rsp.get('count', 0)) <= 0:
            return None
        datas = rsp.get('datas', [])
        if not datas:
            return None
        return datas
        
                

class logistics_hgx_delivery_terminal(osv.osv, hgs_common.HuaguoshanMixin):
    _name = "logistics.hgx.delivery_terminal"
    
    _columns = {
        'name': fields.char(u'配送点名称', size=64, required=True),
        'province': fields.many2one('res.country.state', u'省', required=True),
        'city': fields.many2one('res.country.state.city', u'市', domain="[('state_id','=',province)]", required=True),
        'district': fields.many2one('res.country.state.city.district', u'区', domain="[('city_id','=',city)]", required=True),
        'detail_address': fields.text(u'详细地址', required=True),
        'formatted_address': fields.char(u'结构化地址', size=256),
        'amap_location': fields.char(u'高德坐标', size=64, readonly=True),
        #可达区域
        'available_areas':fields.one2many('logistics.hgx.area.line', 'terminal_available_area', u'可配送区域'),
        #不可达区域
        'unavailable_areas':fields.one2many('logistics.hgx.area.line', 'terminal_unavailable_area', u'不可配送区域'),
        #客户黑名单
        
        'company_id': fields.many2one('logistics.hgx', u'物流公司', required=True),
        'cloud_map': fields.related('company_id', 'cloud_map', type='char', string=u'云图表ID'),
        'cloud_map_point': fields.char(u'云图元素ID', readonly=True),
        'available_address':fields.many2many('res.country.address', 'available_address_4_delivery_terminal', 'terminal_id', 'address_id', u'可配送地址'),
        
    }
    
    @check_amap_settings
    def get_amap_location(self, cr, uid, ids, context=None):
        if not ids:
            return
        
        delivery_terminal_list = self.browse(cr, uid, ids)
        rsp, error_info = Amap_request_sdk.batch_get_geocode(AMAP_WEB_SERVICE_KEY, AMAP_WEB_SERVICE_SECRET, AMAP_WEB_API_ADDRESS,\
                                                             address_list = map(lambda x: x.detail_address or '', delivery_terminal_list))
        update_data_list = []
        for index, geocode in rsp.iteritems():
            update_info = {}
            update_info['formatted_address'] = geocode.get('formatted_address', '')
            update_info['amap_location'] = geocode.get('location', '')
            update_data = ([delivery_terminal_list[index].id], update_info)
            update_data_list.append(update_data)
        #批量更新地址数据
        try:
            self.speed_update_by_sql(cr, uid, 'logistics.hgx.delivery_terminal', update_data_list)
            cr.commit()
            if error_info:
                raise osv.except_orm('提示', error_info)
            return
        except Exception, e:
            if getattr(e, 'name', None) and getattr(e, 'value', None):
                raise osv.except_orm(e.name, e.value)
            else:
                raise osv.except_orm('提示', str(e))
        
    @check_amap_settings
    def update_cloud_map_point_info(self, cr, uid, ids, context=None):    
        '''更新云图元素信息：有ID则更新，无ID则创建'''
        if not ids:
            return
        
        error_info = ''
        for terminal in self.browse(cr, uid, ids):
            if not terminal.amap_location:
                error_info += '[%s]无坐标信息，请先获取高德坐标\n' %terminal.name
                continue
            if terminal.cloud_map_point:
                rsp, error_msg = Amap_request_sdk.update_a_point_4_cloud_map(AMAP_WEB_SERVICE_KEY, AMAP_WEB_SERVICE_SECRET, AMAP_YUNTU_API_ADDRESS, \
                                                                             map_id=terminal.cloud_map, point_id=terminal.cloud_map_point, \
                                                                             name=terminal.name, location=terminal.amap_location, \
                                                                             address=terminal.detail_address)
            else:
                rsp, error_msg = Amap_request_sdk.create_a_point_4_cloud_map(AMAP_WEB_SERVICE_KEY, AMAP_WEB_SERVICE_SECRET, AMAP_YUNTU_API_ADDRESS, \
                                                                             map_id=terminal.cloud_map, name=terminal.name, location=terminal.amap_location, \
                                                                             address=terminal.detail_address)
            if error_msg:
                error_info += '[%s]%s\n' %(terminal.name, error_msg)
                continue
            if not rsp.has_key('status'):
                error_info += '[%s]%s\n' %(terminal.name, rsp)
                continue
            elif int(rsp.get('status', 0)) != 1:
                error_info += '[%s]%s(%s)\n' %(terminal.name, rsp.get('info', None), rsp)
                continue
            if rsp.has_key('_id'):
                point_id = rsp.get('_id', None)
                self.write(cr, uid, terminal.id, {'cloud_map_point': point_id})
        if error_info:
            cr.commit()
            raise osv.except_orm('提示', error_info)
        return

class logistics_hgx_area_line(osv.osv):
    _name = 'logistics.hgx.area.line'
    _columns = {
            'province_id':fields.many2one('res.country.state',u'省'),
            'city_id':fields.many2one('res.country.state.city',u'市',domain="[('state_id','=',province_id)]"),
            'district_id':fields.many2one('res.country.state.city.district',u'区',domain="[('city_id','=',city_id)]"),
            'company_available_area':fields.many2one('logistics.hgx',u'物流公司可达'),
            'company_unavailable_area':fields.many2one('logistics.hgx',u'物流公司不可达'),
            'terminal_available_area':fields.many2one('logistics.hgx.delivery_terminal',u'配送点可达'),
            'terminal_unavailable_area':fields.many2one('logistics.hgx.delivery_terminal',u'配送点不可达'),
    }






