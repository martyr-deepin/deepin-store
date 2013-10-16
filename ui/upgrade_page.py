#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
#               2012 ~ 2013 Kaisheng Ye
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#             Kaisheng Ye <kaisheng.ye@gmail.com>
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
import json
from constant import BUTTON_NORMAL, BUTTON_HOVER, BUTTON_PRESS, NO_NOTIFY_FILE, CHECK_BUTTON_PADDING_X, cute_info_dir
import os
import time
from dtk.ui.treeview import TreeView, TreeItem
from dtk.ui.button import CheckButtonBuffer, ImageButton, CheckAllButton
from star_buffer import DscStarBuffer
from dtk.ui.draw import draw_pixbuf, draw_text, draw_vlinear
from deepin_utils.core import split_with
from deepin_utils.net import is_network_connected
from deepin_utils.file import read_file, format_file_size
from dtk.ui.utils import is_in_rect, container_remove_all, get_content_size
from dtk.ui.label import Label
from dtk.ui.theme import DynamicPixbuf, DynamicColor
from item_render import (render_pkg_info, STAR_SIZE, get_star_level, ITEM_PADDING_Y, get_icon_pixbuf_path,
                         ITEM_INFO_AREA_WIDTH, ITEM_CANCEL_BUTTON_PADDING_RIGHT, NAME_SIZE, ICON_SIZE, ITEM_PADDING_MIDDLE,
                         ITEM_STAR_AREA_WIDTH, ITEM_STATUS_TEXT_PADDING_RIGHT,
                         ITEM_BUTTON_AREA_WIDTH, ITEM_BUTTON_PADDING_RIGHT, ITEM_PADDING_X,
                         ITEM_HEIGHT, ITEM_CHECKBUTTON_WIDTH, ITEM_CHECKBUTTON_PADDING_X, ITEM_CHECKBUTTON_PADDING_Y,
                         PROGRESSBAR_HEIGHT, ITEM_NO_NOTIFY_AREA_WIDTH, ITEM_NO_NOTIFY_STRING, ITEM_NO_NOTIFY_WIDTH, ITEM_NO_NOTIFY_HEIGHT,
                         ITEM_NOTIFY_AGAIN_STRING, ITEM_NOTIFY_AGAIN_WIDTH, ITEM_NOTIFY_AGAIN_HEIGHT,
                         )
from skin import app_theme
from dtk.ui.progressbar import ProgressBuffer, ProgressBar
from events import global_event
from constant import ACTION_UPGRADE
from dtk.ui.cycle_strip import CycleStrip
import dtk.ui.tooltip as Tooltip
from utils import get_last_upgrade_time, handle_dbus_error, handle_dbus_reply
import utils
from nls import _
import widgets

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
        
        self.message_label = Label(_("Last upgraded time: "))
        self.message_time = widgets.HumanTimeTip(utils.get_last_upgrade_time())

        self.message_box = gtk.HBox()
        self.message_box.pack_start(self.message_label, False, False)
        self.message_box.pack_start(self.message_time, False, False)

        self.message_box_align = gtk.Alignment()
        self.message_box_align.set(0.0, 0.5, 0, 0)
        self.message_box_align.set_padding(0, 0, 8, 0)
        self.message_box_align.add(self.message_box)
        
        self.no_notify_label = Label(
            hover_color=app_theme.get_color("homepage_hover")
            )
        self.no_notify_label.set_clickable()
        self.no_notify_label_align = gtk.Alignment()
        self.no_notify_label_align.set(1.0, 0.5, 0, 0)
        self.no_notify_label_align.set_padding(0, 0, 0, 40)
        
        self.pack_start(self.message_box_align, False, False)
        self.pack_start(self.no_notify_label_align, True, True)
        
        self.no_notify_label.connect("button-press-event", lambda w, e: global_event.emit("show-no-notify-page"))
        
    def set_no_notify_num(self, no_notify_num):
        
        container_remove_all(self.no_notify_label_align)
        if no_notify_num > 0:
            self.no_notify_label.set_text(_("Unwatched (%s)") % no_notify_num)
            self.no_notify_label_align.add(self.no_notify_label)
            
            self.show_all()

    def set_update_time(self):
        self.message_time.timestamp = utils.get_last_upgrade_time()
        
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
            insensitive_dpixbuf=DynamicPixbuf(utils.get_common_image('button/upgrade_all_insensitive.png')),
            )
        Tooltip.text(self.upgrade_selected_button, _("Upgrade select items"))
        self.upgrade_selected_button_align = gtk.Alignment()
        self.upgrade_selected_button_align.set(1.0, 0.5, 0, 0)
        self.upgrade_selected_button_align.set_padding(0, 0, 6, ITEM_BUTTON_PADDING_RIGHT)
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
        self.message_label.set_text(_("%s applications are available for upgrade") % upgrade_num)
        
        container_remove_all(self.no_notify_label_align)
        if no_notify_num > 0:
            self.no_notify_label.set_text(_("Unwatched (%s)") % no_notify_num)
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
            _("Watch again"),
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
        self.message_label.set_text(_("%s applications are not being watched") % notify_again_num)
        
        self.message_label_align.show_all()
        
