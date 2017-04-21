# -*- coding: utf-8 -*-
'''
Created on 2016-03-20

@author: HuangLi
'''

import time
import hashlib
import requests
import urllib

class AMAP(object):
    def __init__(self, key=None, secret=None):
        self.key = key
        self.secret = secret
    
    def _getTimestamp(self):
        return int(time.time())
    
    def _sign(self, secret, params):
        keys = params.keys()
        keys.sort(lambda str1, str2: cmp(str1.lower(), str2.lower()))
        params = "%s%s" % (('').join('%s%s' % (key, params[key]) for key in keys), secret)
        sign = hashlib.md5(params).hexdigest().upper()
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

    def execute(self, api_address, api_name, router=None, http_method='POST', **kwargs):
        params = {}
        #解析api应用级参数
        for k, v in kwargs.iteritems():
            if v: params[k] = v
        #拼接系统级参数
        params['key'] = self.key
        params['sig'] = self._sign(self.secret, params)
        #提交请求
        url = '%s%s/%s' %(api_address, router or '', api_name)
        headers = {}
        print url
        rsp, error_info = self._get_resp(url, params, headers=headers, http_method=http_method)
        print rsp
        print error_info
        #解析请求是否成功
        return self.parse_resp_error(rsp, error_info)

    def __call__(self, api_address, api_name, router=None, http_method=None, **kwargs):
        return self.execute(api_address, api_name, router=router, http_method=http_method, **kwargs)
    
    def parse_resp_error(self, rsp, error_info):
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


