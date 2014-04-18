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
from constant import BUTTON_NORMAL, BUTTON_HOVER, BUTTON_PRESS
from dtk.ui.treeview import TreeView, TreeItem
from dtk.ui.progressbar import ProgressBuffer
from star_buffer import DscStarBuffer
from dtk.ui.utils import is_in_rect, get_content_size
from dtk.ui.draw import draw_pixbuf, draw_text, draw_vlinear
from item_render import (render_pkg_info, STAR_SIZE, get_star_level, get_icon_pixbuf_path,
                         ITEM_INFO_AREA_WIDTH, ITEM_CONFIRM_BUTTON_PADDING_RIGHT, ITEM_CANCEL_BUTTON_PADDING_RIGHT, ITEM_PADDING_X,
                         ITEM_STAR_AREA_WIDTH, ITEM_STATUS_TEXT_PADDING_RIGHT, NAME_SIZE, ITEM_PADDING_Y, ICON_SIZE, ITEM_PADDING_MIDDLE,
                         ITEM_BUTTON_AREA_WIDTH, ITEM_BUTTON_PADDING_RIGHT,
                         ITEM_HEIGHT, PROGRESSBAR_HEIGHT, ITEM_PKG_OFFSET_X
                         )
from skin import app_theme
from events import global_event
from constant import ACTION_UNINSTALL
from dtk.ui.entry import InputEntry
from dtk.ui.button import ImageButton
from dtk.ui.cycle_strip import CycleStrip
from dtk.ui.label import Label
from utils import handle_dbus_error, get_purg_flag
from nls import _

