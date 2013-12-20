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
from deepin_utils.file import get_parent_dir, remove_file
sys.path.append(os.path.join(get_parent_dir(__file__, 3), "download_manager", "deepin_storm"))

import signal
import uuid
import gobject
import dbus
import dbus.service
import dbus.mainloop.glib
import os
import json
import threading as td
from Queue import Queue
import apt_pkg
import apt.progress.base as apb
import aptsources.distro

from deepin_utils.ipc import auth_with_policykit
from deepin_utils.file import read_file, write_file

from download_manager import DownloadManager
from parse_pkg import (
        get_pkg_download_info, 
        get_pkg_dependence_file_path, 
        get_pkg_own_size,
        get_cache_archive_dir,
        )
import parse_pkg
from constant import (
        DSC_SERVICE_NAME, 
        DSC_SERVICE_PATH, 
        ACTION_INSTALL, 
        ACTION_UPGRADE, 
        ACTION_UNINSTALL, 
        DOWNLOAD_STATUS_NOTNEED, 
        DOWNLOAD_STATUS_ERROR,
        PKG_SIZE_OWN,
        PKG_SIZE_DOWNLOAD,
        PKG_SIZE_ERROR,
        )
from apt_cache import AptCache
from action import AptActionPool
from events import global_event
from utils import log
import utils
import db_build

DATA_DIR = os.path.join(get_parent_dir(__file__, 3), "data")
SOURCE_LIST = '/etc/apt/sources.list'

ubuntu_source_content_template = [
"deb %s %s main restricted universe multiverse",
"deb %s %s-security main restricted universe multiverse",
"deb %s %s-updates main restricted universe multiverse",
"# deb %s %s-proposed main restricted universe multiverse",
"# deb %s %s-backports main restricted universe multiverse",
"deb-src %s %s main restricted universe multiverse",
"deb-src %s %s-security main restricted universe multiverse",
"deb-src %s %s-updates main restricted universe multiverse",
"# deb-src %s %s-proposed main restricted universe multiverse",
"# deb-src %s %s-backports main restricted universe multiverse",
]

deepin_source_content_template = [
"deb %s %s main universe non-free",
"deb-src %s %s main universe non-free",
"#deb %s %s-updates main universe non-free",
"#deb-src %s %s-updates main universe non-free",
]

def get_source_list_contents(ubuntu_repo_url, deepin_repo_url):
    head = '# This file was created by deepin software center, please do not modify manually!'
    codename = aptsources.distro.get_distro().codename
    
    s = []
    s.append(head)
    s.append("")

    for line in ubuntu_source_content_template:
        try:
            line = line % (ubuntu_repo_url, codename)
        except:
            pass
        s.append(line)
    s.append("")

    for line in deepin_source_content_template:
        try:
            line = line % (deepin_repo_url, codename)
        except:
            pass
        s.append(line)
                    
    return "\n".join(s)

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
                    utils.set_running_lock(False)
                else:
                    print "Pass"
                    self.loop()

class ThreadMethod(td.Thread):
    '''
    func: a method name
    args: arguments tuple
    '''
    def __init__(self, func, args, daemon=False):
        td.Thread.__init__(self)
        self.func = func
        self.args = args
        self.setDaemon(daemon)
        self.download_dir = "/var/cache/apt/archives"

    def run(self):
        self.func(*self.args)

