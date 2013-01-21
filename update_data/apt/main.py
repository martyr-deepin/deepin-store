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

import dbus
import dbus.service
import dbus.mainloop.glib
import gobject
import signal
from deepin_utils.ipc import auth_with_policykit, is_dbus_name_exists
from deepin_utils.file import get_parent_dir
import os
import tarfile
import uuid

DSC_UPDATER_NAME = "com.linuxdeepin.softwarecenterupdater"
DSC_UPDATER_PATH = "/com/linuxdeepin/softwarecenterupdater"
DATA_DIR = os.path.join(get_parent_dir(__file__, 3), "data")

class UpdateDataService(dbus.service.Object):
    '''
    class docs
    '''
	
    def __init__(self, system_bus):
        '''
        init docs
        '''
        # Init dbus service.
        dbus.service.Object.__init__(self, system_bus, DSC_UPDATER_PATH)
        
        self.data_origin_dir = os.path.join(DATA_DIR, "origin")
        self.data_current_dir = os.path.join(DATA_DIR, "current")
        self.data_temp_dir = os.path.join(DATA_DIR, "temp")
        self.data_update_dir = os.path.join(DATA_DIR, "update")
        
    def run(self):
        # Extract data if current directory is not exists.
        if not os.path.exists(self.data_current_dir):
            print "进行第一次数据解压..."
            for data_file in os.listdir(self.data_origin_dir):
                with tarfile.open(os.path.join(self.data_origin_dir, data_file), "r:gz") as tar_file:
                    tar_file.extractall(self.data_current_dir)
            print "进行第一次数据解压完成"
            
        # Update data.
        update_unique_id = str(uuid.uuid4())
        for data_file in os.listdir(self.data_origin_dir):
            self.update(update_unique_id, data_file)
            
    def update(self, update_unique_id, data_file):
        space_name = data_file.split(".tar.gz")[0]
        print space_name
        
if __name__ == "__main__":
    # Init.
    dbus.mainloop.glib.DBusGMainLoop(set_as_default = True)
    gobject.threads_init()
    
    # Exit if updater has running.
    if is_dbus_name_exists(DSC_UPDATER_NAME, False):
        print "Deepin software center updater has running!"
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
        else:
            # Init dbus.
            system_bus = dbus.SystemBus()
            bus_name = dbus.service.BusName(DSC_UPDATER_NAME, system_bus)
            
            # Init package manager.
            UpdateDataService(system_bus).run()
            
            # Run.
            mainloop.run()
    
# import os
# import sys
# import tarfile
# import subprocess
# import traceback
# from dtk.ui.threads import Thread
# from events import global_event
# from constant import UPDATE_DATA_URL
# from deepin_utils.file import read_file, write_file, get_parent_dir, create_directory, remove_directory
# from deepin_utils.hash import md5_file
# from deepin_storm.download import FetchServiceThread, join_glib_loop, FetchFiles
# from gevent.queue import Queue
# import urllib2

# UPDATE_TEMP_DIR = os.path.join(get_parent_dir(__file__, 3), "data", "update_temp")
# DATA_DIR = os.path.join(get_parent_dir(__file__, 3), "data")

# join_glib_loop()
            
# class UpdateData(Thread):
#     '''
#     class docs
#     '''
	
#     def __init__(self):
#         '''
#         init docs
#         '''
#         Thread.__init__(self)
#         self.signal = Queue()
        
#     def run(self):
#         try:
#             global_event.emit("update-data-start")
#             md5_filepath = os.path.join(get_parent_dir(__file__, 3), "data", "update_md5")
#             current_data_md5 = read_file(md5_filepath, True)
#             patch_list = urllib2.urlopen("%s/3.0/zh_CN/patch/patch_list.txt" % UPDATE_DATA_URL).read()
            
#             download_patches = []
#             if patch_list != "":
#                 # Get patch names.
#                 print patch_list
#                 for patch_line in patch_list.split("\n"):
#                     if patch_line != "":
#                         (data_md5, patch_md5, patch_name) = tuple(patch_line.split(" "))
#                         print (data_md5, current_data_md5, data_md5 == current_data_md5)
#                         if data_md5 == current_data_md5:
#                             download_patches = []
#                         else:
#                             download_patches.append((data_md5, patch_md5, patch_name))
                            
