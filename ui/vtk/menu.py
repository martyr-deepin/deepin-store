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



class MenuStrip(object):
    pass
    
    def add(self, item):
        pass

    def add_range(self, items):
        pass

class MenuItem(list):
    def __init__(self):
        pass

    def add(self, item):
        print item

    def add_range(self, items):
        print items


if __name__ == "__main__":
    MenuItem()



