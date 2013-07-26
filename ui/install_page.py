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
import os
import gtk
import gobject
from constant import BUTTON_NORMAL, BUTTON_HOVER, BUTTON_PRESS
from deepin_utils.file import format_file_size
from dtk.ui.utils import is_in_rect, get_content_size, container_remove_all
from dtk.ui.treeview import TreeView, TreeItem
from star_buffer import DscStarBuffer
from dtk.ui.draw import draw_text, draw_pixbuf, draw_vlinear
from dtk.ui.progressbar import ProgressBuffer
from events import global_event
from skin import app_theme
from item_render import (render_pkg_info, STAR_SIZE, get_star_level, get_icon_pixbuf_path, ITEM_BUTTON_PADDING_RIGHT,
                         ITEM_INFO_AREA_WIDTH, ITEM_CANCEL_BUTTON_PADDING_RIGHT, ITEM_PADDING_X, ICON_SIZE, ITEM_PADDING_MIDDLE, ITEM_PADDING_Y, NAME_SIZE,
                         ITEM_STAR_AREA_WIDTH, ITEM_STATUS_TEXT_PADDING_RIGHT,
                         ITEM_BUTTON_AREA_WIDTH, 
                         ITEM_HEIGHT, ITEM_PKG_OFFSET_X,
                         PROGRESSBAR_HEIGHT
                         )
from constant import ACTION_INSTALL, cute_info_dir
from message_bar import MessageBar
from nls import _

class InstallPage(gtk.VBox):
    '''
    class docs
    '''
	
    STATUS_INSTALL_FINISH = 7
    
    def __init__(self, bus_interface, data_manager):
        '''
        init docs
        '''
        # Init.
        gtk.VBox.__init__(self)
        self.bus_interface = bus_interface
        self.data_manager = data_manager

        self.message_bar = MessageBar(32)
        self.message_box = gtk.HBox()
        
        self.treeview = TreeView(enable_drag_drop=False)
        self.treeview.set_expand_column(0)
        self.cute_message_image = gtk.VBox()
        self.content_box = gtk.VBox()
        
        self.pack_start(self.message_box, False, False)
        self.pack_start(self.content_box, True, True)
        
        self.cute_message_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(cute_info_dir, "no_download.png"))
        self.content_box.pack_start(self.cute_message_image, True, True)
        
        self.treeview.draw_mask = self.draw_mask
        
        self.cute_message_image.connect("expose-event", self.expose_cute_message_image)
        self.treeview.connect("items-change", self.update_message_bar)
        self.treeview.connect("items-change", lambda treeview: global_event.emit("update-install-notify-number", self.get_installing_pkgs_number()))
        
    def expose_cute_message_image(self, widget, event):
        if self.cute_message_pixbuf:
            cr = widget.window.cairo_create()
            rect = widget.allocation
            
            cr.set_source_rgb(1, 1, 1)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
            
            draw_pixbuf(
                cr,
                self.cute_message_pixbuf,
                rect.x + (rect.width - self.cute_message_pixbuf.get_width()) / 2,
                rect.y + (rect.height - self.cute_message_pixbuf.get_height()) / 2,
                )
            
    def update_install_status(self):
        global_event.emit("update-install-notify-number", self.get_installing_pkgs_number())
        self.update_message_bar(self.treeview)
            
    def get_installing_pkgs_number(self):
        return len(filter(lambda item: item.status != self.STATUS_INSTALL_FINISH, self.treeview.visible_items))

    def get_installed_pkgs_number(self):
        return len(filter(lambda item: item.status == self.STATUS_INSTALL_FINISH, self.treeview.visible_items))
        
    def delete_item_match_pkgname(self, pkg_name):
        for install_item in self.treeview.visible_items:
            if install_item.pkg_name == pkg_name:
                self.treeview.delete_items([install_item])
                break
    
    def update_message_bar(self, treeview):
        if self.get_installing_pkgs_number() == 0:
            if self.get_installed_pkgs_number() == 0:
                container_remove_all(self.message_box)
                
                children = self.content_box.get_children()
                if len(children) == 0 or children[0] == self.treeview:
                    if self.cute_message_pixbuf == None:
                        self.cute_message_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(cute_info_dir, "no_download.png"))
                    
                    container_remove_all(self.content_box)
                    self.content_box.pack_start(self.cute_message_image, True, True)
                    
                    self.show_all()
            else:
                self.message_bar.set_message("")
        else:
            container_remove_all(self.message_box)
            self.message_box.pack_start(self.message_bar, True, True)
            self.message_bar.set_message(_("%s applications are being installed") % self.get_installing_pkgs_number())
            
            children = self.content_box.get_children()
            if len(children) == 0 or children[0] == self.cute_message_image:
                if self.cute_message_pixbuf:
                    del self.cute_message_pixbuf
                    self.cute_message_pixbuf = None
                
                container_remove_all(self.content_box)
                self.content_box.pack_start(self.treeview, True, True)
                
                self.show_all()
        
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
        
    def update_download_status(self, pkg_infos):
        pkg_items = []
        for (pkg_name, download_status) in pkg_infos:
            pkg_item = None
            for item in self.treeview.visible_items:
                if item.pkg_name == pkg_name:
                    pkg_item = item
                    break

            if pkg_item == None:
                pkg_item = InstallItem(pkg_name, self.bus_interface.request_pkgs_install_version([pkg_name])[0], self.data_manager)
                
            if download_status == "wait":
                pkg_item.download_wait()
            elif download_status == "start":
                pkg_item.download_start()
            elif download_status == "update":
                pkg_item.download_update(0, 0)
            pkg_items.append(pkg_item)
                
        pkg_items = filter(lambda item: item not in self.treeview.visible_items, pkg_items)
        self.treeview.add_items(pkg_items)        
    
    def update_action_status(self, pkg_infos):
        pkg_items = []
        for (pkg_name, action_status) in pkg_infos:
            pkg_item = None
            for item in self.treeview.visible_items:
                if item.pkg_name == pkg_name:
                    pkg_item = item
                    break

            if pkg_item == None:
                pkg_item = InstallItem(pkg_name, self.bus_interface.request_pkgs_install_version([pkg_name])[0], self.data_manager)
                
            if action_status == "wait":
                pkg_item.download_finish()
            elif action_status == "start":
                pkg_item.action_start()
            elif action_status == "update":
                pkg_item.action_update(0)
            pkg_items.append(pkg_item)
                
        pkg_items = filter(lambda item: item not in self.treeview.visible_items, pkg_items)
        self.treeview.add_items(pkg_items)        
        
    def add_install_actions(self, pkg_names):
        for pkg_name in pkg_names:
            self.get_action_item(pkg_name)
    
    def get_action_item(self, pkg_name):
        action_item = None
        for item in self.treeview.visible_items:
            if item.pkg_name == pkg_name:
                action_item = item
                break
        
        if action_item == None:
            action_item = InstallItem(pkg_name, self.bus_interface.request_pkgs_install_version([pkg_name])[0], self.data_manager)
            self.treeview.add_items([action_item])

        return action_item    
        
    def download_ready(self, pkg_name):
        self.get_action_item(pkg_name).download_ready()

    def download_wait(self, pkg_name):
        self.get_action_item(pkg_name).download_wait()

    def download_start(self, pkg_name):
        self.get_action_item(pkg_name).download_start()

    def download_update(self, pkg_name, percent, speed):
        for item in self.treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.download_update(percent, speed)
                break
        
    def download_finish(self, pkg_name):
        for item in self.treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.download_finish()
                break

    def download_stop(self, pkg_name):
        pass
    
    def download_parse_failed(self, pkg_name):
        for item in self.treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.download_parse_failed()
                break
            
    def action_start(self, pkg_name):
        self.get_action_item(pkg_name).action_start()

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
            
