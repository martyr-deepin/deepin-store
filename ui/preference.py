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


import gtk
from skin import app_theme
from dtk.ui.dialog import PreferenceDialog

preference_dialog = PreferenceDialog()
preference_dialog.set_preference_items([
    ("常规设置", gtk.VBox().pack_start(gtk.Label("常规设置"))),
    ("热键设置", gtk.Label("热键设置")),
    ("歌词设置", [
        ("桌面歌词", gtk.Label("桌面歌词")),
        ("窗口歌词", gtk.Label("窗口歌词")),
        ]),
    ("插件", gtk.Label("插件")),
    ("关于", gtk.Label("关于")),
    ])

preference_dialog.show_all()
gtk.main()
