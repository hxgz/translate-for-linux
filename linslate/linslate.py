#!/usr/bin/python
#coding: utf-8
#author : ning
#date   : 2013-03-08 21:16:14

import os
import re
import time
import fcntl
import logging

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import webkit
import linconf
import trans_engine

#logging.basicConfig(filename=LOG_PATH, level=logging.DEBUG)
class WebView(webkit.WebView):
    def __init__(self):
        webkit.WebView.__init__(self)
        settings = self.get_settings()
        settings.set_property('enable-universal-access-from-file-uris', True)
        settings.set_property('enable-file-access-from-file-uris', True)
        settings.set_property('default-encoding',"utf-8")
        #settings.set_property('auto-resize-window', True)
        self.set_size_request(300,150)
        self.connect("navigation-policy-decision-requested",self._on_open_link)
        self.show()
    def _on_open_link(self,view,frame,request,nav_action,decision):
        uri = request.get_uri()
        if (uri.startswith("http://")
            or uri.startswith("https://")):
            decision.ignore()
            import webbrowser
            webbrowser.open(uri)
            return True
    
class EventBox(gtk.EventBox):
    def __init__(self):
        gtk.EventBox.__init__(self)
        self.mouse_in = False
        self.select_handler_id=self.connect("selection_received", self._on_selection_received)
        self.connect('enter-notify-event', self._on_mouse_enter)
        self.connect('leave-notify-event', self._on_mouse_leave)
        self.show()
        self.view=WebView()

        self.add(self.view)
        self.popuptime=0
        self.last_selection=''
    def _on_selection_received(self, widget, selection_data, data):
        if str(selection_data.type) == "STRING":
            text = selection_data.data
            if not text:
                return False
            #text = text.decode('raw-unicode-escape')
            if not text or self.last_selection == text:
                return False
            self.last_selection = text
            m = re.search(r'[a-zA-Z-]+', text.encode('utf8')) 
            if not m:
                return False

            word = m.group(0).lower()
            x, y, mods = self.get_screen().get_root_window().get_pointer()
            #超出边界时,
            if x+self.size_request()[0]+15>self.get_screen().get_width():
                x=self.get_screen().get_width()-self.size_request()[0]-15
            if y+self.size_request()[1]+10>self.get_screen().get_height():
                y=self.get_screen().get_height()-self.size_request()[1]-10
            self.get_toplevel().move(x+15, y+10)
            self.get_toplevel().show()

            self.query_text(text)
        return False
    def query_text(self, text):
        import urllib
        text_urlencode=urllib.quote_plus(text)
        translation = ""
        if linconf.translate_engine == "google":
            trans_engine.google().query(text)
        elif linconf.translate_engine == "baidu":
            trans_engine.baidu().query(text)
        else:
            trans_engine.youdao().query(text)
        self.view.open("file://%s" % linconf.result_html)
        #self.view.load_string(html,"text/html","utf-8","")
        self.view.reload()
        self.popuptime = time.time()

    def does_block_event(self,isblock=False):
        if isblock:
            self.handler_block(self.select_handler_id)
        else:
            self.handler_unblock(self.select_handler_id)
    def _on_mouse_enter(self, widget,event):
        if not self.mouse_in:
            self.does_block_event(True)
        self.mouse_in = True
            
    def _on_mouse_leave(self,widget,event):
        #为了能在webview右键不出现windows hide的情况
        if not 0<widget.get_pointer()[0] <self.size_request()[0] \
           or not 0<widget.get_pointer()[1] <self.size_request()[1]:
            self.get_toplevel().hide()
            self.does_block_event(False)
            self.mouse_in = False
