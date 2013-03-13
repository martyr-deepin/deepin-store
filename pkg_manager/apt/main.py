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

import sys
import os
from deepin_utils.file import get_parent_dir
sys.path.append(os.path.join(get_parent_dir(__file__, 3), "download_manager", "deepin_storm"))

import signal
from download_manager import DownloadManager
import apt.debfile as debfile
from parse_pkg import get_pkg_download_info, get_deb_download_info
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import os
from constant import DSC_SERVICE_NAME, DSC_SERVICE_PATH, ACTION_INSTALL, ACTION_UPGRADE, ACTION_UNINSTALL, DOWNLOAD_STATUS_NOTNEED, DOWNLOAD_STATUS_ERROR
from apt_cache import AptCache
from action import AptActionPool
from events import global_event
from deepin_utils.ipc import auth_with_policykit
from utils import log, LOG_PATH
from update_list import UpdateList
import threading as td
from Queue import Queue

DATA_DIR = os.path.join(get_parent_dir(__file__, 3), "data")

class ExitManager(td.Thread):
    '''
    class docs
    '''
	
    def __init__(self, 
                 mainloop,
                 is_update_list_running, 
                 is_download_action_running,
                 is_apt_action_running,
                 have_exit_request):
        '''
        init docs
        '''
        td.Thread.__init__(self)
        self.setDaemon(True)
        
        self.mainloop = mainloop
        self.is_update_list_running = is_update_list_running
        self.is_download_action_running = is_download_action_running
        self.is_apt_action_running = is_apt_action_running
        self.have_exit_request = have_exit_request
        
        self.signal = Queue()
        
    def check(self):
        self.signal.put("check")
        
    def run(self):
        self.loop()
    
    def loop(self):
        signal = self.signal.get()
        if signal == "check":
            if self.is_download_action_running():
                print "Download action still runing, exit later"
                self.loop()
            elif self.is_update_list_running():
                print "Update list still runing, exit later"
                self.loop()
            elif self.is_apt_action_running():
                print "Apt action still running, exit later"
                self.loop()
            else:
                if self.have_exit_request():
                    print "Exit"
                    self.mainloop.quit()
                else:
                    print "Pass"
                    self.loop()
                    
