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

import apt_pkg
import apt.progress.base as apb
from dtk.ui.thread_pool import MissionThread, MissionThreadPool
import time
import gobject

from events import global_event
import traceback
from utils import log
from constant import ACTION_INSTALL, ACTION_UPGRADE, ACTION_UNINSTALL

from update_list import UpdateList

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

class CommitProcess(apb.InstallProgress):
    def __init__(self, pkg_names, action_type, upgrade_id):
        '''Init for install progress.'''
        # Init.
        apb.InstallProgress.__init__(self)
        self.pkg_names = pkg_names
        self.action_type = action_type
        self.upgrade_id = upgrade_id

    def conffile(self, current, new):
        #global_event.emit("action-conffile", (current, new))
        log("conffile: %s %s" % (current, new))
        
    def error(self, pkg_name, errorstr):
        #global_event.emit("action-error", (self.pkg_names, errorstr))
        log("error: %s" % errorstr)

    def start_update(self):
        '''Start update.'''
        log("start action...")
        
    def status_change(self, pkg, percent, status):
        '''Progress status change.'''
        global_event.emit("action-update", (self.upgrade_id, self.action_type, int(percent), status))
        log((self.pkg_names, self.action_type, int(percent), status))

class GInstallProgress(gobject.GObject, apb.InstallProgress):
    """Installation progress with global_event signals.

    Signals:

        * action-update()
        * action-start()
        * action-finish()
        * action-timeout()
        * action-error()
        * action-conffile()

    """
    # Seconds until a maintainer script will be regarded as hanging
    INSTALL_TIMEOUT = 5 * 60

    def __init__(self, pkg_names, action_type, upgrade_id):
        apb.InstallProgress.__init__(self)
        gobject.GObject.__init__(self)

        self.finished = False
        self.time_last_update = time.time()

        self.pkg_names = pkg_names
        self.action_type = action_type
        self.upgrade_id = upgrade_id

    def error(self, pkg, errormsg):
        """Called when an error happens.

        Emits: action-error()
        """
        global_event.emit("action-error", (pkg, errormsg))
        global_event.emit("action-failed", (pkg, ACTION_UPGRADE, [], str(errormsg)))
        log("error: %s" % errormsg)

    def conffile(self, current, new):
        """Called during conffile.

        Emits: action-conffile()
        """
        #global_event.emit("action-conffile", current, new)
        print "conffile >>", current, new

    def start_update(self):
        """Called when the update starts.

        Emits: action-start()
        """
        #global_event.emit("action-start")

    def run(self, obj):
        """Run."""
        self.finished = False
        return apb.InstallProgress.run(self, obj)

    def finish_update(self):
        """Called when the update finished.

        Emits: action-finish()
        """
        #global_event.emit("action-finish")

    def processing(self, pkg, stage):
        """Called when entering a new stage in dpkg."""
        # We have no percentage or alike, send -1 to let the bar pulse.
        #global_event.emit("action-update", pkg, ("Installing stage: %s...") % stage, -1)
        print "processing >>", pkg, stage

    def status_change(self, pkg, percent, status):
        """Called when the status changed.

        Emits: action-update(status, percent)
        """
        self.time_last_update = time.time()
        global_event.emit("action-update", (self.upgrade_id, self.action_type, int(percent), status))

    def update_interface(self):
        """Called periodically to update the interface.

        Emits: action-timeout() [When a timeout happens]
        """
        #print "update_interface >>", self.time_last_update
        apb.InstallProgress.update_interface(self)
        if self.time_last_update + self.INSTALL_TIMEOUT < time.time():
            global_event.emit("action-timeout")

