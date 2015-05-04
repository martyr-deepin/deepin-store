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
import dbus
import subprocess

#from dtk.ui.threads import post_gui
from dtk.ui.dialog import PreferenceDialog
from dtk.ui.entry import InputEntry
from dtk.ui.button import Button, CheckButton
from dtk.ui.label import Label
from dtk.ui.line import HSeparator
from dtk.ui.treeview import TreeView, TreeItem, get_background_color
from dtk.ui.utils import (
        get_content_size, is_in_rect, alpha_color_hex_to_cairo,
        color_hex_to_cairo)
from dtk.ui.draw import draw_text, draw_pixbuf
from dtk.ui.spin import SpinBox
#from dtk.ui.progressbar import ProgressBar
#from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.theme import DynamicColor, ui_theme
from dtk.ui.combo import ComboBox
from deepin_utils.file import get_parent_dir
from deepin_utils.ipc import is_dbus_name_exists

from nls import _
from utils import (
        get_purg_flag,
        set_purge_flag,
        #handle_dbus_reply,
        #handle_dbus_error,
        get_update_interval,
        set_update_interval,
        get_software_download_dir,
        set_software_download_dir,
        get_download_number,
        set_download_number,
        )
import utils
from mirror_test import all_mirrors, get_best_mirror
from events import global_event
#import aptsources
#import aptsources.distro
#from loading_widget import Loading
from constant import PROGRAM_VERSION
#import time

from dialog_widgets import WaitingDialog

DSC_UPDATE_DAEMON_NAME = "com.linuxdeepin.softwarecenter.update.daemon"
DSC_UPDATE_DAEMON_PATH = "/com/linuxdeepin/softwarecenter/update/daemon"

