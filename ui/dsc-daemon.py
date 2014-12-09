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
import gobject
import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from datetime import datetime
import threading
import urllib2
import uuid
import json

from deepin_utils.ipc import is_dbus_name_exists
from deepin_utils.file import touch_file
from deepin_utils.config import Config

from nls import _
from logger import Logger

DSC_SERVICE_NAME = "com.linuxdeepin.softwarecenter"
DSC_SERVICE_PATH = "/com/linuxdeepin/softwarecenter"

DSC_FRONTEND_NAME = "com.linuxdeepin.softwarecenter_frontend"
DSC_FRONTEND_PATH = "/com/linuxdeepin/softwarecenter_frontend"

DSC_UPDATE_DAEMON_NAME = "com.deepin.softwarecenter.UpdateDaemon"
DSC_UPDATE_DAEMON_PATH = "/com/deepin/softwarecenter/UpdateDaemon"

DSC_UPDATER_NAME = "com.linuxdeepin.softwarecenterupdater"
DSC_UPDATER_PATH = "/com/linuxdeepin/softwarecenterupdater"

NOTIFICATIONS_NAME = "org.freedesktop.Notifications"
NOTIFICATIONS_PATH = "/org/freedesktop/Notifications"

LOG_PATH = "/tmp/dsc-update-daemon.log"
DATA_CURRENT_ID_CONFIG_PATH = '/tmp/deepin-software-center/data_current_id.ini'

DELAY_UPDATE_INTERVAL = 600

SERVER_ADDRESS = "http://apis.linuxdeepin.com/dscapi/statistics/?uid="

from constant import NO_NOTIFY_FILE, dsc_root_dir, DEFAULT_UPDATE_INTERVAL, CONFIG_INFO_PATH
if not os.path.exists(CONFIG_INFO_PATH):
    touch_file(CONFIG_INFO_PATH)
config = Config(CONFIG_INFO_PATH)
config.load()

def get_common_image(name):
    return os.path.join(dsc_root_dir, "image", name)

def is_auto_update():
    if config.has_option('update', 'auto'):
        if config.get('update', 'auto') == 'False':
            return False
    return True

def get_update_interval():
    if config.has_option('update', 'interval'):
        return config.get('update', 'interval')
    return DEFAULT_UPDATE_INTERVAL

def is_first_started():
    return not config.has_option('settings', 'first_started')

def set_first_started():
    config.set("settings", "first_started", "false")
    config.write()

def log(message):
    if not os.path.exists(LOG_PATH):
        open(LOG_PATH, "w").close()
        os.chmod(LOG_PATH, 0777)
    with open(LOG_PATH, "a") as file_handler:
        now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        file_handler.write("%s %s\n" % (now, message))

