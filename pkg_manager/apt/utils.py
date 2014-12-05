#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
#
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
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

import os
from datetime import datetime
import time
import dbus
import subprocess

from constant import LOG_PATH, SYS_CONFIG_INFO_PATH, BACKEND_PID

from deepin_utils.config import Config
from deepin_utils.file import touch_file

def desktop_name_to_desktop_path(desktop_name):
    """ get desktop absolute path from a desktop name

    @param desktop_name: A desktop name, such as: firefox.desktop or firefox
    @return: The absolute path from search paths
    """
    search_paths = ["/usr/share/applications/", "/usr/share/applications/kde4"]
    if not desktop_name.endswith(".desktop"):
        desktop_name += ".desktop"
    for folder in search_paths:
        if os.path.exists(folder):
            files = os.listdir(folder)
            for desktop in files:
                if desktop == desktop_name:
                    return os.path.join(folder, desktop)
    return ""

def file_path_to_package_name(file_path):
    """ a wrap of dpkg -S

    @param file_path: Any absolute file path
    @return: the name of package that own the file
    """
    try:
        result = subprocess.check_output(['dpkg', '-S', file_path]).strip().split(":")
        if len(result) == 2 and result[1].strip() == file_path.strip():
            return result[0].strip()
        else:
            return ""
    except:
        return ""

def set_running_lock(running):
    if running:
        touch_file(BACKEND_PID)
        with open(BACKEND_PID, "w") as file_handler:
            file_handler.write(str(os.getpid()))
    else:
        if os.path.exists(BACKEND_PID):
            os.remove(BACKEND_PID)

def log(message):
    with open(LOG_PATH, "a") as file_handler:
        now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        file_handler.write("%s %s\n" % (now, message))

def set_last_update_time():
    config_info_config = get_config_info_config()
    config_info_config.set("update", "last_update_time", time.time())
    config_info_config.write()

def get_config_info_config():
    config_info_config = Config(SYS_CONFIG_INFO_PATH)

    if os.path.exists(SYS_CONFIG_INFO_PATH):
        config_info_config.load()
    else:
        touch_file(SYS_CONFIG_INFO_PATH)
        config_info_config.load()

    return config_info_config

def auth_with_policykit(action, interactive=1):
    policykit_dbus_name = "org.freedesktop.PolicyKit1"
    authority_dbus_path = "/org/freedesktop/PolicyKit1/Authority"
    authority_dbus_iface = "org.freedesktop.PolicyKit1.Authority"
    system_bus = dbus.SystemBus()
    obj = system_bus.get_object(policykit_dbus_name,
            authority_dbus_path, authority_dbus_iface)

    policykit = dbus.Interface(obj, authority_dbus_iface)
    pid = os.getpid()

    subject = ('unix-process',
                {
                    'pid' : dbus.UInt32(pid, variant_level=1),
                    'start-time' : dbus.UInt64(0),
                }
              )
    details = { '' : '' }
    flags = dbus.UInt32(interactive)
    cancel_id = ''
    (ok, notused, details) = policykit.CheckAuthorization(subject, action, details, flags, cancel_id)

    return ok
