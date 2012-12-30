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

import gtk
import gobject
from constant import VIEW_PADDING_X, VIEW_PADDING_Y, BUTTON_NORMAL, BUTTON_HOVER, BUTTON_PRESS
from dtk.ui.new_treeview import TreeView, TreeItem
from dtk.ui.progressbar import ProgressBuffer
from dtk.ui.threads import post_gui, AnonymityThread
from dtk.ui.star_view import StarBuffer
from dtk.ui.utils import is_in_rect
from dtk.ui.draw import draw_pixbuf, draw_text, draw_vlinear
from item_render import (render_pkg_info, STAR_SIZE, get_star_level, 
                         ITEM_INFO_AREA_WIDTH, ITEM_CONFIRM_BUTTON_PADDING_RIGHT, ITEM_CANCEL_BUTTON_PADDING_RIGHT,
                         ITEM_STAR_AREA_WIDTH, ITEM_STATUS_TEXT_PADDING_RIGHT,
                         ITEM_BUTTON_AREA_WIDTH, ITEM_BUTTON_PADDING_RIGHT,
                         ITEM_HEIGHT, PROGRESSBAR_HEIGHT, ITEM_PKG_OFFSET_X
                         )
from skin import app_theme
from events import global_event
from constant import ACTION_UNINSTALL
from dtk.ui.cycle_strip import CycleStrip

