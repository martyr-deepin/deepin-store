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

from software_center import DeepinSoftwareCenter
import sys
import dbus
import dbus.service
import dbus.mainloop.glib
from dbus.mainloop.glib import DBusGMainLoop
from constant import DSC_FRONTEND_NAME, DSC_FRONTEND_PATH
from deepin_utils.ipc import is_dbus_name_exists
import gobject

if __name__ == "__main__" :
    # Init.
    DBusGMainLoop(set_as_default=True)
    gobject.threads_init()
    session_bus = dbus.SessionBus()
    arguments = sys.argv[1::]
    
    # Send hello message if updater has running.
    if is_dbus_name_exists(DSC_FRONTEND_NAME, True):
        print "Software center has running!"
        
        bus_object = session_bus.get_object(DSC_FRONTEND_NAME, DSC_FRONTEND_PATH)
        bus_interface = dbus.Interface(bus_object, DSC_FRONTEND_NAME)
        bus_interface.hello(arguments)
        
        print "Say hello to software center"
    else:
        # Init dbus.
        bus_name = dbus.service.BusName(DSC_FRONTEND_NAME, session_bus)
            
        software_center = DeepinSoftwareCenter(session_bus, arguments)
        try:
            software_center.run()
        except KeyboardInterrupt:
            software_center.bus_interface.request_quit()
    
