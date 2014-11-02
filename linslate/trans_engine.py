#!/usr/bin/env python
#coding: utf-8
#author : ning
#date   : 2013-03-08 21:06:42

import urllib, urllib2
import os, sys
import re, time
import logging
import tempfile
import commands
import json
import subprocess
import linconf 
def json_encode(j):
    return json.dumps(j, indent=4,ensure_ascii=False)
def json_decode(str):
    return json.loads(str)

def system(cmd, log=True):
    subprocess.Popen(cmd, shell=True)

class youdao():
    def query_word(self,word):
        url = 'http://fanyi.youdao.com/openapi.do?keyfrom=tinxing&key=1312427901&type=data&doctype=json&version=1.1&q=' + word
        data = urllib2.urlopen(url).read()
        print json_encode(json_decode(data))
        return json_decode(data)
    def query(self,text):
        engine_title=linconf.yd_title
        engine_icon=linconf.yd_logo
        text_urlencode=urllib.quote(text)
        translation=self.query_sentence(text)
        external_url="http://fanyi.youdao.com/translate?i=%s&keyfrom=dict.top" % text_urlencode
        #获取模版
        ori_html=open(linconf.template_html,'r')
        content=''.join(ori_html.readlines())
        ori_html.close()
        #写入翻译结果到文件中
        result_html=open(linconf.result_html,'w')
        result_html.write(content % locals())
        result_html.close()
    def query_sentence(self,text):
       post_data = urllib.urlencode({'type' : 'auto',
                               'doctype':'json',
                                     'i'  :text})
       url = "http://fanyi.youdao.com/translate"
       data = urllib2.urlopen(url,data=post_data).read()
       json_data = json_decode(data)
       result=set()
       for x in json_data["translateResult"]:
           for y in x:
               result.add(y['tgt'])
       return "".join(result)
    
    def pronounce(self,word):
        url = 'http://dict.youdao.com/dictvoice?audio=%s' % word
        cmd = 'nohup mplayer "%s" >/dev/null 2>&1 ' % (url,)
        system(cmd)
class google():
    def query(self,text):
        engine_title=linconf.google_title
        engine_icon=linconf.google_logo
        text_urlencode=urllib.quote(text)
        translation=self.query_sentence(text)
        external_url="https://translate.google.com/#auto/zh-CN/%s" % text_urlencode
        #获取模版
        ori_html=open(linconf.template_html,'r')
        content=''.join(ori_html.readlines())
        ori_html.close()
        #写入翻译结果到文件中
        result_html=open(linconf.result_html,'w')
        result_html.write(content % locals())
        result_html.close()
    def query_sentence(self,text):
        GOOGLE_TRASLATE_URL = 'https://translate.google.com/translate_a/t'
        GOOGLE_TRASLATE_PARAMETERS = {
            'client': 'z',
            'sl': 'auto',
            'tl': 'zh-CN',
            'ie': 'UTF-8',
            'oe': 'UTF-8',
            'text': text
            }

        url = '?'.join((GOOGLE_TRASLATE_URL, urllib.urlencode(GOOGLE_TRASLATE_PARAMETERS)))
        request = urllib2.Request(url, headers={'User-Agent':'Mozilla/4.0'})
        if linconf.http_proxy:
            request.set_proxy(linconf.http_proxy,'http')
        _opener = urllib2.build_opener()
        try:
            response = _opener.open(request, timeout=4)
            content = response.read().decode('utf-8')
        except Exception as err:
            return "翻译出错:<br>   %s" % str(err).strip('<>')
        json_data = json_decode(content)
        return "".join([x['trans'] for x in json_data['sentences'] ])
class baidu():
    def query(self,text):
        engine_title=linconf.baidu_title
        engine_icon=linconf.baidu_logo
        text_urlencode=urllib.quote(text)
        translation=self.query_sentence(text)
        external_url="http://fanyi.baidu.com/#en/zh/%s" % text_urlencode
        #获取模版
        ori_html=open(linconf.template_html,'r')
        content=''.join(ori_html.readlines())
        ori_html.close()
        #写入翻译结果到文件中
        result_html=open(linconf.result_html,'w')
        result_html.write(content % locals())
        result_html.close()
    def query_sentence(self,text):
       post_data = urllib.urlencode({'from' : 'auto',
                                     'to':'zh',
                                     'query'  :text})
       url = "http://fanyi.baidu.com/v2transapi"
       data = urllib2.urlopen(url,data=post_data).read()
       json_data = json_decode(data)
       result=set()
       for x in json_data["trans_result"]["data"]:
           result.add(x['dst'])
       return "".join(result)
    

def main():
    print query('The result is in translation,呵呵 and its usually a unicode string.')
    #print pronounce('The result is in translation, and its usually a unicode string.')
    #pronounce('hello')
    pass

if __name__ == "__main__":
    main()
