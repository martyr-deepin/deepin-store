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

import copy
import gtk
import os
import gobject
from message_bar import MessageBar
from dtk.ui.utils import remove_timeout_id, cairo_state, get_content_size
from constant import BUTTON_NORMAL, BUTTON_HOVER, BUTTON_PRESS
from item_render import STAR_SIZE, get_star_level, get_icon_pixbuf_path, NAME_SIZE, ITEM_PADDING_X, ICON_SIZE
from search_page import SearchPage
from dtk.ui.treeview import TreeView, TreeItem
from dtk.ui.draw import draw_text, draw_pixbuf, draw_vlinear
from deepin_utils.file import get_parent_dir
from dtk.ui.utils import color_hex_to_cairo, container_remove_all, is_in_rect
from dtk.ui.star_view import StarBuffer
from dtk.ui.iconview import IconView
from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.iconview import IconItem
from recommend_page import RecommendIconItem
from dtk.ui.box import BackgroundBox
from slide_switcher import SlideSwitcher
from album_page import AlbumPage
from tab_switcher import TabSwitcher
from download_rank_page import DownloadRankPage
from completion_window import search_entry, completion_window, completion_grab_window
from events import global_event
from skin import app_theme
from data import DATA_ID
from category_info import get_category_name
from nls import _

FIRST_CATEGORY_PADDING_X = 66
SECOND_CATEGORY_PADDING_X = 46

CATEGORY_VIEW_WIDTH = 155
SLIDE_PICTURE_DIR = os.path.join(get_parent_dir(__file__, 2), "data", "update", DATA_ID, "home", "slide_picture", "zh_CN")

