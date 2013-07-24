#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011~2012 Deepin, Inc.
#               2011~2012 Kaisheng Ye
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

import threading

class ThreadFetch(threading.Thread):            
    
    def __init__(self, fetch_funcs, success_funcs=None, fail_funcs=None):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.fetch_funcs = fetch_funcs
        self.success_funcs = success_funcs
        self.fail_funcs = fail_funcs
        
    def run(self):    
        result = self.fetch_funcs[0](*self.fetch_funcs[1])
        if result:
            if self.success_funcs:
                self.success_funcs[0](result, *self.success_funcs[1])
        else:        
            if self.fail_funcs:
                self.fail_funcs[0](*self.fail_funcs[1])

