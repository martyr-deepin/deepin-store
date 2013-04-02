#!/usr/bin/env python
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

import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
import signal
import shutil
from deepin_utils.ipc import auth_with_policykit, is_dbus_name_exists
from deepin_utils.file import get_parent_dir, create_directory, write_file, eval_file, remove_file, remove_directory, remove_path
from deepin_utils.config import Config
from deepin_utils.hash import md5_file
from pystorm.tasks import TaskObject
from gevent.queue import Queue
import urllib2
import os
import tarfile
import uuid
import subprocess
from datetime import datetime

join_glib_loop()

DSC_UPDATER_NAME = "com.linuxdeepin.softwarecenterupdater"
DSC_UPDATER_PATH = "/com/linuxdeepin/softwarecenterupdater"
DATA_DIR = os.path.join(get_parent_dir(__file__, 3), "data")
UPDATE_DATA_URL = "b0.upaiyun.com"

UPDATE_DATE = "2013-03-27"  # origin data update date flag

LOG_PATH = "/tmp/dsc-updater.log"

def log(message):
    with open(LOG_PATH, "a") as file_handler:
        now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        file_handler.write("%s %s\n" % (now, message))

class UpdateDataService(dbus.service.Object):
    '''
    class docs
    '''
	
    def __init__(self, system_bus, mainloop):
        '''
        init docs
        '''
        # Init dbus service.
        dbus.service.Object.__init__(self, system_bus, DSC_UPDATER_PATH)
        self.mainloop = mainloop
        
        self.data_origin_dir = os.path.join(DATA_DIR, "origin")
        self.data_newest_dir = os.path.join(DATA_DIR, "newest")
        self.data_patch_dir = os.path.join(DATA_DIR, "patch")
        self.data_patch_config_filepath = os.path.join(DATA_DIR, "patch_status.ini")
        self.data_newest_id_path = os.path.join(DATA_DIR, "data_newest_id.ini")
        
    def get_unique_id(self):
        return str(uuid.uuid4())
        
    def run(self):
        # Init ini files.
            
        if not os.path.exists(self.data_newest_id_path):
            newest_data_id_config = Config(self.data_newest_id_path)
            newest_data_id_config.load()
            newest_data_id_config.set("newest", "data_id", "")
            newest_data_id_config.set("newest", "update_date", "")
            newest_data_id_config.write()
            
        # Extract data if current directory is not exists.
        newest_data_id_config = Config(self.data_newest_id_path)
        newest_data_id_config.load()

        try:
            update_date = newest_data_id_config.get("newest", "update_date")
        except Exception:
            update_date = ""

        if newest_data_id_config.get("newest", "data_id") == "" or update_date != UPDATE_DATE:
            self.clean()
            newest_data_id = self.get_unique_id()
            newest_data_dir = os.path.join(DATA_DIR, "update", newest_data_id)
            
            print "进行第一次数据解压..."
            log("进行第一次数据解压...")
            for data_file in os.listdir(self.data_origin_dir):
                with tarfile.open(os.path.join(self.data_origin_dir, data_file), "r:gz") as tar_file:
                    tar_file.extractall(newest_data_dir)
            print "进行第一次数据解压完成"
            log("进行第一次数据解压完成")
            
            newest_data_id_config.set("newest", "data_id", newest_data_id)
            newest_data_id_config.set("newest", "update_date", UPDATE_DATE)
            newest_data_id_config.write()
            
        if not os.path.exists(self.data_patch_config_filepath):
            self.patch_status_config = Config(self.data_patch_config_filepath)
            self.patch_status_config.load()
            self.patch_status_config.set("data_md5", "dsc-search-data", "")
            self.patch_status_config.set("data_md5", "dsc-category-data", "")
            self.patch_status_config.set("data_md5", "dsc-software-data", "")
            self.patch_status_config.set("data_md5", "dsc-home-data", "")
            self.patch_status_config.set("data_md5", "dsc-icon-data", "")
            self.patch_status_config.set("data_md5", "dsc-desktop-data", "")
            self.patch_status_config.write()
        else:
            self.patch_status_config = Config(self.data_patch_config_filepath)
            self.patch_status_config.load()
        
        # Download update data.
        self.have_update = []
        for data_file in os.listdir(self.data_origin_dir):
            self.download_data(data_file)
            
        if self.have_update:   
            # Apply update data.
            for space_name in os.listdir(self.data_patch_dir):
                if space_name in self.have_update:
                    self.apply_data(space_name)
                
            # Extra data.
            newest_data_id = self.get_unique_id()
            newest_data_dir = os.path.join(DATA_DIR, "update", newest_data_id)
            
            print "解压最新数据..."
            log("解压最新数据...")
            for data_file in os.listdir(self.data_newest_dir):
                space_name = data_file.split(".tar.gz")[0]
                with tarfile.open(os.path.join(self.data_newest_dir, data_file), "r:gz") as tar_file:
                    tar_file.extractall(newest_data_dir)
            print "解压最新数据完成"
            log("解压最新数据完成")
            
            newest_data_id_config.set("newest", "data_id", newest_data_id)
            newest_data_id_config.write()
            
        # TODO: Design how to remove unused data when UI is running
        DATA_CURRENT_ID_CONFIG_FILE = "/tmp/deepin-software-center/data_current_id.ini"
        if os.path.exists(DATA_CURRENT_ID_CONFIG_FILE):
            current_data_id_config = Config(DATA_CURRENT_ID_CONFIG_FILE)
            current_data_id_config.load()
            current_data_id = current_data_id_config.get("current", "data_id")
        else:
            current_data_id = None
        newest_data_id_config.load()
        data_file_list = ["newest",
                          "origin",
                          "patch",
                          "update",
                          "data_current_id.ini", 
                          "data_newest_id.ini",
                          "patch_status.ini",
                          "clean.py",
                          ]
        data_id_list = [current_data_id,
                        newest_data_id_config.get("newest", "data_id")]
        
        for data_file in os.listdir(DATA_DIR):
            if data_file not in data_file_list:
                remove_directory(os.path.join(DATA_DIR, data_file))
                print "remove file: %s" % data_file
                log("remove file: %s" % data_file)
            elif data_file == "update":
                for data_id in os.listdir(os.path.join(DATA_DIR, "update")):
                    if data_id not in data_id_list:
                        remove_directory(os.path.join(DATA_DIR, "update", data_id))
        
    def download_data(self, data_file, test=False):
        origin_data_md5 = md5_file(os.path.join(self.data_origin_dir, data_file))
        space_name = data_file.split(".tar.gz")[0]
        patch_dir = os.path.join(self.data_patch_dir, space_name)
        
        # Create download directory.
        create_directory(patch_dir)
                
        if space_name == "dsc-icon-data":
            if test:
                remote_url = "http://%s.%s/3.0_test" % (space_name, UPDATE_DATA_URL)
            else:
                remote_url = "http://%s.%s/3.0" % (space_name, UPDATE_DATA_URL)
        else:
            if test:
                remote_url = "http://%s.%s/3.0_test/zh_CN" % (space_name, UPDATE_DATA_URL)
            else:
                remote_url = "http://%s.%s/3.0/zh_CN" % (space_name, UPDATE_DATA_URL)
            
        patch_list_url = "%s/patch/%s/patch_md5.json" % (remote_url, origin_data_md5)    

        try:
            patch_list_json = eval(urllib2.urlopen(patch_list_url).read())
        except:
            patch_list_json = ""
            
        if patch_list_json != "":
            patch_name = patch_list_json["current_patch"][0]["name"]
            patch_md5 = patch_list_json["current_patch"][0]["md5"]

            local_patch_info = self.patch_status_config.get("data_md5", space_name)
            if local_patch_info and eval(local_patch_info)[1] != patch_md5:
                
                # Start download.
                download_url = "%s/patch/%s/%s" % (remote_url, origin_data_md5, patch_name)
                local_patch_file = os.path.join(patch_dir, patch_name)
                
                # TODO: 此处添加下载返回值判断
                download_task = TaskObject(download_url, local_patch_file)
                download_task.run()

                if md5_file(local_patch_file) == patch_md5:
                    self.have_update.append(space_name)
                    remove_file(os.path.join(self.data_patch_dir, eval(local_patch_info)[0]))
                    self.patch_status_config.set("data_md5", space_name, (patch_name, patch_md5))
                    print "%s: 补丁%s下载成功" % (space_name, patch_name)
                    log("%s: 补丁%s下载成功" % (space_name, patch_name))
                else:
                    print "%s: 补丁%s下载错误" (space_name, patch_name)
                    log("%s: 补丁%s下载错误" (space_name, patch_name))
            else:
                print "%s: 当前数据是最新的" % space_name
                log("%s: 当前数据是最新的" % space_name)
        else:
            print "%s: 远端没有任何更新补丁" % space_name
            log("%s: 远端没有任何更新补丁" % space_name)
            
    def apply_data(self, space_name):
        space_dir = os.path.join(self.data_newest_dir, space_name)
        create_directory(space_dir)        
        
        data_filename = "%s.tar.gz" % space_name
        patch_dir = os.path.join(self.data_patch_dir, space_name)
        patch_name = eval(self.patch_status_config.get("data_md5", space_name))[0]

        origin_data_file = os.path.join(self.data_origin_dir, data_filename)
        patch_file = os.path.join(self.data_patch_dir, space_name, patch_name)
        newest_data_file = os.path.join(self.data_newest_dir, data_filename)

        print "%s: 补丁%s合并开始..." % (space_name, patch_name)
        log("%s: 补丁%s合并开始..." % (space_name, patch_name))
        subprocess.Popen("xdelta3 -ds %s %s %s" % (origin_data_file,
                                                    patch_file,
                                                    newest_data_file),
                                                    shell=True).wait()
                        
        print "%s: 补丁%s合并完成" % (space_name, patch_name)
        log("%s: 补丁%s合并完成" % (space_name, patch_name))

    def clean(self):
        remove_file(os.path.join(DATA_DIR, "patch_status.ini"))
        for dir_name in os.listdir(DATA_DIR):
            if dir_name in ["newest", "update", "patch"]:
                remove_path(os.path.join(DATA_DIR, dir_name))
        
if __name__ == "__main__":
    # Init.
    dbus.mainloop.glib.DBusGMainLoop(set_as_default = True)
    gobject.threads_init()
    
    # Exit if updater has running.
    if is_dbus_name_exists(DSC_UPDATER_NAME, False):
        print "Deepin software center updater has running!"
        log("Deepin software center updater has running!")
    else:
        # Init mainloop.
        mainloop = gobject.MainLoop()
        signal.signal(signal.SIGINT, lambda : mainloop.quit()) # capture "Ctrl + c" signal
        
        # Auth with root permission.
        if not auth_with_policykit("com.linuxdeepin.softwarecenterupdater.action",
                                   "org.freedesktop.PolicyKit1", 
                                   "/org/freedesktop/PolicyKit1/Authority", 
                                   "org.freedesktop.PolicyKit1.Authority",
                                   ):
            print "Authority failed"
            log("Authority failed")
        else:
            # Init dbus.
            system_bus = dbus.SystemBus()
            bus_name = dbus.service.BusName(DSC_UPDATER_NAME, system_bus)
            
            # Init package manager.
            log("Start update data...")
            UpdateDataService(system_bus, mainloop).run()
            log("Finish update data.")
            
            # Run.
            #log("Run Loop")
            #mainloop.run()
