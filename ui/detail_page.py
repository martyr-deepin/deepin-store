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

import urllib
import traceback
import sys
import pango
from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.constant import ALIGN_MIDDLE
from deepin_utils.net import is_network_connected
from dtk.ui.button import ImageButton
from dtk.ui.star_view import StarView
from dtk.ui.browser import WebView
from constant import CONFIG_DIR, SERVER_ADDRESS
from skin import app_theme
from deepin_utils.file import get_parent_dir, read_file, write_file, remove_file
from deepin_utils.process import run_command
from dtk.ui.utils import color_hex_to_cairo, container_remove_all, get_resize_pixbuf_with_height
import zipfile
from dtk.ui.label import Label
from dtk.ui.label_utils import show_label_tooltip
from dtk.ui.draw import draw_pixbuf, draw_text
from resizable_label import ResizableLabel
from slide_switcher import SlideSwitcher
from constant import SCREENSHOT_HOST, SCREENSHOT_DOWNLOAD_DIR
from deepin_utils.multithread import create_thread
import gobject
import gtk
from item_render import get_icon_pixbuf_path
import os
from events import global_event
import urllib2
import webbrowser
from category_info import get_category_name
import time

PKG_SCREENSHOT_DIR = os.path.join(get_parent_dir(__file__, 2), "data", "update_data", "pkg_screenshot", "zh_CN")