class MessageBar(CycleStrip):
    '''
    class docs
    '''
	
    def __init__(self, padding_left=0,):
        '''
        init docs
        '''
        # Init.
        CycleStrip.__init__(self, app_theme.get_pixbuf("strip/background.png"))
        
        self.label = Label()
        self.label_align = gtk.Alignment()
        self.label_align.set(0.0, 0.5, 0, 0)
        self.label_align.set_padding(0, 0, padding_left, 0)
        self.label_align.add(self.label)

        self.search_button = ImageButton(
            app_theme.get_pixbuf("entry/search_normal.png"),
            app_theme.get_pixbuf("entry/search_hover.png"),
            app_theme.get_pixbuf("entry/search_press.png"),
            )
        self.search_entry = InputEntry(action_button=self.search_button)
        self.search_entry.set_size(220, 24)
        entry_align = gtk.Alignment(0.5, 0.5, 0, 0)
        entry_align.set_padding(0, 0, 5, 5)
        entry_align.add(self.search_entry)

        self.pack_start(self.label_align, True, True)
        self.pack_start(entry_align, False, False)
        
    def set_message(self, message):
        self.label.set_text(message)

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

        self.search_flag = False
        self.uninstall_change_items = {"add": [], "delete": []}
        
        self.message_bar = MessageBar(32)
        self.message_bar.search_entry.entry.connect("changed", self.search_cb)
        self.message_bar.search_button.connect("clicked", self.search_cb)
        self.treeview = TreeView(enable_drag_drop=False)
        self.treeview.set_expand_column(0)

        top_hbox = gtk.HBox()
        top_hbox.pack_start(self.message_bar)

        self.pack_start(top_hbox, False, False)
        self.pack_start(self.treeview, True, True)
        
        self.treeview.connect("items-change", self.update_message_bar)
        
        self.fetch_uninstall_info()
        
        self.treeview.draw_mask = self.draw_mask

    def search_cb(self, widget, event=None):
        if not self.search_flag:
            self.cache_items = [item for item in self.treeview.visible_items]
        results = []
        keywords = self.message_bar.search_entry.get_text().strip()

        if keywords != "":
            self.search_flag = True
            # TODO: comment this search_query api, there are many problems for this api
            '''
            pkg_names = self.data_manager.search_query(map(lambda word: word.encode("utf8"), keywords.split(" ")))
            for item in self.cache_items:
                if item.pkg_name in pkg_names:
                    results.append(item)
            '''
            for item in self.cache_items:
                if keywords in item.pkg_name:
                    results.append(item)
            self.treeview.clear()
            self.treeview.add_items(results)
        else:
            self.treeview.clear()
            self.search_flag = False

            # for add items
            if self.uninstall_change_items["add"] != []:
                for item in self.uninstall_change_items["add"]:
                    self.cache_items.append(item)
                self.uninstall_change_items["add"] = []

            # for delete items
            if self.uninstall_change_items["delete"] != []:
                for item in self.uninstall_change_items["delete"]:
                    if item in self.cache_items:
                        self.cache_items.remove(item)
                self.uninstall_change_items["delete"] = []

            self.treeview.add_items(self.cache_items)

    def normal_search_cb(self, keywords):
        pass
        
    def update_message_bar(self, treeview):    
        self.message_bar.set_message(_("%s applications can be uninstalled") % len(treeview.visible_items))
        
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
        self.bus_interface.request_uninstall_pkgs(
                        reply_handler=self.render_uninstall_info,
                        error_handler=lambda e:handle_dbus_error("request_uninstall_pkgs", e))
    
    def render_uninstall_info(self, pkg_infos):
        self.add_uninstall_items(pkg_infos)
        
    def add_uninstall_items(self, pkg_infos):
        items = []
        for pkg_info in pkg_infos:
            (pkg_name, pkg_version) = eval(pkg_info)
            if self.data_manager.is_pkg_have_desktop_file(pkg_name) != None \
                and self.data_manager.is_pkg_display_in_uninstall_page(pkg_name):
                items.append(UninstallItem(pkg_name, pkg_version, self.data_manager))
            
        if self.search_flag:
            self.uninstall_change_items["add"] += items
        else:
            self.treeview.add_items(items)

    def delete_uninstall_items(self, items):
        if self.search_flag:
            self.uninstall_change_items["delete"] += items
            for item in items:
                if item in self.treeview.visible_items:
                    self.treeview.delete_items([item])
        else:
            self.treeview.delete_items(items)
        
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
        
        info = data_manager.get_item_pkg_info(self.pkg_name)
        self.alias_name = info[1]
        self.short_desc = info[2]
        self.star_level = get_star_level(5.0)
        self.star_buffer = DscStarBuffer(pkg_name)

        self.grade_star = 0
        
        button_pixbuf = app_theme.get_pixbuf("button/uninstall_normal.png").get_pixbuf()
        (self.button_width, self.button_height) = button_pixbuf.get_width(), button_pixbuf.get_height()
        self.button_status = BUTTON_NORMAL
        
        self.status = self.STATUS_NORMAL
        self.status_text = ""
        self.progress_buffer = ProgressBuffer()
        #self.action_wait()

    def render_pkg_info(self, cr, rect):
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        if self.icon_pixbuf == None:
            self.icon_pixbuf = gtk.gdk.pixbuf_new_from_file(get_icon_pixbuf_path(self.pkg_name))        
            
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
                rect.x + rect.width - 50,
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
        if column == 0:
            if self.is_in_icon_area(column, offset_x, offset_y):
                global_event.emit("set-cursor", gtk.gdk.HAND2)    
            elif self.is_in_name_area(column, offset_x, offset_y):
                global_event.emit("set-cursor", gtk.gdk.HAND2)    
            else:
                global_event.emit("set-cursor", None)
        else:
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
        if column == 0:
            if self.is_in_icon_area(column, offset_x, offset_y):
                global_event.emit("switch-to-detail-page", self.pkg_name)    
                global_event.emit("set-cursor", None)    
            elif self.is_in_name_area(column, offset_x, offset_y):
                global_event.emit("switch-to-detail-page", self.pkg_name)    
                global_event.emit("set-cursor", None)    
        else:
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
                    self.status_text = _("Waiting for uninstall")
                    
                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("uninstall-pkg", self.pkg_name, get_purg_flag())
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
    
    def is_in_name_area(self, column, offset_x, offset_y):
        (name_width, name_height) = get_content_size(self.alias_name, NAME_SIZE)
        return (column == 0
                and is_in_rect((offset_x, offset_y),
                               (ITEM_PADDING_X + ITEM_PKG_OFFSET_X + ICON_SIZE + ITEM_PADDING_MIDDLE,
                                ITEM_PADDING_Y,
                                name_width,
                                NAME_SIZE)))
    
    def is_in_icon_area(self, column, offset_x, offset_y):
        return (column == 0
                and self.icon_pixbuf != None
                and is_in_rect((offset_x, offset_y),
                               (ITEM_PADDING_X + ITEM_PKG_OFFSET_X,
                                ITEM_PADDING_Y,
                                self.icon_pixbuf.get_width(),
                                self.icon_pixbuf.get_height())))
    
    def action_wait(self):
        self.status = self.STATUS_WAIT_ACTION
        self.status_text = _("Waiting for uninstall")

        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def action_start(self):
        self.status = self.STATUS_IN_ACTION
        self.status_text = _("Uninstalling")
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
                
    def action_update(self, percent):
        self.progress_buffer.progress = percent
        self.status_text = _("Uninstalling")
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def action_finish(self):
        self.progress_buffer.progress = 100
        self.status_text = _("Uninstall successful")
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
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
        if self.icon_pixbuf:
            del self.icon_pixbuf
            self.icon_pixbuf = None

        return True    
    
gobject.type_register(UninstallItem)
