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
from dtk.ui.dialog import PreferenceDialog, DialogBox, DIALOG_MASK_SINGLE_PAGE
from dtk.ui.entry import InputEntry
from dtk.ui.button import Button, CheckButton, RadioButtonBuffer
from dtk.ui.label import Label
from dtk.ui.line import HSeparator
from dtk.ui.treeview import TreeItem, TreeView
from dtk.ui.utils import get_content_size
from dtk.ui.draw import draw_text
from dtk.ui.spin import SpinBox
from dtk.ui.progressbar import ProgressBar
from dtk.ui.scrolled_window import ScrolledWindow
from dtk.ui.theme import DynamicColor
from dtk.ui.combo import ComboBox
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
        get_download_number,
        set_download_number,
        is_auto_update,
        set_auto_update,
        )
import utils
from mirror_test import Mirror, MirrorTest
from events import global_event
import aptsources
import aptsources.distro
from loading_widget import Loading
from constant import PROGRAM_VERSION
import time
import subprocess

class MirrorItem(TreeItem):

    __gsignals__ = {
        "item-clicked" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }

    PADDING_X = 5
    NAME_WIDTH = 130

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
        
        rect.x -= 2
        rect.width = rect.width - self.PADDING_X
        self.radio_button.render(cr, rect)

    def render_name(self, cr, rect):
        self.render_odd_line_bg(cr, rect)

        self.name = self.mirror.name
        self.render_background(cr, rect)
        #rect.x -= self.PADDING_X
        rect.width -= self.PADDING_X * 2        
        if self.name:
            (text_width, text_height) = get_content_size(self.name)
            draw_text(cr, self.name, rect.x, rect.y, rect.width, rect.height,
                    alignment = pango.ALIGN_LEFT)
        else:
            name = _("Untitled")
            (text_width, text_height) = get_content_size(name)
            draw_text(cr, name, rect.x, rect.y, rect.width, rect.height,
                    alignment = pango.ALIGN_LEFT)

    def render_url(self, cr, rect):
        self.render_odd_line_bg(cr, rect)

        self.mirror_url = self.mirror.hostname
        self.render_background(cr, rect)
        #rect.x += self.NAME_WIDTH
        rect.width -= self.PADDING_X * 2
        if self.mirror_url:
            (text_width, text_height) = get_content_size(self.mirror_url)
            draw_text(cr, self.mirror_url, rect.x, rect.y, rect.width, rect.height,
                    alignment = pango.ALIGN_LEFT)
        else:
            mirror_url = _("Unknown mirror url")
            (text_width, text_height) = get_content_size(mirror_url)
            draw_text(cr, mirror_url, rect.x, rect.y, rect.width, rect.height,
                    alignment = pango.ALIGN_LEFT)
        
    def get_column_renders(self):
        return [self.render_radio_button, self.render_name, self.render_url]

    def get_column_widths(self):
        '''docstring for get_column_widths'''
        return [30, self.NAME_WIDTH, 300]

    def get_height(self):
        return 24

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

    def redraw(self):
        if self.redraw_request_callback:
            self.redraw_request_callback(self)

    def render_background(self,  cr, rect):
        pass

def create_separator_box(padding_x=0, padding_y=0):    
    separator_box = HSeparator(
        app_theme.get_shadow_color("hSeparator").get_color_info(),
        padding_x, padding_y)
    return separator_box

TABLE_ROW_SPACING = 25
CONTENT_ROW_SPACING = 8

