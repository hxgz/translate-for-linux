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

import youdao_trans

VERSION = "0.1.0"
PWD = os.path.dirname(os.path.realpath(__file__))
LOGO = PWD + '/icon.png'

HOME = os.getenv("HOME") + '/.youdao-dict/'
LOG_PATH = '/tmp/dict.log'
LOCK_PATH = '/tmp/.lock'

logging.basicConfig(filename=LOG_PATH, level=logging.DEBUG)

class Dict:
    def __init__(self):
        self.mouse_in = False
        self.popuptime = 0

        self.window = None
        self.view = None
        self.last_selection=''
        self.init_widgets()

    def does_block_event(self,isblock=False):
        if isblock:
            self.eventbox.handler_block(self.sel_handler_id)
        else:
            self.eventbox.handler_unblock(self.sel_handler_id)
    def init_widgets(self):
        '''
        window->vbox->eventbox->view
        '''
        self.window = gtk.Window(gtk.WINDOW_POPUP)
        self.window.set_title("translation for linux")
        self.window.set_border_width(3)
        self.window.connect("destroy", lambda w: gtk.main_quit())
        self.window.resize(360, 200)

        vbox = gtk.VBox(False, 0)
        vbox.show()

        self.eventbox = gtk.EventBox()
        self.sel_handler_id=self.eventbox.connect("selection_received", self._on_selection_received)
        self.eventbox.connect('enter-notify-event', self._on_mouse_enter)
        self.eventbox.connect('leave-notify-event', self._on_mouse_leave)
        gobject.timeout_add(500, self._on_timer, self.eventbox)
        self.eventbox.show()
        self.view = webkit.WebView()
        def title_changed(widget, frame, title):
            logging.debug('title_changed to %s, will open webbrowser ' % title)
            import webbrowser
            webbrowser.open('http://fanyi.youdao.com/translate?i=%s&keyfrom=dict.top' % title )
        self.view.connect('title-changed', title_changed)
        self.view.show()

        #add one by one
        self.window.add(vbox)
        vbox.pack_start(self.eventbox) # means add
        self.eventbox.add(self.view)

    def _on_timer(self, widget):
        '''
        1. Requests the contents of a selection. (will trigger `selection_received`)
        2. hide window if necessary
        '''

        widget.selection_convert("PRIMARY", "STRING")

        #if pop_up_show && distance (xxx):
            #hide;
        if self.window.get_property('visible') and not self.mouse_in:
            x, y = self.window.get_position()
            px, py, mods = self.window.get_screen().get_root_window().get_pointer()
            if (px-x)*(px-x) + (py-y)*(py-y) > 400:  # distance > 20 in x, 20 in y
                logging.debug('distance big enough, hide window')
                self.window.hide();
            if(time.time() - self.popuptime > 3):   # popup for some seconds
                logging.debug('time long enough, hide window')
                self.window.hide();
        return True

    def _on_selection_received(self, widget, selection_data, data):
        if str(selection_data.type) == "STRING":
            text = selection_data.get_text()
            if not text:
                return False
            text = text.decode('raw-unicode-escape')
            if not text or self.last_selection == text:
                return False
            self.last_selection = text
            m = re.search(r'[a-zA-Z-]+', text.encode('utf8')) # the selection mostly be: "widget,", "&window" ...
            if not m:
                logging.info("Query nothing")
                return False

            word = m.group(0).lower()

            logging.info('QueryWord: ' + word)
            self.query_text(text.encode("utf-8"))

        return False

    def query_text(self, text):
        translation = youdao_trans.query_sentence(text)
        #youdao_client.pronounce(word)
        x, y, mods = self.window.get_screen().get_root_window().get_pointer()
        self.window.move(x+15, y+10)
        self.window.present()
        html = '''
        <style>
        .add_to_wordbook {
        background: url('http://shared.ydstatic.com/r/2.0/p/fanyi-logo-s.png') no-repeat;
        background-size: 120px 24px;
        display: inline-block;
        vertical-align: top;
        width: 50px;
        padding-top: 26px;
        margin-left: .5em;
        }
        </style>

        <h3 style="margin:0em;color:#AAC0C0;">有道翻译
        <a href="javascript:void(0);" id="wordbook" class="add_to_wordbook" title="浏览器中打开" onclick="document.title='%(text)s'">
        </a>
        </h3>
        %(translation)s
        ''' % locals()
        self.view.load_string(html,"text/html","utf-8","")
        self.view.reload()
        self.popuptime = time.time()

    def ignore(self, word):
        if len(word)<=3:
            return True
        return False

    def _on_mouse_enter(self, wid, event):
        logging.debug('_on_mouse_enter')
        self.mouse_in = True
        self.does_block_event(True)

    def _on_mouse_leave(self, *args):
        logging.debug('_on_mouse_leave')
        self.mouse_in = False
        self.window.hide()
        self.does_block_event(False)

class DictStatusIcon:
    def __init__(self,dict):
        self.dict=dict
        self.statusicon = gtk.StatusIcon()
        self.statusicon.set_from_file(LOGO)
        self.statusicon.connect("popup-menu", self.right_click_event)
        #self.statusicon.connect("activate", self.right_click_event)
        self.statusicon.set_tooltip("translate")
        self.does_trans=True
        # 这里可以放一个配置界面
        #window = gtk.Window()
        #window.connect("destroy", lambda w: gtk.main_quit())
        #window.show_all()

    def right_click_event(self, icon, button, time):
        self.menu = gtk.Menu()

        itemlist = [(u'About', self.show_about_dialog),
                    (u'Quit', gtk.main_quit)]
        a=gtk
        self.EnableTransMenu = gtk.CheckMenuItem("划词")
        self.EnableTransMenu.set_active(self.does_trans)
        self.EnableTransMenu.connect('toggled', self.trans_or_not_menu_view)
        self.menu.append(self.EnableTransMenu)
        # radio = gtk.RadioMenuItem(None, "Radio Menu Item")
        # radio.set_active(True)
        # radio.show()
        # self.menu.append(radio)
        for text, callback in itemlist:
            item = gtk.MenuItem(text)
            item.connect('activate', callback)
            item.show()
            self.menu.append(item)

        self.menu.show_all()
        self.menu.popup(None, None, gtk.status_icon_position_menu, button, time, self.statusicon)

    def show_about_dialog(self, widget):
        about_dialog = gtk.AboutDialog()

        about_dialog.set_destroy_with_parent(True)
        about_dialog.set_name("translation for linux")
        about_dialog.set_version(VERSION)
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
    f=open(LOCK_PATH, 'w')
    try:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB)
    except:
        print 'a process is already running!!!'
        exit(0)

    main()