gobject.type_register(NoNotifyBar)        

class UpgradingBox(gtk.VBox):
    def __init__(self, preference_dialog):
        gtk.VBox.__init__(self)
        self.preference_dialog = preference_dialog

        self.upgrade_page_logo = widgets.ImageBox(utils.get_common_image("upgrade/download.png"))

        self.progress_box = gtk.VBox(spacing=6)
        self.progress_box.set_size_request(400, -1)
        self.upgrading_progress_title = widgets.TextLoading(_("正在下载更新"), text_size=16)
        self.upgrading_progressbar = ProgressBar()
        self.upgrading_progressbar.set_size_request(360, 12)
        self.upgrading_progressbar.progress_buffer.progress = 0.0
        self.upgrading_progress_detail = Label("")

        bottom_info_box = gtk.Table(3, 2)
        recent_update_time_label = utils.create_right_align_label(_("最近更新列表时间："))
        self.recent_update_time = widgets.HumanTimeTip(utils.get_last_update_time())
        bottom_info_box.attach(recent_update_time_label, 0, 1, 0, 1, xoptions=gtk.FILL, xpadding=0, ypadding=4)
        bottom_info_box.attach(self.recent_update_time, 1, 2, 0, 1, xoptions=gtk.FILL, xpadding=0, ypadding=4)

        recent_upgrade_time_label = utils.create_right_align_label(_("最近更新时间："))
        self.recent_upgrade_time = widgets.HumanTimeTip(get_last_upgrade_time())
        bottom_info_box.attach(recent_upgrade_time_label, 0, 1, 1, 2, xoptions=gtk.FILL, xpadding=0, ypadding=4)
        bottom_info_box.attach(self.recent_upgrade_time, 1, 2, 1, 2, xoptions=gtk.FILL, xpadding=0, ypadding=4)

        software_mirror_label = utils.create_right_align_label(_("接收更新软件源："))
        if self.preference_dialog.current_mirror_item:
            self.software_mirror = utils.create_left_align_label( 
                self.preference_dialog.current_mirror_item.mirror.name)
        else:
            self.software_mirror = utils.create_left_align_label(utils.get_current_mirror_hostname())
        bottom_info_box.attach(software_mirror_label, 0, 1, 2, 3, xoptions=gtk.FILL, xpadding=0, ypadding=4)
        bottom_info_box.attach(self.software_mirror, 1, 2, 2, 3, xoptions=gtk.FILL, xpadding=0, ypadding=4)

        bottom_info_box_align = utils.create_align((0.0, 0.5, 0, 0), (20, 0, 0, 0))
        bottom_info_box_align.add(bottom_info_box)

        self.progress_box.pack_start(self.upgrading_progress_title, False, False)
        self.progress_box.pack_start(self.upgrading_progressbar, False, False)
        self.progress_box.pack_start(self.upgrading_progress_detail, False, False)
        self.progress_box.pack_start(bottom_info_box_align, False, False)
        self.progress_box_align = utils.create_align((0.5, 0.0, 1, 1), (2, 2, 10, 10))
        self.progress_box_align.add(self.progress_box)

        upper_box = gtk.HBox()
        upper_box.pack_start(self.upgrade_page_logo, False, False)
        upper_box.pack_start(self.progress_box_align)

        upgrading_view_align = utils.create_align((0.5, 0.5, 0, 1), (170, 40, 50, 50))
        upgrading_view_align.add(upper_box)
        self.pack_start(upgrading_view_align, True, True)

        #gtk.timeout_add(2000, lambda:self.show_error("download_failed"))

    def upload_error_log(self):
        global_event.emit("upload-error-log")

    def create_download_failed_box(self):
        download_failed_box = gtk.VBox(spacing=10)
        download_failed_box.set_size_request(400, -1)
        error_title = Label(_("更新下载失败"), text_color=DynamicColor('#ff0000'), text_size=16)

        detail_info_start = Label(_("请求的软件包在服务器上不存在，建议"))
        detail_info_middle = widgets.ActionButton(_("刷新软件列表"), lambda:global_event.emit("start-update-list"))
        detail_info_end = Label(_("后，再尝试更新。"))
        detail_info_box = gtk.HBox()
        detail_info_box.pack_start(detail_info_start, False, False)
        detail_info_box.pack_start(detail_info_middle, False, False)
        detail_info_box.pack_start(detail_info_end, False, False)

        download_failed_box.pack_start(error_title, False, False)
        download_failed_box.pack_start(detail_info_box, False, False)
        download_failed_box.pack_start(UploadErrorLabelBox(), False, False)
        return download_failed_box
    
    def create_install_failed_box(self):
        install_failed_box = gtk.VBox(spacing=10)
        install_failed_box.set_size_request(400, -1)
        error_title = Label(_("安装更新失败"), text_color=DynamicColor('#ff0000'), text_size=16)

        error_info = Label(_("出现这种情况的原因可能是本地依赖被破坏"), wrap_width=360)

        detail_info_start = Label(_("建议"))
        detail_info_middle = widgets.ActionButton(_("刷新软件列表"), lambda:global_event.emit("start-update-list"))
        detail_info_end = Label(_("后，再尝试更新。"))
        detail_info_box = gtk.HBox()
        detail_info_box.pack_start(detail_info_start, False, False)
        detail_info_box.pack_start(detail_info_middle, False, False)
        detail_info_box.pack_start(detail_info_end, False, False)

        install_failed_box.pack_start(error_title, False, False)
        install_failed_box.pack_start(error_info, False, False)
        install_failed_box.pack_start(detail_info_box, False, False)
        install_failed_box.pack_start(UploadErrorLabelBox(), False, False)
        return install_failed_box

    def create_marked_delete_system_pkgs_box(self):
        marked_delete_box = gtk.VBox(spacing=10)
        marked_delete_box.set_size_request(400, -1)
        error_title = Label(_("警告"), text_color=DynamicColor('#ff0000'), text_size=16)

        error_info = Label(_("本次升级要卸载重要的系统组件，出现这种情况的原因可能是本地依赖被破坏，或者服务端软件包依赖不正确"), wrap_width=360)
    
        detail_info_start = Label(_("建议"))
        detail_info_middle = widgets.ActionButton(_("刷新软件列表"), lambda:global_event.emit("start-update-list"))
        detail_info_end = Label(_("后，再尝试更新。"))
        detail_info_box = gtk.HBox()
        detail_info_box.pack_start(detail_info_start, False, False)
        detail_info_box.pack_start(detail_info_middle, False, False)
        detail_info_box.pack_start(detail_info_end, False, False)

        marked_delete_box.pack_start(error_title, False, False)
        marked_delete_box.pack_start(error_info, False, False)
        marked_delete_box.pack_start(detail_info_box, False, False)
        marked_delete_box.pack_start(UploadErrorLabelBox(), False, False)
        return marked_delete_box

    def switch_info(self, info_box):
        container_remove_all(self.progress_box_align)
        self.progress_box_align.add(info_box)

    def show_error(self, error_type, infos=None):
        if error_type == 'download_failed':
            self.download_failed_box = self.create_download_failed_box()
            self.switch_info(self.download_failed_box)
            self.upgrade_page_logo.change_image(utils.get_common_image('upgrade/download_failed.png'))

        elif error_type == 'upgrade_failed':
            self.install_failed_box = self.create_install_failed_box()
            self.switch_info(self.install_failed_box)
            self.upgrade_page_logo.change_image(utils.get_common_image('upgrade/upgrade_failed.png'))

        elif error_type == 'pkgs_not_in_cache':
            print infos

        elif error_type == 'pkgs_mark_failed':
            print infos
            
        elif error_type == 'marked_delete_system_pkgs':
            """infos format: list of system package names"""
            self.marked_delete_box = self.create_marked_delete_system_pkgs_box()
            self.switch_info(self.marked_delete_box)

        elif error_type == 'pkgs_parse_download_error':
            print infos

    def update(self):
        container_remove_all(self.progress_box_align)
        self.progress_box_align.add(self.progress_box)
        self.recent_update_time.timestamp = utils.get_last_update_time()
        self.recent_upgrade_time.timestamp = get_last_upgrade_time()
        if self.preference_dialog.current_mirror_item:
            self.software_mirror = utils.create_left_align_label( 
                self.preference_dialog.current_mirror_item.mirror.name)
        else:
            self.software_mirror = utils.create_left_align_label(utils.get_current_mirror_hostname())

