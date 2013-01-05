#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.constant import ALIGN_MIDDLE
import traceback
import sys
from dtk.ui.utils import color_hex_to_cairo, container_remove_all, get_parent_dir, get_resize_pixbuf_with_height, format_file_size, run_command, read_file, write_file, remove_file
import zipfile
from dtk.ui.label import Label
from dtk.ui.draw import draw_pixbuf, draw_text
from dtk.ui.star_view import StarBuffer
from resizable_label import ResizableLabel
from slide_switcher import SlideSwitcher
from dtk.ui.button import Button
from constant import SCREENSHOT_HOST, SCREENSHOT_DOWNLOAD_DIR
import threading
import gobject
import gtk
from item_render import get_icon_pixbuf_path
import os
from deepin_storm.download import FetchServiceThread, join_glib_loop, FetchFiles
from events import global_event
import urllib2

join_glib_loop()

PKG_SCREENSHOT_DIR = os.path.join(get_parent_dir(__file__, 2), "data", "update_data", "pkg_screenshot", "zh_CN")

class DetailPage(gtk.HBox):
    '''
    class docs
    '''
    
    PADDING_Y = 20	
    
    ICON_SIZE = 64
    ICON_PADDING_X = 50
    
    STAR_PADDING_X = 30
    STAR_PADDING_Y = 10
    STAR_SIZE = 13

    MARK_NUMBER_SIZE = 11
    MARK_NUMBER_PADDING_X = 4
    MARK_NUMBER_PADDING_Y = 10
    
    INFO_RENDER_X = 10
    INFO_RENDER_Y = 140
    INFO_RENDER_HEIGHT = 18
    INFO_CATEGORY_RENDER_Y = INFO_RENDER_Y + INFO_RENDER_HEIGHT
    INFO_VERSION_RENDER_Y = INFO_RENDER_Y + INFO_RENDER_HEIGHT * 2
    INFO_SIZE_RENDER_Y = INFO_RENDER_Y + INFO_RENDER_HEIGHT * 3
    INFO_DOWNLOAD_RENDER_Y = INFO_RENDER_Y + INFO_RENDER_HEIGHT * 4
    INFO_HOMEPAGE_RENDER_Y = INFO_RENDER_Y + INFO_RENDER_HEIGHT * 5
    
    LEFT_INFO_PADDING_X = 18
    LEFT_INFO_PADDING_Y = 50
    
    LEFT_BUTTON_PADDING_Y = 50
    
    LEFT_INFO_WIDTH = 164
    
    RIGHT_INFO_PADDING_X = 30
    
    RIGHT_TITLE_BOX_HEIGHT = 70
    
    ALIAS_NAME_SIZE = 16
    ALIAS_NAME_PADDING_Y = 20
    
    LONG_DESC_PADDING_Y = 10
    LONG_DESC_WRAP_WIDTH = 630
    LONG_DESC_INIT_HEIGHT = 45
    
    def __init__(self, data_manager):
        '''
        init docs
        '''
        gtk.HBox.__init__(self)
        self.data_manager = data_manager
        self.pkg_name = None
        self.pkg_pixbuf = None
        
        self.left_view_box = gtk.VBox()
        self.left_view_box.set_size_request(self.LEFT_INFO_WIDTH, - 1)
        
        self.left_logo_box = gtk.VBox()
        self.left_logo_box.set_size_request(-1, 150)
        
        self.left_label_table = gtk.Table(4, 1)
        self.left_label_table.set_row_spacings(4)
        
        self.left_label_align = gtk.Alignment()
        self.left_label_align.set(0.5, 0.5, 0, 0)
        self.left_label_align.set_padding(0, 0, 6, 0)
        
        self.left_category_label = Label()
        self.left_version_label = Label()
        self.left_size_label = Label()
        self.left_download_label = Label()
        
        self.left_homepage_align = gtk.Alignment()
        self.left_homepage_align.set(0.5, 0.5, 0, 0)
        self.left_homepage_align.set_padding(10, 10, 0, 0)
        self.left_homepage_box = gtk.HBox()
        
        self.right_info_box = gtk.VBox()
        self.scrolled_window = ScrolledWindow()
        self.right_view_box = gtk.VBox()
        
        self.right_title_box = gtk.VBox()
        self.right_title_box.set_size_request(-1, self.RIGHT_TITLE_BOX_HEIGHT)
        self.right_desc_box = gtk.VBox()
        self.right_slide_box = gtk.VBox()
        self.right_comment_box = gtk.VBox()
        
        self.right_view_box.pack_start(self.right_title_box, False, False)
        self.right_view_box.pack_start(self.right_desc_box, False, False)
        self.right_view_box.pack_start(self.right_slide_box, False, False)
        self.right_view_box.pack_start(self.right_comment_box, False, False)
        self.scrolled_window.add_child(self.right_view_box)
        
        self.left_view_box.pack_start(self.left_logo_box, False, False)
        self.left_label_table.attach(self.left_category_label, 0, 1, 0, 1)
        self.left_label_table.attach(self.left_version_label, 0, 1, 1, 2)
        self.left_label_table.attach(self.left_size_label, 0, 1, 2, 3)
        self.left_label_table.attach(self.left_download_label, 0, 1, 3, 4)
        self.left_label_align.add(self.left_label_table)
        self.left_view_box.pack_start(self.left_label_align, False, False)
        self.left_homepage_align.add(self.left_homepage_box)
        self.left_view_box.pack_start(self.left_homepage_align, False, False)
        self.right_info_box.pack_start(self.scrolled_window, True, True)
        self.pack_start(self.left_view_box, False, False)
        self.pack_start(self.right_info_box, True, True)
        
        self.left_view_box.connect("expose-event", self.expose_left_view)
        self.right_view_box.connect("expose-event", self.expose_right_view)
        self.left_logo_box.connect("expose-event", self.expose_left_logo_box)
        self.right_title_box.connect("expose-event", self.expose_right_title_box)
        
        self.download_screenshot = DownloadScreenshot()

        global_event.register_event("download-screenshot-finish", self.download_screenshot_finish)
        
    def expose_left_view(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw background.
        cr.set_source_rgb(*color_hex_to_cairo("#FFFFFF"))
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()
        
        # Draw split line.
        cr.set_source_rgb(*color_hex_to_cairo("#AAAAAA"))
        cr.rectangle(rect.x + rect.width - 1, rect.y, 1, rect.height)
        cr.fill()
        
    def expose_right_view(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw background.
        cr.set_source_rgb(*color_hex_to_cairo("#FFFFFF"))
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()
            
    def expose_left_logo_box(self, widget, event):
        if self.pkg_name != None:
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation
            
            # Draw pkg icon.
            self.pkg_pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(get_icon_pixbuf_path(self.pkg_name), self.ICON_SIZE, self.ICON_SIZE)
            draw_pixbuf(cr,
                        self.pkg_pixbuf,
                        rect.x + self.ICON_PADDING_X,
                        rect.y + self.PADDING_Y)
            
            # Draw star.
            self.star_buffer.render(
                cr, 
                gtk.gdk.Rectangle(rect.x + self.STAR_PADDING_X, 
                                  rect.y + self.PADDING_Y + self.ICON_SIZE + self.STAR_PADDING_Y,
                                  self.STAR_SIZE * 5,
                                  self.STAR_SIZE))
            
            # Draw mark number.
            draw_text(
                cr, 
                "<b>%s</b>" % str(self.star),
                rect.x + self.STAR_PADDING_X + self.STAR_SIZE * 5 + self.MARK_NUMBER_PADDING_X,
                rect.y + self.PADDING_Y + self.ICON_SIZE + self.MARK_NUMBER_PADDING_Y,
                rect.width - (self.STAR_PADDING_X + self.STAR_SIZE * 5 + self.MARK_NUMBER_PADDING_X),
                self.MARK_NUMBER_SIZE,
                text_size=self.MARK_NUMBER_SIZE,
                text_color="#F07200"
                )
            
    def expose_right_title_box(self, widget, event):
        if self.pkg_name != None:
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation
            
            # Draw background.
            cr.set_source_rgb(*color_hex_to_cairo("#FFFFFF"))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
            
            # Draw alias name.
            draw_text(
                cr,
                "<b>%s</b>" % self.alias_name,
                rect.x + self.RIGHT_INFO_PADDING_X,
                rect.y + self.ALIAS_NAME_PADDING_Y,
                rect.width - self.RIGHT_INFO_PADDING_X,
                self.ALIAS_NAME_SIZE,
                text_size=self.ALIAS_NAME_SIZE)
            
    def expose_resizable_label_background(self, widget, event):
        if self.pkg_name != None:
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation
            
            # Draw background.
            cr.set_source_rgb(*color_hex_to_cairo("#FFFFFF"))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
            
    def update_pkg_info(self, pkg_name):
        self.pkg_name = pkg_name
        (self.category, self.long_desc, 
         self.version, self.homepage, 
         self.size, self.star, 
         self.download, self.alias_name,
         self.have_screenshot) = self.data_manager.get_pkg_detail_info(self.pkg_name)
        self.star_buffer = StarBuffer(self.star)
        
        if self.category == None:
            self.category = ("", "")
        self.left_category_label.set_text("类别：%s %s" % self.category)
        self.left_version_label.set_text("版本：%s" % self.version)
        self.left_size_label.set_text("大小：%s" % format_file_size(self.size))
        self.left_download_label.set_text("下载：%s" % self.download)
        
        container_remove_all(self.left_homepage_box)
        if self.homepage != "":
            homepage_button = Button("访问首页")
            homepage_button.connect("clicked", lambda w: run_command("xdg-open %s" % self.homepage))
            self.left_homepage_box.pack_start(homepage_button)
        
        container_remove_all(self.right_desc_box)
        resizable_label = ResizableLabel(self.long_desc, self.LONG_DESC_WRAP_WIDTH, self.LONG_DESC_INIT_HEIGHT, 3)
        resizable_align = gtk.Alignment()
        resizable_align.set(0.5, 0.5, 1, 1)
        resizable_align.set_padding(0, 0, self.RIGHT_INFO_PADDING_X, self.RIGHT_INFO_PADDING_X)
        resizable_align.add(resizable_label)
        resizable_align.connect("expose-event", self.expose_resizable_label_background)
        self.right_desc_box.pack_start(resizable_align, False, False)
        
        self.show_screenshot()
        
        if eval(self.have_screenshot):
            thread = threading.Thread(target=self.fetch_screenshot)
            thread.setDaemon(True)
            thread.start()
        
        self.queue_draw()
        
        self.show_all()
        
    def fetch_screenshot(self):
        screenshot_dir = os.path.join(SCREENSHOT_DOWNLOAD_DIR, self.pkg_name)
        screenshot_md5_path = os.path.join(screenshot_dir, "screenshot_md5.txt")
        remote_screenshot_md5_url = "%s/zh_CN/%s/screenshot_md5.txt" % (SCREENSHOT_HOST, self.pkg_name)
        remote_screenshot_zip_url = "%s/zh_CN/%s/screenshot.zip" % (SCREENSHOT_HOST, self.pkg_name)
        try:
            remote_md5 = urllib2.urlopen(remote_screenshot_md5_url).read()
            need_download = False
            
            if os.path.exists(screenshot_dir):
                if os.path.exists(screenshot_md5_path):
                    local_md5 = read_file(screenshot_md5_path)
                    if remote_md5 != local_md5:
                        need_download = True
                else:
                    need_download = True
            else:
                need_download = True
                
            if need_download:    
                write_file(screenshot_md5_path, remote_md5, True)
                self.download_screenshot.add_download(self.pkg_name, remote_screenshot_zip_url)
        except Exception, e:
            traceback.print_exc(file=sys.stdout)
            print "fetch_screenshot got error: %s" % e
            
    def download_screenshot_finish(self, pkg_name):
        if self.pkg_name == pkg_name:
            screenshot_dir = os.path.join(SCREENSHOT_DOWNLOAD_DIR, pkg_name)
            screenshot_zip_path = os.path.join(screenshot_dir, "screenshot.zip")
            if os.path.exists(screenshot_zip_path):
                # Remove unused files first.
                for screenshot_file in os.listdir(screenshot_dir):
                    if screenshot_file not in ["screenshot_md5.txt", "screenshot.zip"]:
                        remove_file(os.path.join(screenshot_dir, screenshot_file))
                
                # Extract zip file.
                zip_file = zipfile.ZipFile(screenshot_zip_path)
                for extract_file in zip_file.namelist():
                    with open(os.path.join(screenshot_dir, os.path.split(extract_file)[1]), "wb") as screenshot_file:
                        screenshot_file.write(zip_file.read(extract_file))
                zip_file.close()
                
                # Remove zip file.
                remove_file(screenshot_zip_path)
                
                # Add screenshots.
                self.show_screenshot()
                    
    def show_screenshot(self):
        container_remove_all(self.right_slide_box)
        screenshot_dir = os.path.join(SCREENSHOT_DOWNLOAD_DIR, self.pkg_name)
        
        if os.path.exists(screenshot_dir):
            screenshot_files = map(lambda filename: os.path.join(screenshot_dir, filename),
                                   filter(lambda file_name: file_name.endswith(".png"), os.listdir(screenshot_dir)))
                    
            if len(screenshot_files) > 0:
                slide_switcher = SlideSwitcher(
                    map(lambda screenshot_file: get_resize_pixbuf_with_height(screenshot_file, 300), screenshot_files),
                    pointer_offset_x=-370,
                    pointer_offset_y=-15,
                        horizontal_align=ALIGN_MIDDLE,
                        vertical_align=ALIGN_MIDDLE,
                        height_offset=60,
                        hover_switch=False,
                        auto_switch=False,
                        )
                slide_align = gtk.Alignment()
                slide_align.set(0.5, 0.5, 1, 1)
                slide_align.add(slide_switcher)
                slide_align.connect("expose-event", self.expose_resizable_label_background)
                self.right_slide_box.pack_start(slide_align, True, True)
                    
                self.show_all()
            else:
                print "%s haven't any screenshot from zip file" % self.pkg_name
        
gobject.type_register(DetailPage)        

class DownloadScreenshot(object):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        self.fetch_service_thread = FetchServiceThread(5)
        self.fetch_service_thread.start()
        
        join_glib_loop()
        
        self.fetch_files_dict = {}
        
    def add_download(self, pkg_name, url):
        download_dir = os.path.join(SCREENSHOT_DOWNLOAD_DIR, pkg_name)
        fetch_files = FetchFiles(
            [url],
            file_save_dir=download_dir,
            )
        fetch_files.signal.register_event(
            "start", 
            lambda : global_event.emit("download-screenshot-start", pkg_name))
        fetch_files.signal.register_event(
            "update",
            lambda percent, speed: global_event.emit("download-screenshot-update", pkg_name, percent, speed))
        fetch_files.signal.register_event(
            "finish", 
            lambda : global_event.emit("download-screenshot-finish", pkg_name))
        fetch_files.signal.register_event(
            "pause",
            lambda : global_event.emit("download-screenshot-pause", pkg_name))
        fetch_files.signal.register_event(
            "stop",
            lambda : global_event.emit("download-screenshot-stop", pkg_name))
        
        self.fetch_files_dict[pkg_name] = fetch_files
        self.fetch_service_thread.fetch_service.add_fetch(fetch_files)
        
    def stop_download(self, pkg_name):
        if self.fetch_files_dict.has_key(pkg_name):
            self.fetch_service_thread.fetch_service.pause_fetch(self.fetch_files_dict[pkg_name])
            self.fetch_files_dict.pop(pkg_name)
