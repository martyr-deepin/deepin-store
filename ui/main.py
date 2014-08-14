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
import dbus
import dbus.service
import dbus.mainloop.glib
from dbus.mainloop.glib import DBusGMainLoop
from constant import DSC_FRONTEND_NAME, DSC_FRONTEND_PATH
from deepin_utils.ipc import is_dbus_name_exists
import gtk
import os

from optparse import OptionParser

def start_main():
    # Init.
    DBusGMainLoop(set_as_default=True)
    gtk.gdk.threads_init()
    session_bus = dbus.SessionBus()
    options, arguments = get_parser()

    # Send hello message if updater has running.
    if is_dbus_name_exists(DSC_FRONTEND_NAME, True):

        bus_object = session_bus.get_object(DSC_FRONTEND_NAME, DSC_FRONTEND_PATH)
        bus_interface = dbus.Interface(bus_object, DSC_FRONTEND_NAME)
        bus_interface.raise_to_top()
        if options.show_page:
            bus_interface.show_page(options.show_page)
    else:
        # Init dbus.
        bus_name = dbus.service.BusName(DSC_FRONTEND_NAME, session_bus)

        software_center = DeepinSoftwareCenter(session_bus, arguments)
        if options.show_page:
            gtk.timeout_add(500, lambda:software_center.show_page(options.show_page))
        if options.show_recommend:
            software_center.recommend_status = options.show_recommend
        if options.start_quiet:
            software_center.init_hide = True

        try:
            software_center.run()
        except KeyboardInterrupt:
            software_center.bus_interface.request_quit()

def get_parser():
    parser = OptionParser()
    parser.add_option("-p", "--page", dest="show_page",
            help="show four page: home, upgrade, uninstall, install", metavar="pages")
    parser.add_option("--home-recommend", dest="show_recommend",
            help="show home page with status", metavar="status")
    parser.add_option("-q", "--quiet", action="store_true", dest="start_quiet",
            help="start deepin software center in quiet mode")
    (options, args) = parser.parse_args()
    return (options, args)

if __name__ == '__main__':
    if os.getuid() == 0:
        import sys
        print "can't start width root privilege"
        sys.exit(1)
    start_main()