class PackageManager(dbus.service.Object):
    '''
    docs
    '''

    def __init__(self, system_bus, mainloop):
        log("init dbus")
        
        # Init dbus service.
        dbus.service.Object.__init__(self, system_bus, DSC_SERVICE_PATH)
        # Init.
        self.mainloop = mainloop
        self.pkg_cache = AptCache()
        self.exit_flag = False
        self.simulate = False
        self.all_upgrade_pkg_names = []
        
        self.apt_action_pool = AptActionPool(self.pkg_cache)
        self.apt_action_pool.start()
        
        global_event.register_event('parse-download-error', self.send_parse_download_error)

        global_event.register_event("action-start", self.action_start)
        global_event.register_event("action-update", self.action_update)
        global_event.register_event("action-finish", self.action_finish)
        global_event.register_event("action-failed", self.action_failed)
        
        
        global_event.register_event("download-start", self.download_start)
        global_event.register_event("download-update", self.download_update)
        global_event.register_event("download-finish", self.download_finish)
        global_event.register_event("download-stop", self.download_stop)
        global_event.register_event("download-error", self.download_failed)
        
        self.in_update_list = False
        global_event.register_event("update-list-start", self.update_list_start)
        global_event.register_event("update-list-finish", self.update_list_finish)
        global_event.register_event("update-list-failed", self.update_list_failed)
        global_event.register_event("update-list-update", self.update_list_update)

        self.packages_status = {}
        
        self.exit_manager = ExitManager(
            self.mainloop,
            self.is_update_list_running,
            self.is_download_action_running,
            self.is_apt_action_running,
            self.have_exit_request)
        self.exit_manager.start()
        
        log("init finish")
        self.set_download_dir('/var/cache/apt/archives')
        self.init_download_manager(5)

    def download_start(self, pkg_name, action_type):
        utils.set_running_lock(True)
        self.update_signal([("download-start", (pkg_name, action_type))])

    def download_update(self, *argv):
        self.update_signal([("download-update", argv)])

    def download_stop(self, pkg_name, action_type):
        self.update_signal([("download-stop", (pkg_name, action_type))])
        
        self.exit_manager.check()    
        
    def download_failed(self, pkg_name, action_type, e):
        utils.set_running_lock(False)
        self.update_signal([("download-failed", (pkg_name, action_type, e))])
        
        self.exit_manager.check()    
           
    def download_finish(self, action_id, action_type, all_pkg_names):
        utils.set_running_lock(False)
        self.update_signal([("download-finish", (action_id, action_type))])
        
        if action_type == ACTION_INSTALL:
            self.apt_action_pool.add_install_action(all_pkg_names)
        elif action_type == ACTION_UPGRADE:
            self.start_upgrade(all_pkg_names, action_id)
            
        self.exit_manager.check()

    def action_start(self, signal_content):
        utils.set_running_lock(True)
        self.update_signal([("action-start", signal_content)])
        
    def action_update(self, signal_content):
        self.update_signal([("action-update", signal_content)])
        
    def action_finish(self, signal_content):
        utils.set_running_lock(False)
        pkg_name, action_type, pkg_info_list = signal_content
        if action_type == ACTION_INSTALL:
            for pkg_info in pkg_info_list:
                self.pkg_cache.set_pkg_status(pkg_name, self.pkg_cache.PKG_STATUS_INSTALLED)
        elif action_type == ACTION_UPGRADE:
            for pkg_info in pkg_info_list:
                self.pkg_cache.set_pkg_status(pkg_name, self.pkg_cache.PKG_STATUS_UPGRADED)
        elif action_type == ACTION_UNINSTALL:
            for pkg_info in pkg_info_list:
                self.pkg_cache.set_pkg_status(pkg_name, self.pkg_cache.PKG_STATUS_UNINSTALLED)

        self.update_signal([("action-finish", signal_content)])
        self.exit_manager.check()

    def action_failed(self, signal_content):
        utils.set_running_lock(False)
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

    def update_list_finish(self):
        self.update_signal([("update-list-merge", "")])
        self.pkg_cache.open(apb.OpProgress())
        db_build.BuildSoftwareDB(self.pkg_cache)

        self.update_signal([("update-list-finish", "")])
        self.in_update_list = False
        self.exit_manager.check()

    def update_list_failed(self):
        self.in_update_list = False
        self.update_signal([("update-list-failed", "")])
        
        self.exit_manager.check()
        
    def update_list_update(self, percent, status_message, speed_str):
        self.update_signal([("update-list-update", (percent, status_message, speed_str))])

    def handle_dbus_reply(self, *reply):
        log("%s (reply): %s" % (self.module_dbus_name, str(reply)))        
        
    def handle_dbus_error(self, *error):
        log("%s (error): %s" % (self.module_dbus_name, str(error)))

    def send_parse_download_error(self, pkg_name, action_type):
        self.update_signal([("parse-download-error", (pkg_name, action_type))])

    def get_unique_id(self):
        return str(uuid.uuid4())

    def get_real_pkg_name(self, pkg_name):
        if pkg_name in self.pkg_cache:
            return pkg_name
        elif (pkg_name + ":i386") in self.pkg_cache:
            return pkg_name + ":i386"
        else:
            return None

    def add_upgrade_download_with_new_policy(self, pkg_names, action_type):
        action_id = '%s_%s' % (self.get_unique_id(), action_type)
        self.update_signal([("ready-download-start", (action_id, action_type))])

        real_pkg_dict, not_in_cache = parse_pkg.get_real_pkg_dict(self.pkg_cache, pkg_names)
        if not_in_cache:
            self.update_signal([("pkgs-not-in-cache", (json.dumps(not_in_cache), action_type))])
        else:
            (all_change_pkgs, mark_failed_pkg_dict, marked_delete_sys_pkgs
                    ) = parse_pkg.get_changes_pkgs(self.pkg_cache, real_pkg_dict)

            if mark_failed_pkg_dict:
                self.update_signal([("pkgs-mark-failed", (json.dumps(mark_failed_pkg_dict.keys()), action_type))])

            elif marked_delete_sys_pkgs:
                self.update_signal([("marked-delete-system-pkgs", (json.dumps(marked_delete_sys_pkgs), action_type))])
            else:
                self.update_signal([("ready-download-finish", (action_id, action_type))])
                download_pkg_infos = parse_pkg.check_pkg_download_info(all_change_pkgs)
                if download_pkg_infos[0] == DOWNLOAD_STATUS_ERROR:
                    self.update_signal([("pkgs-parse-download-error", (str(download_pkg_infos[1]), action_type))])
                elif download_pkg_infos[0] == DOWNLOAD_STATUS_NOTNEED:
                    self.start_upgrade(pkg_names, action_id)
                else:
                    (names, download_urls, download_hash_infos, pkg_sizes) = download_pkg_infos
                    self.all_upgrade_pkg_names = all_change_pkgs
                    self.download_manager.add_download(
                                            action_id,
                                            action_type,
                                            download_urls,
                                            download_hash_infos,
                                            pkg_sizes,
                                            all_pkg_names=pkg_names,
                                            all_change_pkgs=all_change_pkgs,
                                            file_save_dir=self.download_dir,
                                            )
        
    def add_download(self, pkg_name, action_type, simulate=False):
        pkg_infos = get_pkg_download_info(self.pkg_cache, pkg_name)
        self.update_signal([("ready-download-finish", (pkg_name, action_type))])
        if pkg_infos[0] == DOWNLOAD_STATUS_NOTNEED:
            self.download_finish(pkg_name, action_type, [pkg_name,])
            print "Don't need download"
        elif pkg_infos[0] == DOWNLOAD_STATUS_ERROR:
            self.update_signal([("parse-download-error", (pkg_name, action_type))])
            print "Download error"
        else:
            (names, download_urls, download_hash_infos, pkg_sizes) = pkg_infos
            
            self.download_manager.add_download(
                                        pkg_name, 
                                        action_type, 
                                        download_urls, 
                                        download_hash_infos, 
                                        file_sizes=pkg_sizes, 
                                        all_pkg_names=[pkg_name,],
                                        file_save_dir=self.download_dir)

    def start_upgrade(self, pkg_names, action_id):
        self.apt_action_pool.add_multi_upgrade_mission(pkg_names, action_id)
        
    def del_source_list_d(self):
        white_list_path = os.path.join(get_parent_dir(__file__), 'white_list.txt')
        if os.path.exists(white_list_path):
            with open(white_list_path) as fp:
                for line in fp:
                    line = line.strip()
                    if os.path.exists(line):
                        os.remove(line)

    @dbus.service.method(DSC_SERVICE_NAME, in_signature='', out_signature='as')
    def read_no_notify_config(self, no_notify_config_path):
        if os.path.exists(no_notify_config_path):
           no_notify_config_str = read_file(no_notify_config_path)
           try:
               no_notify_config = eval(no_notify_config_str)
               
               if type(no_notify_config).__name__ != "list":
                   no_notify_config = []
           except Exception:
               no_notify_config = []
               
           return no_notify_config
        else:
            return []

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")
    def add_no_notify_pkg(self, info):
        pkg_name, path = info
        no_notify_config = self.read_no_notify_config(path)
        
        if pkg_name not in no_notify_config:
            pkg_name = str(pkg_name)
            no_notify_config.append(pkg_name)
            write_file(path, str(no_notify_config))

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")
    def remove_no_notify_pkg(self, info):
        pkg_name, path = info
        pkg_name = str(pkg_name)
        path = str(path)
        no_notify_config = self.read_no_notify_config(path)
        
        if pkg_name in no_notify_config:
            write_file(path, str(filter(lambda config_pkg_name: config_pkg_name != pkg_name, no_notify_config)))

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="i", out_signature="")
    def init_download_manager(self, number):
        self.download_manager = DownloadManager(global_event, number)

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="s", out_signature="")
    def set_download_dir(self, local_dir):
        apt_pkg.config.set("Dir::Cache::Archives", local_dir)
        self.download_dir = local_dir
    
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="s", out_signature="ai")
    def get_download_size(self, pkg_name):
        total_size = 0
        pkg_infos = get_pkg_download_info(self.pkg_cache, pkg_name)
        if pkg_infos[0] == DOWNLOAD_STATUS_NOTNEED:
            total_size = get_pkg_own_size(self.pkg_cache, pkg_name)
            size_flag = PKG_SIZE_OWN
        elif pkg_infos[0] == DOWNLOAD_STATUS_ERROR:
            total_size = -1
            size_flag = PKG_SIZE_ERROR
        else:
            (names, download_urls, download_hash_infos, pkg_sizes) = pkg_infos
            for size in pkg_sizes:
                total_size += size
            size_flag = PKG_SIZE_DOWNLOAD
        return [size_flag, total_size]

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="as")
    def get_upgrade_download_size(self, pkg_names):
        real_pkg_dict, not_in_cache = parse_pkg.get_real_pkg_dict(self.pkg_cache, pkg_names)
        if not_in_cache:
            return ["0", "error"]
        else:
            (all_change_pkgs, mark_failed_pkg_dict, marked_delete_sys_pkgs
                    ) = parse_pkg.get_changes_pkgs(self.pkg_cache, real_pkg_dict)

            download_pkg_infos = parse_pkg.check_pkg_download_info(all_change_pkgs)
            change_pkg_names = [pkg.name for pkg in all_change_pkgs]
            if download_pkg_infos[0] == DOWNLOAD_STATUS_ERROR:
                return ["0", "error"]
            elif download_pkg_infos[0] == DOWNLOAD_STATUS_NOTNEED:
                return ["0", json.dumps(change_pkg_names)]
            else:
                (names, download_urls, download_hash_infos, pkg_sizes) = download_pkg_infos
                total_size = 0
                for size in pkg_sizes:
                    total_size += size
                return [str(total_size), json.dumps(change_pkg_names)]

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="", out_signature="ai")
    def clean_download_cache(self):
        '''Clean download cache.'''
        # get action packages.
        remain_pkgs = []
        for (pkg_name, info_dict) in self.download_manager.fetch_files_dict.items():
            remain_pkgs.append(pkg_name)

        for (pkg_name, info_dict) in self.apt_action_pool.install_action_dict.items():
            remain_pkgs.append(pkg_name)
        for (pkg_name, info_dict) in self.apt_action_pool.upgrade_action_dict.items():
            remain_pkgs.append(pkg_name)
        
        # Get depend packages.
        remain_pkgs_paths = []
        for pkg_name in remain_pkgs:
            result = get_pkg_dependence_file_path(self.pkg_cache, pkg_name)
            if not result:
                remain_pkgs_paths += result

        # Init clean size.
        packageNum = 0
        cleanSize = 0
                
        # Delete cache directory.
        cache_archive_dir = get_cache_archive_dir()
        if os.path.exists(cache_archive_dir):
            for root, folder, files in os.walk(cache_archive_dir):
                for file_name in files:
                    path = os.path.join(root, file_name)
                    if path.endswith(".deb") and (path not in remain_pkgs_paths):
                        packageNum += 1
                        cleanSize += os.path.getsize(path)
                        remove_file(path)

        return [packageNum, cleanSize]
        
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
        self.update_signal([("frontend-quit", "")])

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")
    def change_source_list(self, repo_urls):
        ubuntu_repo_url, deepin_repo_url = repo_urls
        new_source_list_content = get_source_list_contents(ubuntu_repo_url, deepin_repo_url)
        os.system('cp %s %s.save' % (SOURCE_LIST, SOURCE_LIST))
        with open(SOURCE_LIST, 'w') as fp:
            fp.write(new_source_list_content)
        
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="", out_signature="as")    
    def request_upgrade_pkgs(self):
        if self.in_update_list:
            return []
        else:
            cache_upgrade_pkgs = self.pkg_cache.get_upgrade_pkgs()
            return cache_upgrade_pkgs
    
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="", out_signature="as")    
    def request_uninstall_pkgs(self):
        return self.pkg_cache.get_uninstall_pkgs()

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="as")    
    def request_pkgs_install_version(self, pkg_names):
        pkg_versions = []
        for pkg_name in pkg_names:
            try:
                version = self.pkg_cache[pkg_name].versions[0].version
                pkg_versions.append(version)
            except:
                try:
                    version = self.pkg_cache[pkg_name+":i386"].versions[0].version
                    pkg_versions.append(version)
                except:
                    self.update_signal([("pkg-not-in-cache", pkg_name)])
        return pkg_versions

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="s", out_signature="as")    
    def is_pkg_in_cache(self, pkg_name):
        result = []
        try:
            self.pkg_cache[pkg_name]
            result.append(pkg_name)
        except:
            try:
                pkg_name += ":i386"
                self.pkg_cache[pkg_name]
                result.append(pkg_name)
            except:
                pass
        return result

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="as")    
    def request_pkgs_uninstall_version(self, pkg_names):
        return self.pkg_cache.get_pkgs_uninstall_version(pkg_names)

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")    
    def install_pkg(self, pkg_names):
        for pkg_name in pkg_names:
            real_pkg_name = self.get_real_pkg_name(pkg_name)
            if real_pkg_name:
                ThreadMethod(self.add_download, (real_pkg_name, ACTION_INSTALL, self.simulate)).start()
            else:
                self.update_signal([("pkg-not-in-cache", pkg_name)])
    
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="sb", out_signature="")    
    def uninstall_pkg(self, pkg_name, purge):
        real_pkg_name = self.get_real_pkg_name(pkg_name)
        if real_pkg_name:
            self.apt_action_pool.add_uninstall_action(real_pkg_name, self.simulate, purge)
        else:
            self.update_signal([("pkg-not-in-cache", pkg_name)])

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")    
    def upgrade_pkg(self, pkg_names):
        for pkg_name in pkg_names:
            real_pkg_name = self.get_real_pkg_name(pkg_name)
            if real_pkg_name:
                self.update_signal([("ready-download-start", (real_pkg_name, ACTION_UPGRADE))])
                ThreadMethod(self.add_download, (real_pkg_name, ACTION_UPGRADE, self.simulate)).start()
            else:
                self.update_signal([("pkg-not-in-cache", pkg_name)])

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")    
    def upgrade_pkgs_with_new_policy(self, pkg_names):
        ThreadMethod(self.add_upgrade_download_with_new_policy, (pkg_names, ACTION_UPGRADE)).start()

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="")    
    def stop_download_pkg(self, pkg_names):
        for pkg_name in pkg_names:
            self.download_manager.stop_download(pkg_name)

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="", out_signature="")
    def cancel_upgrade_download(self):
        if getattr(self, 'upgrade_id'):
            self.download_manager.stop_download(self.upgrade_id)
            
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
    
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="", out_signature="")
    def start_update_list(self):
        log("start update list...")
        self.del_source_list_d()
        self.pkg_cache.open(apb.OpProgress())
        self.apt_action_pool.add_update_list_mission()
        log("start update list done")
        
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="as", out_signature="ab")
    def request_pkgs_install_status(self, pkg_names):
        _status = []
        for pkg in pkg_names:
            _status.append(self.pkg_cache.is_pkg_installed(pkg))
        return _status
            
    @dbus.service.method(DSC_SERVICE_NAME, in_signature="(si)", out_signature="")
    def set_pkg_status(self, pkg_status):
        pkg_name, status = pkg_status
        self.pkg_cache.set_pkg_status(pkg_name, pkg_status)

    @dbus.service.method(DSC_SERVICE_NAME, in_signature="s", out_signature="i")
    def get_pkg_status(self, pkg_name):
        return self.pkg_cache.get_pkg_status(pkg_name)

    @dbus.service.signal(DSC_SERVICE_NAME)    
    # Use below command for test:
    # dbus-monitor --system "type='signal', interface='com.linuxdeepin.softwarecenter'" 
    def update_signal(self, message):
        # The signal is emitted when this method exits
        # You can have code here if you wish
        pass
        
if __name__ == "__main__":
    # dpkg will failed if not set TERM and PATH environment variable.  
    os.environ["TERM"] = "xterm"
    os.environ["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/X11R6/bin"
        
    # Init environment variable.
    os.environ["DEBIAN_FRONTEND"] = "noninteractive" # don't popup debconf dialog
    
    # Init.
    dbus.mainloop.glib.DBusGMainLoop(set_as_default = True)
    dbus.mainloop.glib.threads_init()
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
    #if os.path.exists(LOG_PATH):
        #os.remove(LOG_PATH)
        
    # Remove lock file if it exist.
    if os.path.exists("/var/lib/apt/lists/lock"):
        os.remove("/var/lib/apt/lists/lock")
        
    # Init dbus.
    system_bus = dbus.SystemBus()
    bus_name = dbus.service.BusName(DSC_SERVICE_NAME, system_bus)
    
    # Init package manager.
    PackageManager(system_bus, mainloop)
    
    # Run.
    mainloop.run()
