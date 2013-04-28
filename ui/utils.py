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

import threading as td
from datetime import datetime
import os
from constant import CACHE_INFO_PATH
from deepin_utils.config import Config
from deepin_utils.file import touch_file
from deepin_utils.date_time import get_current_time

LOG_PATH = "/tmp/dsc-frontend.log"

def log(message):
    with open(LOG_PATH, "a") as file_handler:
        now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        file_handler.write("%s %s\n" % (now, message))

class ThreadMethod(td.Thread):
    '''
    func: a method name
    args: arguments tuple
    '''
    def __init__(self, func, args, daemon=False):
        td.Thread.__init__(self)
        self.func = func
        self.args = args
        self.setDaemon(daemon)

    def run(self):
        self.func(*self.args)

def is_64bit_system():
    if os.uname()[-1] == "x86_64":
        return True
    else:
        return False

def set_last_upgrade_time():
    cache_info_config = get_cache_info_config()
    cache_info_config.set("upgrade", "last_upgrade_time", get_current_time())
    cache_info_config.write()

def get_last_upgrade_time():
    cache_info_config = get_cache_info_config()
    if cache_info_config.has_option("upgrade", "last_upgrade_time"):
        return cache_info_config.get("upgrade", "last_upgrade_time")
    else:
        cache_info_config.set("upgrade", "last_upgrade_time", "")
        cache_info_config.write()
        return ""

def get_cache_info_config():
    cache_info_config = Config(CACHE_INFO_PATH)

    if os.path.exists(CACHE_INFO_PATH):
        cache_info_config.load()
    else:
        touch_file(CACHE_INFO_PATH)
        cache_info_config.load()

    return cache_info_config
