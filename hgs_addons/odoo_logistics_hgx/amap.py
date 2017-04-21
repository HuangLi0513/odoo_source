# -*- coding: utf-8 -*-
'''
Created on 2016-03-20

@author: HuangLi
'''

import time
import hashlib
import requests
import urllib
import json

    
class AMAP(object):
    def __init__(self, key=None, secret=None):
        self.key = key
        self.secret = secret
    
    def _getTimestamp(self):
        return int(time.time())
    
    def _sign(self, secret, params):
        keys = params.keys()
        keys.sort(lambda str1, str2: cmp(str1.lower(), str2.lower()))
        params = "%s%s" % (('&').join('%s=%s' % (key, params[key]) for key in keys), secret)
        print params
        sign = hashlib.md5(params).hexdigest()
        print sign
        return sign

    def _get_resp(self, url, params, headers=None, http_method='POST'):
        ''' 提交http请求，获取并初步解析请求结果'''
        if not headers:
            headers = {
                         "Content-type": "application/x-www-form-urlencoded;charset=UTF-8",
                         "Cache-Control": "no-cache",
                         "Connection": "Keep-Alive",
                    }
        try:
            if http_method == 'GET':
                url += '?%s' %urllib.urlencode(params)
                r = requests.get(url, data=params, headers=headers)
            else:
                r = requests.post(url, data=params, headers=headers)
            return r.json(), None
        except Exception, e:
            return None, str(e)

    def execute(self, api_address, api_router, http_method='POST', **kwargs):
        params = {}
        #解析api应用级参数
        for k, v in kwargs.iteritems():
            if v: params[k] = v
        #拼接系统级参数
        params['key'] = self.key
        params['sig'] = self._sign(self.secret, params)
        #提交请求
        url = '%s%s' %(api_address, api_router or '')
        headers = {}
        print url
        rsp, error_info = self._get_resp(url, params, headers=headers, http_method=http_method)
        print rsp
        print error_info
        #解析请求是否成功
        return self._parse_resp_error(rsp, error_info)

    def __call__(self, api_address, api_router, http_method=None, **kwargs):
        return self.execute(api_address, api_router, http_method=http_method, **kwargs)
    
    def _parse_resp_error(self, rsp, error_info):
        '''预先解析返回的错误信息'''
        if error_info:
            return rsp, error_info
        try:
            result = rsp.get('infocode', None)
            if result == '10000':
                return rsp, None
            else:
                return rsp, rsp.get('info', '%s' %rsp)
        except Exception, e:
            return rsp, '%s' %rsp
        
class Amap_request_sdk(object):
    '''封装高德地图部分API的请求方法'''
    
    @staticmethod
    def batch_get_geocode(key, secret, api_address, api_router='/v3/geocode/geo', http_method='GET', address_list=[]):
        '''批量请求高德地理编码接口，获得高德地图坐标；request_address_list为待请求的地址列表'''
        if not isinstance(address_list, list):
            address_list = [address_list]
        
        address_index_geocode_map = {}  #参数地址列表中每个地址的下标与请求获得的坐标信息的映射表
        #高德地图支持批量请求，最多支持10个
        start_index = 0
        interval = 10
        error_info = ''
        while start_index < len(address_list):
            request_address_list = address_list[start_index: start_index + interval]
            start_index += interval
            print request_address_list
            #拼接请求数据
            req_address = '|'.join(map(lambda x: x.replace('|', ''), request_address_list))
            amap = AMAP(key=key, secret=secret)
            rsp, error_msg = amap(api_address, api_router, http_method=http_method, \
                                  batch='true', address=req_address)
            if error_msg:
                error_info += '[%s~%s]%s\n' %(start_index - interval + 1, start_index, error_msg)
                continue
            try:
                geocode_list = rsp['geocodes']
                if len(geocode_list) != len(request_address_list):
                    error_info += '[%s~%s]返回结果与请求数据不匹配，请检查数据\n' %(start_index - interval + 1, start_index)
                    continue
                for i, geocode in enumerate(geocode_list):
                    address_index_geocode_map[start_index - interval + i] = geocode
            except Exception, e:
                print str(e)
                error_info += '[%s~%s]%s\n' %(start_index - interval + 1, start_index, str(e))
                continue
            
        print address_index_geocode_map        
        return address_index_geocode_map, error_info or None
        
    @staticmethod
    def create_a_cloud_map(key, secret, api_address, api_router='/datamanage/table/create', http_method='POST', map_name=None):
        if not map_name:
            return None, 'Check parmas please'
        amap = AMAP(key=key, secret=secret)
        rsp, error_info = amap(api_address, api_router, http_method=http_method, \
                               name=map_name)
        if error_info:
            return None, error_info
        return rsp, None
        
    @staticmethod
    def create_a_point_4_cloud_map(key, secret, api_address, api_router='/datamanage/data/create', http_method='POST', \
                                   map_id=None, name=None, location=None, address=None):
        if not (map_id and name and location):
            return None, 'Check parmas please'
        amap = AMAP(key=key, secret=secret)
        data = {}
        data['_name'] = name
        data['_location'] = location
        if address:
            data['_address'] = address
        data = json.dumps(data)
        rsp, error_info = amap(api_address, api_router, http_method=http_method, \
                               tableid=map_id, loctype='1', data=data)
        if error_info:
            return None, error_info
        return rsp, None
    
    @staticmethod
    def update_a_point_4_cloud_map(key, secret, api_address, api_router='/datamanage/data/update', http_method='POST', \
                                   map_id=None, point_id=None, name=None, location=None, address=None):
        if not (map_id and point_id and name and location):
            return None, 'Check parmas please'
        amap = AMAP(key=key, secret=secret)
        data = {}
        data['_id'] = point_id
        data['_name'] = name
        data['_location'] = location
        if address:
            data['_address'] = address
        data = json.dumps(data)
        rsp, error_info = amap(api_address, api_router, http_method=http_method, \
                               tableid=map_id, loctype='1', data=data)
        if error_info:
            return None, error_info
        return rsp, None
    
    @staticmethod
    def yuntu_search_around(key, secret, api_address, api_router='/datasearch/around? parameters', http_method='POST', \
                            map_id=None, center_location=None, radius=None):
        if not (map_id and center_location and radius):
            return None, 'Check parmas please'
        amap = AMAP(key=key, secret=secret)
        rsp, error_info = amap(api_address, api_router, http_method=http_method, \
                               tableid=map_id, center=center_location, radius=radius)
        if error_info:
            return None, error_info
        return rsp, None
    
    
    