class Window(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self,gtk.WINDOW_POPUP)
        self.set_title("translation for linux")
        #self.set_border_width(3)
        self.connect("destroy", lambda w: gtk.main_quit())
        #self.resize(360, 200)
        #self.set_resizable(True)
        vbox = gtk.VBox(False, 0)
        vbox.show()

        self.eventbox=EventBox()
        gobject.timeout_add(500, self._on_timer, self.eventbox)

        self.add(vbox)
        self.show_all()
        vbox.pack_start(self.eventbox)
        self.hide()
        
    def _on_timer(self, widget):
        '''
        1. Requests the contents of a selection. (will trigger `selection_received`)
        2. hide window if necessary
        '''
        widget.selection_convert("PRIMARY", "STRING")
        if self.get_property('visible') and not self.eventbox.mouse_in:
            x, y = self.get_position()
            px, py, mods = self.get_screen().get_root_window().get_pointer()
            if (px-x)*(px-x) + (py-y)*(py-y) > 22500:  # distance > 20 in x, 20 in y
                self.hide();
            if(time.time() - self.eventbox.popuptime > 3):   # popup for some seconds
                self.hide();
        return True

    def load(self, url):
        self.output.load_uri(url)
    def reload(self):
        self.output.reload()
    def settitle(self,title):
        self.set_title(title)

class Dict:
    def __init__(self):
        self.window = Window()
    def does_block_event(self,isblock):
        self.window.eventbox.does_block_event(isblock)
class DictStatusIcon:
    def __init__(self,dict):
        self.dict=dict
        self.statusicon = gtk.StatusIcon()
        self.statusicon.set_from_file(linconf.LOGO)
        self.statusicon.connect("popup-menu", self.right_click_event)
        #self.statusicon.connect("activate", self.right_click_event)
        self.statusicon.set_tooltip("translate")
        self.does_trans=True
        # 这里可以放一个配置界面
        #window = gtk.Window()
        #window.connect("destroy", lambda w: gtk.main_quit())
        #window.show_all()
        self.menu = gtk.Menu()

        itemlist = [(u'About', self.show_about_dialog),
                    (u'Quit', gtk.main_quit)]

        self.EnableTransMenu = gtk.CheckMenuItem("划句")
        self.EnableTransMenu.set_active(self.does_trans)
        self.EnableTransMenu.connect('toggled', self.trans_or_not_menu_view)
        self.menu.append(self.EnableTransMenu)


        engine_menu=gtk.Menu()
        google_item=gtk.RadioMenuItem(None,"google")
        youdao_item=gtk.RadioMenuItem(google_item,"有道")
        baidu_item=gtk.RadioMenuItem(google_item,"百度")
        google_item.connect('activate', self._engine_select,"google")
        youdao_item.connect('activate', self._engine_select,"youdao")
        baidu_item.connect('activate', self._engine_select,"baidu")
        youdao_item.set_active(linconf.translate_engine=="youdao")
        google_item.set_active(linconf.translate_engine=="google")
        baidu_item.set_active(linconf.translate_engine=="baidu")

        engine_menu.add(google_item)
        engine_menu.add(youdao_item)
        engine_menu.add(baidu_item)        
        
        engine_menu_item = gtk.MenuItem("搜索引擎")        
        engine_menu_item.set_submenu(engine_menu)
        self.menu.add(engine_menu_item)

        for text, callback in itemlist:
            item = gtk.MenuItem(text)
            item.connect('activate', callback)
            item.show()
            self.menu.append(item)

        self.menu.show_all()
    def right_click_event(self, icon, button, time):
        self.menu.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusicon)
    def _engine_select(self,mrmi,data):
        if mrmi.active:
            linconf.translate_engine=data
    def show_about_dialog(self, widget):
        about_dialog = gtk.AboutDialog()

        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name("translation for linux")
        about_dialog.set_version(linconf.VERSION)
        about_dialog.set_authors(["OOO"])

        about_dialog.run()
        about_dialog.destroy()
    def trans_or_not_menu_view(self, widget):
        self.does_trans=widget.active
        self.dict.does_block_event(not self.does_trans)
def main():
    dict=Dict()
    dsi=DictStatusIcon(dict)
    gtk.main()

if __name__ == "__main__":
    f=open(linconf.LOCK_PATH, 'w')
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB)
    except:
        print 'a process is already running!!!'
        exit(0)

    main()