#                 if len(download_patches) > 0:            
#                     # Clean download directory.
#                     create_directory(UPDATE_TEMP_DIR, True)        
                            
#                     # Start download.
#                     download_urls = map(lambda (data_md5, patch_md5, patch_name): "%s/3.0/zh_CN/patch/%s" % (UPDATE_DATA_URL, patch_name), download_patches)
#                     download_hash_infos = map(lambda (data_md5, patch_md5, patch_name): ("md5", patch_md5), download_patches)
                    
#                     download_service_thread = FetchServiceThread(5)
#                     download_service_thread.start()
                    
#                     fetch_files = FetchFiles(
#                         file_urls=download_urls, 
#                         file_hash_infos=download_hash_infos,
#                         file_save_dir=UPDATE_TEMP_DIR)
#                     print fetch_files.signal
#                     fetch_files.signal.register_event("finish", lambda : self.signal.put("download-finish"))
#                     download_service_thread.fetch_service.add_fetch(fetch_files)
                    
#                     origin_update_file = os.path.join(DATA_DIR, "update_data.tar.gz")
#                     patch_update_file = os.path.join(DATA_DIR, "patch_data.tar.gz")
#                     temp_file = ""
#                     signal = self.signal.get()
#                     if signal == "download-finish":
#                         for (patch_index, (data_md5, patch_md5, patch_name)) in enumerate(download_patches):
#                             patch_path = os.path.join(UPDATE_TEMP_DIR, patch_name)
#                             if md5_file(patch_path) == patch_md5:
#                                 print "Check patch md5 sucess: %s" % (patch_path)
#                             else:
#                                 print "Check patch md5 failed: %s" % (patch_path)
                                
#                             if temp_file == "":    
#                                 temp_file = os.path.join(UPDATE_TEMP_DIR, "update_data_%s.tar.gz" % patch_name)
#                                 if os.path.exists(patch_update_file):
#                                     subprocess.Popen("xdelta3 -ds %s %s %s" % (patch_update_file, patch_path, temp_file), shell=True).wait()    
#                                 else:
#                                     subprocess.Popen("xdelta3 -ds %s %s %s" % (origin_update_file, patch_path, temp_file), shell=True).wait()    
                                
#                                 os.remove(patch_path)
#                             else:
#                                 new_temp_file = os.path.join(UPDATE_TEMP_DIR, "update_data_%s.tar.gz" % patch_name)
#                                 subprocess.Popen("xdelta3 -ds %s %s %s" % (temp_file, patch_path, new_temp_file), shell=True).wait()    
                                
#                                 os.remove(patch_path)
#                                 os.remove(temp_file)
                                
#                                 temp_file = new_temp_file
                                
#                             write_file(md5_filepath, data_md5)    
                            
#                             global_event.emit("update-data-update", patch_index + 1, len(download_patches))
                            
#                             print "Apply patch: %s sucess" % patch_name
                            
#                         if os.path.exists(patch_update_file):
#                             os.remove(patch_update_file)
#                         os.renames(temp_file, patch_update_file)
                        
#                         print "Update data file."
                        
#                         with tarfile.open(patch_update_file, "r:gz") as tar:
#                             tar.extractall(UPDATE_TEMP_DIR)
#                         print "Extra file to: %s" % (UPDATE_TEMP_DIR)
                        
#                         UPDATE_DATA_DIR = os.path.join(DATA_DIR, "update_data")    
#                         remove_directory(UPDATE_DATA_DIR)
#                         os.renames(UPDATE_TEMP_DIR, UPDATE_DATA_DIR)
#                         print "Update directory: %s" % (UPDATE_DATA_DIR)
                
#                     global_event.emit("update-data-finish")
#                 else:
#                     global_event.emit("update-data-not-need")
#         except Exception, e:
#             traceback.print_exc(file=sys.stdout)
#             print "update data failed: %s" % (e)

#             global_event.emit("update-data-failed")
        
# if __name__ == "__main__":
#     import gtk
#     gtk.gdk.threads_init()
    
#     UpdateData().start()

#     gtk.main()
