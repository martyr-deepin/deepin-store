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
from constant import BUTTON_NORMAL, BUTTON_HOVER, BUTTON_PRESS, CONFIG_DIR, CHECK_BUTTON_PADDING_X
import os
from dtk.ui.new_treeview import TreeView, TreeItem
from dtk.ui.threads import post_gui, AnonymityThread
from dtk.ui.button import CheckButtonBuffer, ImageButton, CheckAllButton
from dtk.ui.star_view import StarBuffer
from dtk.ui.draw import draw_pixbuf, draw_text, draw_vlinear
from deepin_utils.core import split_with
from deepin_utils.net import is_network_connected
from deepin_utils.date_time import get_current_time
from deepin_utils.file import read_file, write_file, format_file_size, get_parent_dir
from dtk.ui.utils import is_in_rect, container_remove_all, get_content_size
from dtk.ui.label import Label
from item_render import (render_pkg_info, STAR_SIZE, get_star_level, ITEM_PADDING_Y, get_icon_pixbuf_path,
                         ITEM_INFO_AREA_WIDTH, ITEM_CANCEL_BUTTON_PADDING_RIGHT, NAME_SIZE, ICON_SIZE, ITEM_PADDING_MIDDLE,
                         ITEM_STAR_AREA_WIDTH, ITEM_STATUS_TEXT_PADDING_RIGHT,
                         ITEM_BUTTON_AREA_WIDTH, ITEM_BUTTON_PADDING_RIGHT, ITEM_PADDING_X,
                         ITEM_HEIGHT, ITEM_CHECKBUTTON_WIDTH, ITEM_CHECKBUTTON_PADDING_X, ITEM_CHECKBUTTON_PADDING_Y,
                         PROGRESSBAR_HEIGHT, ITEM_NO_NOTIFY_AREA_WIDTH, ITEM_NO_NOTIFY_STRING, ITEM_NO_NOTIFY_WIDTH, ITEM_NO_NOTIFY_HEIGHT,
                         ITEM_NOTIFY_AGAIN_STRING, ITEM_NOTIFY_AGAIN_WIDTH, ITEM_NOTIFY_AGAIN_HEIGHT,
                         )
from skin import app_theme
from dtk.ui.progressbar import ProgressBuffer
from events import global_event
from constant import ACTION_UPGRADE
from dtk.ui.cycle_strip import CycleStrip

class UpgradingBar(gtk.HBox):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        gtk.HBox.__init__(self)

        self.message_label = Label()
        self.message_label_align = gtk.Alignment()
        self.message_label_align.set(0.0, 0.5, 0, 0)
        self.message_label_align.set_padding(0, 0, 8, 0)
        self.message_label_align.add(self.message_label)
        
        self.pack_start(self.message_label_align, True, True)
        
    def set_upgrading_message(self, message):
        self.message_label.set_text(message)
        
class NewestBar(gtk.HBox):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        gtk.HBox.__init__(self)
        
        self.message_label = Label()
        self.message_label_align = gtk.Alignment()
        self.message_label_align.set(0.0, 0.5, 0, 0)
        self.message_label_align.set_padding(0, 0, 8, 0)
        self.message_label_align.add(self.message_label)
        
        self.no_notify_label = Label(
            hover_color=app_theme.get_color("homepage_hover")
            )
        self.no_notify_label.set_clickable()
        self.no_notify_label_align = gtk.Alignment()
        self.no_notify_label_align.set(1.0, 0.5, 0, 0)
        self.no_notify_label_align.set_padding(0, 0, 0, 40)
        
        self.pack_start(self.message_label_align, False, False)
        self.pack_start(self.no_notify_label_align, True, True)
        
        self.no_notify_label.connect("button-press-event", lambda w, e: global_event.emit("show-no-notify-page"))
        
    def set_update_time(self):
        self.message_label.set_text("最后更新时间: %s" % get_current_time())
        
    def set_no_notify_num(self, no_notify_num):
        
        container_remove_all(self.no_notify_label_align)
        if no_notify_num > 0:
            self.no_notify_label.set_text("不再提醒升级(%s)" % no_notify_num)
            self.no_notify_label_align.add(self.no_notify_label)
            
            self.show_all()
        
class UpgradeBar(gtk.HBox):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        gtk.HBox.__init__(self)
        
        self.select_button = CheckAllButton()
        self.select_button.set_active(True)
        self.select_button_align = gtk.Alignment()
        self.select_button_align.set(0.0, 0.5, 0, 0)
        self.select_button_align.set_padding(0, 0, CHECK_BUTTON_PADDING_X, 0)
        self.select_button_align.add(self.select_button)
        self.message_label = Label()
        self.message_label_align = gtk.Alignment()
        self.message_label_align.set(0.0, 0.5, 0, 0)
        self.message_label_align.set_padding(0, 0, 0, 0)
        self.message_label_align.add(self.message_label)
        self.no_notify_label = Label(
            hover_color=app_theme.get_color("homepage_hover")
            )
        self.no_notify_label.set_clickable()
        self.no_notify_label_align = gtk.Alignment()
        self.no_notify_label_align.set(1.0, 0.5, 0, 0)
        self.no_notify_label_align.set_padding(0, 0, 0, 100)
        self.upgrade_selected_button = ImageButton(
            app_theme.get_pixbuf("button/upgrade_all_normal.png"),
            app_theme.get_pixbuf("button/upgrade_all_hover.png"),
            app_theme.get_pixbuf("button/upgrade_all_press.png"),
            )
        self.upgrade_selected_button_align = gtk.Alignment()
        self.upgrade_selected_button_align.set(0.0, 0.5, 0, 0)
        self.upgrade_selected_button_align.set_padding(0, 0, 40, 40)
        self.upgrade_selected_button_align.add(self.upgrade_selected_button)
        
        self.pack_start(self.select_button_align, False, False)
        self.pack_start(self.message_label_align, False, False)
        self.pack_start(self.no_notify_label_align, True, True)
        self.pack_start(self.upgrade_selected_button_align, False, False)
        
        self.no_notify_label.connect("button-press-event", lambda w, e: global_event.emit("show-no-notify-page"))
        self.select_button.connect("active-changed", self.handle_active_changed)
        self.upgrade_selected_button.connect("clicked", lambda w: global_event.emit("upgrade-selected-pkg"))
        
    def handle_active_changed(self, widget, state):
        if state:
            global_event.emit("select-all-upgrade-pkg")
        else:
            global_event.emit("unselect-all-upgrade-pkg")
        
    def set_upgrade_info(self, upgrade_num, no_notify_num):
        self.message_label.set_text("当前可升级软件共 %s 款" % upgrade_num)
        
        container_remove_all(self.no_notify_label_align)
        if no_notify_num > 0:
            self.no_notify_label.set_text("不再提醒升级(%s)" % no_notify_num)
            self.no_notify_label_align.add(self.no_notify_label)
            
            self.show_all()
            
