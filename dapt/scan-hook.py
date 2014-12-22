#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2011~2013 Deepin, Inc.
#               2011~2013 Kaisheng Ye
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

import dbus

DBUS_NAME = "com.deepin.store.Api"
DBUS_PATH = "/com/deepin/store/Api"
DBUS_INTERFACE = "com.deepin.store.Api"

system_bus = dbus.SystemBus()
bus_object = system_bus.get_object(DBUS_NAME, DBUS_PATH)
bus_interface = dbus.Interface(bus_object, DBUS_INTERFACE)
bus_interface.Scan()

