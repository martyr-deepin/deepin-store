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

import pango
import gtk
import cairo
import gobject
from item_render import get_icon_pixbuf_path
from dtk.ui.draw import draw_pixbuf, draw_text
from dtk.ui.constant import DEFAULT_FONT_SIZE
from dtk.ui.popup_grab_window import PopupGrabWindow, wrap_grab_window
from dtk.ui.iconview import IconView, IconItem
from dtk.ui.scrolled_window import ScrolledWindow
from events import global_event
from dtk.ui.window import Window

DESKTOP_ICON_WIDTH = 80
DESKTOP_ICON_HEIGHT = 95

class StartDesktopWindow(Window):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        Window.__init__(self)

        self.window_width = 0
        self.window_height = 0
        
        self.max_columns = 4
        self.max_rows = 3
        
        self.iconview = IconView(mask_bound_height=0)
        self.iconview.draw_mask = self.draw_iconview_mask
        self.iconview.draw_background = self.draw_iconvew_background
        self.iconview_scrolledwindow = ScrolledWindow(0, 0)
        self.iconview_scrolledwindow.add_child(self.iconview)
        
        self.window_frame.add(self.iconview_scrolledwindow)
        
        self.connect("show", self.show_start_desktop_window)
        
        wrap_grab_window(start_desktop_grab_window, self)
        
    def draw_iconview_mask(self, cr, x, y, w, h):
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(x, y, w, h)
        cr.fill()
        
    def draw_iconvew_background(self, widget, cr):
        pass
        
    def draw_background(self, cr, x, y, w, h):
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        
        pass
    
    def draw_skin(self, cr, x, y, w, h):
        pass
    
    def draw_mask(self, cr, x, y, w, h):
        pass
        
    def show_start_desktop_window(self, widget):
        (shadow_x, shadow_y) = self.get_shadow_size()
        self.window_width += shadow_x * 2
        self.window_height += shadow_y * 2
        
        self.set_geometry_hints(
            None,
            self.window_width,       # minimum width
            self.window_height,       # minimum height
            self.window_width,
            self.window_height,
            -1, -1, -1, -1, -1, -1
            )
        
        self.move_x -= shadow_x
        self.move_y -= shadow_y * 2
         
        self.move(self.move_x, self.move_y)
            
    def get_scrolledwindow(self):
        return self.iconview_scrolledwindow
        
    def start(self, pkg_name, desktop_infos, (x, y)):
        desktop_num = len(desktop_infos)
        
        if desktop_num <= self.max_columns:
            window_width = DESKTOP_ICON_WIDTH * desktop_num
            window_height = DESKTOP_ICON_HEIGHT
        elif desktop_num <= self.max_columns * 2:
            window_width = DESKTOP_ICON_WIDTH * self.max_columns
            window_height = DESKTOP_ICON_HEIGHT * 2
        else:
            window_width = DESKTOP_ICON_WIDTH * self.max_columns
            window_height = DESKTOP_ICON_HEIGHT * self.max_rows
            
        self.window_width = window_width
        self.window_height = window_height
        
        # Add items.
        self.iconview.clear()
        items = []
        for desktop_info in desktop_infos:
            items.append(StartDesktopItem(pkg_name, desktop_info))
        self.iconview.add_items(items)
        self.iconview_scrolledwindow.show_all()
        
        self.move_x = x - window_width / 2
        self.move_y = y - window_height

        self.show_all()
        
gobject.type_register(StartDesktopWindow)

class StartDesktopItem(IconItem):
    '''
    Icon item.
    '''
	
    DESKTOP_ICON_PADDING_Y = 5
    DESKTOP_TEXT_PADDING_X = 10
    DESKTOP_TEXT_PADDING_Y = 60
    
    def __init__(self, pkg_name, desktop_info):
        '''
        Initialize ItemIcon class.
        
        @param pixbuf: Icon pixbuf.
        '''
        IconItem.__init__(self)
        self.pkg_name = pkg_name
        (self.desktop_path, self.desktop_icon_name, self.desktop_display_name) = desktop_info
        self.icon_pixbuf = None
        self.hover_flag = False
        self.highlight_flag = False
        
        self.icon_size = 32
        
    def get_width(self):
        '''
        Get item width.
        
        This is IconView interface, you should implement it.
        '''
        return DESKTOP_ICON_WIDTH
        
    def get_height(self):
        '''
        Get item height.
        
        This is IconView interface, you should implement it.
        '''
        return DESKTOP_ICON_HEIGHT
    
    def render(self, cr, rect):
        '''
        Render item.
        
        This is IconView interface, you should implement it.
        '''
        if self.icon_pixbuf == None:
            self.icon_pixbuf = gtk.gdk.pixbuf_new_from_file(get_icon_pixbuf_path(self.desktop_icon_name))
            
        draw_pixbuf(
            cr,
            self.icon_pixbuf,
            rect.x + (rect.width - self.icon_pixbuf.get_width()) / 2,
            rect.y + self.DESKTOP_ICON_PADDING_Y)    
        
        text_width = rect.width - self.DESKTOP_TEXT_PADDING_X * 2
        draw_text(
            cr,
            self.desktop_display_name,
            rect.x + self.DESKTOP_TEXT_PADDING_X,
            rect.y + self.DESKTOP_TEXT_PADDING_Y,
            text_width,
            DEFAULT_FONT_SIZE,
            alignment=pango.ALIGN_CENTER,
            wrap_width=text_width)
        
    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.
        
        This is IconView interface, you should implement it.
        '''
        global_event.emit("start-desktop", self.pkg_name, self.desktop_path)
    
    def icon_item_release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> if self.pixbuf:
        >>>     del self.pixbuf
        >>>     self.pixbuf = None
        >>>
        >>> return True

        This is IconView interface, you should implement it.
        
        @return: Return True if do release work, otherwise return False.
        
        When this function return True, IconView will call function gc.collect() to release object to release memory.
        '''
        if self.icon_pixbuf:
            del self.icon_pixbuf
            self.icon_pixbuf = None
        
        return True
        
gobject.type_register(StartDesktopItem)

start_desktop_grab_window = PopupGrabWindow(StartDesktopWindow)

if __name__ == "__main__":
    window = StartDesktopWindow()
    
    # window.start(["a", "b"])
    # window.start(["a", "b", "c"])
    window.start(["a", "b", "c", "d"])
    # window.start(["a", "b", "c", "d"] * 2)
    # window.start(["a", "b", "c", "d"] * 3)
    # window.start(["a", "b", "c", "d"] * 4)
    window.connect("destroy", lambda w: gtk.main_quit())
    
    gtk.main()
