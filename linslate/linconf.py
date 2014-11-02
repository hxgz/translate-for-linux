#encoding=utf-8
import os
VERSION = "0.1.0"
PWD = os.path.dirname(os.path.realpath(__file__))
LOGO = PWD + '/linslate.png'
LOG_PATH = '/tmp/linslate.log'
LOCK_PATH = '/tmp/.lslock'
result_dir=PWD+'/local/'
#main
template_html=result_dir+'result'
result_html=result_dir+'result.html'
translate_engine="google"
##youdao engine
#翻译的图标,显示title
yd_logo=result_dir+"/youdao.png"
yd_title="有道翻译"
##google engine
google_logo=result_dir+"/google.png"
google_title="Google翻译"
http_proxy='127.0.0.1:8087'
## engine
