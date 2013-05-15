#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 ~ 2013 Deepin, Inc.
#               2012 ~ 2013 Kaisheng Ye
# 
# Author:     Kaisheng Ye <kaisheng.ye@gmail.com>
# Maintainer: Kaisheng Ye <kaisheng.ye@gmail.com>
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
import gtk
import gobject
import pango
import os
import threading
import apt_pkg
from dtk.ui.dialog import PreferenceDialog, DialogBox, DIALOG_MASK_MULTIPLE_PAGE
from dtk.ui.entry import InputEntry
from dtk.ui.button import Button, CheckButton, RadioButtonBuffer
from dtk.ui.label import Label
from dtk.ui.line import HSeparator
from dtk.ui.treeview import TreeItem, TreeView
from dtk.ui.utils import get_content_size, color_hex_to_cairo, container_remove_all
from dtk.ui.draw import (draw_text, draw_vlinear)
from dtk.ui.spin import SpinBox
from dtk.ui.threads import AnonymityThread, post_gui
from dtk.ui.progressbar import ProgressBar
from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.theme import DynamicColor
from deepin_utils.file import get_parent_dir
from nls import _
from utils import (
        get_purg_flag, 
        set_purge_flag, 
        handle_dbus_reply, 
        handle_dbus_error, 
        get_update_interval, 
        set_update_interval,
        get_software_download_dir,
        set_software_download_dir,
        )
from mirror_test import Mirror, MirrorTest
from events import global_event
import aptsources
import aptsources.distro
from aptsources.sourceslist import SourcesList

from constant import PROGRAM_VERSION