class DetailPage(gtk.HBox):
    '''
    class docs
    '''
    
    PADDING_Y = 20	
    
    ICON_SIZE = 64
    ICON_PADDING_X = 50
    
    STAR_PADDING_X = 36
    STAR_PADDING_Y = 12
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

    MARK_SIZE = 11
    MARK_PADDING_X = 5
    MARK_PADDING_Y = -3
    
    def __init__(self, data_manager):
        '''
        init docs
        '''
        gtk.HBox.__init__(self)
        self.data_manager = data_manager
        self.pkg_name = None
        self.alias_name = ""
        self.pkg_pixbuf = None
        
        self.left_view_box = gtk.VBox()
        self.left_view_box.set_size_request(self.LEFT_INFO_WIDTH, - 1)
        
        self.left_logo_box = gtk.VBox()
        self.left_logo_box.set_size_request(-1, 90)

        self.star_box = gtk.HBox()
        self.star_align = gtk.Alignment(0.4, 0.5, 0, 0)
        self.star_align.set_padding(0, 5, 0, 0)
        self.star_align.add(self.star_box)

        self.left_action_box = gtk.HBox()
        self.left_action_align = gtk.Alignment()
        self.left_action_align.set(0.5, 0.5, 0, 0)
        self.left_action_align.set_padding(0, 30, 0, 0)
        self.left_action_align.add(self.left_action_box)
        
        self.left_label_table = gtk.Table(4, 1)
        self.left_label_table.set_row_spacings(4)
        
        self.left_label_align = gtk.Alignment()
        self.left_label_align.set(0.0, 0.5, 0, 0)
        self.left_label_align.set_padding(0, 0, 14, 0)
        
        self.left_category_name_label = Label()
        self.left_category_label = Label(hover_color=app_theme.get_color("homepage_hover"))
        self.left_category_label.set_clickable()
        self.left_category_label_align = gtk.Alignment()
        self.left_category_label_align.set(0.0, 0.5, 0, 0)
        self.left_category_label_align.add(self.left_category_label)
        self.left_category_label_box = gtk.HBox()
        self.left_category_label_box.pack_start(self.left_category_name_label, False, False)
        self.left_category_label_box.pack_start(self.left_category_label_align, True, True)
        self.left_category_box = gtk.VBox()
        self.left_version_label = Label(label_width=136)
        show_label_tooltip(self.left_version_label)
        self.left_version_label.set_ellipsize(pango.ELLIPSIZE_MIDDLE)
        self.left_download_label = Label()
        
        self.left_homepage_box = gtk.HBox()
        self.left_homepage_box_align = gtk.Alignment()
        self.left_homepage_box_align.set(0.0, 0.5, 0, 0)
        self.left_homepage_box_align.add(self.left_homepage_box)
        
        self.left_recommend_box = gtk.VBox()
        self.left_recommend_box_align = gtk.Alignment()
        self.left_recommend_box_align.set(0.0, 0.0, 0, 0)
        self.left_recommend_box_align.set_padding(30, 0, 14, 0)
        self.left_recommend_box_align.add(self.left_recommend_box)
        
        self.left_recommend_label = Label("同类热门推荐")
        
        self.right_info_box = gtk.VBox()
        self.scrolled_window = ScrolledWindow(0, 0)
        self.right_view_box = gtk.VBox()
        
        self.right_top_box = gtk.HBox()
        self.right_top_box.set_size_request(-1, self.RIGHT_TITLE_BOX_HEIGHT)
        self.right_desc_box = gtk.VBox()
        self.right_slide_box = gtk.VBox()
        self.right_comment_box = gtk.VBox()
        
        self.right_title_box = gtk.VBox()
        
        self.return_button = ImageButton(
            app_theme.get_pixbuf("detail/normal.png"),
            app_theme.get_pixbuf("detail/hover.png"),
            app_theme.get_pixbuf("detail/press.png"),
            )
        self.return_align = gtk.Alignment()
        self.return_align.set(0.5, 0.5, 1, 1)
        self.return_align.set_padding(self.ALIAS_NAME_PADDING_Y, 0, 0, self.RIGHT_INFO_PADDING_X)
        self.return_align.add(self.return_button)
        
        self.return_button.connect("clicked", lambda w: global_event.emit("switch-from-detail-page"))
        
        self.right_top_box.pack_start(self.right_title_box, True, True)
        self.right_top_box.pack_start(self.return_align, False, False)
        
        self.right_view_box.pack_start(self.right_top_box, False, False)
        self.right_view_box.pack_start(self.right_desc_box, False, False)
        self.right_view_box.pack_start(self.right_slide_box, False, False)
        self.right_view_box.pack_start(self.right_comment_box, False, False)
        self.scrolled_window.add_child(self.right_view_box)
        
        self.left_view_box.pack_start(self.left_logo_box, False, False)
        self.left_view_box.pack_start(self.star_align, False, False)
        self.left_view_box.pack_start(self.left_action_align, False, False)
        self.left_label_table.attach(self.left_category_box, 0, 1, 0, 1)
        self.left_label_table.attach(self.left_version_label, 0, 1, 1, 2)
        self.left_label_table.attach(self.left_download_label, 0, 1, 3, 4)
        self.left_label_table.attach(self.left_homepage_box_align, 0, 1, 4, 5)
        self.left_label_align.add(self.left_label_table)
        self.left_view_box.pack_start(self.left_label_align, False, False)
        self.left_view_box.pack_start(self.left_recommend_box_align, False, False)
        self.right_info_box.pack_start(self.scrolled_window, True, True)
        self.pack_start(self.left_view_box, False, False)
        self.pack_start(self.right_info_box, True, True)
        
        self.left_view_box.connect("expose-event", self.expose_left_view)
        self.right_view_box.connect("expose-event", self.expose_right_view)
        self.left_logo_box.connect("expose-event", self.expose_left_logo_box)
        self.right_top_box.connect("expose-event", self.expose_right_top_box)
        self.right_title_box.connect("expose-event", self.expose_right_title_box)
        self.connect("hierarchy-changed", self.hierarchy_change)
        
        self.left_category_label.connect("button-press-event", lambda w, e: self.jump_to_category())
        
        global_event.register_event("download-screenshot-finish", self.download_screenshot_finish)
        
    def hierarchy_change(self, widget, previous_toplevel):
        # When detail page remove from it's container, previous_toplevel is not None.
        if previous_toplevel != None:
            container_remove_all(self.right_slide_box) # remove slide box first, to avoid screenshot area flash
            container_remove_all(self.right_comment_box) # remove comment box first, to avoid comment area flash
        
    def grade_pkg(self):
        global_event.emit("grade-pkg", self.pkg_name, self.pkg_star_view.star_buffer.star_level)
        
        self.pkg_star_view.star_buffer.star_level = int(self.star)
        self.pkg_star_view.queue_draw()
        
    def expose_star_mark(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        draw_text(
            cr, 
            str(self.star),
            rect.x + self.MARK_PADDING_X,
            rect.y + self.MARK_PADDING_Y,
            100,
            self.MARK_SIZE,
            text_size=self.MARK_SIZE,
            text_color="#F07200"
            )

    def jump_to_category(self):
        global_event.emit("jump-to-category", self.category[0], self.category[1])
        
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
                        rect.x + self.ICON_PADDING_X + (self.ICON_SIZE - self.pkg_pixbuf.get_width()) / 2,
                        rect.y + self.PADDING_Y)
            
    def expose_right_top_box(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        # Draw background.
        cr.set_source_rgb(*color_hex_to_cairo("#FFFFFF"))
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()
            
    def expose_right_title_box(self, widget, event):
        if self.pkg_name != None:
            # Init.
            cr = widget.window.cairo_create()
            rect = widget.allocation
            
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
            
    def button_press_start_button(self, widget, event):
        pixbuf = app_theme.get_pixbuf("button/start_normal.png").get_pixbuf()
        desktop_info = self.data_manager.get_pkg_desktop_info(self.pkg_name)
        global_event.emit("start-pkg", 
                          self.alias_name, 
                          desktop_info, 
                          (int(event.x), int(event.y), pixbuf.get_width() / 2, 0))
            
    def update_pkg_info(self, pkg_name):
        start_time = time.time()
        print "%s: start update_pkg_info" % pkg_name
        self.pkg_name = pkg_name
        (self.category, self.long_desc, 
         self.version, self.homepage, self.star, 
         self.download, self.alias_name,
         self.recommend_pkgs) = self.data_manager.get_pkg_detail_info(self.pkg_name)
        
        self.pkg_star_view = StarView()
        self.pkg_star_view.connect("clicked", lambda w: self.grade_pkg())
        self.pkg_star_mark = gtk.VBox()
        self.pkg_star_mark.connect("expose-event", self.expose_star_mark)
        container_remove_all(self.star_box)
        self.star_box.pack_start(self.pkg_star_view, False, False)
        self.star_box.pack_start(self.pkg_star_mark, False, False)
        self.pkg_star_view.star_buffer.star_level = int(self.star)
        
        print "%s: #1# %s" % (pkg_name, time.time() - start_time)
        create_thread(self.fetch_pkg_status).start()
        
        container_remove_all(self.left_category_box)
        if self.category != None:
            self.left_category_name_label.set_text("类别：")
            self.left_category_label.set_text(get_category_name(self.category[1]))
            self.left_category_box.add(self.left_category_label_box)
        self.left_version_label.set_text("版本：%s" % self.version)
        self.left_download_label.set_text("下载：%s" % self.download)
        
        print "%s: #2# %s" % (pkg_name, time.time() - start_time)
        container_remove_all(self.left_homepage_box)
        if self.homepage != "":
            homepage_label = Label("访问首页", 
                                   text_color=app_theme.get_color("homepage"),
                                   hover_color=app_theme.get_color("homepage_hover"))
            homepage_label.set_clickable()
            homepage_label.connect("button-press-event", lambda w, e: run_command("xdg-open %s" % self.homepage))
            self.left_homepage_box.pack_start(homepage_label)
            
        print "%s: #3# %s" % (pkg_name, time.time() - start_time)
        container_remove_all(self.left_recommend_box)    
        if len(self.recommend_pkgs) > 0:
            self.left_recommend_box.pack_start(self.left_recommend_label, False, False, 8)
            
            for (recommend_pkg_name, alias_name, star) in self.recommend_pkgs:
                self.left_recommend_box.pack_start(RecommendPkgItem(self, recommend_pkg_name, alias_name, star), False, False, 4)
        
        container_remove_all(self.right_desc_box)
        resizable_label = ResizableLabel(self.long_desc.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), 
                                         self.LONG_DESC_WRAP_WIDTH, 
                                         self.LONG_DESC_INIT_HEIGHT, 
                                         3)
        resizable_align = gtk.Alignment()
        resizable_align.set(0.5, 0.5, 1, 1)
        resizable_align.set_padding(0, 0, self.RIGHT_INFO_PADDING_X, self.RIGHT_INFO_PADDING_X)
        resizable_align.add(resizable_label)
        resizable_align.connect("expose-event", self.expose_resizable_label_background)
        self.right_desc_box.pack_start(resizable_align, False, False)
        
        print "%s: #4# %s" % (pkg_name, time.time() - start_time)
        self.show_screenshot()
        
        self.fetch_comment()
        # create_thread(self.fetch_comment).start()
        
        self.show_all()
        print "%s: end update_pkg_info, %s" % (pkg_name, time.time() - start_time)
        
    def handle_pkg_status(self, *reply):
        container_remove_all(self.left_action_box)
        install_status = reply
        if install_status[0][0]:
            if self.category == None:
                status_label = Label("安装")
                self.left_action_box.pack_start(status_label)
            else:
                action_button = ImageButton(
                    app_theme.get_pixbuf("button/start_normal.png"),
                    app_theme.get_pixbuf("button/start_hover.png"),
                    app_theme.get_pixbuf("button/start_press.png"),
                    )
                action_button.connect("button-press-event", self.button_press_start_button)
                self.left_action_box.pack_start(action_button)
        else:
            action_button = ImageButton(
                app_theme.get_pixbuf("button/install_normal.png"),
                app_theme.get_pixbuf("button/install_hover.png"),
                app_theme.get_pixbuf("button/install_press.png"),
                )
            action_button.connect("clicked", lambda w: global_event.emit("install-pkg", [self.pkg_name]))
            self.left_action_box.pack_start(action_button)
        self.left_action_box.show_all()
        
    def handle_dbus_error(self, *error):
        container_remove_all(self.left_action_box)
        print "***** request_pkgs_install_status handle_dbus_error"
        print error
    
    def fetch_pkg_status(self):
        start_time = time.time()
        self.data_manager.get_pkgs_install_status([self.pkg_name], self.handle_pkg_status, self.handle_dbus_error)
        print self.pkg_name, time.time() - start_time
        
    def open_url(self, webview, frame, network_request, nav_action, policy_dec):
        webbrowser.open(network_request.get_uri())
        
    def fetch_comment(self):
        if is_network_connected():
            container_remove_all(self.right_comment_box)    
            loading_label = gtk.Label("正在加载评论...")
            loading_label_align = gtk.Alignment(0.5, 0, 0, 0)
            loading_label_align.add(loading_label)
            loading_label_align.set_padding(10, 0, 0, 0)
            self.right_comment_box.pack_start(loading_label_align, False, False)
            web_view = WebView(os.path.join(CONFIG_DIR, "cookie.txt"))
            #web_view.enable_inspector()
            web_view.connect("new-window-policy-decision-requested", self.open_url)
            web_view_align = gtk.Alignment()
            web_view_align.set(0.5, 0, 0, 0)
            web_view_align.set_padding(33, 33, 33, 33)
            web_view_align.add(web_view)
            web_settings = web_view.get_settings()
            web_settings.set_property("enable-plugins", True)
            web_settings.set_property("enable-scripts", True)    
            web_view.open("%s/softcenter/v1/comment?n=%s&hl=%s" % (
                    SERVER_ADDRESS, 
                    self.pkg_name, 
                    "zh_CN"
                    ))
            #self.right_comment_box.pack_start(web_view_align, True, True)
            web_view.connect("load-finished", self.comment_load_finished_cb, web_view_align)
            
            # self.fetch_screenshot()
            
            create_thread(self.fetch_screenshot).start()

    def comment_load_finished_cb(self, webview, frame, web_view_align):
        self.scrolled_window.connect("vscrollbar-state-changed", lambda w, p: self.load_more_comment(p, webview))
        container_remove_all(self.right_comment_box)
        self.right_comment_box.pack_start(web_view_align, True, True)
        self.right_comment_box.show_all()

    def load_more_comment(self, postion, webview):
        if postion == "bottom":
            webview.execute_script('$("#nav_next").click();')
            
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
                
                print "Download start"
                try:
                    urllib.urlretrieve(remote_screenshot_zip_url, 
                                       os.path.join(SCREENSHOT_DOWNLOAD_DIR, self.pkg_name, "screenshot.zip")
                                       )
                    global_event.emit("download-screenshot-finish", self.pkg_name)
                    print "Download finish"
                except Exception, e:
                    traceback.print_exc(file=sys.stdout)
                    print "Download screenshot error: %s" % e
        except Exception, e:
            # traceback.print_exc(file=sys.stdout)
            # print "fetch_screenshot got error: %s" % e
            pass
            
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
                    map(lambda screenshot_file: get_resize_pixbuf_with_height(screenshot_file, 290), screenshot_files),
                    pointer_offset_x=-370,
                    pointer_offset_y=-15,
                        horizontal_align=ALIGN_MIDDLE,
                        vertical_align=ALIGN_MIDDLE,
                        height_offset=60,
                        hover_switch=False,
                        auto_switch=False,
                        navigate_switch=True,
                        )
                slide_align = gtk.Alignment()
                slide_align.set(0.5, 0.5, 1, 1)
                slide_align.add(slide_switcher)
                slide_align.connect("expose-event", self.expose_resizable_label_background)
                self.right_slide_box.pack_start(slide_align, True, True)
                
                powered_link = Label(
                    "Powered by 又拍云存储",
                    text_color=app_theme.get_color("homepage"),
                    hover_color=app_theme.get_color("homepage_hover"),
                    )
                powered_link.set_clickable()
                powered_link.connect("button-press-event", lambda w, e: run_command("xdg-open https://www.upyun.com/"))
                powered_link_align = gtk.Alignment()
                powered_link_align.set(1.0, 0.5, 0, 0)
                powered_link_align.set_padding(0, 0, 0, 100)
                powered_link_align.add(powered_link)
                self.right_slide_box.pack_start(powered_link_align, False, False)
                    
                self.show_all()
            else:
                print "%s haven't any screenshot from zip file" % self.pkg_name
        
