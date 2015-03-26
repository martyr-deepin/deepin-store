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

import gobject
import glib
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

import os
import sys
import signal
import functools
import cPickle
import time
import json

DBUS_NAME = "com.deepin.store.Api"
DBUS_PATH = "/com/deepin/store/Api"
DBUS_INTERFACE = "com.deepin.store.Api"
DB_PATH = "/var/cache/deepin-store/new-desktop.db"
ORIGIN_DESKTOPS = []
XDG_DATA_DIRS = "/usr/share/deepin:/usr/local/share/:/usr/share/"

class DStoreDesktop(gobject.GObject):

    __gsignals__ = {
        "new-desktop-added": (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (str, int)),
    }

    def __init__(self):
        gobject.GObject.__init__(self)

        self.db = {}
        self.application_dirs = []

        #init application_dirs
        data_dirs = os.environ.get("XDG_DATA_DIRS", None)
        if not data_dirs:
            data_dirs = XDG_DATA_DIRS
        data_dirs = data_dirs.split(":")
        for folder in data_dirs:
            folder = folder.strip()
            if folder:
                self.application_dirs.append(os.path.join(folder, "applications"))
                self.application_dirs.append(os.path.join(folder, "applications", "kde4"))

        # init self.db
        if os.path.exists(DB_PATH):
            with open(DB_PATH) as fp:
                self.db = cPickle.load(fp)
        else:
            self.mark_all_launched()

    def save_db(self):
        db_dir = os.path.dirname(DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        with open(DB_PATH, "w") as fp:
            cPickle.dump(self.db, fp)

    def real_scan(self, emit_signal=True):
        all_desktops = []
        for folder in self.application_dirs:
            if os.path.exists(folder):
                files = os.listdir(folder)
                for f in files:
                    if not f.endswith(".desktop"):
                        continue
                    if f not in all_desktops:
                        all_desktops.append(f)
                    desktop_info = self.db.get(f)
                    if desktop_info == None:
                        now = int(time.time())
                        self.db[f] = [now, True]
                        if emit_signal:
                            desktop_path = os.path.join(folder, f)
                            self.emit("new-desktop-added", desktop_path, now)
        # delete desktops
        keys = self.db.keys()
        for key in keys:
            if key not in all_desktops:
                self.db.pop(key)
        self.save_db()

    def mark_launched(self, desktop):
        if not desktop.endswith(".desktop"):
            desktop += ".desktop"
        desktop_info = self.db.get(desktop)
        if desktop_info != None:
            self.db[desktop][1] = False
            self.save_db()
            return True
        else:
            return False

    def mark_all_launched(self):
        self.real_scan(emit_signal=False)
        desktops = self.db.keys()
        for desktop in desktops:
            desktop_info = self.db.get(desktop)
            if desktop_info != None:
                self.db[desktop][1] = False
        self.save_db()

    def get_new_desktops(self):
        new_desktops = []
        for key in self.db:
            desktop_info = self.db[key]
            if desktop_info[1]:
                new_desktops.append((key, desktop_info[0]))
        return sorted(new_desktops, key=lambda info: info[1], reverse=True)

    def get_all_desktops(self):
        all_desktops = []
        for key in self.db:
            desktop_info = self.db[key]
            all_desktops.append((key, desktop_info[0], desktop_info[1]))
        return sorted(all_desktops, key=lambda info: info[1], reverse=True)

class DStoreDBusApi(dbus.service.Object):
    def __init__(self, bus_name, bus_path, mainloop):
        self.bus_name = bus_name
        self.mainloop = mainloop
        dbus.service.Object.__init__(self, bus_name, bus_path)

        self.dstore_desktop = DStoreDesktop()
        self.dstore_desktop.connect("new-desktop-added",
            lambda widget, desktop, time: self.NewDesktopAdded(desktop, time))

        self.timeout_id = None

    def timeout(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            self = args[0]
            if self.timeout_id:
                glib.source_remove(self.timeout_id)
            self.timeout_id = glib.timeout_add_seconds(30, self.Quit)
            return func(*args, **kw)
        return wrapper

    @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="")
    def Quit(self):
        self.remove_from_connection()
        self.mainloop.quit()

    @timeout
    @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="")
    def Scan(self):
        glib.timeout_add(10, self.dstore_desktop.real_scan)

    @timeout
    @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="")
    def Scanning(self):
        self.dstore_desktop.real_scan()

    @timeout
    @dbus.service.method(DBUS_INTERFACE, in_signature="s", out_signature="b")
    def MarkLaunched(self, desktop):
        desktop = desktop.encode("utf-8")
        return self.dstore_desktop.mark_launched(desktop)

    @timeout
    @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="b")
    def MarkAll(self):
        self.dstore_desktop.mark_all_launched()
        return True

    @timeout
    @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="s")
    def GetNewDesktops(self):
        return json.dumps(self.dstore_desktop.get_new_desktops())

    @timeout
    @dbus.service.method(DBUS_INTERFACE, in_signature="", out_signature="s")
    def GetAllDesktops(self):
        return json.dumps(self.dstore_desktop.get_all_desktops())

    @dbus.service.signal(DBUS_INTERFACE, signature='si')
    # Use below command for test:
    # dbus-monitor --system "type='signal', interface='com.deepin.store.Api'"
    def NewDesktopAdded(self, desktop, time):
        pass

if __name__ == "__main__":
    DBusGMainLoop(set_as_default=True)
    mainloop = glib.MainLoop()
    signal.signal(signal.SIGINT, lambda : mainloop.quit()) # capture "Ctrl + c" signal
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-s", "--scan",
                    action="store_true", dest="scan", default=False,
                    help="scan desktop changes in all desktop folders")
    (options, args) = parser.parse_args()
    dstore_obj = DStoreDesktop()
    system_bus = dbus.SystemBus()
    if options.scan:
        if system_bus.name_has_owner(DBUS_NAME):
            print DBUS_NAME, "is running..."
            bus_object = system_bus.get_object(DBUS_NAME, DBUS_PATH)
            bus_interface = dbus.Interface(bus_object, DBUS_INTERFACE)
            bus_interface.Scanning()
        else:
            bus_name = dbus.service.BusName(DBUS_NAME, bus=system_bus)
            service = DStoreDBusApi(bus_name, DBUS_PATH, mainloop)
            service.Scanning()
    else:
        if system_bus.name_has_owner(DBUS_NAME):
            print DBUS_NAME, "is running..."
        else:
            bus_name = dbus.service.BusName(DBUS_NAME, bus=system_bus)
            service = DStoreDBusApi(bus_name, DBUS_PATH, mainloop)
            mainloop.run()

