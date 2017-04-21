# -*- coding: utf-8 -*-

import openerp
from openerp.osv import fields, osv, orm
from openerp import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)
from openerp.addons.odoo_hgs_erp import hgs_common

class init_address_records(osv.osv_memory):
    _name = 'hgs.init_address_records'
    
    _columns = {
        'operation_note': fields.text(u'操作提示'),
        'province_id':fields.many2one('res.country.state', u'省'),
        'city_id':fields.many2one('res.country.state.city', u'市', domain="[('state_id','=',province_id)]"),
        'district_id':fields.many2one('res.country.state.city.district', u'区', domain="[('city_id','=',city_id)]"),
        'order_created_start' : fields.datetime(u'下单时间', help=u'按照订单下单时间筛选，支持单向查找'),
        'order_created_end' : fields.datetime(u'至'),
    }
    
    def default_get(self, cr, uid, fields, context={}):
        vals = {}
        vals['operation_note'] = u'请至少填写“省”，尽量使用时间区间（下单时间），避免订单量过大导致处理时间过长'
        return vals
    
    def onchange_city(self, cr, uid, ids, province_id=False, city_id=False, context=None):
        '''填写“市”未填写“省”时自动补全'''
        if not city_id:
            return
        value = {}
        print city_id
        city = self.pool.get('hgs.country.state.city').browse(cr, uid, city_id)
        if not province_id:
            value['province_id'] = city.state_id.id
        return {'value': value}
    
    def onchange_district(self, cr, uid, ids, province_id=False, city_id=False, district_id=False, context=None):
        '''填写“区”未填写“省“、“市”时自动补全'''
        if not district_id:
            return
        value = {}
        print district_id
        district = self.pool.get('hgs.country.state.city.district').browse(cr, uid, district_id)
        if not province_id:
            value['province_id'] = district.state_id.id
        if not city_id:
            value['city_id'] = district.city_id.id
        return {'value': value}
    
    def init_address_records_by_sale_order(self, cr, uid, ids, context={}):
        ''''''
        if not ids:
            raise osv.except_orm('提示', '获取信息失败，请关闭窗口，重新操作')
        condition = self.browse(cr,uid,ids)[0]
        province_id = condition.province_id
        city_id = condition.city_id
        district_id = condition.district_id
        if not province_id:
            raise osv.except_orm('提示', '请至少填写”省“')
        elif district_id and not city_id:
            raise osv.except_orm('提示', '请选择”市“')
        order_created_start = condition.order_created_start
        order_created_end = condition.order_created_end
        address_select_sql = '''SELECT so.province_id AS province, so.city_id AS city, so.district_id AS district, so.receiver_address AS detail_address 
                                FROM sale_order so 
                                WHERE '''
        where_list = []
        #至少会有省条件
        where_list.append("so.province_id = %s" %province_id.id)
        if city_id:
            where_list.append("so.city_id = %s" %city_id.id)
        if district_id:
            where_list.append("so.district_id = %s" %district_id.id)
        if order_created_start:
            order_created_start = hgs_common.transformUTCTime2LocalTime(order_created_start)
            where_list.append("so.order_created >= '%s'" %order_created_start)
        if order_created_end:
            order_created_end = hgs_common.transformUTCTime2LocalTime(order_created_end)
            where_list.append("so.order_created <= '%s'" %order_created_end)
        where_string = " AND ".join(where_list)
        address_select_sql += where_string
        print address_select_sql
        cr.execute(address_select_sql)
        address_info_list = cr.dictfetchall()
        print address_info_list
        try:
            self.pool.get('res.country.address').batch_create_address_record(cr, uid, address_info_list)
            return True
        except Exception, e:
            if getattr(e, 'name', None) and getattr(e, 'value', None):
                raise osv.except_orm(e.name, e.value)
            else:
                raise osv.except_orm('提示', str(e))
        
    
    
    
    
    