gobject.type_register(UpgradeBar)        

class NoNotifyBar(gtk.HBox):
    '''
    class docs
    '''
	
    def __init__(self):
        '''
        init docs
        '''
        gtk.HBox.__init__(self)
        
        self.select_button = CheckAllButton()
        self.select_button.set_active(True)
        self.select_button_align = gtk.Alignment()
        self.select_button_align.set(0.0, 0.5, 0, 0)
        self.select_button_align.set_padding(0, 0, CHECK_BUTTON_PADDING_X, 0)
        self.select_button_align.add(self.select_button)
        self.message_label = Label()
        self.message_label_align = gtk.Alignment()
        self.message_label_align.set(0.0, 0.5, 0, 0)
        self.message_label_align.set_padding(0, 0, 0, 0)
        self.message_label_align.add(self.message_label)
        self.notify_again_label = Label(
            "重新提醒",
            hover_color=app_theme.get_color("homepage_hover")
            )
        self.notify_again_label.set_clickable()
        self.notify_again_label_align = gtk.Alignment()
        self.notify_again_label_align.set(1.0, 0.5, 0, 0)
        self.notify_again_label_align.set_padding(0, 0, 0, 5)
        self.notify_again_label_align.add(self.notify_again_label)
        self.return_button = ImageButton(
            app_theme.get_pixbuf("detail/normal.png"),
            app_theme.get_pixbuf("detail/hover.png"),
            app_theme.get_pixbuf("detail/press.png"),
            )
        self.return_align = gtk.Alignment()
        self.return_align.set(0.5, 0.5, 0, 0)
        self.return_align.set_padding(0, 0, 5, 5)
        self.return_align.add(self.return_button)
        
        self.pack_start(self.select_button_align, False, False)
        self.pack_start(self.message_label_align, True, True)
        self.pack_start(self.notify_again_label_align, False, False)
        self.pack_start(self.return_align, False, False)
        
        self.select_button.connect("active-changed", self.handle_active_changed)
        self.notify_again_label.connect("button-press-event", lambda w, e: global_event.emit("notify-selected-pkg"))
        self.return_button.connect("clicked", lambda w: global_event.emit("show-upgrade-page"))
        
    def handle_active_changed(self, widget, state):
        if state:
            global_event.emit("select-all-notify-pkg")
        else:
            global_event.emit("unselect-all-notify-pkg")
        
    def set_notify_info(self, notify_again_num):
        self.message_label.set_text("有%s款软件不再提醒" % notify_again_num)
        
        self.message_label_align.show_all()
        
gobject.type_register(NoNotifyBar)        

