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
from dtk.ui.dialog import PreferenceDialog
from dtk.ui.entry import InputEntry
from dtk.ui.button import Button
from dtk.ui.label import Label
from dtk.ui.line import HSeparator
from nls import _

def create_separator_box(padding_x=0, padding_y=0):    
    separator_box = HSeparator(
        app_theme.get_shadow_color("hSeparator").get_color_info(),
        padding_x, padding_y)
    return separator_box

CONTENT_ROW_SPACING = 8

class DscPreferenceDialog(PreferenceDialog):
    def __init__(self):
        PreferenceDialog.__init__(self)

    def create_lyrics_dir_table(self):    
        main_table = gtk.Table(3, 2)
        main_table.set_row_spacings(CONTENT_ROW_SPACING)
        
        dir_title_label = Label(_("Lyrics directory"))
        dir_title_label.set_size_request(200, 12)
        label_align = gtk.Alignment()
        label_align.set_padding(0, 0, 0, 0)
        label_align.add(dir_title_label)
        
        self.dir_entry = InputEntry()
        self.dir_entry.set_text("/var/cache/apt/archives")
        self.dir_entry.set_editable(False)        
        self.dir_entry.set_size(250, 25)
        
        modify_button = Button(_("Change"))
        modify_button.connect("clicked", self.change_lyrics_save_dir)
        hbox = gtk.HBox(spacing=5)
        hbox.pack_start(self.dir_entry, False, False)
        hbox.pack_start(modify_button, False, False)
        
        main_table.attach(label_align, 0, 2, 0, 1, yoptions=gtk.FILL, xpadding=8)
        main_table.attach(create_separator_box(), 0, 2, 1, 2, yoptions=gtk.FILL)
        main_table.attach(hbox, 0, 2, 2, 3, xpadding=10, xoptions=gtk.FILL)
        return main_table


normal_settings = gtk.VBox()

choose_download_dir_hbox = gtk.HBox()
choose_download_dir_entry = InputEntry()
choose_download_dir_entry.set_size(250, 22)
choose_download_dir_button = Button("Choose")
choose_download_dir_hbox.pack_start(Label("选择下载目录:"), False, False)
choose_download_dir_hbox.pack_start(choose_download_dir_entry, True, True)
choose_download_dir_hbox.pack_start(choose_download_dir_button, False, False)
choose_download_dir_align = gtk.Alignment(0, 0.5, 1, 1)
choose_download_dir_align.set_padding(5, 5, 2, 2)
choose_download_dir_align.add(choose_download_dir_hbox)

normal_settings.pack_start(choose_download_dir_align)

preference_dialog = PreferenceDialog()
preference_dialog.set_preference_items([
    ("常规", normal_settings),
    ("软件源", gtk.Label("热键设置")),
    ("关于", gtk.Label("关于")),
    ])

if __name__ == "__main__":
    preference_dialog.show_all()
    gtk.main()
