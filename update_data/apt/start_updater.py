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

import dbus
import dbus.service
from deepin_utils.ipc import is_dbus_name_exists
import traceback
import sys

DSC_UPDATER_NAME = "com.linuxdeepin.softwarecenterupdater"
DSC_UPDATER_PATH = "/com/linuxdeepin/softwarecenterupdater"

if __name__ == "__main__":
    try:
        dbus.mainloop.glib.DBusGMainLoop(set_as_default = True)
        
        if is_dbus_name_exists(DSC_UPDATER_NAME, False):
            print "Deepin software center updater has running!"
        else:
            system_bus = dbus.SystemBus()
            bus_object = system_bus.get_object(DSC_UPDATER_NAME, DSC_UPDATER_PATH)
            dbus.Interface(bus_object, DSC_UPDATER_NAME)
            
            print "Start updater finish."
    except Exception, e:
        print "got error: %s" % (e)
        traceback.print_exc(file=sys.stdout)
        