gobject.type_register(InstallPage)

class InstallItem(TreeItem):
    '''
    class docs
    '''
    
    STATUS_WAIT_DOWNLOAD = 1
    STATUS_IN_DOWNLOAD = 2
    STATUS_STOP_DOWNLOAD = 3
    STATUS_WAIT_INSTALL = 4
    STATUS_STOP_WAIT_INSTALL = 5 
    STATUS_IN_INSTALL = 6
    STATUS_INSTALL_FINISH = 7
    STATUS_PARSE_DOWNLOAD_FAILED = 8
    STATUS_READY_DOWNLOAD= 9
	
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
        self.star_buffer = DscStarBuffer(pkg_name)
        
        self.grade_star = 0
        
        self.status = self.STATUS_READY_DOWNLOAD
        self.status_text = _("Analyzing dependencies")
        self.progress_buffer = ProgressBuffer()
        
        button_pixbuf = app_theme.get_pixbuf("button/start_normal.png").get_pixbuf()
        (self.button_width, self.button_height) = button_pixbuf.get_width(), button_pixbuf.get_height()
        self.button_status = BUTTON_NORMAL
        
        self.is_have_desktop_file = False
        
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
        
        if self.status == self.STATUS_READY_DOWNLOAD:
            draw_text(
                cr,
                self.status_text,
                rect.x + rect.width - ITEM_STATUS_TEXT_PADDING_RIGHT,
                rect.y,
                rect.width - ITEM_STAR_AREA_WIDTH - self.STATUS_PADDING_X,
                ITEM_HEIGHT,
                )
        elif self.status == self.STATUS_WAIT_DOWNLOAD:
            # Draw star.
            self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))
            
            draw_text(
                cr,
                self.status_text,
                rect.x + rect.width - ITEM_STATUS_TEXT_PADDING_RIGHT,
                rect.y,
                rect.width - ITEM_STAR_AREA_WIDTH - self.STATUS_PADDING_X,
                ITEM_HEIGHT,
                )
            
            pixbuf = app_theme.get_pixbuf("button/stop.png").get_pixbuf()
            draw_pixbuf(
                cr,
                pixbuf,
                rect.x + rect.width - ITEM_CANCEL_BUTTON_PADDING_RIGHT,
                rect.y + (rect.height - pixbuf.get_height()) / 2,
                )
        elif self.status == self.STATUS_IN_DOWNLOAD:
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
                rect.width - ITEM_STAR_AREA_WIDTH - self.STATUS_PADDING_X,
                ITEM_HEIGHT,
                )
            
            pixbuf = app_theme.get_pixbuf("button/stop.png").get_pixbuf()
            draw_pixbuf(
                cr,
                pixbuf,
                rect.x + rect.width - ITEM_CANCEL_BUTTON_PADDING_RIGHT,
                rect.y + (rect.height - pixbuf.get_height()) / 2,
                )
        elif self.status == self.STATUS_STOP_DOWNLOAD:
            # Draw star.
            self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))
            
            draw_text(
                cr,
                self.status_text,
                rect.x + rect.width - ITEM_STATUS_TEXT_PADDING_RIGHT,
                rect.y,
                rect.width - ITEM_STAR_AREA_WIDTH - self.STATUS_PADDING_X,
                ITEM_HEIGHT,
                )
        elif self.status == self.STATUS_WAIT_INSTALL:
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
                rect.width - ITEM_STAR_AREA_WIDTH - self.STATUS_PADDING_X,
                ITEM_HEIGHT,
                )
            
            pixbuf = app_theme.get_pixbuf("button/stop.png").get_pixbuf()
            draw_pixbuf(
                cr,
                pixbuf,
                rect.x + rect.width - ITEM_CANCEL_BUTTON_PADDING_RIGHT,
                rect.y + (rect.height - pixbuf.get_height()) / 2,
                )
        elif self.status == self.STATUS_STOP_WAIT_INSTALL:
            # Draw star.
            self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))
            
            draw_text(
                cr,
                self.status_text,
                rect.x + rect.width - ITEM_STATUS_TEXT_PADDING_RIGHT,
                rect.y,
                rect.width - ITEM_STAR_AREA_WIDTH - self.STATUS_PADDING_X,
                ITEM_HEIGHT,
                )
        elif self.status == self.STATUS_IN_INSTALL:
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
                rect.width - ITEM_STAR_AREA_WIDTH - self.STATUS_PADDING_X,
                ITEM_HEIGHT,
                )
        elif self.status == self.STATUS_INSTALL_FINISH:
            # Draw star.
            self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))
            
            # Draw button.
            if self.is_have_desktop_file:
                if self.button_status == BUTTON_NORMAL:
                    pixbuf = app_theme.get_pixbuf("button/start_normal.png").get_pixbuf()
                elif self.button_status == BUTTON_HOVER:
                    pixbuf = app_theme.get_pixbuf("button/start_hover.png").get_pixbuf()
                elif self.button_status == BUTTON_PRESS:
                    pixbuf = app_theme.get_pixbuf("button/start_press.png").get_pixbuf()
                draw_pixbuf(
                    cr,
                    pixbuf,
                    rect.x + rect.width - ITEM_BUTTON_PADDING_RIGHT - pixbuf.get_width(),
                    rect.y + (ITEM_HEIGHT - self.button_height) / 2,
                    )
            else:
                pixbuf = app_theme.get_pixbuf("button/start_normal.png").get_pixbuf()
                draw_text(
                    cr,
                    _("Successfully installed"),
                    rect.x + rect.width - ITEM_BUTTON_PADDING_RIGHT - pixbuf.get_width(),
                    rect.y + (rect.height - pixbuf.get_height()) / 2,
                    pixbuf.get_width(),
                    pixbuf.get_height(),
                    alignment=pango.ALIGN_CENTER,
                    )
        elif self.status == self.STATUS_PARSE_DOWNLOAD_FAILED:
            # Draw star.
            self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))
            
            draw_text(
                cr,
                self.status_text,
                rect.x + rect.width - ITEM_STATUS_TEXT_PADDING_RIGHT,
                rect.y,
                rect.width - ITEM_STAR_AREA_WIDTH - self.STATUS_PADDING_X,
                ITEM_HEIGHT,
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
            if self.status == self.STATUS_INSTALL_FINISH:
                if self.is_have_desktop_file:
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
                            
            elif self.status == self.STATUS_READY_DOWNLOAD:
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
            if self.status == self.STATUS_WAIT_DOWNLOAD:
                if self.is_stop_button_can_click(column, offset_x, offset_y):
                    self.status = self.STATUS_STOP_DOWNLOAD
                    self.status_text = _("Download was interrupted")
                    
                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("remove-wait-download", [self.pkg_name])
                    global_event.emit("request-stop-install-actions", [self.pkg_name])
                elif self.is_in_star_area(column, offset_x, offset_y):
                    global_event.emit("grade-pkg", self.pkg_name, self.grade_star)
            elif self.status == self.STATUS_IN_DOWNLOAD:
                if self.is_stop_button_can_click(column, offset_x, offset_y):
                    self.status = self.STATUS_STOP_DOWNLOAD
                    self.status_text = _("Download was interrupted")
                    
                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("stop-download-pkg", [self.pkg_name])
                    global_event.emit("request-stop-install-actions", [self.pkg_name])
            elif self.status == self.STATUS_WAIT_INSTALL:
                if self.is_stop_button_can_click(column, offset_x, offset_y):
                    self.status = self.STATUS_STOP_WAIT_INSTALL
                    self.status_text = _("Installation was interrupted")
                    
                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("remove-wait-action", [(str((self.pkg_name, ACTION_INSTALL)))])
                    global_event.emit("request-stop-install-actions", [self.pkg_name])
            elif self.status == self.STATUS_INSTALL_FINISH:
                if self.is_in_star_area(column, offset_x, offset_y):
                    global_event.emit("grade-pkg", self.pkg_name, self.grade_star)
                elif self.is_in_button_area(column, offset_x, offset_y):
                    if self.is_have_desktop_file:
                        desktop_info = self.data_manager.get_pkg_desktop_info(self.pkg_name)
                        global_event.emit("start-pkg", self.alias_name, desktop_info, self.get_offset_with_button(offset_x, offset_y))
                        
                        self.button_status = BUTTON_PRESS
                            
                        if self.redraw_request_callback:
                            self.redraw_request_callback(self, True)
                    
    def get_offset_with_button(self, offset_x, offset_y):
        pixbuf = app_theme.get_pixbuf("button/start_normal.png").get_pixbuf()
        popup_x = self.get_column_widths()[1] - ITEM_BUTTON_PADDING_RIGHT - pixbuf.get_width() / 2
        popup_y = (ITEM_HEIGHT - pixbuf.get_height()) / 2
        return (offset_x, offset_y, popup_x, popup_y)
    
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
    
    def is_stop_button_can_click(self, column, offset_x, offset_y):
        pixbuf = app_theme.get_pixbuf("button/stop.png").get_pixbuf()
        return (column == 1
                and is_in_rect((offset_x, offset_y),
                               (self.get_column_widths()[column] - ITEM_CANCEL_BUTTON_PADDING_RIGHT,
                                (ITEM_HEIGHT - pixbuf.get_height()) / 2,
                                pixbuf.get_width(),
                                pixbuf.get_height())))
    
    def download_ready(self):
        self.status = self.STATUS_READY_DOWNLOAD
        self.status_text = _("Analyzing dependencies")

        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def download_wait(self):
        self.status = self.STATUS_WAIT_DOWNLOAD
        self.status_text = _("Waiting for download")

        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def download_start(self):
        self.status = self.STATUS_IN_DOWNLOAD
        self.status_text = _("Downloading")
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def download_update(self, percent, speed):
        self.status = self.STATUS_IN_DOWNLOAD
        self.progress_buffer.progress = percent
        self.status_text = "%s/s" % (format_file_size(speed))
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def download_finish(self):
        self.status = self.STATUS_WAIT_INSTALL
        self.progress_buffer.progress = 0
        self.status_text = _("Waiting for installation")
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def download_stop(self):
        pass
    
    def download_parse_failed(self):
        self.status = self.STATUS_PARSE_DOWNLOAD_FAILED
        self.status_text = _("Analyzing dependencies failed")
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
        global_event.emit("request-clear-failed-action", self.pkg_name, ACTION_INSTALL)    
        
    def action_start(self):
        self.status = self.STATUS_IN_INSTALL
        self.status_text = _("Installing")
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
                
    def action_update(self, percent):
        self.status = self.STATUS_IN_INSTALL
        self.status_text = _("Installing")
        self.progress_buffer.progress = percent
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def action_finish(self):
        self.status = self.STATUS_INSTALL_FINISH
        self.progress_buffer.progress = 100
        self.status_text = _("Installation complete")
        
        self.is_have_desktop_file = self.data_manager.is_pkg_have_desktop_file(self.pkg_name) != None
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
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
    
gobject.type_register(InstallItem)        

