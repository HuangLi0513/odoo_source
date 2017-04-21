# -*- coding: utf-8 -*-
'''
Created on 2017-03-30

@author: huangli
'''
from openerp.osv import fields, osv

AMAP_WEB_API_ADDRESS = None
AMAP_WEB_SERVICE_KEY = None
AMAP_WEB_SERVICE_SECRET = None
AMAP_YUNTU_API_ADDRESS = None



class logistics_hgx_configuration(osv.osv):
    _name = 'logistics.hgx.configuration'
    _columns = {
            'amap_web_api_address': fields.char(u'Web API Address', help=u'高德地图Web服务API地址', required=True),
            'amap_web_service_key':fields.char(u'Web API Key', help=u'高德地图Web服务API类型Key', required=True),
            'amap_web_service_secret':fields.char(u'Web API Secret', help=u'高德地图Web服务API类型私钥', required=True),
            'amap_yuntu_api_address': fields.char(u'Yuntu API Address', help=u'高德地图云图服务API地址', required=True),
        }
    _default = {
        }
    
class logistics_hgx_config_settings(osv.osv_memory):
    _name = 'logistics.hgx.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
            'amap_web_api_address': fields.char(u'Web API Address', help=u'高德地图Web服务API地址', required=True),
            'amap_web_service_key':fields.char(u'Web API Key', help=u'高德地图Web服务API类型Key', required=True),
            'amap_web_service_secret':fields.char(u'Web API Secret', help=u'高德地图Web服务API类型私钥', required=True),
            'amap_yuntu_api_address': fields.char(u'Yuntu API Address', help=u'高德地图云图服务API地址', required=True),
        }
    
    def get_default_hgx_configuration(self,cr, uid, fields, context=None):
        vals = {}
        hgx_configuration_obj = self.pool.get('logistics.hgx.configuration')
        hgx_configuration_ids = hgx_configuration_obj.search(cr,uid,[])
        amap_web_api_address = ''
        amap_web_service_key = ''
        amap_web_service_secret = ''
        amap_yuntu_api_address = ''
        if hgx_configuration_ids:
            hgx_configuration = hgx_configuration_obj.browse(cr, uid, hgx_configuration_ids[0])
            amap_web_api_address = hgx_configuration.amap_web_api_address
            amap_web_service_key = hgx_configuration.amap_web_service_key
            amap_web_service_secret = hgx_configuration.amap_web_service_secret
            amap_yuntu_api_address = hgx_configuration.amap_yuntu_api_address
        vals['amap_web_api_address'] = amap_web_api_address
        vals['amap_web_service_key'] = amap_web_service_key
        vals['amap_web_service_secret'] = amap_web_service_secret
        vals['amap_yuntu_api_address'] = amap_yuntu_api_address
        return vals
    
    def set_hgx_configuration(self,cr, uid, ids, context=None):
        vals = {}
        config = self.browse(cr, uid, ids[0])
        vals['amap_web_api_address'] = config.amap_web_api_address
        vals['amap_web_service_key'] = config.amap_web_service_key
        vals['amap_web_service_secret'] = config.amap_web_service_secret
        vals['amap_yuntu_api_address'] = config.amap_yuntu_api_address
        
        hgx_configuration_obj = self.pool.get('logistics.hgx.configuration')
        hgx_configuration_ids = hgx_configuration_obj.search(cr, uid, [])
        if hgx_configuration_ids:
            hgx_configuration_obj.write(cr, uid, hgx_configuration_ids[0], vals)
        else:
            hgx_configuration_ids = hgx_configuration_obj.create(cr, uid, vals)

logistics_hgx_configuration()