class UninstallPage(gtk.VBox):
    '''
    class docs
    '''
	
    def __init__(self, bus_interface, data_manager):
        '''
        init docs
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.bus_interface = bus_interface        
        self.data_manager = data_manager
        
        self.cycle_strip = CycleStrip(app_theme.get_pixbuf("strip/background.png"))
        self.treeview = TreeView(enable_drag_drop=False)
        self.pack_start(self.cycle_strip,False, False)
        self.pack_start(self.treeview, True, True)
        
        self.fetch_uninstall_info()
        
        self.treeview.draw_mask = self.draw_mask    
        
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
        
    def update_action_status(self, pkg_infos):
        pkg_items = []
        for (pkg_name, action_status) in pkg_infos:
            pkg_item = None
            for item in self.treeview.visible_items:
                if item.pkg_name == pkg_name:
                    pkg_item = item
                    break

            if pkg_item == None:
                pkg_item = UninstallItem(pkg_name, self.bus_interface.request_pkgs_uninstall_version([pkg_name])[0], self.data_manager)
                
            if action_status == "wait":
                pkg_item.action_wait()
            elif action_status == "start":
                pkg_item.action_start()
            elif action_status == "update":
                pkg_item.action_update(0)
            pkg_items.append(pkg_item)
                
        pkg_items = filter(lambda item: item not in self.treeview.visible_items, pkg_items)
        self.treeview.add_items(pkg_items)        
        
    def fetch_uninstall_info(self):
        AnonymityThread(lambda : self.bus_interface.request_uninstall_pkgs(),
                        self.render_uninstall_info).run()
    
    @post_gui
    def render_uninstall_info(self, pkg_infos):
        self.add_uninstall_items(pkg_infos)
        
    def add_uninstall_items(self, pkg_infos):
        items = []
        for pkg_info in pkg_infos:
            (pkg_name, pkg_version) = eval(pkg_info)
            if self.data_manager.is_pkg_have_desktop_file(pkg_name) != None:
                items.append(UninstallItem(pkg_name, pkg_version, self.data_manager))
            
        self.treeview.add_items(items)    
        
    def action_start(self, pkg_name):
        for item in self.treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.action_start()
                break
    
    def action_update(self, pkg_name, percent):
        for item in self.treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.action_update(percent)
                break
    
    def action_finish(self, pkg_name, pkg_info_list):
        for item in self.treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.action_finish()
                
                global_event.emit("request-clear-action-pages", pkg_info_list)
                break
            
gobject.type_register(UninstallPage)

class UninstallItem(TreeItem):
    '''
    class docs
    '''
    
    STATUS_NORMAL = 1
    STATUS_CONFIRM = 2
    STATUS_WAIT_ACTION = 3
    STATUS_IN_ACTION = 4
    
    STATUS_PADDING_X = 15
	
    def __init__(self, pkg_name, pkg_version, data_manager):
        '''
        init docs
        '''
        TreeItem.__init__(self)
        self.pkg_name = pkg_name
        self.pkg_version = pkg_version
        self.data_manager = data_manager
        self.icon_pixbuf = None
        
        (self.short_desc, star, self.alias_name) = data_manager.get_item_pkg_info(self.pkg_name)
        self.star_level = get_star_level(star)
        self.star_buffer = StarBuffer(self.star_level)

        self.grade_star = 0
        
        button_pixbuf = app_theme.get_pixbuf("button/uninstall_normal.png").get_pixbuf()
        (self.button_width, self.button_height) = button_pixbuf.get_width(), button_pixbuf.get_height()
        self.button_status = BUTTON_NORMAL
        
        self.status = self.STATUS_NORMAL
        self.status_text = ""
        self.progress_buffer = ProgressBuffer()
        
    def render_pkg_info(self, cr, rect):
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        render_pkg_info(cr, rect, self.alias_name, self.pkg_name, self.icon_pixbuf, self.pkg_version, self.short_desc, ITEM_PKG_OFFSET_X)
        
    def render_pkg_status(self, cr, rect):
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        if self.status == self.STATUS_CONFIRM:
            # Draw star.
            self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))
            
            confirm_pixbuf = app_theme.get_pixbuf("button/uninstall_confirm.png").get_pixbuf()
            cancel_pixbuf = app_theme.get_pixbuf("button/uninstall_cancel.png").get_pixbuf()
            
            draw_pixbuf(
                cr,
                confirm_pixbuf,
                rect.x + rect.width - ITEM_CONFIRM_BUTTON_PADDING_RIGHT,
                rect.y + (ITEM_HEIGHT - confirm_pixbuf.get_height()) / 2,
                )

            draw_pixbuf(
                cr,
                cancel_pixbuf,
                rect.x + rect.width - ITEM_CANCEL_BUTTON_PADDING_RIGHT,
                rect.y + (ITEM_HEIGHT - cancel_pixbuf.get_height()) / 2,
                )
        elif self.status == self.STATUS_IN_ACTION:
            self.progress_buffer.render(
                cr, 
                gtk.gdk.Rectangle(
                    rect.x, 
                    rect.y + (ITEM_HEIGHT - PROGRESSBAR_HEIGHT) / 2, 
                    ITEM_STAR_AREA_WIDTH, 
                    PROGRESSBAR_HEIGHT))
            
            draw_text(
                cr,
                self.status_text,
                rect.x + rect.width - ITEM_STATUS_TEXT_PADDING_RIGHT,
                rect.y,
                rect.width - ITEM_STAR_AREA_WIDTH,
                ITEM_HEIGHT,
                )
        elif self.status == self.STATUS_WAIT_ACTION:
            # Draw star.
            self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))
            
            draw_text(
                cr,
                self.status_text,
                rect.x + rect.width - ITEM_STATUS_TEXT_PADDING_RIGHT,
                rect.y,
                rect.width - ITEM_STAR_AREA_WIDTH,
                ITEM_HEIGHT,
                )
            
            cancel_pixbuf = app_theme.get_pixbuf("button/uninstall_cancel.png").get_pixbuf()
            
            draw_pixbuf(
                cr,
                cancel_pixbuf,
                rect.x + rect.width - ITEM_CANCEL_BUTTON_PADDING_RIGHT,
                rect.y + (ITEM_HEIGHT - cancel_pixbuf.get_height()) / 2,
                )
        elif self.status == self.STATUS_NORMAL:
            # Draw star.
            self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))
            
            # Draw button.
            if self.button_status == BUTTON_NORMAL:
                pixbuf = app_theme.get_pixbuf("button/uninstall_normal.png").get_pixbuf()
            elif self.button_status == BUTTON_HOVER:
                pixbuf = app_theme.get_pixbuf("button/uninstall_hover.png").get_pixbuf()
            elif self.button_status == BUTTON_PRESS:
                pixbuf = app_theme.get_pixbuf("button/uninstall_press.png").get_pixbuf()
            draw_pixbuf(
                cr,
                pixbuf,
                rect.x + rect.width - ITEM_BUTTON_PADDING_RIGHT - pixbuf.get_width(),
                rect.y + (ITEM_HEIGHT - self.button_height) / 2,
                )
        
    def get_height(self):
        return ITEM_HEIGHT
    
    def get_column_widths(self):
        return [ITEM_INFO_AREA_WIDTH,
                ITEM_STAR_AREA_WIDTH + ITEM_BUTTON_AREA_WIDTH]
    
    def get_column_renders(self):
        return [self.render_pkg_info,
                self.render_pkg_status]
    
    def unselect(self):
        pass
    
    def select(self):
        pass
    
    def unhover(self, column, offset_x, offset_y):
        pass

    def hover(self, column, offset_x, offset_y):
        pass
    
    def motion_notify(self, column, offset_x, offset_y):
        if self.status == self.STATUS_NORMAL:
            if self.is_in_button_area(column, offset_x, offset_y):
                self.button_status = BUTTON_HOVER
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self)
            elif self.button_status != BUTTON_NORMAL:
                self.button_status = BUTTON_NORMAL
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self)
    
            if self.is_in_star_area(column, offset_x, offset_y):
                global_event.emit("set-cursor", gtk.gdk.HAND2)
                
                times = offset_x / STAR_SIZE 
                self.grade_star = times * 2 + 2
                    
                self.grade_star = min(self.grade_star, 10)    
                self.star_buffer.star_level = self.grade_star
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self)
            else:
                global_event.emit("set-cursor", None)
                
                if self.star_buffer.star_level != self.star_level:
                    self.star_buffer.star_level = self.star_level
                    
                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                    
    def button_press(self, column, offset_x, offset_y):
        if self.status == self.STATUS_NORMAL:
            if self.is_in_button_area(column, offset_x, offset_y):
                self.status = self.STATUS_CONFIRM
            
                if self.redraw_request_callback:
                    self.redraw_request_callback(self)            
            elif self.is_in_star_area(column, offset_x, offset_y):
                global_event.emit("grade-pkg", self.pkg_name, self.grade_star)
        elif self.status == self.STATUS_CONFIRM:
            if self.is_confirm_button_area(column, offset_x, offset_y):
                self.status = self.STATUS_WAIT_ACTION
                self.status_text = "等待卸载"
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self)
                    
                global_event.emit("uninstall-pkg", [self.pkg_name])
            elif self.is_cancel_button_area(column, offset_x, offset_y):
                self.status = self.STATUS_NORMAL
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self)
        elif self.status == self.STATUS_WAIT_ACTION:
            if self.is_cancel_button_area(column, offset_x, offset_y):
                self.status = self.STATUS_NORMAL
                
                global_event.emit("remove-wait-action", [(str((self.pkg_name, ACTION_UNINSTALL)))])
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self)
                
    def button_release(self, column, offset_x, offset_y):
        pass
                    
    def single_click(self, column, offset_x, offset_y):
        pass        

    def double_click(self, column, offset_x, offset_y):
        pass        
    
    def is_in_star_area(self, column, offset_x, offset_y):
        return (column == 1 
                and is_in_rect((offset_x, offset_y), 
                               (0,
                                (ITEM_HEIGHT - STAR_SIZE) / 2,
                                ITEM_STAR_AREA_WIDTH,
                                STAR_SIZE)))
    
    def is_in_button_area(self, column, offset_x, offset_y):
        return (column == 1
                and is_in_rect((offset_x, offset_y), 
                               (self.get_column_widths()[column] - ITEM_BUTTON_PADDING_RIGHT - self.button_width,
                                (ITEM_HEIGHT - self.button_height) / 2,
                                self.button_width,
                                self.button_height)))
    
    def is_confirm_button_area(self, column, offset_x, offset_y):
        confirm_pixbuf = app_theme.get_pixbuf("button/uninstall_confirm.png").get_pixbuf()
        return (column == 1
                and is_in_rect((offset_x, offset_y),
                               (self.get_column_widths()[column] - ITEM_CONFIRM_BUTTON_PADDING_RIGHT,
                                (ITEM_HEIGHT - confirm_pixbuf.get_height()) / 2,
                                confirm_pixbuf.get_width(),
                                confirm_pixbuf.get_height())))

    def is_cancel_button_area(self, column, offset_x, offset_y):
        cancel_pixbuf = app_theme.get_pixbuf("button/uninstall_cancel.png").get_pixbuf()
        return (column == 1
                and is_in_rect((offset_x, offset_y),
                               (self.get_column_widths()[column] - ITEM_CANCEL_BUTTON_PADDING_RIGHT,
                                (ITEM_HEIGHT - cancel_pixbuf.get_height()) / 2,
                                cancel_pixbuf.get_width(),
                                cancel_pixbuf.get_height())))
    
    def action_wait(self):
        self.status = self.STATUS_WAIT_ACTION
        self.status_text = "等待卸载"

        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def action_start(self):
        self.status = self.STATUS_IN_ACTION
        self.status_text = "卸载中"
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
                
    def action_update(self, percent):
        self.progress_buffer.progress = percent
        self.status_text = "卸载中"
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def action_finish(self):
        self.progress_buffer.progress = 100
        self.status_text = "卸载完成"
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
gobject.type_register(UninstallItem)        