class SendStatistics(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.init_config()
        self.daemon = True

    def init_config(self):
        global config
        has_init = config.has_option("statistics", "uid") and config.get("statistics", "uid")
        if not has_init:
            uid = uuid.uuid4().hex
            config.set("statistics", 'uid', uid)
            config.set("statistics", 'last_date', '')
            config.write()

    @staticmethod
    def has_running():
        last_date = config.get('statistics', 'last_date')
        current_date = datetime.now().strftime("%Y-%m-%d")
        return last_date == current_date

    def run(self):
        if self.has_running():
            return

        global config
        uid = config.get('statistics', 'uid')
        current_date = datetime.now().strftime("%Y-%m-%d")
        try:
            result = urllib2.urlopen(SERVER_ADDRESS+uid).read()
            msg = "SendStatistics:", result
            log(msg)
            print msg
            if result == "OK":
                config.set('statistics', "last_date", current_date)
                config.write()
        except Exception, e:
            msg = "Error in SendStatistics: %s" % (e)
            log(msg)
            print msg

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

class Update(dbus.service.Object, Logger):
    def __init__(self, mainloop, session_bus):
        self.session_bus = session_bus
        dbus.service.Object.__init__(self, self.session_bus)
        Logger.__init__(self)
        self.mainloop = mainloop

        self.is_run_in_daemon = True

        self.exit_flag = False
        self.is_in_update_list = False
        self.update_status = None

        self.system_bus = None
        self.bus_interface = None
        self.delay_update_id = None

        self.update_num = 0
        self.remind_num = 0

        self.net_detector = NetworkDetector()

        self.loginfo("Start Update List Daemon")

    def handle_mirror_test(self):
        if is_first_started():
            self.loginfo("Mirror test start...")
            from mirror_test import get_best_mirror
            best_mirror = get_best_mirror()
            repo_urls = best_mirror.get_repo_urls()
            if not self.is_fontend_running():
                self.bus_interface.change_source_list(repo_urls)
                set_first_started()
                self.loginfo("first started has setted!")
            self.loginfo("Mirror test finish!")

    def run(self, daemon):
        self.is_run_in_daemon = daemon
        self.loginfo("run in daemon: %s" % self.is_run_in_daemon)
        self.update_handler()
        return False

    def send_notify(self, body, summary):
        self.notify_id = None
        self.notify_interface = None
        try:
            notify_obj = self.session_bus.get_object(NOTIFICATIONS_NAME, NOTIFICATIONS_PATH)
            self.notify_interface = dbus.Interface(notify_obj, NOTIFICATIONS_NAME)
            self.session_bus.add_signal_receiver(
                handler_function=self.handle_notification_action,
                signal_name="ActionInvoked",
                dbus_interface=NOTIFICATIONS_NAME
            )
            self.session_bus.add_signal_receiver(
                handler_function=self.handle_notification_close,
                signal_name="NotificationClosed",
                dbus_interface=NOTIFICATIONS_NAME
            )
        except:
            pass

        app_name = "deepin-software-center"
        replaces_id = 0
        app_icon = get_common_image("logo48.png")
        actions = ["default", "default", "_id_open_update_", _("Upgrade")]
        hints = {"image-path": app_icon}
        timeout = 3500
        if self.notify_interface:
            r = self.notify_interface.Notify(app_name, replaces_id, app_icon,
                summary, body, actions, hints, timeout,
                )
            self.notify_id = int(r)

    def handle_notification_action(self, notify_id, action_id):
        notify_id = int(notify_id)
        action_id = str(action_id)
        if self.notify_id == notify_id:
            dsc_obj = self.session_bus.get_object(DSC_FRONTEND_NAME, DSC_FRONTEND_PATH)
            self.dsc_interface = dbus.Interface(dsc_obj, DSC_FRONTEND_NAME)
            if action_id == "default":
                self.dsc_interface.show_page("home")
                self.dsc_interface.raise_to_top()
            elif action_id == "_id_open_update_":
                self.dsc_interface.show_page("upgrade")
                self.dsc_interface.raise_to_top()

    def handle_notification_close(self, notify_id, reason):
        notify_id = int(notify_id)
        if self.notify_id == notify_id and not self.is_run_in_daemon:
            gobject.timeout_add_seconds(5, self.mainloop.quit)

    def set_delay_update(self, seconds):
        if not self.is_run_in_daemon:
            self.mainloop.quit()
        else:
            if self.delay_update_id:
                gobject.source_remove(self.delay_update_id)

            if is_auto_update() and seconds:
                self.delay_update_id = gobject.timeout_add_seconds(seconds, self.update_handler)
            else:
                self.mainloop.quit()

    def start_dsc_backend(self):
        self.loginfo("Start dsc backend service")
        self.system_bus = dbus.SystemBus()
        bus_object = self.system_bus.get_object(DSC_SERVICE_NAME, DSC_SERVICE_PATH)
        self.bus_interface = dbus.Interface(bus_object, DSC_SERVICE_NAME)
        self.system_bus.add_signal_receiver(
                self.handle_dsc_update_signal,
                signal_name="update_signal",
                dbus_interface=DSC_SERVICE_NAME,
                path=DSC_SERVICE_PATH)

    def handle_dsc_update_signal(self, messages):
        for message in messages:
            (signal_type, action_content) = message
            if signal_type == "update-list-update":
                self.is_in_update_list = True
                self.update_status = "update"
            elif signal_type == "update-list-finish":
                self.is_in_update_list = False
                self.update_status = "finish"
                (upgrade_state, pkg_infos) = self.bus_interface.RequestUpgradeStatus()
                need_upgrade_pkg_names = []
                for info in pkg_infos:
                    need_upgrade_pkg_names.append(json.loads(info)[0])
                hold_upgrade_pkg_names = self.bus_interface.read_no_notify_config(NO_NOTIFY_FILE)
                for name in hold_upgrade_pkg_names:
                    if name in need_upgrade_pkg_names:
                        need_upgrade_pkg_names.remove(name)
                remind_num = len(need_upgrade_pkg_names)
                self.loginfo("Remind update number: %s" % remind_num)
                if remind_num != self.remind_num:
                    if remind_num > 1:
                        self.send_notify(_("There are %s packages needed to "
                            "upgrade in your system, please use Deepin Store "
                            "to upgrade.") % remind_num, _("Deepin Store"))
                    else:
                        self.send_notify(_("There is %s package needed to "
                            "upgrade in your system, please use Deepin Store "
                            "to upgrade.") % remind_num, _("Deepin Store"))

                self.remind_num = remind_num
                self.loginfo("Finish update list.")

                self.bus_interface.request_quit()
                self.loginfo("Quit dsc backend service.")

                self.set_delay_update(int(get_update_interval())*3600)
            elif signal_type == "update-list-failed":
                self.is_in_update_list = False
                self.update_status = "failed"
                self.bus_interface.request_quit()
                self.start_detector()
                self.loginfo("update failed, daemon will try when network is OK!")
        return True

    def start_detector(self):
        self.net_detector.start_detect_source_available()
        self.net_detector.connect("network-status-changed", self.network_changed_handler)

    def network_changed_handler(self, obj, status):
        if status == NetworkDetector.NETWORK_STATUS_OK:
            self.update_handler()

    def update_handler(self):
        if self.is_fontend_running():
            self.logwarn("Fontend is running, waite 10 minutes to try again!")
            self.set_delay_update(DELAY_UPDATE_INTERVAL)
        elif not is_auto_update():
            self.loginfo('Auto update closed, exit...')
            self.mainloop.quit()
        else:
            self.start_dsc_backend()
            self.handle_mirror_test()
            gobject.timeout_add_seconds(1, self.start_updater, False)
            gobject.timeout_add_seconds(1, self.start_update_list, self.bus_interface)
            SendStatistics().start()
        return True

    def start_update_list(self, bus_interface):
        if not self.is_in_update_list:
            self.loginfo("Start update list...")
            bus_interface.start_update_list()
        else:
            self.loginfo("other app is running update list")
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

    @dbus.service.method(DSC_UPDATE_DAEMON_NAME, in_signature="", out_signature="b")
    def get_update_list_status(self):
        return self.is_in_update_list

    # for deepin software center data update
    def start_updater(self, loop=True):
        try:
            if is_dbus_name_exists(DSC_UPDATER_NAME, False):
                self.logwarn("Deepin software center updater has running!")
            else:
                system_bus = dbus.SystemBus()
                bus_object = system_bus.get_object(DSC_UPDATER_NAME, DSC_UPDATER_PATH)
                dbus.Interface(bus_object, DSC_UPDATER_NAME)
                self.loginfo("Start dsc data update service.")
        except Exception, e:
            self.logerror("got error: %s" % (e))

        return loop

if __name__ == "__main__" :
    uid = os.geteuid()
    if uid == 0:
        sys.exit(0)
    args = sys.argv[1::]

    DBusGMainLoop(set_as_default=True)
    mainloop = gobject.MainLoop()

    session_bus = dbus.SessionBus()
    if session_bus.name_has_owner(DSC_UPDATE_DAEMON_NAME):
        print "dbus service \"%s\" is running..." % DSC_UPDATE_DAEMON_NAME
        sys.exit(0)
    else:
        bus_name = dbus.service.BusName(DSC_UPDATE_DAEMON_NAME, session_bus)

    update = Update(mainloop, session_bus)
    update.add_to_connection(session_bus, DSC_UPDATE_DAEMON_PATH)
    #update.send_notify("body", "message")
    if '--no-daemon' in args:
        gobject.timeout_add_seconds(1, update.run, False )
    else:
        gobject.timeout_add_seconds(120, update.run, True)
    mainloop.run()