class UploadErrorLabelBox(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        upload_info_start = Label(_("根据上面的建议，如果您尝试后依然看到本提示，您可以"))
        upload_info_middle = widgets.ActionButton(_("上报错误"), self.upload_error_log)
        upload_info_end = Label(_("。"))
        
        action_info_box = gtk.HBox()
        action_info_box.pack_start(upload_info_start, False, False)
        action_info_box.pack_start(upload_info_middle, False, False)
        action_info_box.pack_start(upload_info_end, False, False)
        self.pack_start(action_info_box, False, False)

        global_event.register_event("upload-error-log-success", self.handle_upload_success)
        global_event.register_event("upload-error-log-failed", self.handle_upload_failed)

    def show_uploading(self):
        container_remove_all(self)
        uploading = widgets.TextLoading(_("正在上传错误日志"), text_color="#000000")
        self.pack_start(uploading, False, False)
        self.show_all()

    def show_upload_sucess(self):
        uploading = Label(_("错误上报成功，感谢您的支持，我们会尽快修复您上报的错误。"))
        container_remove_all(self)
        self.pack_start(uploading, False, False)
        self.show_all()

    def show_upload_failed(self, e):
        upload_info_start = Label(_("错误上报失败，您可以再次尝试"))
        upload_info_middle = widgets.ActionButton(_("上报错误"), self.upload_error_log)
        upload_info_end = Label(_("。"))

        action_info_box = gtk.HBox()
        action_info_box.pack_start(upload_info_start, False, False)
        action_info_box.pack_start(upload_info_middle, False, False)
        action_info_box.pack_start(upload_info_end, False, False)

        error_code = Label("Error: %s" % e)

        container_remove_all(self)
        self.pack_start(action_info_box, False, False)
        self.pack_start(error_code, False, False)
        self.show_all()

    def handle_upload_success(self):
        self.show_upload_sucess()
        global_event.emit("set-cursor", None)

    def handle_upload_failed(self, e):
        self.show_upload_failed()
        global_event.emit("set-cursor", None)

    def upload_error_log(self):
        global_event.emit("set-cursor", gtk.gdk.WATCH)
        self.hide_all()
        self.show_uploading()
        global_event.emit("upload-error-log")

class UpgradePage(gtk.VBox):
    '''
    class docs
    '''
	
    def __init__(self, bus_interface, data_manager, preference_dialog):
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

        self.upgrading_view = UpgradingBox(preference_dialog)
        self.create_init_box()
        
        self.upgrade_treeview = TreeView(enable_drag_drop=False)
        self.upgrade_treeview.set_expand_column(1)
        self.upgrade_treeview.connect("items-change", self.monitor_upgrade_view)
        self.upgrade_treeview.connect("items-change", lambda treeview: global_event.emit("update-upgrade-notify-number", len(treeview.visible_items)))
        
        
        self.no_notify_treeview = TreeView(enable_drag_drop=False)
        self.no_notify_treeview.set_expand_column(1)
        self.no_notify_treeview.connect("items-change", self.monitor_no_notify_view)
        
        self.in_no_notify_page = False
        self.in_upgrading_view = False
        
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
        global_event.register_event("show-upgrading-view", self.show_upgrading_view)
        
        global_event.register_event("click-upgrade-check-button", self.click_upgrade_check_button)
        global_event.register_event("click-notify-check-button", self.click_notify_check_button)
        
        self.upgrade_treeview.draw_mask = self.draw_mask
        self.no_notify_treeview.draw_mask = self.draw_mask
        
        global_event.emit("show-updating-view")

    def cancel_upgrade_download(self, widget):
        self.bus_interface.cancel_upgrade_download(
                reply_handler=self.cancel_upgrade_download_replay,
                error_handler=lambda e:handle_dbus_error("cancel_upgrade_download -> %s" % e),
                )

    def cancel_upgrade_download_replay(self):
        self.fetch_upgrade_info()

    def hide_window(self, widget):
        global_event.emit("hide-window")

    def click_upgrade_check_button(self):
        global_event.emit("set-cursor", gtk.gdk.WATCH)

        self.bus_interface.get_upgrade_download_size(
                                        self.get_current_selected_pkgs(),
                                        reply_handler=self.update_download_size_info,
                                        error_handler=lambda e: handle_dbus_error("get_upgrade_download_size -> %s" % e),
                                        )

    def get_current_selected_pkgs(self):
        select_pkg_names = []
        for item in self.upgrade_treeview.visible_items:
            if item.check_button_buffer.active:
                select_pkg_names.append(item.pkg_name)
        return select_pkg_names

        #self.upgrade_bar.select_button.update_status(map(lambda item: item.check_button_buffer.active, self.upgrade_treeview.visible_items))

    def update_download_size_info(self, info):
        size, change_pkg_names = info
        size = int(size)
        change_pkg_names = json.loads(change_pkg_names)

        # TODO: add and remove action is different
        #for item in self.upgrade_treeview.visible_items:
            #if item.pkg_name in change_pkg_names:
                #item.check_button_buffer.active = True
        #self.upgrade_treeview.queue_draw()

        self.select_pkg_names = self.get_current_selected_pkgs()

        if self.select_pkg_names:
            self.upgrade_bar.upgrade_selected_button.set_sensitive(True)
            self.upgrade_bar.upgrade_selected_button.set_state(gtk.STATE_NORMAL)
        else:
            self.upgrade_bar.upgrade_selected_button.set_sensitive(False)

        self.upgrade_bar.message_label.set_text(_("已经选择%s个更新，将会下载%s。") % (
            len(self.select_pkg_names), utils.bit_to_human_str(size)))
        global_event.emit("set-cursor", None)
        
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
        else:
            self.upgrade_bar.set_upgrade_info(len(treeview.visible_items), self.no_notify_pkg_num)
            self.click_upgrade_check_button()
            
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

    def show_upgrading_view(self):
        container_remove_all(self)
        self.pack_start(self.upgrading_view)
        self.upgrading_view.update()

        #self.in_upgrading_view = True
        self.show_all()
            
    def show_newest_view(self):
        start = time.time()
        self.in_upgrading_view = False
        container_remove_all(self)
        container_remove_all(self.cycle_strip)
        
        self.newest_bar.set_update_time()
        self.newest_bar.set_no_notify_num(self.no_notify_pkg_num)
        self.cycle_strip.add(self.newest_bar)
        self.pack_start(self.cycle_strip, False, False)
        self.pack_start(self.newest_view, True, True)
        
        print "show newest time:", time.time() - start

    def show_network_disable_view(self):
        self.in_upgrading_view = False
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
        self.click_upgrade_check_button()
    
    def unselect_all_pkg(self):
        for item in self.upgrade_treeview.visible_items:
            item.check_button_buffer.active = False
            
        self.upgrade_treeview.queue_draw()
        self.click_upgrade_check_button()
        
    def upgrade_selected_pkg(self):
        global_event.emit("upgrade-pkg", self.select_pkg_names)        
        self.show_upgrading_view()
        
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
            pkg_name = str(pkg_name)
            download_status = str(download_status)
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
            pkg_name = str(pkg_name)
            action_status = str(action_status)
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
            
            self.current_progress = "%.2f" % float(self.current_progress)
            self.upgrading_bar.set_upgrading_message(_("Refresh applications lists %s%%") % self.current_progress)
            
        return True    
        
    def update_upgrade_progress(self, percent):
        gtk.timeout_add(500, self.render_upgrade_progress)
        self.upgrade_progress_status.append(percent)
        
    def expose_update_view(self, widget, event):
        # Init.
        cr = widget.window.cairo_create()
        rect = widget.allocation
        
        if self.update_list_pixbuf == None:
            self.update_list_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(cute_info_dir, "upgrading.png"))
        
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
            self.newest_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(cute_info_dir, "newest.png"))
        
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
            self.network_disable_pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(cute_info_dir, "network_disable.png"))
        
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()
        
        draw_pixbuf(
            cr,
            self.network_disable_pixbuf,
            rect.x + (rect.width - self.network_disable_pixbuf.get_width()) / 2,
            rect.y + (rect.height - self.network_disable_pixbuf.get_height()) / 2)
        
    def read_no_notify_config(self):
        no_notify_config_path = NO_NOTIFY_FILE
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
        self.bus_interface.add_no_notify_pkg((pkg_name, NO_NOTIFY_FILE),
                reply_handler=lambda :handle_dbus_reply("add_no_notify_pkg-> %s" % pkg_name),
                error_handler=lambda e:handle_dbus_error('add_no_notify_pkg-> %s' % pkg_name, e))
    
    def remove_no_notify_pkg(self, pkg_name):
        self.bus_interface.remove_no_notify_pkg((pkg_name, NO_NOTIFY_FILE),
                reply_handler=lambda :handle_dbus_reply("remove_no_notify_pkg-> %s" % pkg_name),
                error_handler=lambda e:handle_dbus_error('remove_no_notify_pkg-> %s' % pkg_name, e))

    def create_init_box(self):
        self.loading_box = widgets.LoadingBox()
        self.loading_box_align = utils.create_align((0.5, 0.5, 1, 1), (10, 10, 10, 10))
        self.loading_box_align.add(self.loading_box)

    def show_loading_page(self):
        container_remove_all(self)

        self.pack_start(self.loading_box_align)
    
    def fetch_upgrade_info(self, in_upgrading=False):
        self.show_loading_page()
        self.bus_interface.request_upgrade_pkgs(
                reply_handler=lambda pkg_infos:self.render_upgrade_info(pkg_infos, in_upgrading), 
                error_handler=lambda e:handle_dbus_error("request_upgrade_pkgs", e))

    def refresh_status(self, pkg_info_list):
        self.show_loading_page()
        self.bus_interface.request_status(
                reply_handler=lambda reply: self.request_status_reply_hander(
                    reply, pkg_info_list),
                error_handler=lambda e: handle_dbus_error("request_status", e),
                )

    def request_status_reply_hander(self, result, clear_action_list):
        if len(clear_action_list) > 0:
            upgraded_items = []
            for (pkg_name, marked_delete, marked_install, marked_upgrade) in clear_action_list:
                if marked_upgrade:
                    for item in self.upgrade_treeview.visible_items:
                        if item.pkg_name == pkg_name:
                            upgraded_items.append(item)
                            break
                        
            self.upgrade_treeview.delete_items(upgraded_items)
        if len(self.upgrade_treeview.visible_items) > 0:
            container_remove_all(self)
            container_remove_all(self.cycle_strip)
            
            self.cycle_strip.add(self.upgrade_bar)
            
            self.pack_start(self.cycle_strip, False, False)
            self.pack_start(self.upgrade_treeview, True, True)
        
    def render_upgrade_info(self, pkg_infos, in_upgrading):
        if in_upgrading:
            global_event.emit("show-upgrading-view")
            return 

        if len(pkg_infos) > 0:
            if self.update_list_pixbuf:
                del self.update_list_pixbuf
                self.update_list_pixbuf = None
            
            (desktop_pkg_infos, library_pkg_infos) = split_with(
                pkg_infos, 
                lambda pkg_info: self.data_manager.is_pkg_have_desktop_file((eval(pkg_info)[0])))
                
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
                
            #self.upgrade_bar.set_upgrade_info(len(self.upgrade_treeview.visible_items), self.no_notify_pkg_num)
            
            if len(upgrade_items) == 0 and len(self.upgrade_treeview.visible_items) == 0:
                self.upgrade_treeview.clear()
                global_event.emit("show-newest-view")
            else:
                if len(self.get_children()) == 0 or self.get_children()[0] != self.upgrade_treeview:
                    container_remove_all(self)
                    container_remove_all(self.cycle_strip)
                    
                    self.cycle_strip.add(self.upgrade_bar)
                    
                    self.pack_start(self.cycle_strip, False, False)
                    self.pack_start(self.upgrade_treeview, True, True)

                self.upgrade_treeview.add_items(upgrade_items)    
                
            self.no_notify_treeview.add_items(no_notify_items)
        else:
            self.upgrade_treeview.clear()
            global_event.emit("show-newest-view")

        #global_event.emit("show-upgrading-view")
        #global_event.emit("show-newest-view")

    def download_ready(self, pkg_name):
        self.upgrading_view.upgrading_progress_detail.set_text(_("分析依赖..."))

    def download_wait(self, pkg_name):
        self.upgrading_view.upgrading_progress_detail.set_text(_("依赖分析完成"))

    def download_start(self, pkg_name):
        self.upgrading_view.upgrading_progress_detail.set_text(_("开始下载..."))

    def download_failed(self, pkg_name, error):
        self.upgrading_view.show_error("download_failed")

    def download_update(self, pkg_name, percent, speed, finish_number, total, downloaded_size, total_size):
        self.upgrading_view.upgrading_progress_detail.set_text(_("已完成：%s/%s (%s/%s) 下载速度：%s/s") % (
            utils.bit_to_human_str(downloaded_size),
            utils.bit_to_human_str(total_size),
            finish_number,
            total,
            utils.bit_to_human_str(speed),
            ))
        self.upgrading_view.upgrading_progressbar.set_progress(percent)
        
    def download_finish(self, pkg_name):
        self.upgrading_view.upgrading_progress_detail.set_text(_("下载完成!"))
        self.upgrading_view.upgrading_progressbar.set_progress(100.0)

    def download_stop(self, pkg_name):
        self.upgrading_view.upgrading_progress_detail.set_text(_("下载停止！"))
            
    def download_parse_failed(self, pkg_name):
        self.upgrading_view.upgrading_progress_detail.set_text(_("依赖分析失败!"))
            
    def action_start(self, pkg_name):
        self.upgrading_view.upgrade_page_logo.change_image(utils.get_common_image("upgrade/upgrade.png"))
        self.upgrading_view.upgrading_progress_title.change_text(_("正在安装更新"))
        self.upgrading_view.upgrading_progress_detail.set_text(_("开始更新..."))
    
    def action_update(self, pkg_name, percent, status):
        self.upgrading_view.upgrading_progress_detail.set_text(str(status))
        self.upgrading_view.upgrading_progressbar.set_progress(percent)
    
    def action_finish(self, pkg_name, pkg_info_list):
        self.upgrading_view.upgrading_progress_detail.set_text(_("升级完成!"))
        self.upgrading_view.upgrading_progressbar.set_progress(100.0)

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
    STATUS_PARSE_DOWNLOAD_FAILED = 7
    STATUS_READY_DOWNLOAD = 8
    
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
        if self.row_index % 2 == 1:
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()
            
        if self.status == self.STATUS_NORMAL:
            if self.notify_button_hover:
                text_color = "#00AAFF"
            else:
                text_color = "#000000"
            
            draw_text(
                cr,
                ITEM_NO_NOTIFY_STRING,
                rect.x + rect.width - ITEM_BUTTON_PADDING_RIGHT - ITEM_NO_NOTIFY_WIDTH,
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
                #ITEM_STAR_AREA_WIDTH + ITEM_BUTTON_AREA_WIDTH,
                ]
    
    def get_column_renders(self):
        return [self.render_check_button,
                self.render_pkg_info,
                self.render_no_notify,
                #self.render_pkg_status,
                ]
    
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
            elif self.status == self.STATUS_WAIT_UPGRADE:
                if self.is_in_button_area(column, offset_x, offset_y):
                    global_event.emit("set-cursor", gtk.gdk.HAND2)
                else:
                    global_event.emit("set-cursor", None)
    
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
                    self.status_text = _("Waiting for download")
                    
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
        self.status = self.STATUS_WAIT_UPGRADE
        self.progress_buffer.progress = 0
        self.status_text = _("Waiting for upgrade")
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def download_stop(self):
        pass
            
    def download_parse_failed(self):
        self.status = self.STATUS_PARSE_DOWNLOAD_FAILED
        self.status_text = _("Analyzing dependencies failed")
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
        global_event.emit("request-clear-failed-action", self.pkg_name, ACTION_UPGRADE)    
            
    def action_start(self):
        self.status = self.STATUS_IN_UPGRADE
        self.status_text = _("Upgrading")
    
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
                
    def action_update(self, percent):
        self.status = self.STATUS_IN_UPGRADE
        self.status_text = _("Upgrading")
        self.progress_buffer.progress = percent
        
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
            
    def action_finish(self):
        self.status = self.STATUS_UPGRADE_FINISH
        self.progress_buffer.progress = 100
        self.status_text = _("Upgrade complete")
        
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
        self.star_buffer = DscStarBuffer(pkg_name)
        
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
            #self.star_buffer.render(cr, gtk.gdk.Rectangle(rect.x, rect.y, ITEM_STAR_AREA_WIDTH, ITEM_HEIGHT))
            
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
