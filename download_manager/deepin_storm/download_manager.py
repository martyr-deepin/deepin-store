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

from deepin_storm.download import FetchServiceThread, join_glib_loop, FetchFiles
from deepin_utils.hash import get_hash
import os
import sys

class DownloadManager(object):
    '''
    class docs
    '''
	
    def __init__(self, global_event=None, number=5, verbose=False):
        '''
        init docs
        '''
        self.global_event = global_event
        self.fetch_service_thread = FetchServiceThread(number)
        self.fetch_service_thread.start()
        self.verbose = verbose
        
        join_glib_loop(0.05)
        
        self.fetch_files_dict = {}
        
    def add_download(self, 
                    pkg_name, 
                    action_type, 
                    download_urls, 
                    download_hash_infos, 
                    file_sizes=[], 
                    all_pkg_names=[], 
                    all_change_pkgs=[], 
                    file_save_dir="/var/cache/apt/archives"
                    ):
        fetch_files = FetchFiles(
            download_urls,
            file_hash_infos=download_hash_infos,
            file_sizes=file_sizes,
            file_save_dir=file_save_dir)

        if self.global_event:
            fetch_files.signal.register_event("start", lambda : self.start_download(pkg_name, action_type))
            fetch_files.signal.register_event("update", lambda percent, speed: self.update_download(
                pkg_name, action_type, percent, speed, fetch_files, all_change_pkgs))
            fetch_files.signal.register_event("finish", lambda : self.finish_download(pkg_name, action_type, all_pkg_names))
            fetch_files.signal.register_event("pause", lambda : self.global_event.emit("download-stop", pkg_name, action_type))
            fetch_files.signal.register_event("stop", lambda : self.global_event.emit("download-stop", pkg_name, action_type))
            fetch_files.signal.register_event("error", lambda e: self.download_error(pkg_name, action_type, e))
            
        if self.verbose:    
            fetch_files.signal.register_event("start", self.print_signal)
            fetch_files.signal.register_event("update", self.print_signal)
            fetch_files.signal.register_event("finish", self.print_signal)
            fetch_files.signal.register_event("pause", self.print_signal)
            fetch_files.signal.register_event("stop", self.print_signal)
            
        self.fetch_files_dict[pkg_name] = {
            "fetch_files" : fetch_files,
            "action_type" : action_type,
            "status" : "wait"}
        self.fetch_service_thread.fetch_service.add_fetch(fetch_files)

    def download_error(self, pkg_name, action_type, e):
        if self.fetch_files_dict.has_key(pkg_name):
            self.fetch_files_dict.pop(pkg_name)

        self.global_event.emit("download-error", pkg_name, action_type, e)
        
    def start_download(self, pkg_name, action_type):
        if self.fetch_files_dict.has_key(pkg_name):
            self.fetch_files_dict[pkg_name]["status"] = "start"
            
        self.global_event.emit("download-start", pkg_name, action_type)    
    
    def update_download(self, pkg_name ,action_type, percent, speed, fetch_files, all_change_pkgs):
        total = len(all_change_pkgs)
        if self.fetch_files_dict.has_key(pkg_name):
            self.fetch_files_dict[pkg_name]["status"] = "update"

        finish_number = total - len(fetch_files.fetch_file_dict)
        for fetch_file in fetch_files.fetch_file_dict.values():
            (expect_hash_type, expect_hash_value) = fetch_file.file_hash_info
            if os.path.exists(fetch_file.file_save_path):
                hash_value = get_hash(fetch_file.file_save_path, expect_hash_type)
                if hash_value == expect_hash_value:
                    finish_number += 1
            
        self.global_event.emit("download-update", \
                pkg_name, action_type, percent, speed, finish_number, total, \
                fetch_files.downloaded_size, fetch_files.total_size)
        
    def finish_download(self, pkg_name, action_type, all_pkg_names):
        if self.fetch_files_dict.has_key(pkg_name):
            self.fetch_files_dict.pop(pkg_name)
            
        self.global_event.emit("download-finish", pkg_name, action_type, all_pkg_names)    
            
    def stop_download(self, pkg_name):
        if self.fetch_files_dict.has_key(pkg_name):
            self.fetch_service_thread.fetch_service.pause_fetch(self.fetch_files_dict[pkg_name]["fetch_files"])
            self.fetch_files_dict.pop(pkg_name)
            
    def stop_wait_download(self, pkg_name):
        self.stop_download(pkg_name)
            
    def print_signal(self, *message):
        print message

if __name__ == "__main__":
    
    def get_parent_dir(filepath, level=1):
        '''
        Get parent directory with given return level.
        
        @param filepath: Filepath.
        @param level: Return level, default is 1
        @return: Return parent directory with given return level. 
        '''
        parent_dir = os.path.realpath(filepath)
        
        while(level > 0):
            parent_dir = os.path.dirname(parent_dir)
            level -= 1
        
        return parent_dir

    sys.path.append(os.path.join(get_parent_dir(__file__, 3), "pkg_manager", "apt"))
    
    from parse_pkg import get_pkg_download_info
    from apt_cache import AptCache
    import gtk
    import apt_pkg
    
    gtk.gdk.threads_init()
    
    apt_pkg.init()
    cache = AptCache()
    pkg_name = "amarok"
    pkg_infos = get_pkg_download_info(cache, pkg_name)
    download_manager = DownloadManager(verbose=True)
    if pkg_infos != None:
        (names, download_urls, download_hash_infos, pkg_sizes) = pkg_infos
    
        download_manager.add_download(pkg_name, 1, False, download_urls, download_hash_infos, pkg_sizes)
        # download_manager.add_download(
        #     pkg_name, 
        #     ["http://test.packages.linuxdeepin.com/ubuntu/pool/main/k/kdepim/libkdepim4_4.8.5-0ubuntu0.1_amd64.deb"],
        #     None,
        #     None
        #     )
    
    gtk.main()
    
