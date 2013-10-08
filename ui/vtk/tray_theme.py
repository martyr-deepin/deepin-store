#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Deepin, Inc.
#               2012 Hailong Qiu
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


import gtk
import os
import sys
from utils import get_run_app_path

LOAD_IMAGE_PATH = os.path.join(os.path.dirname(sys.argv[0]), "image")
print "load_image_path:", LOAD_IMAGE_PATH


class Theme(object):
    def __init__(self):
        self.__icon_theme = gtk.IconTheme()
        self.name = ThemeName()
        #
        path = get_run_app_path("image")
        self.append_search_path(path)
        if os.path.exists(path):
            self.__search_path_to_theme(path)

    def __search_path_to_theme(self, path):
        # load dir.
        for name in os.listdir(path):
            save_path = os.path.join(path, name)
            if os.path.exists(save_path):
                if os.path.isdir(save_path):
                    self.append_search_path(save_path)
                    # load dir.
                    self.__search_path_to_theme(save_path)
                    
    def append_search_path(self, path):
        self.__icon_theme.append_search_path(path)

    def get_pixbuf(self, name, size=16):
        try:
            return self.__load_icon(name, size)
        except Exception, e:
            print "get_pixbuf[error]:", e

    def __load_icon(self, name, size=16):
        return self.__icon_theme.load_icon(name, 
                                           size, 
                                           gtk.ICON_LOOKUP_FORCE_SIZE)
         

class ThemeName(object):
    def __init__(self):
        self.load_path = LOAD_IMAGE_PATH

    def get_pixbuf(self, path):
        new_path = os.path.join(self.load_path, path)
        abs_path = os.path.abspath(new_path)
        if os.path.exists(abs_path):
            return gtk.gdk.pixbuf_new_from_file(abs_path)
        else:
            return None

    def get_path(self, path):
        new_path = os.path.join(self.load_path, path)
        abs_path = os.path.abspath(new_path)
        if os.path.exists(abs_path):
            return abs_path
        else:
            return None 
    
    def get_image(self, path):
        new_path = os.path.join(self.load_path, path)
        abs_path = os.path.join(new_path)
        if os.path.exists(abs_path):
            return  gtk.image_new_from_file(abs_path)
        else:
            return None


if __name__ == "__main__":
    theme = Theme()
    print theme.name.get_path("power/power_icon.png")
