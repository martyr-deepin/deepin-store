#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 Deepin, Inc.
#               2011 Wang Yong
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

import apt.debfile as debfile
import os
from dtk.ui.thread_pool import MissionThread, MissionThreadPool
import apt.progress.base as apb
from events import global_event
from time import sleep
import traceback
from utils import log
from constant import ACTION_INSTALL, ACTION_UPGRADE, ACTION_UNINSTALL
import time

class AptProcess(apb.InstallProgress):
    '''Install progress.'''

    def __init__(self, pkg_name, action_type):
        '''Init for install progress.'''
        # Init.
        apb.InstallProgress.__init__(self)
        self.pkg_name = pkg_name
        self.action_type = action_type

    def conffile(self, current, new):
        global_event.emit("action-conffile", (current, new))

        log("conffile: %s %s" % (current, new))
        
    def error(self, pkg_name, errorstr):
        global_event.emit("action-error", (self.pkg_name, errorstr))
        
        log("error: %s" % errorstr)

    def start_update(self):
        '''Start update.'''
        log("start action...")
        
    def status_change(self, pkg, percent, status):
        '''Progress status change.'''
        global_event.emit("action-update", (self.pkg_name, self.action_type, int(percent), status))
        log((self.pkg_name, self.action_type, int(percent), status))

class AptActionThread(MissionThread):
    '''
    class docs
    '''
	
    def __init__(self, pkg_cache, pkg_name, action_type, simulate=False, deb_file=""):
        '''
        init docs
        '''
        MissionThread.__init__(self)
        
        self.pkg_cache = pkg_cache
        self.pkg_name = pkg_name
        self.action_type = action_type
        self.simulate = simulate
        self.deb_file = deb_file
        
    def start_mission(self):
        log("start thread")
        #if os.path.exists(self.deb_file):
            #log("install: %s") % self.deb_file
            #deb_package = debfile.DebPackage(self.deb_file, self.pkg_cache)
            #deb_package.install(AptProcess(self.pkg_name, self.action_type))
        
        start = time.time()
        self.pkg_cache.open(None)
        log("Reopen Cache Time: %s" % (time.time()-start,))

        if self.action_type == ACTION_INSTALL:
            self.pkg_cache[self.pkg_name].mark_install()
        elif self.action_type == ACTION_UPGRADE:
            self.pkg_cache[self.pkg_name].mark_upgrade()
        elif self.action_type == ACTION_UNINSTALL:
            self.pkg_cache[self.pkg_name].mark_delete()
            
        for pkg in self.pkg_cache:
            if pkg.is_auto_removable:
                pkg.mark_delete()

        pkg_info_list = map(lambda pkg: (pkg.name, pkg.marked_delete, pkg.marked_install, pkg.marked_upgrade), 
                            sorted(self.pkg_cache.get_changes(), key=lambda p: p.name))
        
        if len(pkg_info_list) > 0:
            global_event.emit("action-start", (self.pkg_name, self.action_type))
            if self.simulate:
                global_event.emit("action-update", (self.pkg_name, self.action_type, 10, ""))
                sleep(2)
        
                global_event.emit("action-update", (self.pkg_name, self.action_type, 30, ""))
                sleep(2)
                
                global_event.emit("action-update", (self.pkg_name, self.action_type, 50, ""))
                sleep(2)
                
                global_event.emit("action-update", (self.pkg_name, self.action_type, 70, ""))
                sleep(2)
        
                global_event.emit("action-update", (self.pkg_name, self.action_type, 100, ""))
                
                global_event.emit("action-finish", (self.pkg_name, self.action_type, pkg_info_list))
            else:
                # FIXME: it's very strange, there is no return code with commit method
                try:
                    self.pkg_cache.commit(None, AptProcess(self.pkg_name, self.action_type))
                    log("success")
                    global_event.emit("action-finish", (self.pkg_name, self.action_type, pkg_info_list))
                except Exception, e:
                    log("Commit Failed: %s" % e)
                    log(str(traceback.format_exc()))
                    global_event.emit("action-failed", (self.pkg_name, self.action_type, pkg_info_list))
        else:
            log("nothing to change")
        log("end thread")
        
    def get_mission_result(self):
        '''Get misssion retsult.'''
        return (self.pkg_name, self.action_type)
    