class WaitingDialog(DialogBox):

    def __init__(self, title, info_message, cancel_callback=None):
        DialogBox.__init__(self, 
                title, 
                mask_type=DIALOG_MASK_SINGLE_PAGE, 
                close_callback=self.dialog_close_action)
        self.set_size_request(-1, -1)
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)

        self.loading_widget = Loading() 
        loading_widget_align = gtk.Alignment()
        loading_widget_align.set(0.5, 0.5, 0, 0)
        loading_widget_align.set_padding(padding_top=0, padding_bottom=0, padding_left=0, padding_right=8)
        loading_widget_align.add(self.loading_widget)

        self.info_message_label = Label(info_message, enable_select=False, wrap_width=200, text_size=10)
        info_message_align = gtk.Alignment()
        info_message_align.set(0.5, 0.5, 0, 0)
        info_message_align.add(self.info_message_label)

        outer_align = gtk.Alignment()
        outer_align.set(0.5, 0.5, 0, 0)
        outer_align.set_padding(padding_top=10, padding_bottom=10, padding_left=25, padding_right=25)

        outer_hbox = gtk.HBox()
        outer_hbox.pack_start(loading_widget_align, False, False)
        outer_hbox.pack_start(info_message_align, False, False)
        outer_align.add(outer_hbox)

        self.close_button = Button(_("Cancel"))
        if cancel_callback:
            self.close_button.connect("clicked", cancel_callback)
        else:
            self.close_button.connect("clicked", lambda w: self.hide_all())

        self.body_box.pack_start(outer_align, False, False)
        self.right_button_box.set_buttons([self.close_button])

    def dialog_close_action(self):
        self.hide_all()

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
        
        describe = _("Deepin Software Center is a commonly used software center on Linux. It selected more than 2,600 decent applications and features easy installation and uninstall, software repository and recommended applications. It supports 1-click install, downloading packages with multi-thread and clearing up cached packages. It provides topics for software introduction and shares good applications. \n")
        
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
            (_("General"), self.normal_settings_align),
            (_("Software repository"), self.mirror_settings_align),
            (_("About"), AboutBox()),
            ])
        
    def mirror_settings_align_expose(self, widget, event=None):
        cr = widget.window.cairo_create()
        rect = widget.allocation

        # draw backgound
        cr.rectangle(*rect)
        #cr.set_source_rgb(*color_hex_to_cairo("#ff0000"))
        cr.set_source_rgba(1, 1, 1, 0)
        cr.fill()

    def mirror_select_action(self, repo_urls):
        self.data_manager.change_source_list(repo_urls, reply_handler=handle_dbus_reply, error_handler=handle_dbus_error)

    def create_mirror_select_table(self):
        main_table = gtk.Table(4, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)
        
        dir_title_label = Label(_("Select mirror"))
        dir_title_label.set_size_request(400, 12)
        label_align = gtk.Alignment()
        label_align.set_padding(0, 0, 0, 0)
        label_align.add(dir_title_label)

        self.mirrors_dir = os.path.join(get_parent_dir(__file__, 2), 'mirrors')
        self.current_mirror_hostname = utils.get_current_mirror_hostname()
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

        self.mirror_test_button = Button(_("Select fastest mirror"))
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
        
        title = _("Select best mirror")
        info_message = _("Please wait. The process will take 30 seconds or more depending on your network connection")
        self.select_best_mirror_dialog = WaitingDialog(title, info_message, self.cancel_mirror_test)
        global_event.register_event("mirror-changed", self.mirror_changed_handler)
        global_event.register_event("update-list-finish", self.update_list_finish_handler)

        return main_table

    def cancel_mirror_test(self, widget):
        try:
            self.mirror_test.terminated = True
            gobject.source_remove(self.update_status_id)
        except:
            pass
        self.select_best_mirror_dialog.hide_all()

    def update_list_finish_handler(self):
        self.select_best_mirror_dialog.hide_all()

    def mirror_changed_handler(self, parent=None):
        self.select_best_mirror_dialog.set_transient_for(self)
        self.select_best_mirror_dialog.info_message_label.set_text(_("The software repository has changed. Refreshing applications lists"))
        self.select_best_mirror_dialog.show_all()
        self.select_best_mirror_dialog.close_button.set_label(_("Run in background"))
    
    def test_mirror_action(self, widget):
        self.select_best_mirror_dialog.set_transient_for(self)
        self.select_best_mirror_dialog.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.select_best_mirror_dialog.show_all()
        distro = aptsources.distro.get_distro()
        #distro.get_sources(SourcesList())
        pipe = os.popen("dpkg --print-architecture")
        arch = pipe.read().strip()
        test_file = "dists/%s/Contents-%s.gz" % \
                    (
                    distro.codename,
                    #"quantal",
                    arch,
                    )

        self.mirror_test = MirrorTest(self.mirrors_list, test_file)
        self.mirror_test.start()

        # now run the tests in a background thread, and update the UI on each event
        self.update_status_id = gtk.timeout_add(100, self.update_progress)

    def update_progress(self):
        if self.mirror_test.running:
            return True
        else:
            time.sleep(1)
            if self.mirror_test.best != None:
                for item in self.mirror_items:
                    if item.mirror == self.mirror_test.best[1]:
                        print item.mirror.get_repo_urls()
                        self.mirror_clicked_callback(item)
            else:
                self.select_best_mirror_dialog.loading_widget.hide_all()
                self.select_best_mirror_dialog.info_message_label.set_text(_("Test for downloading mirror failed. Please check your network connection."))
                self.select_best_mirror_dialog.close_button.set_label(_("Close"))
            return False

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
            if m.hostname == self.current_mirror_hostname:
                item.radio_button.active = True
                self.current_mirror_item = item
            self.mirrors_list.append(m)
            items.append(item)
        
        items.sort(key=lambda x:x.mirror.priority)
        
        return items

    def mirror_clicked_callback(self, item):
        for i in self.mirror_items:
            if i != item and i.radio_button.active == True:
                i.radio_button.active = False
            elif i == item:
                i.radio_button.active = True
        self.mirror_view.queue_draw()
        if item != self.current_mirror_item:
            global_event.emit('change-mirror', item.mirror.get_repo_urls())
            self.current_mirror_item = item
        else:
            self.select_best_mirror_dialog.hide_all()
            

    def create_source_update_frequency_table(self):
        main_table = gtk.Table(3, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)
        
        dir_title_label = Label(_("Update applications lists"))
        dir_title_label.set_size_request(200, 12)
        label_align = gtk.Alignment()
        label_align.set_padding(0, 0, 0, 0)
        label_align.add(dir_title_label)

        self.is_auto_update_button = CheckButton(label_text=_('Update automatically'))
        self.is_auto_update_button.connect('toggled', self.change_auto_update)
        
        self.update_label = Label(_("Time interval: "))
        self.update_spin = SpinBox(int(get_update_interval()), 0, 168, 1)
        self.update_spin.connect("value-changed", lambda w, v: set_update_interval(v))
        self.hour_lablel = Label(_(" hour"))
        self.hour_lablel.set_size_request(50, 12)
        spin_hbox = gtk.HBox(spacing=3)
        spin_hbox.pack_start(self.update_label, False, False)
        spin_hbox.pack_start(self.update_spin, False, False)
        spin_hbox.pack_start(self.hour_lablel, False, False)

        main_table.attach(label_align, 0, 2, 0, 1, yoptions=gtk.FILL, xpadding=8)
        main_table.attach(create_separator_box(), 0, 2, 1, 2, yoptions=gtk.FILL)
        main_table.attach(self.is_auto_update_button, 0, 1, 2, 3, xpadding=10, xoptions=gtk.FILL)
        main_table.attach(spin_hbox, 1, 2, 2, 3, xpadding=10, xoptions=gtk.FILL)

        if is_auto_update():
            self.is_auto_update_button.set_active(True)
        else:
            self.is_auto_update_button.toggled()

        return main_table

    def create_download_dir_table(self):    
        main_table = gtk.Table(4, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)
        
        dir_title_label = Label(_("Download settings"))
        dir_title_label.set_size_request(200, 12)
        label_align = gtk.Alignment()
        label_align.set_padding(0, 0, 0, 0)
        label_align.add(dir_title_label)

        download_number_label = Label(_('Max download task number: '))
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
        
        main_table.attach(label_align, 0, 2, 0, 1, yoptions=gtk.FILL, xpadding=8)
        main_table.attach(create_separator_box(), 0, 2, 1, 2, yoptions=gtk.FILL)
        main_table.attach(download_number_hbox, 0, 2, 2, 3, xpadding=10, xoptions=gtk.FILL)
        main_table.attach(download_dir_hbox, 0, 2, 3, 4, xpadding=10, xoptions=gtk.FILL)
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

    def download_number_comobox_changed(self, widget, name, value, index):
        set_download_number(value)
        global_event.emit('max-download-number-changed', value)

    def change_auto_update(self, widget, data=None):
        self.update_spin.set_sensitive(widget.get_active())
        set_auto_update(widget.get_active())
        self.update_label.set_sensitive(widget.get_active())
        self.hour_lablel.set_sensitive(widget.get_active())
        dsc_daemon_path = os.path.join(get_parent_dir(__file__, 2), 'update_data/apt/dsc-daemon.py')
        if widget.get_active():
            subprocess.Popen(['python', dsc_daemon_path], stderr=subprocess.STDOUT, shell=False)

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

preference_dialog = DscPreferenceDialog()

if __name__ == '__main__':
    #d = TestProgressDialog()
    #d.dialog.show_all()
    preference_dialog.show_all()
    #WaitingDialog("ceshi", "cececececececececeeedddddd").show_all()
    gtk.main()
