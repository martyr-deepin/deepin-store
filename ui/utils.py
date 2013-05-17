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
from constant import CONFIG_INFO_PATH, DEFAULT_UPDATE_INTERVAL, DEFAULT_DOWNLOAD_DIRECTORY, DEFAULT_DOWNLOAD_NUMBER
from deepin_utils.config import Config
from deepin_utils.file import touch_file
from deepin_utils.date_time import get_current_time

LOG_PATH = "/tmp/dsc-frontend.log"

def bit_to_human_str(size):
    if size < 1024:
        return "%sB" % size
    else:
        size = size/1024.0
        if size <= 1024:
            return "%.2fKB" % size
        else:
            size = size/1024.0
            if size <= 1024:
                return "%.2fMB" % size
            else:
                size = size/1024.0
                return "%.2fGB" % size

def log(message):
    with open(LOG_PATH, "a") as file_handler:
        now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        file_handler.write("%s %s\n" % (now, message))

def handle_dbus_reply(*reply):
    print "handle_dbus_reply: ", reply
    
def handle_dbus_error(*error):
    print "handle_dbus_error: ", error

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
    config_info_config = get_config_info_config()
    config_info_config.set("upgrade", "last_upgrade_time", get_current_time())
    config_info_config.write()

def get_last_upgrade_time():
    config_info_config = get_config_info_config()
    if config_info_config.has_option("upgrade", "last_upgrade_time"):
        return config_info_config.get("upgrade", "last_upgrade_time")
    else:
        config_info_config.set("upgrade", "last_upgrade_time", "")
        config_info_config.write()
        return ""

def get_config_info_config():
    config_info_config = Config(CONFIG_INFO_PATH)

    if os.path.exists(CONFIG_INFO_PATH):
        config_info_config.load()
    else:
        touch_file(CONFIG_INFO_PATH)
        config_info_config.load()

    return config_info_config

def is_first_started():
    config = get_config_info_config()
    return not config.has_option("settings" , "first_started")

def set_first_started():
    config = get_config_info_config()
    config.set("settings", "first_started", "false")    
    config.write()

def get_purg_flag():
    config = get_config_info_config()
    if config.has_option('uninstall', 'purge'):
        flag = config.get('uninstall', 'purge')
        if isinstance(flag, str):
            return eval(flag)
        else:
            return flag
    else:
        config.set('uninstall', 'purge', False)
        config.write()
        return False

def set_purge_flag(value):
    config = get_config_info_config()
    config.set('uninstall', 'purge', value)
    config.write()

def get_config_info(section, key):
    config = get_config_info_config()
    if config.has_option(section, key):
        return config.get(section, key)
    else:
        return None

def set_config_info(section, key, value):
    config = get_config_info_config()
    config.set(section, key, value)
    config.write()

def get_update_interval():
    config_info_config = get_config_info_config()
    if config_info_config.has_option('update', 'interval'):
        return config_info_config.get('update', 'interval')
    else:
        return DEFAULT_UPDATE_INTERVAL

def set_update_interval(hour):
    config_info_config = get_config_info_config()
    config_info_config.set('update', 'interval', hour)
    config_info_config.write()

def get_software_download_dir():
    config_info_config = get_config_info_config()
    if config_info_config.has_option('download', 'directory'):
        return config_info_config.get('download', 'directory')
    else:
        return DEFAULT_DOWNLOAD_DIRECTORY
    
def set_software_download_dir(local_dir):
    config_info_config = get_config_info_config()
    config_info_config.set('download', 'directory', local_dir)
    config_info_config.write()

def get_download_number():
    config_info_config = get_config_info_config()
    if config_info_config.has_option('download', 'number'):
        return config_info_config.get('download', 'number')
    else:
        return DEFAULT_DOWNLOAD_NUMBER
    
def set_download_number(number):
    config_info_config = get_config_info_config()
    config_info_config.set('download', 'number', number)
    config_info_config.write()
