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

from constant import VIEW_PADDING_X, VIEW_PADDING_Y, BUTTON_NORMAL, BUTTON_HOVER, BUTTON_PRESS
from skin import app_theme
from dtk.ui.utils import get_content_size, set_cursor, container_remove_all, is_in_rect
import gobject
import pango
from dtk.ui.constant import DEFAULT_FONT_SIZE
from dtk.ui.star_view import StarBuffer
from item_render import get_icon_pixbuf_path, render_star, STAR_SIZE, get_star_level
from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.iconview import IconView, IconItem
import gtk
from dtk.ui.draw import draw_text, draw_pixbuf, draw_vlinear
from events import global_event

class DownloadRankPage(gtk.VBox):
    '''
    class docs
    '''
	
    def __init__(self, data_manager):
        '''
        init docs
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.data_manager = data_manager
        
        self.tab_box = gtk.HBox()
        self.tab_box_align = gtk.Alignment()
        self.tab_box_align.set(1, 0, 0, 0)
        self.tab_box_align.set_padding(3, 9, 25, 48)
        for (tab_index, tab_name) in enumerate(["周排行Top25", "月排行Top25", "总排行Top25"]):
            self.tab_box.pack_start(RankTab(tab_index, tab_name, tab_index == 0), False, False)
            
        self.page_box = gtk.VBox()    
        self.page_align = gtk.Alignment()
        self.page_align.set(0.5, 0.5, 1, 1)
        self.page_align.set_padding(0, 0, 15, 15)
        
        self.week_rank_icon_view = IconView()
        self.week_rank_icon_view_scrlledwindow = ScrolledWindow()
        self.week_rank_icon_view.draw_mask = self.draw_mask
        
        self.month_rank_icon_view = IconView()
        self.month_rank_icon_view_scrlledwindow = ScrolledWindow()
        self.month_rank_icon_view.draw_mask = self.draw_mask
        
        self.all_rank_icon_view = IconView()
        self.all_rank_icon_view_scrlledwindow = ScrolledWindow()
        self.all_rank_icon_view.draw_mask = self.draw_mask
        
        (self.week_rank_infos, self.month_rank_infos, self.all_rank_infos) = self.data_manager.get_download_rank_info()
        for (rank_infos, icon_view) in [(self.week_rank_infos, self.week_rank_icon_view), 
                                        (self.month_rank_infos, self.month_rank_icon_view),
                                        (self.all_rank_infos, self.all_rank_icon_view)]:
            icon_view.add_items(map(lambda info: PkgIconItem(info), rank_infos))
        
        self.week_rank_icon_view_scrlledwindow.add_child(self.week_rank_icon_view)    
        self.month_rank_icon_view_scrlledwindow.add_child(self.month_rank_icon_view)    
        self.all_rank_icon_view_scrlledwindow.add_child(self.all_rank_icon_view)    
            
        self.tab_box_align.add(self.tab_box)
        self.page_align.add(self.week_rank_icon_view_scrlledwindow)
        self.page_box.pack_start(self.page_align)
        self.pack_start(self.tab_box_align, False, False)    
        self.pack_start(self.page_box, True, True)    
        
        global_event.register_event("update-rank-page", self.update_rank_page)
        
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
        
    def update_rank_page(self, page_index):
        container_remove_all(self.page_align)
        
        if page_index == 0:
            self.page_align.add(self.week_rank_icon_view_scrlledwindow)
        elif page_index == 1:
            self.page_align.add(self.month_rank_icon_view_scrlledwindow)
        else:
            self.page_align.add(self.all_rank_icon_view_scrlledwindow)
            
        self.show_all()    
        
gobject.type_register(DownloadRankPage)

class RankTab(gtk.Button):
    '''
    class docs
    '''
	
    def __init__(self, tab_index, tab_name, active_flag):
        '''
        init docs
        '''
        # Init.
        gtk.Button.__init__(self)
        self.tab_index = tab_index
        self.tab_name = tab_name
        self.tab_name_size = 10
        self.tab_padding_x = 10
        self.tab_padding_y = 0
        (self.tab_name_width, self.tab_name_height) = get_content_size(self.tab_name)
        self.tab_width = self.tab_name_width + self.tab_padding_x * 2
        self.tab_height = self.tab_name_height + self.tab_padding_y * 2
        self.active_flag = active_flag
        
        self.set_size_request(self.tab_width, self.tab_height)
        
        self.connect("expose-event", self.expose_rank_tab)
        self.connect("motion-notify-event", self.motion_rank_tab)
        self.connect("button-press-event", self.button_press_rank_tab)
        self.connect("leave-notify-event", self.leave_rank_tab)
        
        global_event.register_event("click-rank-tab", self.click_rank_tab)
        
    def click_rank_tab(self, tab_index):
        if self.tab_index != tab_index:
            self.active_flag = False
        elif not self.active_flag:
            self.active_flag = True
            
            global_event.emit("update-rank-page", self.tab_index)
        
    def expose_rank_tab(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        if self.active_flag:
            text_color = "#2C8BBA"
        else:
            if widget.state == gtk.STATE_NORMAL:
                text_color = "#333333"
            elif widget.state == gtk.STATE_PRELIGHT:
                text_color = "#2C8BBA"
            elif widget.state == gtk.STATE_ACTIVE:
                text_color = "#2C8BBA"
            
        draw_text(cr,
                  self.tab_name,
                  rect.x,
                  rect.y,
                  rect.width,
                  self.tab_height - 3,
                  text_size=self.tab_name_size,
                  text_color=text_color,
                  underline=not self.active_flag)    
        
        return True    

    def motion_rank_tab(self, widget, event):
        if not self.active_flag:
            set_cursor(widget, gtk.gdk.HAND2)
            
    def leave_rank_tab(self, widget, event):
        set_cursor(widget, None)
    
    def button_press_rank_tab(self, widget, event):
        global_event.emit("click-rank-tab", self.tab_index)
        
gobject.type_register(RankTab)

class PkgIconItem(IconItem):
    '''
    Icon item.
    '''
    
    ICON_PADDING_X = 42
    ICON_PADDING_TOP = 20
    
    BUTTON_PADDING_X = 44
    BUTTON_PADDING_BOTTOM = 18
    
    def __init__(self, (pkg_name, alias_name, star, desktop_info, is_installed)):
        '''
        Initialize ItemIcon class.
        
        @param pixbuf: Icon pixbuf.
        '''
        IconItem.__init__(self)
        self.pkg_name = pkg_name
        self.alias_name = alias_name
        self.desktop_info = desktop_info
        self.star_level = get_star_level(star)
        self.star_buffer = StarBuffer(self.star_level)
        self.is_installed = is_installed
        
        self.grade_star = 0
        
        self.icon_padding_y = 10
        self.name_padding_y = 20
        self.star_padding_y = 5
        self.width = 132
        self.height = 150
        
        self.icon_pixbuf = None
        self.hover_flag = False
        self.highlight_flag = False
        
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
        '''
        Render item.
        
        This is IconView interface, you should implement it.
        '''
        if self.icon_pixbuf == None:
            self.icon_pixbuf = gtk.gdk.pixbuf_new_from_file(get_icon_pixbuf_path(self.pkg_name))        
        
        draw_pixbuf(cr,
                    self.icon_pixbuf,
                    rect.x + self.ICON_PADDING_X,
                    rect.y + self.ICON_PADDING_TOP)
        
        draw_text(cr, 
                  self.alias_name,
                  rect.x,
                  rect.y + self.icon_padding_y + self.icon_pixbuf.get_height() + self.name_padding_y - 3,
                  rect.width,
                  DEFAULT_FONT_SIZE,
                  alignment=pango.ALIGN_CENTER)
        
        render_star(cr,
                    gtk.gdk.Rectangle(rect.x + (rect.width - STAR_SIZE * 5) / 2,
                                      rect.y + self.icon_padding_y + self.icon_pixbuf.get_height() + self.name_padding_y + DEFAULT_FONT_SIZE + self.star_padding_y,
                                      STAR_SIZE * 5,
                                      STAR_SIZE
                                      ),
                    self.star_buffer)
        
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
            rect.x + self.BUTTON_PADDING_X,
            rect.y + rect.height - self.BUTTON_PADDING_BOTTOM - pixbuf.get_height())
        
    def is_in_button_area(self, x, y):
        pixbuf = app_theme.get_pixbuf("button/start_small_normal.png").get_pixbuf()
        return is_in_rect((x, y),
                          (self.BUTTON_PADDING_X,
                           self.height - self.BUTTON_PADDING_BOTTOM - pixbuf.get_height(),
                           pixbuf.get_width(),
                           pixbuf.get_height()))
        
    def is_in_star_area(self, x, y):
        return is_in_rect((x, y),
                          ((self.width - STAR_SIZE * 5) / 2,
                           self.icon_padding_y + self.icon_pixbuf.get_height() + self.name_padding_y + DEFAULT_FONT_SIZE + self.star_padding_y,
                           STAR_SIZE * 5,
                           STAR_SIZE
                           ))
    
    def is_in_icon_area(self, x, y):
        return is_in_rect((x, y),
                          (self.ICON_PADDING_X,
                           self.ICON_PADDING_TOP,
                           self.icon_pixbuf.get_width(),
                           self.icon_pixbuf.get_height()))

    def is_in_name_area(self, x, y):
        (name_width, name_height) = get_content_size(self.alias_name, DEFAULT_FONT_SIZE)
        return is_in_rect((x, y),
                          (0,
                           self.icon_padding_y + self.icon_pixbuf.get_height() + self.name_padding_y,
                           name_width,
                           name_height))
        
    def icon_item_motion_notify(self, x, y):
        '''
        Handle `motion-notify-event` signal.
        
        This is IconView interface, you should implement it.
        '''
        self.hover_flag = True
        
        self.emit_redraw_request()
        
        if self.is_in_icon_area(x, y) or self.is_in_name_area(x, y):
            global_event.emit("set-cursor", gtk.gdk.HAND2)
        elif self.is_in_star_area(x, y):
            global_event.emit("set-cursor", gtk.gdk.HAND2)
            
            offset_x = x - (self.width - STAR_SIZE * 5) / 2
                
            times = offset_x / STAR_SIZE 
            self.grade_star = times * 2 + 2
                
            self.grade_star = min(self.grade_star, 10)    
            self.star_buffer.star_level = self.grade_star
            
            self.emit_redraw_request()
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
        pixbuf = app_theme.get_pixbuf("button/start_small_normal.png").get_pixbuf()
        popup_x = self.BUTTON_PADDING_X + pixbuf.get_width() / 2
        popup_y = self.height - self.BUTTON_PADDING_BOTTOM - pixbuf.get_height()
        return (offset_x, offset_y, popup_x, popup_y)
    
    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.
        
        This is IconView interface, you should implement it.
        '''
        if self.is_in_icon_area(x, y) and self.is_in_name_area(x, y):
            global_event.emit("switch-to-detail-page", self.pkg_name)
            global_event.emit("set-cursor", None)
        elif self.is_in_star_area(x, y):
            global_event.emit("grade-pkg", self.pkg_name, self.grade_star)
        elif self.is_in_button_area(x, y):
            if self.is_installed:
                global_event.emit("start-pkg", self.alias_name, self.desktop_info, self.get_offset_with_button(x, y))
            else:
                global_event.emit("install-pkg", [self.pkg_name])
                
            self.button_status = BUTTON_PRESS
            self.emit_redraw_request()
        else:
            global_event.emit("switch-to-detail-page", self.pkg_name)
    
    def icon_item_release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> del self.icon_pixbuf
        >>> self.icon_pixbuf = None

        This is IconView interface, you should implement it.
        
        @return: Return True if do release work, otherwise return False.
        
        When this function return True, IconView will call function gc.collect() to release object to release memory.
        '''
        if self.icon_pixbuf:
            del self.icon_pixbuf
            self.icon_pixbuf = None
            
        return True    
        
gobject.type_register(PkgIconItem)