class HomePage(gtk.HBox):
    '''
    class docs
    '''
	
    def __init__(self, data_manager):
        '''
        init docs
        '''
        # Init.
        gtk.HBox.__init__(self)
        self.data_manager = data_manager
        
        self.background_box = BackgroundBox()
        self.background_box.draw_mask = self.draw_mask
        self.sidebar_box = gtk.VBox()
        self.page_box = gtk.VBox()
        self.sidebar_box.set_size_request(CATEGORY_VIEW_WIDTH, -1)
        
        self.canopy = gtk.VBox()
        self.canopy.set_size_request(-1, 19)
        
        self.search_align = gtk.Alignment()
        self.search_align.set(0.5, 0.5, 0, 0)
        self.search_align.set_padding(15, 5, 13, 13)
        self.search_align.add(search_entry)
        
        self.in_press = False
        self.press_return = False
        self.press_id = 0
        self.show_timeout_id = None
        self.entry_changed = False
        
        search_entry.entry.connect("changed", self.search_entry_changed)
        search_entry.entry.connect("key-press-event", self.search_entry_key_press)
        search_entry.entry.connect("key-release-event", self.search_entry_key_release)
        search_entry.connect("action-active", lambda entry, search_string: self.show_search_page(search_string))
        search_entry.entry.connect("press-return", lambda entry: self.show_search_page(entry.get_text(), True))
        
        self.recommend_item = RecommendItem(data_manager)
       
        category_pkg_info = data_manager.get_category_pkg_info()
        category_items = map(lambda (index, (first_category_name, second_category_items)):
                                 CategoryItem(index + 1, 
                                              first_category_name, 
                                              second_category_items,
                                              data_manager,
                                              ), 
                             enumerate(category_pkg_info.items()))
        
        self.category_view = TreeView(
            [self.recommend_item] + category_items,
            enable_drag_drop=False,
            enable_multiple_select=False,
            expand_column=0,
            )
        self.category_view.draw_mask = self.draw_mask
        self.category_view.set_size_request(-1, 470)
        self.category_view_align = gtk.Alignment()
        self.category_view_align.set(0.5, 0.5, 1, 1)
        self.category_view_align.set_padding(10, 10, 0, 0)
        self.category_view_align.add(self.category_view)
        
        self.background_box.pack_start(self.canopy, False, False)
        self.background_box.pack_start(self.search_align, True, True)
        self.background_box.pack_end(self.category_view_align, False, False)
        self.sidebar_box.pack_start(self.background_box, False, False)
        
        self.split_line = gtk.VBox()
        self.split_line.set_size_request(1, -1)
        
        self.pack_start(self.sidebar_box, False, False)
        self.pack_start(self.split_line, False, False)
        self.pack_start(self.page_box, True, True)
        
        self.canopy.connect("expose-event", self.expose_canopy)
        self.split_line.connect("expose-event", self.expose_split_line)
        
        global_event.register_event("show-pkg-view", self.show_pkg_view)
        
    def jump_to_category(self, first_category_name, second_category_name):
        print (first_category_name, second_category_name)
        
        for item in self.category_view.visible_items:
            if isinstance(item, CategoryItem) and item.is_expand:
                item.unexpand()
        
        for item in self.category_view.visible_items:
            if isinstance(item, CategoryItem) and item.first_category_name == first_category_name:
                item.expand()
                break

        for item in self.category_view.visible_items:
            if isinstance(item, SecondCategoryItem) and item.second_category_name == second_category_name:
                self.category_view.select_items([item])
                self.category_view.visible_item(item)
                item.button_press(0, 0, 0)
                break
        
    def draw_mask(self, cr, x, y, w, h):
        '''
        Draw mask interface.
        
        @param cr: Cairo context.
        @param x: X coordiante of draw area.
        @param y: Y coordiante of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        sidebar_color = app_theme.get_color("sidebar_background").get_color()
        draw_vlinear(cr, x, y, w, h,
                     [(0, (sidebar_color, 0.9)),
                      (1, (sidebar_color, 0.9)),]
                     )
        
    def expose_canopy(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        draw_pixbuf(
            cr,
            app_theme.get_pixbuf("category/canopy.png").get_pixbuf(),
            rect.x,
            rect.y)
        
    def expose_split_line(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation

        cr.set_source_rgb(*color_hex_to_cairo("#e5e5e5"))
        cr.rectangle(rect.x, rect.y, 1, rect.height)
        cr.fill()
        
        return True
        
    def search_entry_changed(self, entry, entry_string):
        self.press_id += 1
        self.press_return = False
        self.entry_changed = True
        
    def search_entry_key_press(self, widget, event):
        self.in_press = True
        self.press_id += 1
        
        remove_timeout_id(self.show_timeout_id)
        
    def search_entry_key_release(self, widget, event):
        self.in_press = False
        press_id = copy.deepcopy(self.press_id)
        remove_timeout_id(self.show_timeout_id)
        self.show_timeout_id = gobject.timeout_add(200, lambda : self.popup_completion(press_id))
        
    def popup_completion(self, press_id):
        if (not self.in_press) and (not self.press_return) and press_id == self.press_id and self.entry_changed:
            search_string = search_entry.get_text()
            if len(search_string) >= 3:
                match_pkgs = self.data_manager.get_pkgs_match_input(search_string)
                if len(match_pkgs) > 0:
                    completion_window.show(search_string, match_pkgs)
                else:
                    completion_grab_window.popup_grab_window_focus_out()
            else:
                completion_grab_window.popup_grab_window_focus_out()
                
            self.entry_changed = False
        
    def show_search_page(self, search_string, press_return=False):
        self.category_view.unselect_all()
        
        self.press_return = press_return
        
        if self.press_return:
            completion_grab_window.popup_grab_window_focus_out()
        
        search_page = SearchPage(self.data_manager)
        search_page.update(map(lambda word: word.encode("utf8"), search_string.split(" ")))
        self.show_pkg_view(search_page)
        
    def show_pkg_view(self, widget):
        container_remove_all(self.page_box)
        self.page_box.pack_start(widget, True, True)
        
        self.page_box.show_all()
        
gobject.type_register(HomePage)

CATEGORY_ITEM_NAME_WIDTH = -1
CATEGORY_ITEM_HEIGHT = 42
CATEGORY_ITEM_NAME_SIZE = 11
SECOND_CATEGORY_ITEM_NAME_SIZE = 10
SECOND_CATEGORY_ITEM_HEIGHT = 35

CATEGORY_ITEM_EXPAND_PADDING_X = 30

class CategoryItem(TreeItem):
    '''
    class docs
    '''
	
    def __init__(self, index, first_category_name, second_category_items, data_manager):
        '''
        init docs
        '''
        TreeItem.__init__(self)
        self.index = index
        self.first_category_name = first_category_name
        self.second_category_items = second_category_items
        self.data_manager = data_manager
    
    def render_name(self, cr, rect):
        text_color = "#333333"
        if self.is_select:
            cr.set_source_rgba(*color_hex_to_cairo(app_theme.get_color("sidebar_select").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
            
            text_color = "#FFFFFF"
        elif self.is_hover:
            cr.set_source_rgba(*color_hex_to_cairo(app_theme.get_color("sidebar_hover").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        pixbuf = app_theme.get_pixbuf("category/%s.png" % (self.index)).get_pixbuf()
        draw_pixbuf(
            cr,
            pixbuf,
            rect.x + 12,
            rect.y + (rect.height - pixbuf.get_height()) / 2)
        
        draw_text(cr, 
                  get_category_name(self.first_category_name),
                  rect.x + pixbuf.get_width() + 22, 
                  rect.y,
                  rect.width,
                  rect.height,
                  text_size=CATEGORY_ITEM_NAME_SIZE,
                  text_color=text_color,
                  )
        
        if self.is_hover:
            if self.is_expand:
                pixbuf = app_theme.get_pixbuf("sidebar/close.png").get_pixbuf()
            else:
                pixbuf = app_theme.get_pixbuf("sidebar/open.png").get_pixbuf()
                
            draw_pixbuf(
                cr,
                pixbuf,
                rect.x + rect.width - CATEGORY_ITEM_EXPAND_PADDING_X,
                rect.y + (rect.height - pixbuf.get_height()) / 2)
        
    def get_height(self):
        return CATEGORY_ITEM_HEIGHT
    
    def get_column_widths(self):
        return [CATEGORY_ITEM_NAME_WIDTH]
        
    def get_column_renders(self):    
        return [self.render_name]
        
    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
        
    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def select(self):
        self.is_select = True
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
        
    def unselect(self):
        self.is_select = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def is_in_expand_button_area(self, column, offset_x, offset_y):
        pixbuf = app_theme.get_pixbuf("sidebar/close.png").get_pixbuf()
        
        return is_in_rect((offset_x, offset_y),
                          (CATEGORY_VIEW_WIDTH - CATEGORY_ITEM_EXPAND_PADDING_X,
                           (self.get_height() - pixbuf.get_height()) / 2,
                           pixbuf.get_width(),
                           pixbuf.get_height()))
    
    def motion_notify(self, column, offset_x, offset_y):
        if self.is_in_expand_button_area(column, offset_x, offset_y):
            global_event.emit("set-cursor", gtk.gdk.HAND2)    
        else:
            global_event.emit("set-cursor", None)    
            
    def button_press(self, column, offset_x, offset_y):
        if self.is_in_expand_button_area(column, offset_x, offset_y):
            if self.is_expand:
                self.unexpand()
            else:
                self.expand()
            
    def single_click(self, column, offset_x, offset_y):
        items = []
        pkg_names = []
        desktop_infos = {}
        for (second_category, pkg_dict) in self.second_category_items.items():
            for (pkg_name, desktop_info) in pkg_dict.items():
                pkg_names.append(pkg_name)
                desktop_infos[pkg_name] = desktop_info
                
        for (pkg_name, is_installed, long_desc, star, alias_name) in self.data_manager.get_item_pkgs_info(pkg_names):
            items.append(PkgIconItem(is_installed, alias_name, pkg_name, long_desc, star, desktop_infos[pkg_name]))
        
        self.page_box = gtk.VBox()    
            
        self.message_bar = MessageBar(18)
        
        self.pkg_icon_view = IconView() 
        self.pkg_icon_scrolled_window = ScrolledWindow()
        self.pkg_icon_view.connect(
            "items-change", 
            lambda iconview: self.message_bar.set_message("%s: %s款软件" % (get_category_name(self.first_category_name), len(iconview.items))))
        items_number = len(items)
        pages = int(items_number/12)
        if pages > 0:
            tmp_items = items[:12]
            self.pkg_icon_view.add_items(tmp_items)
            button_hbox = gtk.HBox(5)
            for i in range(10):
                button = gtk.Button(str(i+1))
                button_hbox.pack_start(button, False, False)
            button_align = gtk.Alignment(0.5, 0.5, 0, 0)
            button_align.add(button_hbox)

            self.pkg_icon_box = gtk.VBox()
            self.pkg_icon_box.pack_start(self.pkg_icon_view)
            self.pkg_icon_box.pack_start(button_align, False, False)
            self.pkg_icon_scrolled_window.add_child(self.pkg_icon_box)
        else:
            self.pkg_icon_view.add_items(items)
            self.pkg_icon_scrolled_window.add_child(self.pkg_icon_view)
        self.pkg_icon_view.draw_mask = self.draw_mask
        self.pkg_icon_view.draw_row_mask = self.draw_row_mask
        
        self.page_box.pack_start(self.message_bar, False, False)
        self.page_box.pack_start(self.pkg_icon_scrolled_window, True, True)
        
        global_event.emit("show-pkg-view", self.page_box)
        
        # from meliae import scanner
        # scanner.dump_all_objects("/tmp/dsc_memory.json")
        
    def draw_row_mask(self, cr, rect, row):
        if row % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
    
    def draw_mask(self, cr, x, y, w, h):
        '''
        Draw mask interface.
        
        @param cr: Cairo context.
        @param x: X coordiante of draw area.
        @param y: Y coordiante of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        draw_vlinear(cr, x, y, w, h,
                     [(0, ("#FFFFFF", 0.9)),
                      (1, ("#FFFFFF", 0.9)),]
                     )
        
    def double_click(self, column, offset_x, offset_y):
        if self.is_expand:
            self.unexpand()
        else:
            self.expand()
        
    def add_child_item(self):
        items = []
        for (second_category_name, second_category_dict) in self.data_manager.get_second_category_pkg_info(self.first_category_name).items():
            pkg_names = []
            desktop_infos = {}
            for (pkg_name, desktop_info) in second_category_dict.items():
                pkg_names.append(pkg_name)
                desktop_infos[pkg_name] = desktop_info
                
            items.append(SecondCategoryItem(self.first_category_name, second_category_name, pkg_names, self.data_manager, desktop_infos))    
            
        self.child_items = items    
        self.add_items_callback(self.child_items, self.row_index + 1)
        
    def delete_chlid_item(self):
        self.delete_items_callback(self.child_items)
    
    def expand(self):
        self.is_expand = True
        
        self.add_child_item()
            
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def unexpand(self):
        self.is_expand = False
        
        self.delete_chlid_item()
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
gobject.type_register(CategoryItem)        

