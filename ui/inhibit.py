#! /usr/bin/env python
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

import os
import dbus
import dbus.service
from nls import _

SYSTEMD_LOGIN1_NAME = "org.freedesktop.login1"
SYSTEMD_LOGIN1_PATH = "/org/freedesktop/login1"
SYSTEMD_LOGIN1_IFCE = "org.freedesktop.login1.Manager"

class InhibitObject(object):
    def __init__(self):
        self.system_bus = dbus.SystemBus()
        self.bus_object = self.system_bus.get_object(SYSTEMD_LOGIN1_NAME, SYSTEMD_LOGIN1_PATH)
        self.bus_interface = dbus.Interface(self.bus_object, SYSTEMD_LOGIN1_IFCE)
        self.inhibit_fd = None

    def set_inhibit(self):
        if not self.inhibit_fd:
            self.inhibit_fd = self.bus_interface.Inhibit(
                "shutdown:sleep:idle:handle-power-key:handle-suspend-key:handle-hibernate-key:handle-lid-switch",
                "deepin-software-center",
                _( "Please wait a moment while system update is being performed... Do not turn off your computer."),
                "block"
                )
            print self.inhibit_fd

    def unset_inhibit(self):
        if self.inhibit_fd:
            os.close(self.inhibit_fd.take())

