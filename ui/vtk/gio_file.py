#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2013 Deepin, Inc.
#               2013 Hailong Qiu
#
# Author:     Hailong Qiu <356752238@qq.com>
# Maintainer: Hailong Qiu <356752238@qq.com>
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

import gio
import os
import gtk




def open_file_manager(file_path):
    os.popen("xdg-open %s" % (file_path))




if __name__ == "__main__":
    def file_changed(file_monitor, child, other_file, event_type):
        if event_type == gio.FILE_MONITOR_EVENT_DELETED:
            print "删除了文件: [%s]" % (child.get_basename())
        elif event_type == gio.FILE_MONITOR_EVENT_CREATED:
            print "回收站添加了 %s" % (child.get_basename())
            open_file_manager("trash://")
    trash_file = gio.File("trash://")
    monitor = trash_file.monitor_directory()
    monitor.connect("changed", file_changed)
    gtk.main()