class SecondCategoryItem(TreeItem):
    '''
    class docs
    '''
	
    def __init__(self, first_category_name, second_category_name, pkg_names, data_manager, desktop_infos):
        '''
        init docs
        '''
        TreeItem.__init__(self)
        self.first_category_name = first_category_name
        self.second_category_name = second_category_name
        self.pkg_names = pkg_names
        self.data_manager = data_manager
        self.desktop_infos = desktop_infos
    
    def render_name(self, cr, rect):
        text_color = "#333333"
        if self.is_select:
            cr.set_source_rgba(*color_hex_to_cairo(app_theme.get_color("sidebar_select").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
            
            text_color = "#FFFFFF"
        elif self.is_hover:
            cr.set_source_rgba(*color_hex_to_cairo(app_theme.get_color("sidebar_hover").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        draw_text(cr, 
                  get_category_name(self.second_category_name),
                  rect.x + SECOND_CATEGORY_PADDING_X,
                  rect.y,
                  rect.width,
                  rect.height,
                  text_size=SECOND_CATEGORY_ITEM_NAME_SIZE,
                  text_color=text_color,
                  )
        
    def get_height(self):
        return SECOND_CATEGORY_ITEM_HEIGHT
    
    def get_column_widths(self):
        return [CATEGORY_ITEM_NAME_WIDTH]
        
    def get_column_renders(self):    
        return [self.render_name]
        
    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
        
    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def select(self):
        self.is_select = True
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
        
    def unselect(self):
        self.is_select = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def button_press(self, column, offset_x, offset_y):
        items = []
        
        for (pkg_name, is_installed, long_desc, star, alias_name) in self.data_manager.get_item_pkgs_info(self.pkg_names):
            items.append(PkgIconItem(is_installed, alias_name, pkg_name, long_desc, star, self.desktop_infos[pkg_name]))
            
        self.page_box = gtk.VBox()    
            
        self.message_bar = MessageBar(18)
        
        self.pkg_icon_view = IconView() 
        self.pkg_icon_view.connect(
            "items-change", 
            lambda iconview: self.message_bar.set_message("%s > %s: %s款软件" % (
                get_category_name(self.first_category_name), 
                get_category_name(self.second_category_name), 
                len(iconview.items))))
        self.pkg_icon_view.add_items(items)
        self.pkg_icon_scrolled_window = ScrolledWindow()
        self.pkg_icon_scrolled_window.add_child(self.pkg_icon_view)
        self.pkg_icon_view.draw_mask = self.draw_mask
        self.pkg_icon_view.draw_row_mask = self.draw_row_mask
        
        self.page_box.pack_start(self.message_bar, False, False)
        self.page_box.pack_start(self.pkg_icon_scrolled_window, True, True)
        
        global_event.emit("show-pkg-view", self.page_box)
        
    def draw_row_mask(self, cr, rect, row):
        if row % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
    
    def draw_mask(self, cr, x, y, w, h):
        '''
        Draw mask interface.
        
        @param cr: Cairo context.
        @param x: X coordiante of draw area.
        @param y: Y coordiante of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        draw_vlinear(cr, x, y, w, h,
                     [(0, ("#FFFFFF", 0.9)),
                      (1, ("#FFFFFF", 0.9)),]
                     )
        
gobject.type_register(SecondCategoryItem)        

class RecommendItem(TreeItem):
    '''
    class docs
    '''
	
    def __init__(self, data_manager):
        '''
        init docs
        '''
        TreeItem.__init__(self)
        self.name = _("Home Recommends")
        self.data_manager = data_manager
    
    def render_name(self, cr, rect):
        text_color = "#333333"
        if self.is_select:
            cr.set_source_rgba(*color_hex_to_cairo(app_theme.get_color("sidebar_select").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
            
            text_color = "#FFFFFF"
        elif self.is_hover:
            cr.set_source_rgba(*color_hex_to_cairo(app_theme.get_color("sidebar_hover").get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        pixbuf = app_theme.get_pixbuf("category/12.png").get_pixbuf()
        draw_pixbuf(
            cr,
            pixbuf,
            rect.x + 12,
            rect.y + (rect.height - pixbuf.get_height()) / 2)
        
        draw_text(cr, 
                  self.name,
                  rect.x + pixbuf.get_width() + 22,
                  rect.y,
                  rect.width,
                  rect.height,
                  text_size=CATEGORY_ITEM_NAME_SIZE,
                  text_color=text_color,
                  )
        
    def get_height(self):
        return CATEGORY_ITEM_HEIGHT
    
    def get_column_widths(self):
        return [CATEGORY_ITEM_NAME_WIDTH]
        
    def get_column_renders(self):    
        return [self.render_name]
        
    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
        
    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def select(self):
        self.is_select = True
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
        
    def unselect(self):
        self.is_select = False
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def button_press(self, column, offset_x, offset_y):
        self.show_page()
        
    def show_page(self):    
        self.recommend_scrolled_window = ScrolledWindow()
        
        self.background_box = BackgroundBox()
        self.background_box.draw_mask = self.draw_mask
        
        self.box = gtk.VBox()
        
        slide_pkg_names = self.data_manager.get_slide_info()
        self.slider_switcher = SlideSwitcher(
            map(lambda pkg_name: gtk.gdk.pixbuf_new_from_file(os.path.join(SLIDE_PICTURE_DIR, "%s.jpg" % pkg_name)),
                slide_pkg_names))
        self.slider_switcher.connect("motion-notify-index", lambda w, i: global_event.emit("set-cursor", gtk.gdk.HAND2))
        self.slider_switcher.connect("button-press-index", lambda w, i: global_event.emit("switch-to-detail-page", slide_pkg_names[i]))
        self.slider_switcher.connect("leave-notify-index", lambda w, i: global_event.emit("set-cursor", None))
        self.box_align = gtk.Alignment()
        self.box_align.set(0.5, 0.5, 1, 1)
        self.box_align.set_padding(5, 0, 10, 11)
        
        self.page_box = gtk.VBox()
        
        self.tab_switcher = TabSwitcher(["热门推荐", "专题介绍", "下载排行"])
        self.tab_switcher_align = gtk.Alignment()
        self.tab_switcher_align.set(0.5, 0.5, 1, 1)
        self.tab_switcher_align.set_padding(10, 0, 0, 9)
        
        items = []
        for pkg_name in self.data_manager.get_recommend_info():
            items.append(RecommendIconItem(pkg_name))
        
        self.pkg_icon_view = IconView() 
        self.pkg_icon_view.add_items(items)
        self.pkg_icon_scrolled_window = ScrolledWindow()
        self.pkg_icon_scrolled_window.add_child(self.pkg_icon_view)
        self.pkg_icon_view.draw_mask = self.draw_mask
        
        self.pkg_icon_view_align = gtk.Alignment()
        self.pkg_icon_view_align.set(0.5, 0.5, 1, 1)
        self.pkg_icon_view_align.set_padding(6, 0, 1, 11)
        self.pkg_icon_view_align.add(self.pkg_icon_scrolled_window)
        
        self.album_page = AlbumPage(self.data_manager)
        
        self.download_rank_page = DownloadRankPage(self.data_manager)
        
        self.pages = [self.pkg_icon_view_align, self.album_page, self.download_rank_page]
        
        self.tab_switcher_align.add(self.tab_switcher)
        
        self.box.pack_start(self.slider_switcher, False, False)
        self.box.pack_start(self.tab_switcher_align, False, False)
        
        self.box_align.add(self.box)
        
        self.background_box.pack_start(self.box_align)
        self.background_box.pack_start(self.page_box)
        
        self.recommend_scrolled_window.add_child(self.background_box)
        
        self.switch_page(0)
        
        self.tab_switcher.connect("tab-switch-start", lambda switcher, page_index: self.switch_page(page_index))
        self.tab_switcher.connect("click-current-tab", lambda switcher, page_index: self.click_page(page_index))
        
        global_event.emit("show-pkg-view", self.recommend_scrolled_window)
        
    def draw_blank_mask(self, cr, x, y, w, h):
        pass
        
    def draw_mask(self, cr, x, y, w, h):
        '''
        Draw mask interface.
        
        @param cr: Cairo context.
        @param x: X coordiante of draw area.
        @param y: Y coordiante of draw area.
        @param w: Width of draw area.
        @param h: Height of draw area.
        '''
        draw_vlinear(cr, x, y, w, h,
                     [(0, ("#FFFFFF", 0.9)),
                      (1, ("#FFFFFF", 0.9)),]
                     )
        
    def click_page(self, page_index):
        if page_index == 1 and self.pages[page_index].in_detail_view:
            self.pages[page_index].switch_to_album_summary_view()
        
    def switch_page(self, page_index):
        container_remove_all(self.page_box)
        self.page_box.pack_start(self.pages[page_index], True, True)
        
        if page_index == 1:
            if self.pages[page_index].in_detail_view:
                self.pages[page_index].switch_to_album_summary_view()
                
        self.recommend_scrolled_window.show_all()
        
gobject.type_register(RecommendItem)        

class PkgIconItem(IconItem):
    '''
    class docs
    '''
    
    ALIAS_NAME_SIZE = 12    
    
    PADDING_X = 10
    PADDING_Y = 10
    PADDING_MIDDLE = 10	
    
    BUTTON_PADDING_X = ITEM_PADDING_X
    BUTTON_PADDING_Y = 60
    BUTTON_WIDTH = 48
    BUTTON_HEIGHT = 18
    
    DRAW_ICON_SIZE = 48
    DRAW_PADDING_LEFT = 20
    DRAW_PADDING_RIGHT = 10
    DRAW_PADDING_Y = 16
    DRAW_BUTTON_PADDING_Y = 13
    DRAW_INFO_PADDING_X = 15
    DRAW_STAR_PADDING_Y = 40
    DRAW_LONG_DESC_PADDING_Y = 68
    
    def __init__(self, is_installed, alias_name, pkg_name, long_desc, mark, desktop_info):
        '''
        init docs
        '''
        IconItem.__init__(self)
        self.is_installed = is_installed
        self.alias_name = alias_name
        self.pkg_name = pkg_name
        self.long_desc = long_desc
        self.mark = mark
        self.desktop_info = desktop_info
        
        self.pkg_icon_pixbuf = None
        
        self.star_level = get_star_level(mark)
        self.star_buffer = StarBuffer(self.star_level)
        self.grade_star = 0
        
        self.width = 240
        self.height = 114
        
        self.button_status = BUTTON_NORMAL
        
    def get_width(self):
        '''
        Get item width.
        
        This is IconView interface, you should implement it.
        '''
        return self.width
    
    def get_height(self):
        '''
        Get item height.
        
        This is IconView interface, you should implement it.
        '''
        return self.height
    
    def render(self, cr, rect):
        # Draw icon.
        if self.pkg_icon_pixbuf == None:
            self.pkg_icon_pixbuf = gtk.gdk.pixbuf_new_from_file(get_icon_pixbuf_path(self.pkg_name))        

        draw_pixbuf(
            cr,
            self.pkg_icon_pixbuf,
            rect.x + self.DRAW_PADDING_LEFT + (ICON_SIZE - self.pkg_icon_pixbuf.get_width()) / 2,
            rect.y + self.DRAW_PADDING_Y)    
        
        # Draw button.
        if self.is_installed:
            name = "button/start_small"
        else:
            name = "button/install_small"
        
        if self.button_status == BUTTON_NORMAL:
            status = "normal"
        elif self.button_status == BUTTON_HOVER:
            status = "hover"
        elif self.button_status == BUTTON_PRESS:
            status = "press"
            
        pixbuf = app_theme.get_pixbuf("%s_%s.png" % (name, status)).get_pixbuf()
        draw_pixbuf(
            cr,
            pixbuf,
            rect.x + self.DRAW_PADDING_LEFT,
            rect.y + self.DRAW_PADDING_Y + self.DRAW_ICON_SIZE + self.DRAW_BUTTON_PADDING_Y)
        
        # Draw name.
        text_width = rect.width - self.DRAW_PADDING_LEFT - self.DRAW_PADDING_RIGHT - self.DRAW_INFO_PADDING_X - self.pkg_icon_pixbuf.get_width()
        draw_text(
            cr,
            self.alias_name,
            rect.x + self.DRAW_PADDING_LEFT + ICON_SIZE + self.DRAW_INFO_PADDING_X,
            rect.y + self.DRAW_PADDING_Y,
            text_width,
            NAME_SIZE,
            text_size=NAME_SIZE)
        
        # Draw star.
        self.star_buffer.render(
            cr,
            gtk.gdk.Rectangle(
                rect.x + self.DRAW_PADDING_LEFT + ICON_SIZE + self.DRAW_INFO_PADDING_X,
                rect.y + self.DRAW_STAR_PADDING_Y,
                STAR_SIZE * 5,
                STAR_SIZE
                ))
        
        # Draw long desc.
        long_desc_height = 32
        if len(self.long_desc.split("\n")) == 1:
            self.long_desc += "\n"
        with cairo_state(cr):
            cr.rectangle(
                rect.x + self.DRAW_PADDING_LEFT + ICON_SIZE + self.DRAW_INFO_PADDING_X,
                rect.y + self.DRAW_LONG_DESC_PADDING_Y,
                text_width,
                long_desc_height,
                )
            cr.clip()
            draw_text(
                cr,
                self.long_desc,
                rect.x + self.DRAW_PADDING_LEFT + ICON_SIZE + self.DRAW_INFO_PADDING_X,
                rect.y + self.DRAW_LONG_DESC_PADDING_Y,
                text_width,
                long_desc_height,
                wrap_width=text_width,
                )
        
    def is_in_star_area(self, x, y):
        return is_in_rect((x, y),
                          (self.DRAW_PADDING_LEFT + self.pkg_icon_pixbuf.get_width() + self.DRAW_INFO_PADDING_X,
                           self.DRAW_STAR_PADDING_Y,
                           STAR_SIZE * 5,
                           STAR_SIZE
                           ))
    
    def is_in_button_area(self, x, y):
        return is_in_rect((x, y),
                          (self.DRAW_PADDING_LEFT,
                           self.DRAW_PADDING_Y + self.DRAW_ICON_SIZE + self.DRAW_BUTTON_PADDING_Y,
                           self.BUTTON_WIDTH,
                           self.BUTTON_HEIGHT,
                           ))
    
    def is_in_icon_area(self, x, y):
        if self.pkg_icon_pixbuf == None:
            self.pkg_icon_pixbuf = gtk.gdk.pixbuf_new_from_file(get_icon_pixbuf_path(self.pkg_name))        
            
        return is_in_rect((x, y),
                          (self.DRAW_PADDING_LEFT,
                           self.DRAW_PADDING_Y,
                           self.pkg_icon_pixbuf.get_width(),
                           self.pkg_icon_pixbuf.get_height()))
    
    def is_in_name_area(self, x, y):
        (text_width, text_height) = get_content_size(self.alias_name, text_size=NAME_SIZE)
        return is_in_rect((x, y),
                          (self.DRAW_PADDING_LEFT + self.pkg_icon_pixbuf.get_width() + self.DRAW_INFO_PADDING_X,
                           self.DRAW_PADDING_Y,
                           text_width,
                           NAME_SIZE))
    
    def icon_item_motion_notify(self, x, y):
        '''
        Handle `motion-notify-event` signal.
        
        This is IconView interface, you should implement it.
        '''
        self.hover_flag = True
        
        self.emit_redraw_request()
        
        if self.is_in_star_area(x, y):
            global_event.emit("set-cursor", gtk.gdk.HAND2)
            
            offset_x = x - (self.DRAW_PADDING_LEFT + self.pkg_icon_pixbuf.get_width() + self.DRAW_INFO_PADDING_X)
            times = offset_x / STAR_SIZE 
            self.grade_star = times * 2 + 2
                
            self.grade_star = min(self.grade_star, 10)    
            self.star_buffer.star_level = self.grade_star
            
            self.emit_redraw_request()
        elif self.is_in_icon_area(x, y) or self.is_in_name_area(x, y):
            global_event.emit("set-cursor", gtk.gdk.HAND2)    
        else:
            global_event.emit("set-cursor", None)
            
            if self.star_buffer.star_level != self.star_level:
                self.star_buffer.star_level = self.star_level
                self.emit_redraw_request()
            
            if self.is_in_button_area(x, y):
                self.button_status = BUTTON_HOVER
                self.emit_redraw_request()
            elif self.button_status != BUTTON_NORMAL:
                self.button_status = BUTTON_NORMAL
                self.emit_redraw_request()
                
    def get_offset_with_button(self, offset_x, offset_y):
        pixbuf = app_theme.get_pixbuf("button/start_normal.png").get_pixbuf()
        popup_x = self.DRAW_PADDING_LEFT + pixbuf.get_width() / 2
        popup_y = self.DRAW_PADDING_Y + self.DRAW_ICON_SIZE + self.DRAW_BUTTON_PADDING_Y
        return (offset_x, offset_y, popup_x, popup_y)
    
    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.
        
        This is IconView interface, you should implement it.
        '''
        if self.is_in_star_area(x, y):
            global_event.emit("grade-pkg", self.pkg_name, self.grade_star)
        elif self.is_in_button_area(x, y):
            if self.is_installed:
                global_event.emit("start-pkg", self.alias_name, self.desktop_info, self.get_offset_with_button(x, y))
            else:
                global_event.emit("install-pkg", [self.pkg_name])
                
            self.button_status = BUTTON_PRESS
            self.emit_redraw_request()
        elif self.is_in_icon_area(x, y) or self.is_in_name_area(x, y):
            global_event.emit("switch-to-detail-page", self.pkg_name)
    
    def icon_item_button_release(self, x, y):
        '''
        Handle button-release event.
        
        This is IconView interface, you should implement it.
        '''
        if self.is_in_button_area(x, y):
            self.button_status = BUTTON_HOVER
            self.emit_redraw_request()
        elif self.button_status != BUTTON_NORMAL:
            self.button_status = BUTTON_NORMAL
            self.emit_redraw_request()
    
    def icon_item_release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> del self.pixbuf
        >>> self.pixbuf = None

        This is IconView interface, you should implement it.
        
        @return: Return True if do release work, otherwise return False.
        
        When this function return True, IconView will call function gc.collect() to release object to release memory.
        '''
        if self.pkg_icon_pixbuf:
            del self.pkg_icon_pixbuf
            self.pkg_icon_pixbuf = None
            
        return True
        
gobject.type_register(PkgIconItem)
        