gobject.type_register(DetailPage)        

class RecommendPkgItem(gtk.HBox):
    '''
    class docs
    '''
    
    MARK_SIZE = 11
    MARK_PADDING_X = 5
    MARK_PADDING_Y = -3
	
    def __init__(self, detail_page, pkg_name, alias_name, star):
        '''
        init docs
        '''
        gtk.HBox.__init__(self)
        self.star = star
        self.pkg_name = pkg_name
                
        v_box = gtk.VBox()
        pkg_icon_image = gtk.image_new_from_pixbuf(
            gtk.gdk.pixbuf_new_from_file_at_size(get_icon_pixbuf_path(pkg_name), 32, 32))
        pkg_alias_label = Label(alias_name,
                                hover_color=app_theme.get_color("homepage_hover"))
        pkg_alias_label.set_clickable()
        pkg_alias_label.connect("button-press-event", lambda w, e: detail_page.update_pkg_info(pkg_name))
        
        self.pkg_star_box = gtk.HBox()
        
        self.pkg_star_view = StarView()
        self.pkg_star_view.star_buffer.star_level = int(star)
        self.pkg_star_view.connect("clicked", lambda w: self.grade_pkg())
        
        self.pkg_star_mark = gtk.VBox()
        
        self.pack_start(pkg_icon_image, False, False)
        self.pack_start(v_box, True, True, 8)
        v_box.pack_start(pkg_alias_label, False, False, 2)
        v_box.pack_start(self.pkg_star_box, False, False, 2)
        self.pkg_star_box.pack_start(self.pkg_star_view, False, False)
        self.pkg_star_box.pack_start(self.pkg_star_mark, False, False)
        
        self.pkg_star_mark.connect("expose-event", self.expose_star_mark)
        
    def grade_pkg(self):
        global_event.emit("grade-pkg", self.pkg_name, self.pkg_star_view.star_buffer.star_level)
        
        self.pkg_star_view.star_buffer.star_level = int(self.star)
        self.pkg_star_view.queue_draw()
        
    def expose_star_mark(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        draw_text(
            cr, 
            str(self.star),
            rect.x + self.MARK_PADDING_X,
            rect.y + self.MARK_PADDING_Y,
            100,
            self.MARK_SIZE,
            text_size=self.MARK_SIZE,
            text_color="#F07200"
            )
        
gobject.type_register(RecommendPkgItem)        
