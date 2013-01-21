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

from skin import app_theme
from constant import BUTTON_NORMAL, BUTTON_HOVER, BUTTON_PRESS
from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.new_treeview import TreeView, TreeItem
from dtk.ui.iconview import IconView, IconItem
from deepin_utils.file import get_parent_dir
from dtk.ui.utils import container_remove_all, is_in_rect, get_content_size, cairo_state
from dtk.ui.draw import draw_pixbuf, draw_text, draw_vlinear
from events import global_event
import gtk
import gobject
import os

ALBUM_PICTURE_DIR = os.path.join(get_parent_dir(__file__, 2), "data", "current", "home", "album_picture", "zh_CN")

class AlbumPage(gtk.VBox):
    '''
    class docs
    '''
	
    def __init__(self, data_manager):
        '''
        init docs
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.in_detail_view = False
        self.data_manager = data_manager
        self.album_summary_view = AlbumSummaryView(data_manager)
        
        self.album_summary_align = gtk.Alignment()
        self.album_summary_align.set(0.5, 0.5, 1, 1)
        self.album_summary_align.set_padding(5, 0, 0, 10)
        
        self.album_detail_align = gtk.Alignment()
        self.album_detail_align.set(0.5, 0.5, 1, 1)
        self.album_detail_align.set_padding(10, 0, 0, 10)
        
        self.switch_to_album_summary_view()
        
        global_event.register_event("switch-to-album-detail-view", self.switch_to_album_detail_view)
        
    def switch_to_album_summary_view(self):
        self.in_detail_view = False
        
        container_remove_all(self)
        container_remove_all(self.album_summary_align)
        self.album_summary_align.add(self.album_summary_view)
        
        self.pack_start(self.album_summary_align, True, True)
        
        self.show_all()
        
    def switch_to_album_detail_view(self, album_id):
        self.in_detail_view = True
        
        container_remove_all(self)
        container_remove_all(self.album_detail_align)
        self.album_detail_align.add(AlbumDetailPage(self.data_manager, album_id))
        
        self.pack_start(self.album_detail_align, True, True)
        
        self.show_all()
        
gobject.type_register(AlbumPage)

class AlbumSummaryView(gtk.VBox):
    '''
    class docs
    '''
	
    def __init__(self, data_manager):
        '''
        init docs
        '''
        gtk.VBox.__init__(self)
        self.scrolled_window = ScrolledWindow()
        self.data_manager = data_manager
        
        self.iconview = IconView()
        self.iconview.draw_mask = self.draw_mask
        
        items = []
        for album_info in self.data_manager.get_album_info():
            items.append(AlbumSummaryItem(album_info))
        self.iconview.add_items(items)    
        
        self.scrolled_window.add_child(self.iconview)
        self.pack_start(self.scrolled_window, True, True)
        
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
        
gobject.type_register(AlbumSummaryView)

class AlbumSummaryItem(IconItem):
    '''
    Icon item.
    '''
    
    PICTURE_PADDING_X = 10
    PICTURE_PADDING_Y = 15
    
    TITLE_PADDING_LEFT = 20
    TITLE_PADDING_RIGHT = 10
    TITLE_SIZE = 11
    
    SUMMARY_PADDING_Y = 5
    SUMMARY_SIZE = 10
	
    def __init__(self, (album_id, album_name, album_summary)):
        '''
        Initialize ItemIcon class.
        
        @param pixbuf: Icon pixbuf.
        '''
        gobject.GObject.__init__(self)
        self.album_id = album_id
        self.album_name = album_name
        self.album_summary = album_summary
        self.pixbuf = None
        self.hover_flag = False
        self.highlight_flag = False
        
    def get_width(self):
        '''
        Get item width.
        
        This is IconView interface, you should implement it.
        '''
        return 355
        
    def get_height(self):
        '''
        Get item height.
        
        This is IconView interface, you should implement it.
        '''
        return 110
    
    def render(self, cr, rect):
        '''
        Render item.
        
        This is IconView interface, you should implement it.
        '''
        # Draw album picture.
        if self.pixbuf == None:
            self.pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(ALBUM_PICTURE_DIR, "%s.jpg" % self.album_id))
            
        draw_pixbuf(cr,
                    self.pixbuf,
                    rect.x + self.PICTURE_PADDING_X,
                    rect.y + self.PICTURE_PADDING_Y,
                    )    
        
        # Draw album title.
        text_width = rect.width - self.PICTURE_PADDING_X - self.pixbuf.get_width() - self.TITLE_PADDING_LEFT - self.TITLE_PADDING_RIGHT
        draw_text(cr,
                  self.album_name,
                  rect.x + self.PICTURE_PADDING_X + self.pixbuf.get_width() + self.TITLE_PADDING_LEFT,
                  rect.y + self.PICTURE_PADDING_Y,
                  text_width,
                  self.TITLE_SIZE,
                  text_size=self.TITLE_SIZE,
                  text_color="#00AAFF",
                  )
        
        # Draw album summary.
        text_height = rect.height - self.PICTURE_PADDING_Y * 2 - self.TITLE_SIZE - self.SUMMARY_PADDING_Y - 12
        with cairo_state(cr):
            draw_x = rect.x + self.PICTURE_PADDING_X + self.pixbuf.get_width() + self.TITLE_PADDING_LEFT
            draw_y = rect.y + self.PICTURE_PADDING_Y * 2 + self.TITLE_SIZE
            cr.rectangle(draw_x,
                         draw_y,
                         text_width,
                         text_height)
            
            cr.clip()
            
            draw_text(cr,
                      self.album_summary,
                      draw_x,
                      draw_y,
                      text_width,
                      text_height,
                      text_size=self.SUMMARY_SIZE,
                      wrap_width=text_width
                      )
        
    def icon_item_button_press(self, x, y):
        '''
        Handle button-press event.
        
        This is IconView interface, you should implement it.
        '''
        global_event.emit("switch-to-album-detail-view", self.album_id)
    
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
        if self.pixbuf:
            del self.pixbuf
            self.pixbuf = None
        
        return True
        
gobject.type_register(AlbumSummaryItem)

class AlbumDetailPage(gtk.VBox):
    '''
    class docs
    '''
	
    def __init__(self, data_manager, album_id):
        '''
        init docs
        '''
        gtk.VBox.__init__(self)
        self.treeview = TreeView(
            enable_drag_drop=False)
        
        items = []
        for (pkg_name, pkg_title, pkg_summary, alias_name, desktop_info, is_installed) in data_manager.get_album_detail_info(album_id):
            items.append(AlbumDetailItem(pkg_name, pkg_title, pkg_summary, alias_name, desktop_info, is_installed))
        self.treeview.add_items(items)    
        self.treeview.draw_mask = self.draw_mask
                
        self.pack_start(self.treeview, True, True)
        
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
        
gobject.type_register(AlbumDetailPage)

class AlbumDetailItem(TreeItem):
    '''
    class docs
    '''
    
    PICTURE_PADDING_X = 10
    PICTURE_PADDING_Y = 15
    
    TITLE_PADDING_LEFT = 20
    TITLE_SIZE = 11
    
    SUMMARY_PADDING_Y = 5
    SUMMARY_SIZE = 10
    
    SUMMARY_WIDTH = 440
    
    BUTTON_PADDING_X = 30
	
    def __init__(self, pkg_name, pkg_title, pkg_summary, alias_name, desktop_info, is_installed):
        '''
        init docs
        '''
        TreeItem.__init__(self)
        self.pkg_name = pkg_name
        self.pkg_title = pkg_title
        self.pkg_summary = pkg_summary
        self.alias_name = alias_name
        self.desktop_info = desktop_info
        self.is_installed = is_installed
        self.pixbuf = None
        
        self.height = 100
        
        self.button_status = BUTTON_NORMAL
        
    def render_pkg_picture(self, cr, rect):
        if self.pixbuf == None:
            self.pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(ALBUM_PICTURE_DIR, "%s.jpg" % self.pkg_name))
            
        draw_pixbuf(cr,
                    self.pixbuf,
                    rect.x + self.PICTURE_PADDING_X,
                    rect.y + self.PICTURE_PADDING_Y)
    
    def render_pkg_summary(self, cr, rect):
        # Draw album title.
        text_width = self.SUMMARY_WIDTH
        draw_text(cr,
                  self.pkg_title,
                  rect.x,
                  rect.y + self.PICTURE_PADDING_Y,
                  text_width,
                  self.TITLE_SIZE,
                  text_size=self.TITLE_SIZE,
                  text_color="#00AAFF",
                  )
    
        # Draw album summary.
        text_height = rect.height - self.PICTURE_PADDING_Y - self.TITLE_SIZE - self.SUMMARY_PADDING_Y
        draw_text(cr,
                  self.pkg_summary,
                  rect.x,
                  rect.y + self.PICTURE_PADDING_Y + self.TITLE_SIZE,
                  text_width,
                  text_height,
                  text_size=self.SUMMARY_SIZE,
                  wrap_width=text_width
                  )
        
    def render_pkg_action(self, cr, rect):
        # Render button.
        if self.is_installed:
            name = "button/start"
        else:
            name = "button/install"
        
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
            rect.y + (rect.height - pixbuf.get_height()) / 2)
        
    def is_in_button_area(self, column, offset_x, offset_y):
        pixbuf = app_theme.get_pixbuf("button/start_normal.png").get_pixbuf()
        return (column == 2
                and is_in_rect((offset_x, offset_y),
                               (self.BUTTON_PADDING_X,
                                (self.height - pixbuf.get_height()) / 2,
                                pixbuf.get_width(),
                                pixbuf.get_height()
                                )))
    
    def is_in_picture_area(self, column, offset_x, offset_y):
        return (column == 0
                and is_in_rect((offset_x, offset_y),
                               (self.PICTURE_PADDING_X, 
                                self.PICTURE_PADDING_Y,
                                self.pixbuf.get_width(),
                                self.pixbuf.get_height())))
    
    def is_in_name_area(self, column, offset_x, offset_y):
        (name_with, name_height) = get_content_size(self.pkg_title, self.TITLE_SIZE)
        return (column == 1
                and is_in_rect((offset_x, offset_y),
                               (0,
                                self.PICTURE_PADDING_Y,
                                name_with,
                                name_height)))
        
    def motion_notify(self, column, offset_x, offset_y):
        if column == 0:
            if self.is_in_picture_area(column, offset_x, offset_y):
                global_event.emit("set-cursor", gtk.gdk.HAND2)    
            else:
                global_event.emit("set-cursor", None)    
        elif column == 1:
            if self.is_in_name_area(column, offset_x, offset_y):
                global_event.emit("set-cursor", gtk.gdk.HAND2)    
            else:
                global_event.emit("set-cursor", None)    
        else:
            global_event.emit("set-cursor", None)
                
            if self.is_in_button_area(column, offset_x, offset_y):
                self.button_status = BUTTON_HOVER
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self, True)
            else:
                self.button_status = BUTTON_NORMAL
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self, True)
            
    def get_offset_with_button(self, offset_x, offset_y):
        pixbuf = app_theme.get_pixbuf("button/start_normal.png").get_pixbuf()
        popup_x = self.BUTTON_PADDING_X
        popup_y = (self.height - pixbuf.get_height()) / 2
        return (offset_x, offset_y, popup_x, popup_y)
    
    def button_press(self, column, offset_x, offset_y):
        if column == 0:
            if self.is_in_picture_area(column, offset_x, offset_y):
                global_event.emit("switch-to-detail-page", self.pkg_name)
                global_event.emit("set-cursor", None)
        elif column == 1:
            if self.is_in_name_area(column, offset_x, offset_y):
                global_event.emit("switch-to-detail-page", self.pkg_name)
                global_event.emit("set-cursor", gtk.gdk.HAND2)    
        else:        
            if self.is_in_button_area(column, offset_x, offset_y):
                if self.is_installed:
                    global_event.emit("start-pkg", self.alias_name, self.desktop_info, self.get_offset_with_button(offset_x, offset_y))
                else:
                    global_event.emit("install-pkg", [self.pkg_name])
                    
                self.button_status = BUTTON_PRESS
                    
                if self.redraw_request_callback:
                    self.redraw_request_callback(self, True)
                
    def button_release(self, column, offset_x, offset_y):
        if self.is_in_button_area(column, offset_x, offset_y):
            if self.button_status != BUTTON_HOVER:
                self.button_status = BUTTON_HOVER
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self, True)
        else:
            if self.button_status != BUTTON_NORMAL:
                self.button_status = BUTTON_NORMAL
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self, True)
    
    def get_height(self):
        return self.height
    
    def get_column_widths(self):
        return [160, -1, 110]
    
    def get_column_renders(self):
        return [self.render_pkg_picture,
                self.render_pkg_summary,
                self.render_pkg_action]
    
    def unselect(self):
        pass
    
    def select(self):
        pass
    
    def unhover(self, column, offset_x, offset_y):
        pass
    
    def hover(self, column, offset_x, offset_y):
        pass
    
    def single_click(self, column, offset_x, offset_y):
        pass        

    def double_click(self, column, offset_x, offset_y):
        pass        
    
    def release_resource(self):
        '''
        Release item resource.

        If you have pixbuf in item, you should release memory resource like below code:

        >>> if self.pixbuf:
        >>>     del self.pixbuf
        >>>     self.pixbuf = None
        >>>
        >>> return True

        This is TreeView interface, you should implement it.
        
        @return: Return True if do release work, otherwise return False.
        
        When this function return True, TreeView will call function gc.collect() to release object to release memory.
        '''
        if self.pixbuf:
            del self.pixbuf
            self.pixbuf = None

        return True    
    
gobject.type_register(AlbumDetailItem)        