class PackageManager(dbus.service.Object):
    
                
    def __init__(self, system_bus, mainloop, pkg_cache):
        log("init dbus")
        
        # Init dbus service.
        dbus.service.Object.__init__(self, system_bus, DSC_SERVICE_PATH)
        # Init.
        self.mainloop = mainloop
        self.pkg_cache = pkg_cache
        self.exit_flag = False
        self.simulate = False
        
        self.apt_action_pool = AptActionPool(self.pkg_cache)
        self.apt_action_pool.start()
        
        global_event.register_event("action-start", lambda signal_content: self.update_signal([("action-start", signal_content)]))
        global_event.register_event("action-update", lambda signal_content: self.update_signal([("action-update", signal_content)]))
        global_event.register_event("action-finish", self.action_finish)
        global_event.register_event("action-failed", self.action_failed)
        
        self.download_manager = DownloadManager(global_event)
        
        global_event.register_event(
            "download-start", 
            lambda pkg_name, action_type: self.update_signal([("download-start", (pkg_name, action_type))]))
        global_event.register_event(
            "download-update",
            lambda pkg_name, action_type, percent, speed: self.update_signal([("download-update", (pkg_name, action_type, percent, speed))]))
        global_event.register_event("download-finish", self.download_finish)
        global_event.register_event("download-stop", self.download_stop)
        
        self.in_update_list = False
        global_event.register_event("update-list-start", self.update_list_start)
        global_event.register_event("update-list-finish", self.update_list_finish)
        global_event.register_event("update-list-failed", self.update_list_failed)
        global_event.register_event("update-list-update", self.update_list_update)
        
        self.exit_manager = ExitManager(
            self.mainloop,
            self.is_update_list_running,
            self.is_download_action_running,
            self.is_apt_action_running,
            self.have_exit_request)
        self.exit_manager.start()
        
        log("init finish")
        
    def action_finish(self, signal_content):
        self.update_signal([("action-finish", signal_content)])
        
        self.exit_manager.check()

    def action_failed(self, signal_content):
        self.update_signal([("action-failed", signal_content)])
        
        self.exit_manager.check()
        
    def is_update_list_running(self):
        return self.in_update_list
    
    def is_download_action_running(self):
        return len(self.download_manager.fetch_files_dict) > 0
    
    def is_apt_action_running(self):
        return len(self.apt_action_pool.active_mission_list) + len(self.apt_action_pool.wait_mission_list) > 0
    
    def have_exit_request(self):
        return self.exit_flag
        
    def update_list_start(self):
        self.in_update_list = True
        self.update_signal([("update-list-start", "")])
        print "start"

    def update_list_finish(self):
        self.in_update_list = False
        self.update_signal([("update-list-finish", "")])
        print "finish"
        
        self.exit_manager.check()

    def update_list_failed(self):
        self.in_update_list = False
        self.update_signal([("update-list-failed", "")])
        print "failed"
        
        self.exit_manager.check()
        
    def update_list_update(self, percent):
        self.update_signal([("update-list-update", percent)])
        print "update: %s" % percent

    def handle_dbus_reply(self, *reply):
        log("%s (reply): %s" % (self.module_dbus_name, str(reply)))        
        
    def handle_dbus_error(self, *error):
        log("%s (error): %s" % (self.module_dbus_name, str(error)))
        
    def add_download(self, pkg_name, action_type, simulate=False):
        pkg_infos = get_pkg_download_info(self.pkg_cache.cache, pkg_name)
        if pkg_infos == DOWNLOAD_STATUS_NOTNEED:
            self.download_finish(pkg_name, action_type, simulate)
            print "Don't need download"
        elif pkg_infos == DOWNLOAD_STATUS_ERROR:
            self.update_signal([("parse-download-error", (pkg_name, action_type))])
            print "Download error"
        else:
            (download_urls, download_hash_infos, pkg_sizes) = pkg_infos
            
            self.download_manager.add_download(pkg_name, action_type, simulate, download_urls, download_hash_infos, pkg_sizes)
            
    def download_finish(self, pkg_name, action_type, simulate, deb_file=""):
        self.update_signal([("download-finish", (pkg_name, action_type))])
        
        if action_type == ACTION_INSTALL:
            self.apt_action_pool.add_install_action([pkg_name], simulate, deb_file)
        elif action_type == ACTION_UPGRADE:
            self.apt_action_pool.add_upgrade_action([pkg_name], simulate)
            
        self.exit_manager.check()    
        
    def download_stop(self, pkg_name, action_type):
        self.update_signal([("download-stop", (pkg_name, action_type))])
        
        self.exit_manager.check()    
        
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="b", out_signature="")    
    def say_hello(self, simulate):
        # Set exit_flag with False to prevent backend exit, 
        # this just useful that frontend start again before backend exit.
        log("Say hello from frontend.")
        
        self.exit_flag = False
        self.simulate = simulate
        
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="", out_signature="")    
    def request_quit(self):
        # Set exit flag.
        self.exit_flag = True
        
        self.exit_manager.check()
        
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="", out_signature="as")    
    def request_upgrade_pkgs(self):
        if self.in_update_list:
            return []
        else:
            return self.pkg_cache.get_upgrade_pkgs()
    
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="", out_signature="as")    
    def request_uninstall_pkgs(self):
        return self.pkg_cache.get_uninstall_pkgs()

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="as")    
    def request_pkgs_install_version(self, pkg_names):
        return self.pkg_cache.get_pkgs_install_version(pkg_names)

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="as")    
    def request_pkgs_uninstall_version(self, pkg_names):
        return self.pkg_cache.get_pkgs_uninstall_version(pkg_names)

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")    
    def install_pkg(self, pkg_names):
        for pkg_name in pkg_names:
            self.add_download(pkg_name, ACTION_INSTALL, self.simulate)
    
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")    
    def uninstall_pkg(self, pkg_names):
        self.apt_action_pool.add_uninstall_action(pkg_names, self.simulate)

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")    
    def upgrade_pkg(self, pkg_names):
        for pkg_name in pkg_names:
            self.add_download(pkg_name, ACTION_UPGRADE, self.simulate)

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")    
    def install_deb_files(self, deb_files):
        if len(deb_files) > 0:
            for deb_file in deb_files:
                deb_package = debfile.DebPackage(deb_file, self.pkg_cache.cache)
                deb_pkg_name = deb_package.pkgname
                
                self.update_signal([("got-install-deb-pkg-name", deb_pkg_name)])
                
                pkg_infos = get_deb_download_info(self.pkg_cache.cache, deb_file)
                if pkg_infos == DOWNLOAD_STATUS_NOTNEED:
                    self.download_finish(deb_pkg_name, ACTION_INSTALL, self.simulate, deb_file)
                    print "Don't need download"
                elif pkg_infos == DOWNLOAD_STATUS_ERROR:
                    self.update_signal([("parse-download-error", (deb_pkg_name, ACTION_INSTALL))])
                    print "Download error"
                else:
                    (download_urls, download_hash_infos, pkg_sizes) = pkg_infos
                    
                    self.download_manager.add_download(deb_pkg_name, 
                                                       ACTION_INSTALL, 
                                                       self.simulate, 
                                                       download_urls, 
                                                       download_hash_infos, 
                                                       pkg_sizes, 
                                                       deb_file)

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")    
    def stop_download_pkg(self, pkg_names):
        for pkg_name in pkg_names:
            self.download_manager.stop_download(pkg_name)
            
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")    
    def remove_wait_missions(self, pkg_infos):
        self.apt_action_pool.remove_wait_missions(pkg_infos)

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")    
    def remove_wait_downloads(self, pkg_names):
        for pkg_name in pkg_names:
            self.download_manager.stop_wait_download(pkg_name)
            
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="s", out_signature="s")        
    def request_pkg_short_desc(self, pkg_name):
        return self.pkg_cache.get_pkg_short_desc(pkg_name)
    
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="", out_signature="as")        
    def request_status(self):
        download_status = {
            ACTION_INSTALL : [],
            ACTION_UPGRADE : []}
        for (pkg_name, info_dict) in self.download_manager.fetch_files_dict.items():
            if info_dict["action_type"] == ACTION_INSTALL:
                download_status[ACTION_INSTALL].append((pkg_name, info_dict["status"]))
            elif info_dict["action_type"] == ACTION_UPGRADE:
                download_status[ACTION_UPGRADE].append((pkg_name, info_dict["status"]))
                
        action_status = {
            ACTION_INSTALL : [],
            ACTION_UPGRADE : [],
            ACTION_UNINSTALL : []}        
        for (pkg_name, info_dict) in self.apt_action_pool.install_action_dict.items():
            action_status[ACTION_INSTALL].append((pkg_name, info_dict["status"]))
        for (pkg_name, info_dict) in self.apt_action_pool.upgrade_action_dict.items():
            action_status[ACTION_UPGRADE].append((pkg_name, info_dict["status"]))
        for (pkg_name, info_dict) in self.apt_action_pool.uninstall_action_dict.items():
            action_status[ACTION_UNINSTALL].append((pkg_name, info_dict["status"]))
        
        return [str(download_status), str(action_status)]
    
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="", out_signature="b")
    def start_update_list(self):
        log("start update list...")
        gobject.timeout_add(10, lambda : UpdateList(self.pkg_cache).start())
        log("start update list done")
        
        return True
    
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="ab")
    def request_pkgs_install_status(self, pkg_names):
        return map(self.pkg_cache.is_pkg_installed, pkg_names)
            
    @dbus.service.signal(DSC_SERVICE_NAME)    
    # Use below command for test:
    # dbus-monitor --system "type='signal', interface='com.linuxdeepin.softwarecenter'" 
    def update_signal(self, message):
        # The signal is emitted when this method exits
        # You can have code here if you wish
        print message
        
