#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 ~ 2013 Deepin, Inc.
#               2012 ~ 2013 Kaisheng Ye
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

import sys, os
import subprocess
import apt_pkg
import gobject
import signal
import dbus
import dbus.service
import dbus.mainloop.glib
from dbus.mainloop.glib import DBusGMainLoop
from datetime import datetime
import traceback
import threading
import urllib2
import uuid
from deepin_utils.ipc import is_dbus_name_exists
from deepin_utils.file import get_parent_dir, touch_file
from deepin_utils.config import Config
from nls import _

DSC_SERVICE_NAME = "com.linuxdeepin.softwarecenter"
DSC_SERVICE_PATH = "/com/linuxdeepin/softwarecenter"

DSC_FRONTEND_NAME = "com.linuxdeepin.softwarecenter_frontend"
DSC_FRONTEND_PATH = "/com/linuxdeepin/softwarecenter_frontend"

DSC_UPDATE_DAEMON_NAME = "com.linuxdeepin.softwarecenter.update.daemon"
DSC_UPDATE_DAEMON_PATH = "/com/linuxdeepin/softwarecenter/update/daemon"

DSC_UPDATER_NAME = "com.linuxdeepin.softwarecenterupdater"
DSC_UPDATER_PATH = "/com/linuxdeepin/softwarecenterupdater"

NOTIFICATIONS_NAME = "org.freedesktop.Notifications"
NOTIFICATIONS_PATH = "/org/freedesktop/Notifications"

LOG_PATH = "/tmp/dsc-update-daemon.log"
DATA_CURRENT_ID_CONFIG_PATH = '/tmp/deepin-software-center/data_current_id.ini'

CONFIG_DIR =  os.path.join(os.path.expanduser("~"), ".config", "deepin-software-center")
CONFIG_INFO_PATH = os.path.join(CONFIG_DIR, "config_info.ini")

DELAY_UPDATE_INTERVAL = 600

SERVER_ADDRESS = "http://apis.linuxdeepin.com/dscapi/statistics/?uid="

sys.path.insert(0, os.path.join(get_parent_dir(__file__, 3), 'ui'))
from constant import NO_NOTIFY_FILE
import utils

def log(message):
    if not os.path.exists(LOG_PATH):
        open(LOG_PATH, "w").close()
        os.chmod(LOG_PATH, 0777)
    with open(LOG_PATH, "a") as file_handler:
        now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        file_handler.write("%s %s\n" % (now, message))

# for deepin software center data update
def start_updater(loop=True):
    try:
        if is_dbus_name_exists(DSC_UPDATER_NAME, False):
            log("Deepin software center updater has running!")
            print "Deepin software center updater has running!"
        else:
            system_bus = dbus.SystemBus()
            bus_object = system_bus.get_object(DSC_UPDATER_NAME, DSC_UPDATER_PATH)
            dbus.Interface(bus_object, DSC_UPDATER_NAME)
            log("Start dsc data update service.")
            print "Start dsc data update service."
    except Exception, e:
        log("got error: %s" % (e))
        print "got error: %s" % (e)
        traceback.print_exc(file=sys.stdout)

    return loop