class AptActionThread(MissionThread):
    '''
    class docs
    '''
	
    def __init__(self, pkg_cache, pkg_name, action_type, simulate=False, deb_file="", purge_flag=False):
        '''
        init docs
        '''
        MissionThread.__init__(self)
        
        self.pkg_cache = pkg_cache
        self.pkg_name = pkg_name
        self.action_type = action_type
        self.simulate = simulate
        self.deb_file = deb_file
        self.purge_flag = purge_flag
        
    def start_mission(self):
        log("start thread")
        start = time.time()
        self.pkg_cache.open(apb.OpProgress())
        log("Reopen Cache Time: %s" % (time.time()-start,))

        if self.action_type == ACTION_INSTALL:
            self.pkg_cache[self.pkg_name].mark_install()
        elif self.action_type == ACTION_UPGRADE:
            self.pkg_cache[self.pkg_name].mark_upgrade()
        elif self.action_type == ACTION_UNINSTALL:
            self.pkg_cache[self.pkg_name].mark_delete(purge=self.purge_flag)
            
        '''
        for pkg in self.pkg_cache:
            if pkg.is_auto_removable:
                pkg.mark_delete()
        '''

        pkg_info_list = map(lambda pkg: (pkg.name, pkg.marked_delete, pkg.marked_install, pkg.marked_upgrade), 
                            self.pkg_cache.get_changes())
        
        if len(pkg_info_list) > 0:
            global_event.emit("action-start", (self.pkg_name, self.action_type))
            if self.simulate:
                global_event.emit("action-update", (self.pkg_name, self.action_type, 10, ""))
                time.sleep(2)
                global_event.emit("action-update", (self.pkg_name, self.action_type, 30, ""))
                time.sleep(2)
                global_event.emit("action-update", (self.pkg_name, self.action_type, 50, ""))
                time.sleep(2)
                global_event.emit("action-update", (self.pkg_name, self.action_type, 70, ""))
                time.sleep(2)
                global_event.emit("action-update", (self.pkg_name, self.action_type, 100, ""))
                global_event.emit("action-finish", (self.pkg_name, self.action_type, pkg_info_list))
            else:
                try:
                    self.pkg_cache.commit(None, AptProcess(self.pkg_name, self.action_type))
                    log("success")
                    global_event.emit("action-finish", (self.pkg_name, self.action_type, pkg_info_list))
                except Exception, e:
                    log("Commit Failed: %s" % e)
                    log(str(traceback.format_exc()))
                    global_event.emit("action-failed", (self.pkg_name, self.action_type, pkg_info_list, str(e)))
        else:
            log("nothing to change")
        log("end thread")
        
    def get_mission_result(self):
        '''Get misssion retsult.'''
        return [(self.pkg_name, self.action_type)]

class MultiAptActionThread(MissionThread):
    def __init__(self, pkg_cache, pkg_names, action_type, upgrade_id, purge_flag=False):
        '''
        init docs
        '''
        MissionThread.__init__(self)
        
        self.pkg_cache = pkg_cache
        self.pkg_names = pkg_names
        self.action_type = action_type
        self.purge_flag = purge_flag
        self.upgrade_id = upgrade_id
        
    def start_mission(self):
        log("start thread")
        start = time.time()
        self.pkg_cache.open(apb.OpProgress())
        log("Reopen Cache Time: %s" % (time.time()-start,))

        for pkg_name in self.pkg_names:
            if self.action_type == ACTION_INSTALL:
                self.pkg_cache[self.pkg_name].mark_install()
            elif self.action_type == ACTION_UPGRADE:
                self.pkg_cache[pkg_name].mark_upgrade()
            elif self.action_type == ACTION_UNINSTALL:
                self.pkg_cache[self.pkg_name].mark_delete(purge=self.purge_flag)
            
        pkg_info_list = map(lambda pkg: (pkg.name, pkg.marked_delete, pkg.marked_install, pkg.marked_upgrade), 
                            self.pkg_cache.get_changes())
        
        if len(pkg_info_list) > 0:
            for pkg_info in pkg_info_list:
                global_event.emit("action-start", (pkg_info[0], self.action_type))

            try:
                self.pkg_cache.commit(None, GInstallProgress(self.pkg_names, self.action_type, self.upgrade_id))
                log("success")
                global_event.emit('action-finish', (self.upgrade_id, self.action_type, pkg_info_list))
            except Exception, e:
                log("Commit Failed: %s" % e)
                log(str(traceback.format_exc()))
                global_event.emit("action-failed", (self.upgrade_id, self.action_type, pkg_info_list, str(e)))
        else:
            log("nothing to change")
        log("end thread")
        
    def get_mission_result(self):
        '''Get misssion retsult.'''
        return [(pkg_name, self.action_type) for pkg_name in self.pkg_names]

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
        for result in mission_result_list:
            if result:
                for r in result:
                    print r
                    pkg_name, action_type = r
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
        
    def add_uninstall_action(self, pkg_name, simulate=False, purge=False):
        missions = []
        thread = AptActionThread(self.pkg_cache, pkg_name, ACTION_UNINSTALL, simulate, purge)
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

    def add_multi_upgrade_mission(self, pkg_names, upgrade_id):
        missions = []

        thread = MultiAptActionThread(self.pkg_cache, pkg_names, ACTION_UPGRADE, upgrade_id=upgrade_id)
        for pkg_name in pkg_names:
            self.upgrade_action_dict[pkg_name] = {
                "thread" : thread,
                "status" : "wait"}
        missions.append(thread)
            
        self.add_missions(missions)

    def add_update_list_mission(self):
        missions = []
        thread = UpdateList(self.pkg_cache)
        #self.uninstall_action_dict[pkg_name] = {
            #"thread" : thread,
            #"status" : "wait"}
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
