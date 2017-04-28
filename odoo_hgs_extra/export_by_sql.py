# -*- coding: utf-8 -*-

import openerp
from openerp import api
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv,orm
import datetime, time
import logging
import pandas
import psycopg2
from pandas.io.excel import ExcelWriter
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import re

_logger = logging.getLogger(__name__)



mail_host = "smtp.exmail.qq.com"
mail_user = 'erp000@huaguoshan.com'
mail_pwd = "HuaGuoShan2017"
mail_postfix = "huaguoshan.com" 

DATABASE_NAME = 'wms20160109'
DATABASE_USER = 'postgres'
DATABASE_PWD = 'admin!@#$%^&*'
DATABASE_HOST = '114.55.93.1'
DATABASE_PORT = '5432'

    
class export_by_sql(osv.osv):
    _name = "export_by_sql"
    
    _columns = {
        'name': fields.char(u'查询名称', size=64, help=u'查询名称将作为邮件的主题，请谨慎填写，简洁易懂'),
        'state': fields.selection([('draft', u'查询草稿'), ('executed', u'查询已执行'), ('email_sent', u'邮件已发送')], u'执行状态'),
        'sql_string': fields.text(u'SQL查询语句', \
                                  states = {'executed': [('readonly', True)], 'email_sent': [('readonly', True)]}),
        'saved_file': fields.binary(u'结果文件', filters='*.xls', help=u'查询结果文件'),
        'email_to': fields.text(u'接收邮箱', help=u'查询结果将excel文件作为附件发送给此列表中的邮箱，多个邮箱用英文逗号“,”分隔'),
        'file_save_path': fields.char(u'文件保存路径', help=u'给出文件保存在服务器中的地址及文件名（中文字符会导致邮件发送时出错）', \
                                      states = {'executed': [('readonly', True)], 'email_sent': [('readonly', True)]}),
    }
    
    _defaults = {
         'state': 'draft',
    }
    
    def execute_sql_2_export(self, cr, uid, ids, context=None):
        
        condition = self.browse(cr, uid, ids)[0]
        sql_string = condition.sql_string
        file_save_path = condition.file_save_path
        if file_save_path[-4:] != '.xls':
            raise osv.except_orm('提示！', '文件保存地址不合法，请以“.xls”结尾')
        connection = psycopg2.connect(database=DATABASE_NAME, user=DATABASE_USER, password=DATABASE_PWD, host=DATABASE_HOST, port=DATABASE_PORT)
        try:
            df = pandas.read_sql(sql_string, connection)
        except Exception, e:
            raise osv.except_orm('查询失败，请检查SQL语句', '')
        try:
            with ExcelWriter(file_save_path) as writer:
                df.to_excel(writer, sheet_name=u'Sheet1')
            condition.write({'state': 'executed'})
        except Exception, e:
            raise osv.except_orm('保存文件出错，请检查地址是否合法', str(e))
        finally:
            connection.close()
        
    def send_email_with_file(self, cr, uid, ids, context=None):
        condition = self.browse(cr, uid, ids)[0]
        subject = condition.name
        email_to = condition.email_to
        file_path = condition.file_save_path
        
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = mail_user
        msg['To'] = email_to
        
        xls_part = MIMEApplication(open(file_path, 'rb').read())
        xls_part.add_header('Content-Disposition', 'attachment', filename=file_path.split('/')[-1])
        msg.attach(xls_part)
        
        try:
            client = smtplib.SMTP()
            client.connect(mail_host)
            client.login(mail_user, mail_pwd)
            client.sendmail(mail_user, email_to, msg.as_string())
            client.quit()
            condition.write({'state': 'email_sent'})
        except smtplib.SMTPRecipientsRefused, e:
            raise osv.except_orm('Recipient refused', str(e))
        except smtplib.SMTPAuthenticationError, e:
            raise osv.except_orm('Auth error', str(e))
        except smtplib.SMTPSenderRefused, e:
            raise osv.except_orm('Sender refused', str(e))
        except smtplib.SMTPException, e:
            raise osv.except_orm('', str(e))
        
        
        
        
        
        
        
    
    