class SendStatistics(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.config = self.init_config()
        self.daemon = True

    def init_config(self):
        if os.path.exists(CONFIG_INFO_PATH):
            config = Config(CONFIG_INFO_PATH)
            config.load()
            uid = config.get("statistics", 'uid')
            if not uid:
                uid = uuid.uuid4().hex
                config.set("statistics", 'uid', uid)
                config.set("statistics", 'last_date', '')
                config.write()
        else:
            touch_file(CONFIG_INFO_PATH)
            uid = uuid.uuid4().hex
            config = Config(CONFIG_INFO_PATH)
            config.load()
            config.set("statistics", 'uid', uid)
            config.set("statistics", 'last_date', '')
            config.write()

        return config

    def run(self):
        uid = self.config.get('statistics', 'uid')
        last_date = self.config.get('statistics', 'last_date')
        current_date = datetime.now().strftime("%Y-%m-%d")
        if last_date == current_date:
            return
        else:
            try:
                result = urllib2.urlopen(SERVER_ADDRESS+uid).read()
                msg = "SendStatistics:", result
                log(msg)
                print msg
                if result == "OK":
                    self.config.set('statistics', "last_date", current_date)
                    self.config.write()
            except Exception, e:
                msg = "Error in SendStatistics: %s" % (e)
                log(msg)
                print msg
                traceback.print_exc(file=sys.stdout)

class NetworkDetector(gobject.GObject):

    NETWORK_STATUS_OK = 0
    NETWORK_STATUS_FAILED = 1

    __gsignals__ = {
            "network-status-changed":(gobject.SIGNAL_RUN_LAST, 
                                      gobject.TYPE_NONE,
                                      (gobject.TYPE_INT, ))
        }

    def __init__(self):
        gobject.GObject.__init__(self)
        self.network_status = self.NETWORK_STATUS_FAILED

    def start_detect_source_available(self):
        apt_pkg.init_config()
        apt_pkg.init_system()
        source_list_obj = apt_pkg.SourceList()
        source_list_obj.read_main_list()
        uri = source_list_obj.list[0].uri.split("/")[2]
        uri = 'www.baidu.com'
        gobject.timeout_add(1000, self.network_detect_loop, uri)

    def network_detect_loop(self, uri):
        current_status = None
        if self.ping_uri(uri):
            current_status = self.NETWORK_STATUS_OK
            if self.network_status != current_status:
                self.network_status = current_status
                self.emit("network-status-changed", self.network_status)
            return False
        else:
            current_status = self.NETWORK_STATUS_FAILED
            if self.network_status != current_status:
                self.network_status = current_status
                self.emit("network-status-changed", self.network_status)
            return True

    def ping_uri(self, uri):
        fnull = open(os.devnull, 'w')
        return1 = subprocess.call('ping -c 1 %s' % uri, shell = True, stdout = fnull, stderr = fnull)
        if return1:
            fnull.close()
            return False
        else:
            fnull.close()
            return True

class Update(dbus.service.Object):
    def __init__(self, session_bus, mainloop):
        dbus.service.Object.__init__(self, session_bus, DSC_UPDATE_DAEMON_PATH)
        self.session_bus = session_bus
        self.mainloop = mainloop

        self.exit_flag = False
        self.is_in_update_list = False
        self.update_status = None

        self.system_bus = None
        self.bus_interface = None
        self.delay_update_id = None

        self.update_num = 0
        self.remind_num = 0

        self.net_detector = NetworkDetector()
        self.init_notify()

        log("Start Update List Daemon")

    def run(self):
        self.update_handler()
        return False

    def init_notify(self):
        self.notify_id = None
        notify_obj = self.session_bus.get_object(NOTIFICATIONS_NAME, NOTIFICATIONS_PATH)
        self.notify_interface = dbus.Interface(notify_obj, NOTIFICATIONS_NAME)
        self.session_bus.add_signal_receiver(
            self.handle_notification_action,
            signal_name="ActionInvoked",
            dbus_interface=NOTIFICATIONS_NAME, 
            bus_name=NOTIFICATIONS_NAME,
            path=NOTIFICATIONS_PATH,
        )

    def send_notify(self, body, summary):
        app_name = "deepin-software-center"
        replaces_id = 0
        app_icon = utils.get_common_image("logo48.png")
        actions = ["_id_default_", "default", "_id_open_update_", _("Upgrade")]
        hints = {"image-path": app_icon}
        timeout = 3500
        return self.notify_interface.Notify(app_name, replaces_id, app_icon,
            summary, body, actions, hints, timeout)

    def handle_notification_action(self, notify_id, action_id):
        if self.notify_id == notify_id:
            dsc_obj = self.session_bus.get_object(DSC_FRONTEND_NAME, DSC_FRONTEND_PATH)
            self.dsc_interface = dbus.Interface(dsc_obj, DSC_FRONTEND_NAME)
            if action_id == "_id_default_":
                self.dsc_interface.show_page("home")
            elif action_id == "_id_open_update_":
                self.dsc_interface.show_page("upgrade")

    def set_delay_update(self, seconds):
        if self.delay_update_id:
            gobject.source_remove(self.delay_update_id)
        if utils.is_auto_update() and seconds:
            self.delay_update_id = gobject.timeout_add_seconds(seconds, self.update_handler)
        else:
            self.mainloop.quit()

    def start_dsc_backend(self):
        print "Start dsc backend service"
        self.system_bus = dbus.SystemBus()
        bus_object = self.system_bus.get_object(DSC_SERVICE_NAME, DSC_SERVICE_PATH)
        self.bus_interface = dbus.Interface(bus_object, DSC_SERVICE_NAME)
        self.system_bus.add_signal_receiver(
                self.signal_receiver, 
                signal_name="update_signal", 
                dbus_interface=DSC_SERVICE_NAME, 
                path=DSC_SERVICE_PATH)

    def signal_receiver(self, messages):
        for message in messages:
            (signal_type, action_content) = message
            
            if signal_type == "update-list-update":
                self.is_in_update_list = True
                self.update_status = "update"
            elif signal_type == "update-list-finish":
                self.is_in_update_list = False
                self.update_status = "finish"
                self.system_bus.remove_signal_receiver(
                        self.signal_receiver, 
                        signal_name="update_signal", 
                        dbus_interface=DSC_SERVICE_NAME, 
                        path=DSC_SERVICE_PATH)
                update_num = len(self.bus_interface.request_upgrade_pkgs())
                remind_num = update_num - len(self.bus_interface.read_no_notify_config(NO_NOTIFY_FILE))
                print "Remind update number:", remind_num
                if remind_num < 0: 
                    log("Error for no notify function\nUpdate number: %s\nNo notify number: %s" % 
                            (update_num, update_num-remind_num))
                elif remind_num > 0 and remind_num != self.remind_num:
                    if remind_num != 1:
                        self.notify_id = self.send_notify(_(
                            "There are %s packages need to upgrade in your system,"
                            " please open the software center to upgrade!"
                            ) % remind_num,
                            _("Software Center"))
                    else:
                        self.notify_id = self.send_notify(_(
                            "There is %s package need to upgrade in your system,"
                            " please open the software center to upgrade!"
                            ) % remind_num,
                            _("Software Center"))
                self.remind_num = remind_num
                print "Finish update list."
                log("Finish update list.")
                self.bus_interface.request_quit()
                print "Quit dsc backend service."
                log("Quit dsc backend service.")
                self.set_delay_update(int(utils.get_update_interval())*3600)
            elif signal_type == "update-list-failed":
                self.is_in_update_list = False
                self.update_status = "failed"
                self.system_bus.remove_signal_receiver(
                        self.signal_receiver, 
                        signal_name="update_signal", 
                        dbus_interface=DSC_SERVICE_NAME, 
                        path=DSC_SERVICE_PATH)
                self.bus_interface.request_quit()
                self.start_detector()
                print "update failed, daemon will try when network is OK!"
                log("update failed, daemon will try when network is OK!")
        return True

    def start_detector(self):
        self.net_detector.start_detect_source_available()
        self.net_detector.connect("network-status-changed", self.network_changed_handler)

    def network_changed_handler(self, obj, status):
        if status == NetworkDetector.NETWORK_STATUS_OK:
            self.update_handler()

    def update_handler(self):
        if self.is_fontend_running():
            print "Fontend is running, waite 10 minutes to try again!"
            log("Fontend is running, waite 10 minutes to try again!")
            self.set_delay_update(DELAY_UPDATE_INTERVAL)
        elif not utils.is_auto_update():
            print 'Auto update closed, exit...'
            log('Auto update closed, exit...')
            self.mainloop.quit()
        else:
            self.start_dsc_backend()
            gobject.timeout_add_seconds(30, start_updater, False)
            gobject.timeout_add_seconds(1, self.start_update_list, self.bus_interface)
            SendStatistics().start()
        return True

    def start_update_list(self, bus_interface):
        if not self.is_in_update_list:
            print "Start update list..."
            log("Start update list...")
            bus_interface.start_update_list()
        else:
            log("other app is running update list")
        return False

    def is_fontend_running(self):
        if os.path.exists(DATA_CURRENT_ID_CONFIG_PATH):
            config = Config(DATA_CURRENT_ID_CONFIG_PATH)
            config.load()
            data_id = config.get('current', 'data_id')
            if data_id:
                return True
            else:
                return False
        else:
            False

    def exit_loop(self):
        self.exit_flag = True

    @dbus.service.method(DSC_UPDATE_DAEMON_NAME, in_signature="", out_signature="b")    
    def get_update_list_status(self):
        return self.is_in_update_list

    @dbus.service.method(DSC_UPDATE_DAEMON_NAME, in_signature="", out_signature="")    
    def quit(self):
        self.mainloop.quit()

if __name__ == "__main__" :

    uid = os.geteuid()
    if uid == 0:
        sys.exit(0)

    arguments = sys.argv[1::]

    DBusGMainLoop(set_as_default=True)
    session_bus = dbus.SessionBus()
    
    mainloop = gobject.MainLoop()
    signal.signal(signal.SIGINT, lambda : mainloop.quit()) # capture "Ctrl + c" signal

    if not is_dbus_name_exists(DSC_UPDATE_DAEMON_NAME, True):
        bus_name = dbus.service.BusName(DSC_UPDATE_DAEMON_NAME, session_bus)
            
        update = Update(session_bus, mainloop)
        try:
            if '--debug' in arguments:
                gobject.timeout_add_seconds(1, update.run)
            else:
                gobject.timeout_add_seconds(120, update.run)
            mainloop.run()
        except KeyboardInterrupt:
            update.exit_loop()