class MirrorItem(TreeItem):

    __gsignals__ = {
        "item-clicked" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    PADDING_X = 5
    NAME_WIDTH = 90

    def __init__(self, mirror, item_clicked_callback=None):

        TreeItem.__init__(self)
        self.mirror = mirror
        self.radio_button = RadioButtonBuffer()

        if item_clicked_callback:
            self.connect('item-clicked', item_clicked_callback)

    def render_odd_line_bg(self, cr, rect):
        #if self.row_index % 2 == 1:
        cr.set_source_rgba(1, 1, 1, 0.9)
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()

    def render_radio_button(self, cr, rect):
        self.render_odd_line_bg(cr, rect)
        
        rect.y += 3
        rect.x -= 2
        self.radio_button.render(cr, rect)

    def render_name(self, cr, rect):
        self.render_odd_line_bg(cr, rect)

        self.name = self.mirror.name
        self.render_background(cr, rect)
        #rect.x += self.PADDING_X
        rect.width -= self.PADDING_X * 2        
        if self.name:
            (text_width, text_height) = get_content_size(self.name)
            draw_text(cr, self.name, rect.x, rect.y, rect.width, rect.height,
                    alignment = pango.ALIGN_LEFT)
        else:
            name = _("No name")
            (text_width, text_height) = get_content_size(name)
            draw_text(cr, name, rect.x, rect.y, rect.width, rect.height,
                    alignment = pango.ALIGN_LEFT)

    def render_url(self, cr, rect):
        self.render_odd_line_bg(cr, rect)

        self.mirror_url = self.mirror.get_repo_url()
        self.render_background(cr, rect)
        #rect.x += self.NAME_WIDTH
        rect.width -= self.PADDING_X * 2
        if self.mirror_url:
            (text_width, text_height) = get_content_size(self.mirror_url)
            draw_text(cr, self.mirror_url, rect.x, rect.y, rect.width, rect.height,
                    alignment = pango.ALIGN_LEFT)
        else:
            mirror_url = _("No mirror url")
            (text_width, text_height) = get_content_size(mirror_url)
            draw_text(cr, mirror_url, rect.x, rect.y, rect.width, rect.height,
                    alignment = pango.ALIGN_LEFT)
        
    def get_column_renders(self):
        return [self.render_radio_button, self.render_name, self.render_url]

    def get_column_widths(self):
        '''docstring for get_column_widths'''
        return [30, self.NAME_WIDTH, 300]

    def get_height(self):
        return 22

    def select(self):
        self.is_select = True
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def unselect(self):
        self.is_select = False
        self.unhighlight()
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def button_press(self, column, x, y):
        if column == 0:
            self.radio_button.press_button(x, y)
        else:
            self.radio_button.set_active()
        self.emit('item-clicked')

    def button_release(self, column, x, y):
        if column == 0:
            if self.radio_button.release_button(x,y):
                self.radio_button.get_active()
                #self.set_autorun_state(state)
    
    def single_click(self, column, offset_x, offset_y):
        self.is_select = True
        self.redraw()

    def double_click(self, column, offset_x, offset_y):
        self.is_double_click = True
        #self.set_autorun_state(not self.autorun)


    def redraw(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)
    

    def render_background(self,  cr, rect):
        #if self.is_highlight:
            #background_color = app_theme.get_color("globalItemHighlight")
        #else:
        #if self.is_select:
            #background_color = app_theme.get_color("globalItemSelect")
        #else:
            #if  self.is_hover:
                #background_color = app_theme.get_color("globalItemHover")
            #else:
                #background_color = app_theme.get_color("tooltipText")
        #cr.set_source_rgb(*color_hex_to_cairo(background_color.get_color()))
        #cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        #cr.fill()
        pass

def create_separator_box(padding_x=0, padding_y=0):    
    separator_box = HSeparator(
        app_theme.get_shadow_color("hSeparator").get_color_info(),
        padding_x, padding_y)
    return separator_box

TABLE_ROW_SPACING = 25
CONTENT_ROW_SPACING = 8


class TestProgressDialog(object):

    def __init__(self, title, short_desc, description):
        self.dialog = DialogBox(title, 376, 188, DIALOG_MASK_MULTIPLE_PAGE, self.dialog_close_action)

        test_label = Label(short_desc, text_size=20, text_color=DynamicColor('#b4dded'))
        test_label_align = gtk.Alignment(0.5, 0.5, 0, 0)
        test_label_align.set_padding(4, 4, 5, 5)
        test_label_align.add(test_label)

        message_label = Label(description)
        message_label_align = gtk.Alignment(0, 0.5, 1, 1)
        message_label_align.set_padding(4, 4, 20, 5)
        message_label_align.add(message_label)

        self.progressbar = ProgressBar()
        self.progressbar.set_size_request(350, 12)
        progressbar_align = gtk.Alignment(0.5, 0.5, 0, 0)
        message_label_align.set_padding(4, 4, 5, 5)
        progressbar_align.add(self.progressbar)

        self.action_message_label = Label()
        self.action_message_label_align = gtk.Alignment(0, 0.5, 1, 1)
        self.action_message_label_align.set_padding(4, 4, 7, 5)
        self.action_message_label_align.add(self.action_message_label)

        self.dialog.body_box.pack_start(test_label_align, False, False)
        self.dialog.body_box.pack_start(message_label_align, False, False)
        self.dialog.body_box.pack_start(progressbar_align, False, False)
        self.dialog.body_box.pack_start(self.action_message_label_align, False, False)

    def dialog_close_action(self):
        pass

class AboutBox(gtk.VBox):    
    
    def __init__(self):
        gtk.VBox.__init__(self)
        main_box = gtk.VBox(spacing=15)
        logo_image = gtk.image_new_from_pixbuf(gtk.gdk.pixbuf_new_from_file(os.path.join(get_parent_dir(__file__, 2), "image", "logo16.png")))
        logo_name = Label(_("Deepin Software Center"), text_size=10)
        logo_box = gtk.HBox(spacing=2)
        logo_box.pack_start(logo_image, False, False)
        logo_box.pack_start(logo_name, False, False)
        
        version_label = Label(_("Version:"))
        version_content = Label(PROGRAM_VERSION, DynamicColor('#4D5154'))
        # publish_label = Label(_("Release date:"))
        # publish_content = Label("2012.07.12", light_color)
        info_box = gtk.HBox(spacing=5)
        info_box.pack_start(version_label, False, False)
        info_box.pack_start(version_content, False, False)
        # info_box.pack_start(publish_label, False, False)
        # info_box.pack_start(publish_content, False, False)
        
        title_box = gtk.HBox()
        title_box.pack_start(logo_box, False, False)
        align = gtk.Alignment()
        align.set(0, 0, 0, 1)
        title_box.pack_start(align, True, True)
        title_box.pack_start(info_box, False, False)
        
        describe = "       深度软件中心是Linux平台通用的软件管理中心，精选了2600多款优秀软件，集成了软件安装与卸载、软件仓库、热门软件推荐等多项功能。支持一键快速安装软件、多线程下载及智能清理下载缓存。提供专题介绍，分享好软件。\n\n深度软件中心是自由软件，遵循自由软件基金会发布的GNU通用公共许可证第三版。"
        
        describe_label = Label(describe, enable_select=False, wrap_width=400, text_size=10)
        main_box.pack_start(title_box, False, False)
        main_box.pack_start(create_separator_box(), False, True)
        main_box.pack_start(describe_label, False, False)
        
        main_align = gtk.Alignment()
        main_align.set_padding(25, 0, 12, 0)
        main_align.set(0, 0, 1, 1)
        main_align.add(main_box)
        self.add(main_align)

class DscPreferenceDialog(PreferenceDialog):
    def __init__(self):
        PreferenceDialog.__init__(self, 566, 488)

        self.normal_settings = gtk.VBox()
        self.normal_settings.set_spacing(TABLE_ROW_SPACING)
        self.normal_settings.pack_start(self.create_uninstall_box(), False, True)
        self.normal_settings.pack_start(self.create_download_dir_table(), False, True)

        self.normal_settings_align = gtk.Alignment(0, 0, 1, 1)
        self.normal_settings_align.set_padding(padding_left=5, padding_right=5, padding_top=25, padding_bottom=10)
        self.normal_settings_align.add(self.normal_settings)

        self.mirror_settings = gtk.VBox()
        self.mirror_settings.set_app_paintable(True)
        self.mirror_settings.connect("expose-event", self.mirror_settings_align_expose)
        self.mirror_settings.set_spacing(TABLE_ROW_SPACING)
        self.mirror_settings.pack_start(self.create_mirror_select_table(), False, True)
        self.mirror_settings.pack_start(self.create_source_update_frequency_table(), False, True)

        self.mirror_settings_inner_align = gtk.Alignment(0.5, 0.5, 1, 1)
        self.mirror_settings_inner_align.set_padding(padding_top=25, padding_bottom=10, padding_left=5, padding_right=0)
        self.mirror_settings_inner_align.add(self.mirror_settings)

        self.mirror_settings_scrolled_win = ScrolledWindow()
        self.mirror_settings_scrolled_win.add_child(self.mirror_settings_inner_align)

        self.mirror_settings_align = gtk.Alignment(0, 0, 1, 1)
        self.mirror_settings_align.set_padding(padding_left=0, padding_right=0, padding_top=0, padding_bottom=3)
        self.mirror_settings_align.add(self.mirror_settings_scrolled_win)

        self.set_preference_items([
            ("常规", self.normal_settings_align),
            ("软件源", self.mirror_settings_align),
            ("关于", AboutBox()),
            ])
        
    def mirror_settings_align_expose(self, widget, event=None):
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # draw backgound
        cr.rectangle(*rect)
        #cr.set_source_rgb(*color_hex_to_cairo("#ff0000"))
        cr.set_source_rgba(1, 1, 1, 0)
        cr.fill()

    def mirror_select_action(self, hostname):
        self.data_manager.change_source_list(hostname, reply_handler=handle_dbus_reply, error_handler=handle_dbus_error)

    def create_mirror_select_table(self):
        main_table = gtk.Table(4, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)
        
        dir_title_label = Label(_("Select software mirror"))
        dir_title_label.set_size_request(400, 12)
        label_align = gtk.Alignment()
        label_align.set_padding(0, 0, 0, 0)
        label_align.add(dir_title_label)

        self.mirrors_dir = os.path.join(get_parent_dir(__file__, 2), 'mirrors')
        self.current_mirror_uri = self.get_current_mirror_uri()
        self.mirror_items = self.get_mirror_items()
        self.mirror_view = TreeView(self.mirror_items,
                                enable_drag_drop=False,
                                enable_hover=False,
                                enable_multiple_select=False,
                                mask_bound_height=0,
                             )
        self.mirror_view.set_expand_column(2)
        self.mirror_view.set_size_request(-1, len(self.mirror_view.visible_items) * self.mirror_view.visible_items[0].get_height())
        self.mirror_view.draw_mask = self.mirror_treeview_draw_mask
        #self.display_current_mirror()

        self.mirror_test_button = Button(_("Select Best Mirror"))
        self.mirror_test_button.connect('clicked', self.test_mirror_action)
        mirror_test_button_align = gtk.Alignment(0, 0.5, 0, 0)
        mirror_test_button_align.set_padding(0, 0, 7, 5)
        mirror_test_button_align.add(self.mirror_test_button)

        self.mirror_message_label = Label()
        mirror_message_label_align = gtk.Alignment(0, 0.5, 1, 1)
        mirror_message_label_align.set_padding(0, 0, 5, 5)
        mirror_message_label_align.add(self.mirror_message_label)
        self.mirror_message_hbox = gtk.HBox()
        self.mirror_message_hbox.pack_start(mirror_message_label_align, False)

        self.mirror_test_progressbar = ProgressBar()

        main_table.attach(label_align, 0, 2, 0, 1, yoptions=gtk.FILL, xpadding=8)
        main_table.attach(create_separator_box(), 0, 2, 1, 2, yoptions=gtk.FILL)
        main_table.attach(self.mirror_view, 0, 2, 2, 3, xpadding=10, xoptions=gtk.FILL)
        main_table.attach(mirror_test_button_align, 0, 1, 3, 4, xoptions=gtk.FILL)
        main_table.attach(self.mirror_message_hbox, 1, 2, 3, 4, xoptions=gtk.FILL)
        
        self.update_list_dialog = TestProgressDialog("正在更新", "更新软件列表中", " 您已经更改了软件下载源，现在正在更新软件列表...")
        global_event.register_event("mirror-changed", lambda :self.update_list_dialog.dialog.show_all())
        global_event.register_event('update-progress-in-update-list-dialog', self.show_update_list_dialog)

        self.test_mirror_dialog = TestProgressDialog("测试下载服务器", "正在测试中", " 为了找到更好的镜像地址，将会执行一系列的测试。")
        global_event.register_event("test-mirror-dialog-update-progress", self.show_test_mirror_dialog)

        return main_table
    
    def show_update_list_dialog(self, percent, status_message):
        if percent != -1:
            self.update_list_dialog.progressbar.progress_buffer.progress = percent
            self.update_list_dialog.action_message_label.set_text(status_message)
        else:
            self.update_list_dialog.action_message_label.set_text(status_message)
            self.update_list_dialog.dialog.hide()

    def show_test_mirror_dialog(self, percent, action):
        if percent != 100:
            self.test_mirror_dialog.progressbar.progress_buffer.progress = percent
            self.test_mirror_dialog.action_message_label.set_text(action)
        else:
            self.test_mirror_dialog.dialog.hide()

    def display_current_mirror(self):
        vadj = self.mirror_view.scrolled_window.get_vadjustment()
        length = self.mirror_items.index(self.current_mirror_item) * 30
        vadj.set_value(min(vadj.upper-vadj.page_size-1, length))

    def test_mirror_action(self, widget):
        self.test_mirror_dialog.dialog.show_all()
        distro = aptsources.distro.get_distro()
        distro.get_sources(SourcesList())
        pipe = os.popen("dpkg --print-architecture")
        arch = pipe.read().strip()
        test_file = "dists/%s/Contents-%s.gz" % \
                    (distro.source_template.name,
                    arch)

        self.running = threading.Event()
        self.running.set()
        progress_update = threading.Event()
        self.mirror_test = MirrorTest(self.mirrors_list,
                        test_file,
                        progress_update,
                        self.running)
        self.mirror_test.start()

        # now run the tests in a background thread, and update the UI on each event
        gtk.timeout_add(100, self.update_progress)

    def update_progress(self):
        if self.mirror_test.running.is_set():

            #while gtk.events_pending():
                #gtk.main_iteration_do(False)

            # don't spin the CPU until there's something to update; but update the
            # UI at least every 100 ms
            self.mirror_test.event.wait(0.1)

            if self.mirror_test.event.is_set():
                global_event.emit('test-mirror-dialog-update-progress', self.mirror_test.progress[2]*100, self.mirror_test.action)
                print self.mirror_test.progress[2]*100
                self.mirror_test.event.clear()
            return True
        else:
            if self.mirror_test.best != None:
                for item in self.mirror_items:
                    if item.mirror == self.mirror_test.best[1]:
                        print item.mirror.get_repo_url()
                        self.mirror_clicked_callback(item)
            else:
                pass
                #dialogs.show_error_dialog(self.dialog, 
                                        #_("No suitable download server was found"),
                                        #_("Please check your Internet connection."))
            return False

    def get_current_mirror_uri(self):
        apt_pkg.init_config()
        apt_pkg.init_system()
        source_list_obj = apt_pkg.SourceList()
        source_list_obj.read_main_list()
        uri = source_list_obj.list[0].uri.split(":")[0] + "://" + source_list_obj.list[0].uri.split("/")[2]
        return uri

    def mirror_treeview_draw_mask(self, cr, x, y, w, h):
        cr.set_source_rgba(1, 1, 1, 0.9)
        cr.rectangle(x, y, w, h)
        cr.fill()

    def get_mirror_items(self):
        items = []
        self.mirrors_list = []
        for ini_file in os.listdir(self.mirrors_dir):
            m = Mirror(os.path.join(self.mirrors_dir, ini_file))
            item = MirrorItem(m, self.mirror_clicked_callback)
            if m.get_change_uri() == self.current_mirror_uri:
                item.radio_button.active = True
                self.current_mirror_item = item
            self.mirrors_list.append(m)
            items.append(item)
        return items

    def mirror_clicked_callback(self, item):
        for i in self.mirror_items:
            if i != item and i.radio_button.active == True:
                i.radio_button.active = False
            elif i == item:
                i.radio_button.active = True
        if item != self.current_mirror_item:
            global_event.emit('change-mirror', item.mirror.get_change_uri())
            self.current_mirror_item = item

    def create_source_update_frequency_table(self):
        main_table = gtk.Table(3, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)
        
        dir_title_label = Label(_("Source update"))
        dir_title_label.set_size_request(200, 12)
        label_align = gtk.Alignment()
        label_align.set_padding(0, 0, 0, 0)
        label_align.add(dir_title_label)
        
        update_label = Label(_("Interval time: "))
        self.update_spin = SpinBox(int(get_update_interval()), 0, 168, 1)
        self.update_spin.connect("value-changed", lambda w, v: set_update_interval(v))
        hour_lablel = Label(_(" hour"))        
        hour_lablel.set_size_request(50, 12)
        spin_hbox = gtk.HBox(spacing=3)
        spin_hbox.pack_start(update_label, False, False)
        spin_hbox.pack_start(self.update_spin, False, False)
        spin_hbox.pack_start(hour_lablel, False, False)

        main_table.attach(label_align, 0, 2, 0, 1, yoptions=gtk.FILL, xpadding=8)
        main_table.attach(create_separator_box(), 0, 2, 1, 2, yoptions=gtk.FILL)
        main_table.attach(spin_hbox, 0, 2, 2, 3, xpadding=10, xoptions=gtk.FILL)
        return main_table

    def create_download_dir_table(self):    
        main_table = gtk.Table(3, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)
        
        dir_title_label = Label(_("Download directory"))
        dir_title_label.set_size_request(200, 12)
        label_align = gtk.Alignment()
        label_align.set_padding(0, 0, 0, 0)
        label_align.add(dir_title_label)
        
        self.dir_entry = InputEntry()
        self.dir_entry.set_text(get_software_download_dir())
        self.dir_entry.set_editable(False)        
        self.dir_entry.set_size(250, 25)
        
        modify_button = Button(_("Change"))
        modify_button.connect("clicked", self.change_download_save_dir)
        hbox = gtk.HBox(spacing=5)
        hbox.pack_start(self.dir_entry, False, False)
        hbox.pack_start(modify_button, False, False)
        
        main_table.attach(label_align, 0, 2, 0, 1, yoptions=gtk.FILL, xpadding=8)
        main_table.attach(create_separator_box(), 0, 2, 1, 2, yoptions=gtk.FILL)
        main_table.attach(hbox, 0, 2, 2, 3, xpadding=10, xoptions=gtk.FILL)
        return main_table

    def create_uninstall_box(self):
        main_table = gtk.Table(2, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)
        uninstall_title_label = Label(_("On uninstall software"))
        uninstall_title_label.set_size_request(350, 12)
        
        # mini_check_button

        self.delete_check_button = CheckButton(_("Delete configuration files"))
        self.delete_check_button.set_active(get_purg_flag())
        self.delete_check_button.connect("toggled", lambda w: set_purge_flag(self.delete_check_button.get_active()))
        
        main_table.attach(uninstall_title_label, 0, 2, 0, 1, yoptions=gtk.FILL, xpadding=8)
        main_table.attach(create_separator_box(), 0, 2, 1, 2, yoptions=gtk.FILL)
        main_table.attach(self.delete_check_button, 0, 1, 2, 3, yoptions=gtk.FILL)
        
        return main_table

    def change_download_save_dir(self, widget):
        local_dir = WinDir(False).run()
        if local_dir:
            local_dir = os.path.expanduser(local_dir)
            if local_dir != get_software_download_dir():
                self.dir_entry.set_editable(True)        
                self.dir_entry.set_text(local_dir)
                self.dir_entry.set_editable(False)
                set_software_download_dir(local_dir)
                global_event.emit('download-directory-changed')

class WinDir(gtk.FileChooserDialog):
    '''Open chooser dir dialog'''

    def __init__(self, return_uri=True, title=_("Select Directory")):
        gtk.FileChooserDialog.__init__(self, title, None, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                       (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                        gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        self.return_uri = return_uri
        self.set_modal(True)
        
    def run(self):    
        response = gtk.FileChooserDialog.run(self)
        folder = None
        if response == gtk.RESPONSE_OK:
            if self.return_uri:
                folder = self.get_uri()
            else:
                folder = self.get_filename()
        self.destroy()    
        return folder

gtk.gdk.threads_init()
preference_dialog = DscPreferenceDialog()

if __name__ == '__main__':
    #d = TestProgressDialog()
    #d.dialog.show_all()
    preference_dialog.show_all()
    gtk.main()
