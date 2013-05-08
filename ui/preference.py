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
    ("常规设置", normal_settings),
    ("软件源", gtk.Label("热键设置")),
    ("关于", gtk.Label("关于")),
    ])

if __name__ == "__main__":
    preference_dialog.show_all()
    gtk.main()