if __name__ == "__main__":
    # dpkg will failed if not set TERM and PATH environment variable.  
    os.environ["TERM"] = "xterm"
    os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/X11R6/bin"
        
    # Init environment variable.
    os.environ["DEBIAN_FRONTEND"] = "noninteractive" # don't popup debconf dialog
    
    # Init.
    dbus.mainloop.glib.DBusGMainLoop(set_as_default = True)
    gobject.threads_init()
    
    # Init mainloop.
    mainloop = gobject.MainLoop()
    signal.signal(signal.SIGINT, lambda : mainloop.quit()) # capture "Ctrl + c" signal
    
    # Auth with root permission.
    if not auth_with_policykit("com.linuxdeepin.softwarecenter.action",
                               "org.freedesktop.PolicyKit1", 
                               "/org/freedesktop/PolicyKit1/Authority", 
                               "org.freedesktop.PolicyKit1.Authority",
                               ):
        log("Auth failed")
        
    # Remove log file.
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)
        
    # Remove lock file if it exist.
    if os.path.exists("/var/lib/apt/lists/lock"):
        os.remove("/var/lib/apt/lists/lock")
        
    # Init dbus.
    system_bus = dbus.SystemBus()
    bus_name = dbus.service.BusName(DSC_SERVICE_NAME, system_bus)
    
    # Init cache.
    pkg_cache = AptCache()
    
    # Init package manager.
    PackageManager(system_bus, mainloop, pkg_cache)
    
    # Run.
    mainloop.run()