class UpgradePage(gtk.VBox):
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
        
        self.upgrade_pkg_num = 0
        self.no_notify_pkg_num = 0
        
        self.current_progress = 0
        self.upgrade_progress_status = []
        
        self.upgrade_bar = UpgradeBar()
        self.no_notify_bar = NoNotifyBar()
        self.newest_bar = NewestBar()
        self.upgrading_bar = UpgradingBar()
        
        self.cycle_strip = CycleStrip(app_theme.get_pixbuf("strip/background.png"))
        
        self.update_view = gtk.VBox()
        self.update_list_pixbuf = None
        self.update_view.connect("expose-event", self.expose_update_view)
        
        self.newest_view = gtk.VBox()
        self.newest_pixbuf = None
        self.newest_view.connect("expose-event", self.expose_newest_view)

        self.network_disable_view = gtk.VBox()
        self.network_disable_pixbuf = None
        self.network_disable_view.connect("expose-event", self.expose_network_disable_view)
        
        self.upgrade_treeview = TreeView(enable_drag_drop=False)
        self.upgrade_treeview.set_expand_column(1)
        self.upgrade_treeview.connect("items-change", self.monitor_upgrade_view)
        self.upgrade_treeview.connect("items-change", lambda treeview: global_event.emit("update-upgrade-notify-number", len(treeview.visible_items)))
        
        gtk.timeout_add(200, self.render_upgrade_progress)
        
        self.no_notify_treeview = TreeView(enable_drag_drop=False)
        self.no_notify_treeview.set_expand_column(1)
        self.no_notify_treeview.connect("items-change", self.monitor_no_notify_view)
        
        self.in_no_notify_page = False
        
        self.pkg_info_dict = {}
        
        global_event.register_event("select-all-upgrade-pkg", self.select_all_pkg)
        global_event.register_event("unselect-all-upgrade-pkg", self.unselect_all_pkg)
        global_event.register_event("upgrade-selected-pkg", self.upgrade_selected_pkg)
        global_event.register_event("show-no-notify-page", self.show_no_notify_page)
        global_event.register_event("no-notify-pkg", self.no_notify_pkg)
        
        global_event.register_event("select-all-notify-pkg", self.select_all_notify_pkg)
        global_event.register_event("unselect-all-notify-pkg", self.unselect_all_notify_pkg)
        global_event.register_event("notify-selected-pkg", self.notify_selected_pkg)
        global_event.register_event("show-upgrade-page", self.show_upgrade_page)
        global_event.register_event("notify-again-pkg", self.notify_again_pkg)
        
        global_event.register_event("show-updating-view", self.show_updating_view)
        global_event.register_event("show-newest-view", self.show_newest_view)
        global_event.register_event("show-network-disable-view", self.show_network_disable_view)
        
        global_event.register_event("click-upgrade-check-button", self.click_upgrade_check_button)
        global_event.register_event("click-notify-check-button", self.click_notify_check_button)
        
        self.upgrade_treeview.draw_mask = self.draw_mask
        self.no_notify_treeview.draw_mask = self.draw_mask
        
        global_event.emit("show-updating-view")
        self.fetch_upgrade_info()
        
    def click_upgrade_check_button(self):
        self.upgrade_bar.select_button.update_status(map(lambda item: item.check_button_buffer.active, self.upgrade_treeview.visible_items))
        
    def click_notify_check_button(self):
        self.no_notify_bar.select_button.update_status(map(lambda item: item.check_button_buffer.active, self.no_notify_treeview.visible_items))
    
    def show_init_page(self):
        if len(self.upgrade_treeview.visible_items) == 0:
            global_event.emit("show-newest-view")
        else:
            global_event.emit("show-upgrade-page")
        
    def monitor_upgrade_view(self, treeview):
        if len(treeview.visible_items) == 0:
            global_event.emit("show-newest-view")
            
    def monitor_no_notify_view(self, treeview):
        if len(treeview.visible_items) == 0:
            global_event.emit("show-upgrade-page")
        
    def show_updating_view(self):
        if is_network_connected():
            container_remove_all(self)
            container_remove_all(self.cycle_strip)
            
            self.cycle_strip.add(self.upgrading_bar)
            self.pack_start(self.cycle_strip, False, False)
            self.pack_start(self.update_view, True, True)
            
            self.show_all()
        else:
            global_event.emit("show-network-disable-view")
            
    def show_newest_view(self):
        container_remove_all(self)
        container_remove_all(self.cycle_strip)
        
        self.newest_bar.set_update_time()
        self.newest_bar.set_no_notify_num(self.no_notify_pkg_num)
        self.cycle_strip.add(self.newest_bar)
        self.pack_start(self.cycle_strip, False, False)
        self.pack_start(self.newest_view, True, True)
        
        self.show_all()

    def show_network_disable_view(self):
        container_remove_all(self)
        self.pack_start(self.network_disable_view, True, True)
        
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
        
    def select_all_pkg(self):
        for item in self.upgrade_treeview.visible_items:
            item.check_button_buffer.active = True
            
        self.upgrade_treeview.queue_draw()
    
    def unselect_all_pkg(self):
        for item in self.upgrade_treeview.visible_items:
            item.check_button_buffer.active = False
            
        self.upgrade_treeview.queue_draw()
        
    def upgrade_selected_pkg(self):
        pkg_names = []
        for item in self.upgrade_treeview.visible_items:
            if item.check_button_buffer.active:
                item.check_button_buffer.set_sensitive(False)
                pkg_names.append(item.pkg_name)
                
        global_event.emit("upgrade-pkg", pkg_names)        
        
    def select_all_notify_pkg(self):
        for item in self.no_notify_treeview.visible_items:
            item.check_button_buffer.active = True
            
        self.no_notify_treeview.queue_draw()
    
    def unselect_all_notify_pkg(self):
        for item in self.no_notify_treeview.visible_items:
            item.check_button_buffer.active = False
            
        self.no_notify_treeview.queue_draw()
        
    def notify_selected_pkg(self):
        pkg_names = []
        for item in self.no_notify_treeview.visible_items:
            if item.check_button_buffer.active:
                pkg_names.append(item.pkg_name)
                
        for pkg_name in pkg_names:
            global_event.emit("notify-again-pkg", pkg_name)
        
    def no_notify_pkg(self, pkg_name):
        self.add_no_notify_pkg(pkg_name)
        self.upgrade_pkg_num -= 1
        self.no_notify_pkg_num += 1
        
        self.upgrade_bar.set_upgrade_info(self.upgrade_pkg_num, self.no_notify_pkg_num)
        self.no_notify_bar.set_notify_info(self.no_notify_pkg_num)
        
        for item in self.upgrade_treeview.visible_items:
            if item.pkg_name == pkg_name:
                self.upgrade_treeview.delete_items([item])
                break
            
        self.no_notify_treeview.add_items([NoNotifyItem(pkg_name, self.pkg_info_dict[pkg_name], self.data_manager)])
        
    def notify_again_pkg(self, pkg_name):
        self.remove_no_notify_pkg(pkg_name)
        self.upgrade_pkg_num += 1
        self.no_notify_pkg_num -= 1

        self.upgrade_bar.set_upgrade_info(self.upgrade_pkg_num, self.no_notify_pkg_num)
        self.no_notify_bar.set_notify_info(self.no_notify_pkg_num)
        
        for item in self.no_notify_treeview.visible_items:
            if item.pkg_name == pkg_name:
                self.no_notify_treeview.delete_items([item])
                break
            
        self.upgrade_treeview.add_items([UpgradeItem(pkg_name, self.pkg_info_dict[pkg_name], self.data_manager)])
            
    def show_no_notify_page(self):
        self.in_no_notify_page = True
        
        container_remove_all(self)
        container_remove_all(self.cycle_strip)
        
        self.no_notify_bar.set_notify_info(self.no_notify_pkg_num)
        self.cycle_strip.add(self.no_notify_bar)
        self.pack_start(self.cycle_strip, False, False)
        self.pack_start(self.no_notify_treeview, True, True)
        
        self.show_all()
        
    def show_upgrade_page(self):
        self.in_no_notify_page = False
        
        container_remove_all(self)
        container_remove_all(self.cycle_strip)
        
        self.cycle_strip.add(self.upgrade_bar)
        self.pack_start(self.cycle_strip, False, False)
        self.pack_start(self.upgrade_treeview, True, True)
        
        self.show_all()
            
    def update_download_status(self, pkg_infos):
        pkg_items = []
        for (pkg_name, download_status) in pkg_infos:
            pkg_item = None
            for item in self.upgrade_treeview.visible_items:
                if item.pkg_name == pkg_name:
                    pkg_item = item
                    break

            if pkg_item == None:
                pkg_item = UpgradeItem(pkg_name, self.bus_interface.request_pkgs_install_version([pkg_name])[0], self.data_manager)
                
            if download_status == "wait":
                pkg_item.download_wait()
            elif download_status == "start":
                pkg_item.download_start()
            elif download_status == "update":
                pkg_item.download_update(0, 0)
            pkg_items.append(pkg_item)
                
        pkg_items = filter(lambda item: item not in self.upgrade_treeview.visible_items, pkg_items)
        self.upgrade_treeview.add_items(pkg_items)        
    
    def update_action_status(self, pkg_infos):
        pkg_items = []
        for (pkg_name, action_status) in pkg_infos:
            pkg_item = None
            for item in self.upgrade_treeview.visible_items:
                if item.pkg_name == pkg_name:
                    pkg_item = item
                    break

            if pkg_item == None:
                pkg_item = UpgradeItem(pkg_name, self.bus_interface.request_pkgs_install_version([pkg_name])[0], self.data_manager)
                
            if action_status == "wait":
                pkg_item.download_finish()
            elif action_status == "start":
                pkg_item.action_start()
            elif action_status == "update":
                pkg_item.action_update(0)
            pkg_items.append(pkg_item)
                
        pkg_items = filter(lambda item: item not in self.upgrade_treeview.visible_items, pkg_items)
        self.upgrade_treeview.add_items(pkg_items)        
        
    def render_upgrade_progress(self):
        if len(self.upgrade_progress_status) > 0:
            self.current_progress = self.upgrade_progress_status[0]
            self.upgrade_progress_status = self.upgrade_progress_status[1::]
            
            self.upgrading_bar.set_upgrading_message("更新软件列表 %s%%" % self.current_progress)
            
        return True    
        
    def update_upgrade_progress(self, percent):
        self.upgrade_progress_status.append(percent)
        
    def expose_update_view(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        if self.update_list_pixbuf == None:
            self.update_list_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(get_parent_dir(__file__, 2), "image", "zh_CN", "upgrading.png"))
        
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()
        
        draw_pixbuf(
            cr,
            self.update_list_pixbuf,
            rect.x + (rect.width - self.update_list_pixbuf.get_width()) / 2,
            rect.y + (rect.height - self.update_list_pixbuf.get_height()) / 2)
        
    def expose_newest_view(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        if self.newest_pixbuf == None:
            self.newest_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(get_parent_dir(__file__, 2), "image", "zh_CN", "newest.png"))
        
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()
        
        draw_pixbuf(
            cr,
            self.newest_pixbuf,
            rect.x + (rect.width - self.newest_pixbuf.get_width()) / 2,
            rect.y + (rect.height - self.newest_pixbuf.get_height()) / 2)

    def expose_network_disable_view(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        if self.network_disable_pixbuf == None:
            self.network_disable_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(get_parent_dir(__file__, 2), "image", "zh_CN", "network_disable.png"))
        
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()
        
        draw_pixbuf(
            cr,
            self.network_disable_pixbuf,
            rect.x + (rect.width - self.network_disable_pixbuf.get_width()) / 2,
            rect.y + (rect.height - self.network_disable_pixbuf.get_height()) / 2)
        
    def read_no_notify_config(self):
        no_notify_config_path = os.path.join(CONFIG_DIR, "no_notify_pkgs")
        if os.path.exists(no_notify_config_path):
           no_notify_config_str = read_file(no_notify_config_path)
           try:
               no_notify_config = eval(no_notify_config_str)
               
               if type(no_notify_config).__name__ != "list":
                   no_notify_config = []
           except Exception:
               no_notify_config = []
               
           return no_notify_config
        else:
            return []
        
    def add_no_notify_pkg(self, pkg_name):
        no_notify_config = self.read_no_notify_config()
        
        if pkg_name not in no_notify_config:
            no_notify_config.append(pkg_name)
            write_file(os.path.join(CONFIG_DIR, "no_notify_pkgs"), str(no_notify_config))
    
    def remove_no_notify_pkg(self, pkg_name):
        no_notify_config = self.read_no_notify_config()
        
        if pkg_name in no_notify_config:
            no_notify_config_path = os.path.join(CONFIG_DIR, "no_notify_pkgs")
            write_file(no_notify_config_path, str(filter(lambda config_pkg_name: config_pkg_name != pkg_name, no_notify_config)))
    
    def fetch_upgrade_info(self):
        gobject.timeout_add(10, lambda : AnonymityThread(self.bus_interface.request_upgrade_pkgs,
                                                    self.render_upgrade_info).run())
        
    @post_gui
    def render_upgrade_info(self, pkg_infos):
        if len(pkg_infos) > 0:
            if self.update_list_pixbuf:
                del self.update_list_pixbuf
                self.update_list_pixbuf = None
            
            (desktop_pkg_infos, library_pkg_infos) = split_with(
                pkg_infos, 
                lambda pkg_info: self.data_manager.is_pkg_have_desktop_file((eval(pkg_info)[0])))
            
            if len(self.get_children()) == 0 or self.get_children()[0] != self.upgrade_treeview:
                container_remove_all(self)
                container_remove_all(self.cycle_strip)
                
                self.cycle_strip.add(self.upgrade_bar)
                
                self.pack_start(self.cycle_strip, False, False)
                self.pack_start(self.upgrade_treeview, True, True)
                
            no_notify_config = self.read_no_notify_config()    
                
            exists_upgrade_pkg_names = map(lambda item: item.pkg_name, self.upgrade_treeview.visible_items)
            exists_no_notify_pkg_names = map(lambda item: item.pkg_name, self.no_notify_treeview.visible_items)
            
            upgrade_items = []
            no_notify_items = []
            for pkg_info in desktop_pkg_infos + library_pkg_infos:
                (pkg_name, pkg_version) = eval(pkg_info)
                
                self.pkg_info_dict[pkg_name] = pkg_version
                
                if pkg_name in no_notify_config:
                    if pkg_name not in exists_no_notify_pkg_names:
                        self.no_notify_pkg_num += 1
                        no_notify_items.append(NoNotifyItem(pkg_name, pkg_version, self.data_manager))
                else:
                    if pkg_name not in exists_upgrade_pkg_names:
                        self.upgrade_pkg_num += 1
                        upgrade_items.append(UpgradeItem(pkg_name, pkg_version, self.data_manager))
                
            self.upgrade_bar.set_upgrade_info(self.upgrade_pkg_num, self.no_notify_pkg_num)
            
            if len(upgrade_items) == 0 and len(self.upgrade_treeview.visible_items) == 0:        
                global_event.emit("show-newest-view")
            else:
                self.upgrade_treeview.add_items(upgrade_items)    
                
            self.no_notify_treeview.add_items(no_notify_items)
        else:
            global_event.emit("show-newest-view")
        
    def download_start(self, pkg_name):
        for item in self.upgrade_treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.download_start()
                break

    def download_update(self, pkg_name, percent, speed):
        for item in self.upgrade_treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.download_update(percent, speed)
                break
        
    def download_finish(self, pkg_name):
        for item in self.upgrade_treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.download_finish()
                break

    def download_stop(self, pkg_name):
        for item in self.upgrade_treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.download_stop()
                break
            
    def download_parse_failed(self, pkg_name):
        for item in self.upgrade_treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.download_parse_failed()
                break
            
    def action_start(self, pkg_name):
        for item in self.upgrade_treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.action_start()
                break
    
    def action_update(self, pkg_name, percent):
        for item in self.upgrade_treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.action_update(percent)
                break
    
    def action_finish(self, pkg_name, pkg_info_list):
        for item in self.upgrade_treeview.visible_items:
            if item.pkg_name == pkg_name:
                item.action_finish()
                
                global_event.emit("request-clear-action-pages", pkg_info_list)
                break
        