class AptActionPool(MissionThreadPool):
    '''
    class docs
    '''
	
    def __init__(self, pkg_cache):
        '''
        init docs
        '''
        MissionThreadPool.__init__(
            self, 
            1,
            1,
            self.clean_action,
            )
        
        self.pkg_cache = pkg_cache
        self.install_action_dict = {}
        self.uninstall_action_dict = {}
        self.upgrade_action_dict = {}
        
        global_event.register_event("action-start", self.start_action)
        global_event.register_event("action-update", self.update_action)
        
    def start_action(self, (pkg_name, action_type)):
        if action_type == ACTION_INSTALL:
            if self.install_action_dict.has_key(pkg_name):
                self.install_action_dict[pkg_name]["status"] = "start"
        elif action_type == ACTION_UNINSTALL:
            if self.uninstall_action_dict.has_key(pkg_name):
                self.uninstall_action_dict[pkg_name]["status"] = "start"
        elif action_type == ACTION_UPGRADE:
            if self.upgrade_action_dict.has_key(pkg_name):
                self.upgrade_action_dict[pkg_name]["status"] = "start"

    def update_action(self, (pkg_name, action_type, percent, status)):
        if action_type == ACTION_INSTALL:
            if self.install_action_dict.has_key(pkg_name):
                self.install_action_dict[pkg_name]["status"] = "update"
        elif action_type == ACTION_UNINSTALL:
            if self.uninstall_action_dict.has_key(pkg_name):
                self.uninstall_action_dict[pkg_name]["status"] = "update"
        elif action_type == ACTION_UPGRADE:
            if self.upgrade_action_dict.has_key(pkg_name):
                self.upgrade_action_dict[pkg_name]["status"] = "update"
        
    def clean_action(self, mission_result_list):
        for (pkg_name, action_type) in mission_result_list:
            if action_type == ACTION_INSTALL:
                if self.install_action_dict.has_key(pkg_name):
                    self.install_action_dict.pop(pkg_name)
            elif action_type == ACTION_UNINSTALL:
                if self.uninstall_action_dict.has_key(pkg_name):
                    self.uninstall_action_dict.pop(pkg_name)
            elif action_type == ACTION_UPGRADE:
                if self.upgrade_action_dict.has_key(pkg_name):
                    self.upgrade_action_dict.pop(pkg_name)
        
    def add_install_action(self, pkg_names, simulate=False, deb_file=""):
        missions = []
        for pkg_name in pkg_names:
            thread = AptActionThread(self.pkg_cache, pkg_name, ACTION_INSTALL, simulate, deb_file)
            self.install_action_dict[pkg_name] = {
                "thread" : thread,
                "status" : "wait"}
            missions.append(thread)
            
        self.add_missions(missions)
        
    def add_uninstall_action(self, pkg_names, simulate=False):
        missions = []
        for pkg_name in pkg_names:
            thread = AptActionThread(self.pkg_cache, pkg_name, ACTION_UNINSTALL, simulate)
            self.uninstall_action_dict[pkg_name] = {
                "thread" : thread,
                "status" : "wait"}
            missions.append(thread)
            
        self.add_missions(missions)
        
    def add_upgrade_action(self, pkg_names, simulate=False):
        missions = []
        for pkg_name in pkg_names:
            thread = AptActionThread(self.pkg_cache, pkg_name, ACTION_UPGRADE, simulate)
            self.upgrade_action_dict[pkg_name] = {
                "thread" : thread,
                "status" : "wait"}
            missions.append(thread)
            
        self.add_missions(missions)

    def remove_wait_missions(self, pkg_infos):
        remove_missions = []
        for pkg_info in pkg_infos:
            (pkg_name, action_type) = eval(pkg_info)
            self.clean_action([(pkg_name, action_type)])
            
            for wait_mission in self.wait_mission_list:
                if wait_mission.pkg_name == pkg_name and wait_mission.action_type == action_type:
                    remove_missions.append(wait_mission)
                    
        self.remove_from_wait_missions(remove_missions)