class SelectedButtonBuffer(gobject.GObject):
    '''
    RaidoButtonBuffer class.

    Use to render RaidoButton in TreeView widget.

    @undocumented: render
    '''

    STATE_NORMAL = 1
    STATE_PRELIGHT = 2
    STATE_ACTIVE = 3

    def __init__(self,
                 active=False,
                 render_padding_x=0,
                 render_padding_y=0,
                 ):
        '''
        Initialize RadioButtonBuffer class.

        @param active: Set True to active buffer status, default is False.
        @param render_padding_x: Horizontal padding value, default is 0.
        @param render_padding_y: Vertical padding value, default is 0.
        '''
        gobject.GObject.__init__(self)
        #self.inactive_normal_dpixbuf = ui_theme.get_pixbuf("button/radio_button_inactive_normal.png")
        #self.active_normal_dpixbuf = ui_theme.get_pixbuf("button/radio_button_active_normal.png")
        #self.inactive_hover_dpixbuf = ui_theme.get_pixbuf("button/radio_button_inactive_hover.png")
        #self.active_hover_dpixbuf = ui_theme.get_pixbuf("button/radio_button_active_hover.png")
        #self.inactive_press_dpixbuf = ui_theme.get_pixbuf("button/radio_button_inactive_press.png")
        #self.active_press_dpixbuf = ui_theme.get_pixbuf("button/radio_button_active_press.png")
        self.active_dpixbuf = app_theme.get_pixbuf("mirror/check_box-2.png")

        self.render_padding_x = render_padding_x
        self.render_padding_y = render_padding_y

        pixbuf = self.active_dpixbuf.get_pixbuf()
        self.render_width = pixbuf.get_width()
        self.render_height = pixbuf.get_height()

        self.active = active
        self.button_state = self.STATE_NORMAL

    def get_active(self):
        '''
        Get active status of raido button buffer.

        @return: Return True if buffer is in active status.
        '''
        return self.active

    def set_active(self):
        self.button_state = self.STATE_ACTIVE
        self.button_press_flag = False
        self.active = True
        #self.queue_draw()

    def is_in_button_area(self, x, y):
        '''
        Helper function to detect button event is in button area.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        return is_in_rect((x, y), (self.render_padding_x, self.render_padding_y, self.render_width, self.render_height))

    def press_button(self, x, y):
        '''
        Helper function to handle button-press-event.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        if self.is_in_button_area(x, y) and self.active == False:
            self.button_state = self.STATE_ACTIVE
            self.button_press_flag = True

            self.active = True

            return True
        else:
            return False

    def release_button(self, x, y):
        '''
        Helper function to handle button-release-event.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        if self.is_in_button_area(x, y):
            self.button_state = self.STATE_ACTIVE
            self.button_press_flag = False

            return True
        else:
            return False

    def motion_button(self, x, y):
        '''
        Helper function to handle motion-notify event.

        You can add this function in callback function of TreeItem, such as:
         - hover/unhover
         - motion_notify
         - button_press/button_release
         - single_click/double_click

        @param x: X coordinate of button event.
        @param y: Y coordiante of button event.
        '''
        if self.is_in_button_area(x, y):
            if self.button_state != self.STATE_PRELIGHT:
                self.button_state = self.STATE_PRELIGHT

                return True
            else:
                return False
        else:
            if self.button_state != self.STATE_NORMAL:
                self.button_state = self.STATE_NORMAL

                return True
            else:
                return False

    def render(self, cr, rect):
        # Get pixbuf along with button's sate.
        image = None
        if self.button_state == self.STATE_NORMAL:
            if self.active:
                image = self.active_dpixbuf.get_pixbuf()
            else:
                image = None

        # Draw button.
        if image:
            draw_pixbuf(
                cr,
                image,
                rect.x + (rect.width - image.get_width())/2,
                rect.y + (rect.height - image.get_height())/2
                )

gobject.type_register(SelectedButtonBuffer)

class MirrorItem(TreeItem):

    __gsignals__ = {
        "item-clicked" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    PADDING_X = 5
    PADDING_Y = 4
    PADDING_MIDDLE = 2

    RADIO_BUTTON_AREA_WIDTH = 20
    NAME_AREA_WIDTH = 124
    URL_AREA_WIDTH = 300

    ITEM_BUTTON_PADDING_RIGHT = 2
    ITEM_HEIGHT = 25

    BUTTON_NORMAL = 1
    BUTTON_HOVER = 2
    BUTTON_PRESS = 3

    def __init__(self, mirror, item_clicked_callback=None):

        TreeItem.__init__(self)
        self.mirror = mirror
        self.radio_button = SelectedButtonBuffer(render_padding_x=2, render_padding_y=4)


        self.pixbuf_normal = app_theme.get_pixbuf("mirror/server_small_normal.png").get_pixbuf()
        self.pixbuf_hover = app_theme.get_pixbuf("mirror/server_small_hover.png").get_pixbuf()
        self.pixbuf_press = app_theme.get_pixbuf("mirror/server_small_press.png").get_pixbuf()

        (self.button_width, self.button_height) = self.pixbuf_normal.get_width(), self.pixbuf_normal.get_height()
        self.button_status = self.BUTTON_NORMAL

        if item_clicked_callback:
            self.connect('item-clicked', item_clicked_callback)

    def is_in_button_area(self, column, offset_x, offset_y):
        return (column == 2
                and is_in_rect((offset_x, offset_y),
                               (self.get_column_widths()[column] - self.ITEM_BUTTON_PADDING_RIGHT - self.button_width,
                                (self.ITEM_HEIGHT - self.button_height) / 2,
                                self.button_width,
                                self.button_height)))

    def get_content_complete(self):
        name_complete = get_content_size(self.mirror.name)[0] < self.NAME_AREA_WIDTH
        url_complate = get_content_size(self.mirror.hostname)[0] < self.URL_AREA_WIDTH
        return name_complete and url_complate

    def render_radio_button(self, cr, rect):
        self.render_background(cr, rect)
        self.radio_button.render(cr, rect)

    def render_url(self, cr, rect):
        self.render_background(cr, rect)
        self.mirror_url = self.mirror.hostname
        self.name = "<b>%s</b>" % self.mirror.name

        (name_width, name_height) = get_content_size(self.name)
        draw_text(cr, self.name, rect.x, rect.y + self.PADDING_Y, rect.width, name_height,
                alignment = pango.ALIGN_LEFT)

        (url_width, url_height) = get_content_size(self.mirror_url)
        draw_text(cr, self.mirror_url, rect.x, rect.y + name_height + self.PADDING_Y + self.PADDING_MIDDLE, rect.width, url_height,
                alignment = pango.ALIGN_LEFT)

    def render_change_button(self, cr, rect):
        self.render_background(cr, rect)
        if self.is_hover and not self.radio_button.active:
            if self.button_status == self.BUTTON_NORMAL:
                self.pixbuf = self.pixbuf_normal
            elif self.button_status == self.BUTTON_HOVER:
                self.pixbuf = self.pixbuf_hover
            elif self.button_status == self.BUTTON_PRESS:
                self.pixbuf = self.pixbuf_press

            draw_pixbuf(
                cr,
                self.pixbuf,
                rect.x,
                rect.y + (rect.height - self.pixbuf.get_height())/2,
                )

    def get_column_renders(self):
        return [self.render_radio_button, self.render_url, self.render_change_button]

    def get_column_widths(self):
        '''docstring for get_column_widths'''
        return [30, -1, 60]

    def get_height(self):
        (name_width, name_height) = get_content_size(self.mirror.name)
        return name_height * 2 + self.PADDING_Y * 2 + self.PADDING_MIDDLE

    def select(self):
        self.is_select = True
        self.redraw()

    def unselect(self):
        self.is_select = False
        self.unhighlight()
        self.redraw()

    def unhighlight(self):
        self.is_highlight = False
        self.redraw()

    def highlight(self):
        self.is_highlight = True
        self.redraw()

    def unhover(self, column, offset_x, offset_y):
        self.is_hover = False
        self.redraw()

    def hover(self, column, offset_x, offset_y):
        self.is_hover = True
        self.redraw()

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

    def redraw(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def render_background(self,  cr, rect):
        backgound_color = ("#FFFFFF", 0.9)
        cr.set_source_rgba(*alpha_color_hex_to_cairo(backgound_color))
        cr.rectangle(rect.x, rect.y, rect.width, rect.height)
        cr.fill()

        background_color = get_background_color(self.is_highlight, False, self.is_hover)
        if background_color:
            cr.set_source_rgb(*color_hex_to_cairo(ui_theme.get_color(background_color).get_color()))
            cr.rectangle(rect.x, rect.y, rect.width, rect.height)
            cr.fill()

    def motion_notify(self, column, offset_x, offset_y):
        if self.is_in_button_area(column, offset_x, offset_y):
            self.button_status = self.BUTTON_HOVER

            if self.redraw_request_callback:
                self.redraw_request_callback(self)
        elif self.button_status != self.BUTTON_NORMAL:
            self.button_status = self.BUTTON_NORMAL

            if self.redraw_request_callback:
                self.redraw_request_callback(self)

    def button_press(self, column, offset_x, offset_y):
        if self.is_in_button_area(column, offset_x, offset_y):
            self.emit("item-clicked")

def create_separator_box(padding_x=0, padding_y=0):
    separator_box = HSeparator(
        app_theme.get_shadow_color("hSeparator").get_color_info(),
        padding_x, padding_y)
    return separator_box

TABLE_ROW_SPACING = 25
CONTENT_ROW_SPACING = 8

class BaseBox(gtk.VBox):
    def __init__(self):
        gtk.VBox.__init__(self)
        self.main_box = gtk.VBox()
        self.main_box.set_size_request(400, -1)
        self.main_box.set_spacing(TABLE_ROW_SPACING)

        self.main_box_align = gtk.Alignment(0, 0, 1, 1)
        self.main_box_align.set_padding(padding_left=12, padding_right=5, padding_top=25, padding_bottom=10)
        self.main_box_align.add(self.main_box)
        self.add(self.main_box_align)

class AboutBox(BaseBox):

    def __init__(self):
        BaseBox.__init__(self)

        logo_image = gtk.image_new_from_icon_name("deepin-software-center", 16)
        if not logo_image:
            logo_image = utils.get_common_image_pixbuf("logo16.png")
        else:
            logo_image.set_pixel_size(16)

        logo_name = Label(_("Deepin Store"), text_size=10)
        logo_box = gtk.HBox(spacing=2)
        logo_box.pack_start(logo_image, False, False)
        logo_box.pack_start(logo_name, False, False)

        version_label = Label(_("Version:"))
        version_content = Label(PROGRAM_VERSION, DynamicColor('#4D5154'))
        info_box = gtk.HBox(spacing=5)
        info_box.pack_start(version_label, False, False)
        info_box.pack_start(version_content, False, False)

        align = gtk.Alignment()
        align.set(0, 0, 0, 1)

        title_box = gtk.HBox()
        title_box.pack_start(logo_box, False, False)
        title_box.pack_start(align, True, True)
        title_box.pack_start(info_box, False, False)

        describe = _("Deepin Store is a commonly used software center on Linux. "
                "We selected more than 2,600 excellent applications with many "
                "functions of installation and uninstalling, software repository "
                "and popular recommendations, which supports 1-click quick "
                "installation, multi-threaded download and clearing of cached "
                "packages. It provides topics for software introduction and "
                "shares good applications.\n"
                "\n"
                "Deepin Store is a free software licensed under GNU GPLv3.")

        describe_label = Label(describe, enable_select=False, wrap_width=400, text_size=10)
        self.main_box.pack_start(title_box, False, False)
        self.main_box.pack_start(create_separator_box(), False, True)
        self.main_box.pack_start(describe_label, False, False)

class GeneralBox(BaseBox):
    def __init__(self):
        BaseBox.__init__(self)

        self.main_box.pack_start(self.create_uninstall_box(), False, True)
        self.main_box.pack_start(self.create_download_dir_table(), False, True)

    def create_uninstall_box(self):
        main_table = gtk.Table(2, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)
        uninstall_title_label = Label(_("On uninstalling the software"))

        # mini_check_button
        self.delete_check_button = CheckButton(_("Delete configuration files"))
        self.delete_check_button.set_active(get_purg_flag())
        self.delete_check_button.connect("toggled", lambda w: set_purge_flag(self.delete_check_button.get_active()))

        main_table.attach(uninstall_title_label, 0, 2, 0, 1, yoptions=gtk.FILL)
        main_table.attach(create_separator_box(), 0, 2, 1, 2, yoptions=gtk.FILL)
        main_table.attach(self.delete_check_button, 0, 1, 2, 3, yoptions=gtk.FILL)

        return main_table

    def create_download_dir_table(self):
        main_table = gtk.Table(4, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)

        dir_title_label = Label(_("Download settings"))
        dir_title_label.set_size_request(200, 12)
        label_align = gtk.Alignment()
        label_align.set_padding(0, 0, 0, 0)
        label_align.add(dir_title_label)

        download_number_label = Label(_('Maximum number of download tasks: '))
        self.download_number_comobox = ComboBox(
                items = [(str(i+1), i+1) for i in range(10)],
                select_index = int(get_download_number())-1,
                )
        self.download_number_comobox.connect("item-selected", self.download_number_comobox_changed)
        download_number_hbox = gtk.HBox(spacing=5)
        download_number_hbox.pack_start(download_number_label, False, False)
        download_number_hbox.pack_start(self.download_number_comobox, False, False)

        change_download_dir_label = Label(_("Download directory: "))
        self.dir_entry = InputEntry()
        self.dir_entry.set_text(get_software_download_dir())
        self.dir_entry.set_editable(False)
        self.dir_entry.set_size(200, 25)

        modify_button = Button(_("Change"))
        modify_button.connect("clicked", self.change_download_save_dir)
        download_dir_hbox = gtk.HBox(spacing=5)
        download_dir_hbox.pack_start(change_download_dir_label, False, False)
        download_dir_hbox.pack_start(self.dir_entry, False, False)
        download_dir_hbox.pack_start(modify_button, False, False)

        main_table.attach(label_align, 0, 2, 0, 1, yoptions=gtk.FILL)
        main_table.attach(create_separator_box(), 0, 2, 1, 2, yoptions=gtk.FILL)
        main_table.attach(download_number_hbox, 0, 2, 2, 3, xoptions=gtk.FILL)
        main_table.attach(download_dir_hbox, 0, 2, 3, 4, xoptions=gtk.FILL)
        return main_table

    def download_number_comobox_changed(self, widget, name, value, index):
        set_download_number(value)
        global_event.emit('max-download-number-changed', value)

    def change_download_save_dir(self, widget):
        local_dir = FolderChooseDialog(False).run()
        if local_dir:
            local_dir = os.path.expanduser(local_dir)
            if local_dir != get_software_download_dir():
                self.dir_entry.set_editable(True)
                self.dir_entry.set_text(local_dir)
                self.dir_entry.set_editable(False)
                set_software_download_dir(local_dir)
                global_event.emit('download-directory-changed')

class MirrorsBox(BaseBox):
    def __init__(self):
        BaseBox.__init__(self)

        self.current_mirror_item = None

        self.select_best_mirror_button_texts = {
                "normal": _("Select the best mirror"),
                "wait": _("Waiting"),
                "success": _("Successfully")
                }

        self.main_box.pack_start(self.create_mirror_select_table(), True, True)
        self.main_box.pack_start(self.create_source_update_frequency_table(), False, True)
        self.mirror_test_obj = None

        global_event.register_event("mirror-test-finished", self.finish_mirror_test)
        global_event.register_event("cancel-mirror-test", self.cancel_mirror_test)
        global_event.register_event("mirror-backend-changed", self.mirror_changed_handler)

    def create_source_update_frequency_table(self):
        main_table = gtk.Table(3, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)

        dir_title_label = Label(_("Refresh package lists"))

        # auto update check button
        self.is_auto_update_button = CheckButton(label_text=_('Upgrade automatically'))
        self.is_auto_update_button.connect('released', self.change_auto_update)
        self.is_auto_update_button.set_active(utils.is_auto_update())

        self.update_label = Label(_("Time interval: "))
        self.update_spin = SpinBox(int(get_update_interval()), 0, 168, 1)
        self.update_spin.connect("value-changed", lambda w, v: set_update_interval(v))
        self.hour_lablel = Label(_(" hour"))
        self.hour_lablel.set_size_request(50, 12)
        spin_hbox = gtk.HBox(spacing=3)
        spin_hbox.pack_start(self.update_label, False, False)
        spin_hbox.pack_start(self.update_spin, False, False)
        spin_hbox.pack_start(self.hour_lablel, False, False)

        main_table.attach(dir_title_label, 0, 2, 0, 1, yoptions=gtk.FILL)
        main_table.attach(create_separator_box(), 0, 2, 1, 2, yoptions=gtk.FILL)
        main_table.attach(self.is_auto_update_button, 0, 1, 2, 3, xoptions=gtk.FILL)
        main_table.attach(spin_hbox, 1, 2, 2, 3, xpadding=10, xoptions=gtk.FILL)
        return main_table

    def change_auto_update(self, widget, data=None):
        widget_active = widget.get_active()
        self.update_spin.set_sensitive(widget_active)
        self.update_label.set_sensitive(widget_active)
        self.hour_lablel.set_sensitive(widget_active)

        utils.set_auto_update(widget_active)

        daemon_running = is_dbus_name_exists(DSC_UPDATE_DAEMON_NAME)
        if widget_active and not daemon_running:
            dsc_daemon_path = os.path.join(get_parent_dir(__file__, 2), 'update_data/apt/dsc-daemon.py')
            subprocess.Popen(['python', dsc_daemon_path], stderr=subprocess.STDOUT, shell=False)
        elif not widget_active and daemon_running:
            session = dbus.SessionBus()
            dbus_obj = session.get_object(DSC_UPDATE_DAEMON_NAME, DSC_UPDATE_DAEMON_PATH)
            iface = dbus.Interface(dbus_obj, DSC_UPDATE_DAEMON_NAME)
            iface.quit()

    def select_best_mirror(self, widget):
        widget.set_label(self.select_best_mirror_button_texts["wait"])
        widget.set_sensitive(False)
        global_event.emit("toggle-waiting-dialog", True)
        utils.ThreadMethod(self.change_to_nearest_mirror_thread, (widget, )).start()

    def cancel_mirror_test(self):
        if self.mirror_test_obj:
            self.mirror_test_obj.cancel()
            self.mirror_test_obj = None
            self.finish_mirror_test("")

    def change_to_nearest_mirror_thread(self, widget):
        best_mirror = get_best_mirror()
        global_event.emit("mirror-test-finished", best_mirror)

    def finish_mirror_test(self, mirror):
        for item in self.mirror_view.visible_items:
            if item.mirror == mirror:
                self.mirror_view.visible_item(item)
        self.select_best_mirror_button.set_sensitive(True)
        self.select_best_mirror_button.set_label(self.select_best_mirror_button_texts["normal"])

    def create_mirror_select_table(self):
        main_table = gtk.Table(3, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)

        mirror_select_title = Label(_("Select mirror"))
        self.select_best_mirror_button = Button(self.select_best_mirror_button_texts["normal"])
        self.select_best_mirror_button.connect("clicked", self.select_best_mirror)

        self.mirrors_dir = os.path.join(get_parent_dir(__file__, 2), 'mirrors')
        self.current_mirror_hostname = utils.get_current_mirror_hostname()
        self.mirror_items = self.get_mirror_items()
        self.mirror_view = TreeView(self.mirror_items,
                                enable_drag_drop=False,
                                enable_multiple_select=False,
                                mask_bound_height=0,
                             )
        self.mirror_view.set_expand_column(1)
        self.mirror_view.set_size_request(-1, 280)
        self.mirror_view.draw_mask = self.mirror_treeview_draw_mask

        main_table.attach(mirror_select_title, 0, 1, 0, 1, yoptions=gtk.FILL)
        main_table.attach(self.select_best_mirror_button, 1, 2, 0, 1, xoptions=gtk.FILL)
        main_table.attach(create_separator_box(), 0, 2, 1, 2, xoptions=gtk.FILL)
        main_table.attach(self.mirror_view, 0, 2, 2, 3, xoptions=gtk.FILL)


        return main_table

    def mirror_changed_handler(self, mirror):
        item = None
        for i in self.mirror_view.visible_items:
            if i.mirror == mirror:
                item = i
                break
        if item:
            self.current_mirror_item = item
            for i in self.mirror_items:
                if i != item and i.radio_button.active == True:
                    i.radio_button.active = False
                elif i == item:
                    i.radio_button.active = True
            self.mirror_view.queue_draw()
            self.mirror_view.visible_item(item)

    def mirror_treeview_draw_mask(self, cr, x, y, w, h):
        cr.set_source_rgba(1, 1, 1, 0.5)
        cr.rectangle(x, y, w, h)
        cr.fill()

    def get_mirror_items(self):
        items = []
        for m in all_mirrors:
            item = MirrorItem(m, self.mirror_clicked_callback)
            if m.hostname == self.current_mirror_hostname:
                item.radio_button.active = True
                self.current_mirror_item = item
            items.append(item)

        items.sort(key=lambda item:item.mirror.priority)
        return items

    def mirror_clicked_callback(self, item):
        if item != self.current_mirror_item:
            global_event.emit('start-change-mirror', item.mirror)

class FolderChooseDialog(gtk.FileChooserDialog):
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

class DscPreferenceDialog(PreferenceDialog):
    def __init__(self):
        PreferenceDialog.__init__(self, 566, 488)

        self.waiting_dialog = WaitingDialog()
        self.waiting_dialog.set_transient_for(self)

        preference_items = []
        self.general_box = GeneralBox()
        preference_items.append((_("General"), self.general_box))
        if len(all_mirrors) > 0:
            self.mirrors_box = MirrorsBox()
            preference_items.append((_("Mirrors"), self.mirrors_box))
        self.about_box = AboutBox()
        preference_items.append((_("About"), self.about_box))
        self.set_preference_items(preference_items)

        global_event.register_event("toggle-waiting-dialog", self.handle_toggle_waiting_dialog)
        global_event.register_event("mirror-backend-changed", self.handle_after_mirror_changed)

    def handle_toggle_waiting_dialog(self, show):
        if show:
            self.waiting_dialog.show_waiting()
        else:
            self.waiting_dialog.hide_all()

    def handle_after_mirror_changed(self, mirror):
        global_event.emit("start-update-list")
        self.hide()

if __name__ == '__main__':
    d = WaitingDialog()
    d.show_waiting()
    #preference_dialog = DscPreferenceDialog()
    #preference_dialog.show_all()
    gtk.main()