gobject.type_register(UpgradePage)

class UpgradeItem(TreeItem):
    '''
    class docs
    '''
    
    STATUS_NORMAL = 1
    STATUS_WAIT_DOWNLOAD = 2
    STATUS_IN_DOWNLOAD = 3
    STATUS_WAIT_UPGRADE = 4
    STATUS_IN_UPGRADE = 5
    STATUS_UPGRADE_FINISH = 6
    
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
        
        button_pixbuf = app_theme.get_pixbuf("button/upgrade_normal.png").get_pixbuf()
        (self.button_width, self.button_height) = button_pixbuf.get_width(), button_pixbuf.get_height()
        self.button_status = BUTTON_NORMAL
        
        self.status = self.STATUS_NORMAL
        self.status_text = ""
        self.progress_buffer = ProgressBuffer()
        
        self.check_button_buffer = CheckButtonBuffer(
            True,
            ITEM_CHECKBUTTON_PADDING_X,
            ITEM_CHECKBUTTON_PADDING_Y)
        self.notify_button_hover = False
        
    def render_check_button(self, cr, rect):
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        self.check_button_buffer.render(cr, rect)
        
    def render_pkg_info(self, cr, rect):
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        if self.icon_pixbuf == None:
            self.icon_pixbuf = gtk.gdk.pixbuf_new_from_file(get_icon_pixbuf_path(self.pkg_name))        
            
        render_pkg_info(cr, rect, self.alias_name, self.pkg_name, self.icon_pixbuf, self.pkg_version, self.short_desc, -ITEM_PADDING_X)
        
    def render_no_notify(self, cr, rect):
        if self.status == self.STATUS_NORMAL:
            if self.row_index % 2 == 1:
                cr.set_source_rgba(1, 1, 1, 0.5)
                cr.rectangle(rect.x, rect.y, rect.width, rect.height)
                cr.fill()
            
            if self.notify_button_hover:
                text_color = "#00AAFF"
            else:
                text_color = "#000000"
            
            draw_text(
                cr,
                ITEM_NO_NOTIFY_STRING,
                rect.x + (ITEM_NO_NOTIFY_AREA_WIDTH - ITEM_NO_NOTIFY_WIDTH) / 2,
                rect.y + (ITEM_HEIGHT - ITEM_NO_NOTIFY_HEIGHT) / 2,
                ITEM_NO_NOTIFY_WIDTH,
                ITEM_NO_NOTIFY_HEIGHT,
                text_color=text_color,
                )
        
    def render_pkg_status(self, cr, rect):
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        if self.status == self.STATUS_WAIT_DOWNLOAD:
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
        elif self.status == self.STATUS_WAIT_UPGRADE:
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
        elif self.status == self.STATUS_IN_UPGRADE:
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
        elif self.status == self.STATUS_UPGRADE_FINISH:
            # Draw progress.
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
        elif self.status == self.STATUS_NORMAL:
            # Draw star.
            self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))
            
            # Draw button.
            if self.button_status == BUTTON_NORMAL:
                pixbuf = app_theme.get_pixbuf("button/upgrade_normal.png").get_pixbuf()
            elif self.button_status == BUTTON_HOVER:
                pixbuf = app_theme.get_pixbuf("button/upgrade_hover.png").get_pixbuf()
            elif self.button_status == BUTTON_PRESS:
                pixbuf = app_theme.get_pixbuf("button/upgrade_press.png").get_pixbuf()
            draw_pixbuf(
                cr,
                pixbuf,
                rect.x + rect.width - ITEM_BUTTON_PADDING_RIGHT - pixbuf.get_width(),
                rect.y + (ITEM_HEIGHT - self.button_height) / 2,
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
        return [ITEM_CHECKBUTTON_WIDTH,
                ITEM_INFO_AREA_WIDTH,
                ITEM_NO_NOTIFY_AREA_WIDTH,
                ITEM_STAR_AREA_WIDTH + ITEM_BUTTON_AREA_WIDTH]
    
    def get_column_renders(self):
        return [self.render_check_button,
                self.render_pkg_info,
                self.render_no_notify,
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
            if self.check_button_buffer.motion_button(offset_x, offset_y):
                if self.redraw_request_callback:
                    self.redraw_request_callback(self)
                    
            global_event.emit("set-cursor", None)    
        elif column == 1:
            if self.is_in_icon_area(column, offset_x, offset_y):
                global_event.emit("set-cursor", gtk.gdk.HAND2)    
            elif self.is_in_name_area(column, offset_x, offset_y):
                global_event.emit("set-cursor", gtk.gdk.HAND2)    
            else:
                global_event.emit("set-cursor", None)    
        elif column == 2:
            global_event.emit("set-cursor", None)    
            
            if self.status == self.STATUS_NORMAL:
                if self.is_in_no_notify_area(column, offset_x, offset_y):
                    if not self.notify_button_hover:
                        self.notify_button_hover = True
                
                        if self.redraw_request_callback:
                            self.redraw_request_callback(self)
                            
                        global_event.emit("set-cursor", gtk.gdk.HAND2)    
                else:
                    if self.notify_button_hover:
                        self.notify_button_hover = False
                
                        if self.redraw_request_callback:
                            self.redraw_request_callback(self)
                            
                        global_event.emit("set-cursor", None)    
        elif column == 3:
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
            if self.check_button_buffer.press_button(offset_x, offset_y):
                global_event.emit("click-upgrade-check-button")
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self)
        elif column == 1:
            if self.is_in_icon_area(column, offset_x, offset_y):
                global_event.emit("switch-to-detail-page", self.pkg_name)
            elif self.is_in_name_area(column, offset_x, offset_y):
                global_event.emit("switch-to-detail-page", self.pkg_name)
        elif column == 2:
            if self.status == self.STATUS_NORMAL:
                if self.is_in_no_notify_area(column, offset_x, offset_y):
                    global_event.emit("no-notify-pkg", self.pkg_name)
        elif column == 3:
            if self.status == self.STATUS_NORMAL:
                if self.is_in_button_area(column, offset_x, offset_y):
                    self.status = self.STATUS_WAIT_DOWNLOAD
                    self.status_text = "等待下载"
                    
                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("upgrade-pkg", [self.pkg_name])
                elif self.is_in_star_area(column, offset_x, offset_y):
                    global_event.emit("grade-pkg", self.pkg_name, self.grade_star)
            elif self.status == self.STATUS_WAIT_DOWNLOAD:
                if self.is_stop_button_can_click(column, offset_x, offset_y):
                    self.status = self.STATUS_NORMAL
                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("remove-wait-download", [self.pkg_name])
            elif self.status == self.STATUS_IN_DOWNLOAD:
                if self.is_stop_button_can_click(column, offset_x, offset_y):
                    self.status = self.STATUS_NORMAL
                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("stop-download-pkg", [self.pkg_name])
            elif self.status == self.STATUS_WAIT_UPGRADE:
                if self.is_stop_button_can_click(column, offset_x, offset_y):
                    self.status = self.STATUS_NORMAL
                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("remove-wait-action", [(str((self.pkg_name, ACTION_UPGRADE)))])
                
    def button_release(self, column, offset_x, offset_y):
        if column == 0 and self.check_button_buffer.release_button(offset_x, offset_y):
            if self.redraw_request_callback:
                self.redraw_request_callback(self)
        elif column == 2:
            if self.status == self.STATUS_NORMAL:
                if self.is_in_no_notify_area(column, offset_x, offset_y):
                    if not self.notify_button_hover:
                        self.notify_button_hover = True
                
                        if self.redraw_request_callback:
                            self.redraw_request_callback(self)
                            
                        global_event.emit("set-cursor", gtk.gdk.HAND2)    
                else:
                    if self.notify_button_hover:
                        self.notify_button_hover = False
                
                        if self.redraw_request_callback:
                            self.redraw_request_callback(self)
                            
                        global_event.emit("set-cursor", None)    
                    
    def single_click(self, column, offset_x, offset_y):
        pass        

    def double_click(self, column, offset_x, offset_y):
        pass        
    
    def is_in_star_area(self, column, offset_x, offset_y):
        return (column == 3
                and is_in_rect((offset_x, offset_y), 
                               (0,
                                (ITEM_HEIGHT - STAR_SIZE) / 2,
                                ITEM_STAR_AREA_WIDTH,
                                STAR_SIZE)))
    
    def is_in_button_area(self, column, offset_x, offset_y):
        return (column == 3 
                and is_in_rect((offset_x, offset_y), 
                               (self.get_column_widths()[column] - ITEM_BUTTON_PADDING_RIGHT - self.button_width,
                                (ITEM_HEIGHT - self.button_height) / 2,
                                self.button_width,
                                self.button_height)))
    
    def is_stop_button_can_click(self, column, offset_x, offset_y):
        pixbuf = app_theme.get_pixbuf("button/stop.png").get_pixbuf()
        return (column == 3
                and is_in_rect((offset_x, offset_y),
                               (self.get_column_widths()[column] - ITEM_CANCEL_BUTTON_PADDING_RIGHT,
                                (ITEM_HEIGHT - pixbuf.get_height()) / 2,
                                pixbuf.get_width(),
                                pixbuf.get_height())))
    
    def is_in_no_notify_area(self, column, offset_x, offset_y):
        return (column == 2
                and is_in_rect((offset_x, offset_y),
                               ((ITEM_NO_NOTIFY_AREA_WIDTH - ITEM_NO_NOTIFY_WIDTH) / 2,
                                (ITEM_HEIGHT - ITEM_NO_NOTIFY_HEIGHT) / 2,
                                ITEM_NO_NOTIFY_WIDTH,
                                ITEM_NO_NOTIFY_HEIGHT)))
            
    def is_in_name_area(self, column, offset_x, offset_y):
        (name_width, name_height) = get_content_size(self.alias_name, NAME_SIZE)
        return (column == 1
                and is_in_rect((offset_x, offset_y),
                               (ICON_SIZE + ITEM_PADDING_MIDDLE,
                                ITEM_PADDING_Y,
                                name_width,
                                NAME_SIZE)))
    
    def is_in_icon_area(self, column, offset_x, offset_y):
        return (column == 1
                and self.icon_pixbuf != None
                and is_in_rect((offset_x, offset_y),
                               (0,
                                ITEM_PADDING_Y,
                                self.icon_pixbuf.get_width(),
                                self.icon_pixbuf.get_height())))
    
    def download_wait(self):
        self.status = self.STATUS_WAIT_DOWNLOAD
        self.status_text = "等待下载"

        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    
    def download_start(self):
        self.status = self.STATUS_IN_DOWNLOAD
        self.status_text = "下载中"
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def download_update(self, percent, speed):
        self.status = self.STATUS_IN_DOWNLOAD
        self.progress_buffer.progress = percent
        self.status_text = "%s/s" % (format_file_size(speed))
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def download_finish(self):
        self.status = self.STATUS_WAIT_UPGRADE
        self.progress_buffer.progress = 0
        self.status_text = "等待升级"
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def download_stop(self):
        pass
            
    def download_parse_failed(self):
        self.status = self.STATUS_PARSE_DOWNLOAD_FAILED
        self.status_text = "分析依赖失败"
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
        global_event.emit("request-clear-failed-action", self.pkg_name, ACTION_UPGRADE)    
            
    def action_start(self):
        self.status = self.STATUS_IN_UPGRADE
        self.status_text = "升级中"
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
                
    def action_update(self, percent):
        self.status = self.STATUS_IN_UPGRADE
        self.status_text = "升级中"
        self.progress_buffer.progress = percent
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def action_finish(self):
        self.status = self.STATUS_UPGRADE_FINISH
        self.progress_buffer.progress = 100
        self.status_text = "升级完成"
        
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
    
gobject.type_register(UpgradeItem)        

class NoNotifyItem(TreeItem):
    '''
    class docs
    '''
    
    STATUS_NORMAL = 1
    STATUS_WAIT_DOWNLOAD = 2
    STATUS_IN_DOWNLOAD = 3
    STATUS_WAIT_UPGRADE = 4
    STATUS_IN_UPGRADE = 5
    STATUS_UPGRADE_FINISH = 6
    
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
        
        button_pixbuf = app_theme.get_pixbuf("button/upgrade_normal.png").get_pixbuf()
        (self.button_width, self.button_height) = button_pixbuf.get_width(), button_pixbuf.get_height()
        self.button_status = BUTTON_NORMAL
        
        self.status = self.STATUS_NORMAL
        self.status_text = ""
        self.progress_buffer = ProgressBuffer()
        
        self.check_button_buffer = CheckButtonBuffer(
            True,
            ITEM_CHECKBUTTON_PADDING_X,
            ITEM_CHECKBUTTON_PADDING_Y)
        self.notify_button_hover = False
        
    def render_check_button(self, cr, rect):
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        self.check_button_buffer.render(cr, rect)
        
    def render_pkg_info(self, cr, rect):
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        if self.icon_pixbuf == None:
            self.icon_pixbuf = gtk.gdk.pixbuf_new_from_file(get_icon_pixbuf_path(self.pkg_name))        
            
        render_pkg_info(cr, rect, self.alias_name, self.pkg_name, self.icon_pixbuf, self.pkg_version, self.short_desc, -ITEM_PADDING_X)
        
    def render_notify_again(self, cr, rect):
        if self.notify_button_hover:
            text_color = "#00AAFF"
        else:
            text_color = "#000000"
        
        pixbuf = app_theme.get_pixbuf("button/upgrade_press.png").get_pixbuf()
        draw_text(
            cr,
            ITEM_NOTIFY_AGAIN_STRING,
            rect.x + rect.width - ITEM_BUTTON_PADDING_RIGHT - pixbuf.get_width(),
            rect.y + (ITEM_HEIGHT - ITEM_NOTIFY_AGAIN_HEIGHT) / 2,
            ITEM_NOTIFY_AGAIN_WIDTH,
            ITEM_NOTIFY_AGAIN_HEIGHT,
            text_color=text_color,
            )
        
    def render_pkg_status(self, cr, rect):
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
        
        if self.status == self.STATUS_NORMAL:
            # Draw star.
            self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))
            
            self.render_notify_again(cr, rect)
        
    def get_height(self):
        return ITEM_HEIGHT
    
    def get_column_widths(self):
        return [ITEM_CHECKBUTTON_WIDTH,
                ITEM_INFO_AREA_WIDTH,
                ITEM_STAR_AREA_WIDTH + ITEM_BUTTON_AREA_WIDTH]
    
    def get_column_renders(self):
        return [self.render_check_button,
                self.render_pkg_info,
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
            if self.check_button_buffer.motion_button(offset_x, offset_y):
                if self.redraw_request_callback:
                    self.redraw_request_callback(self)
        elif column == 1:            
            if self.is_in_icon_area(column, offset_x, offset_y):
                global_event.emit("set-cursor", gtk.gdk.HAND2)    
            elif self.is_in_name_area(column, offset_x, offset_y):
                global_event.emit("set-cursor", gtk.gdk.HAND2)    
            else:
                global_event.emit("set-cursor", None)    
        elif column == 2:
            if self.status == self.STATUS_NORMAL:
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
                            
            if self.is_in_notify_again_area(column, offset_x, offset_y):
                if not self.notify_button_hover:
                    self.notify_button_hover = True

                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("set-cursor", gtk.gdk.HAND2)    
            else:
                if self.notify_button_hover:
                    self.notify_button_hover = False

                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("set-cursor", None)    
                    
    def button_press(self, column, offset_x, offset_y):
        if column == 0:
            if self.check_button_buffer.press_button(offset_x, offset_y):
                global_event.emit("click-notify-check-button")
                
                if self.redraw_request_callback:
                    self.redraw_request_callback(self)
        elif column == 1:
            if self.is_in_icon_area(column, offset_x, offset_y):
                global_event.emit("switch-to-detail-page", self.pkg_name)
            elif self.is_in_name_area(column, offset_x, offset_y):
                global_event.emit("switch-to-detail-page", self.pkg_name)
        elif column == 2:
            if self.is_in_star_area(column, offset_x, offset_y):
                global_event.emit("grade-pkg", self.pkg_name, self.grade_star)
            elif self.is_in_notify_again_area(column, offset_x, offset_y):
                global_event.emit("notify-again-pkg", self.pkg_name)
                
    def button_release(self, column, offset_x, offset_y):
        if column == 0 and self.check_button_buffer.release_button(offset_x, offset_y):
            if self.redraw_request_callback:
                self.redraw_request_callback(self)
        elif column == 2:
            if self.is_in_notify_again_area(column, offset_x, offset_y):
                if not self.notify_button_hover:
                    self.notify_button_hover = True

                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("set-cursor", gtk.gdk.HAND2)    
            else:
                if self.notify_button_hover:
                    self.notify_button_hover = False

                    if self.redraw_request_callback:
                        self.redraw_request_callback(self)
                        
                    global_event.emit("set-cursor", None)    
                    
    def single_click(self, column, offset_x, offset_y):
        pass        

    def double_click(self, column, offset_x, offset_y):
        pass        
    
    def is_in_star_area(self, column, offset_x, offset_y):
        return (column == 2
                and is_in_rect((offset_x, offset_y), 
                               (0,
                                (ITEM_HEIGHT - STAR_SIZE) / 2,
                                ITEM_STAR_AREA_WIDTH,
                                STAR_SIZE)))
    
    def is_in_notify_again_area(self, column, offset_x, offset_y):
        pixbuf = app_theme.get_pixbuf("button/upgrade_press.png").get_pixbuf()
        return (column == 2
                and is_in_rect((offset_x, offset_y),
                               (ITEM_STAR_AREA_WIDTH + ITEM_BUTTON_AREA_WIDTH - ITEM_BUTTON_PADDING_RIGHT - pixbuf.get_width(),
                                (ITEM_HEIGHT - ITEM_NOTIFY_AGAIN_HEIGHT) / 2,
                                ITEM_NOTIFY_AGAIN_WIDTH,
                                ITEM_NOTIFY_AGAIN_HEIGHT,
                                )
                               ))
            
    def is_in_name_area(self, column, offset_x, offset_y):
        (name_width, name_height) = get_content_size(self.alias_name, NAME_SIZE)
        return (column == 1
                and is_in_rect((offset_x, offset_y),
                               (ICON_SIZE + ITEM_PADDING_MIDDLE,
                                ITEM_PADDING_Y,
                                name_width,
                                NAME_SIZE)))
    
    def is_in_icon_area(self, column, offset_x, offset_y):
        return (column == 1
                and self.icon_pixbuf != None
                and is_in_rect((offset_x, offset_y),
                               (0,
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
    
gobject.type_register(NoNotifyItem)        
