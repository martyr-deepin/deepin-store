#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
#               2012 ~ 2014 Kaisheng Ye
#
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#             Kaisheng Ye <kaisheng.ye@gmail.com>
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

from deepin_storm.tasks import MultiTaskObject
from deepin_storm.services import FetchService
from deepin_storm.logger import Logger
from deepin_storm.report import parse_bytes, parse_time

import sys

class DownloadManager(Logger):
    def __init__(self, global_event=None, number=5, verbose=False):

        self.global_event = global_event
        self.fetch_service_thread = FetchService(number)
        self.fetch_service_thread.start()
        self.verbose = verbose

        self.fetch_files_dict = {}

    def add_download(self, pkg_name, action_type, download_urls, all_pkg_names=[], 
            all_change_pkgs=[], file_save_dir="/var/cache/apt/archives"):

        self.loginfo("add download: %s" % download_urls)
        fetch_files = MultiTaskObject(download_urls, output_dir=file_save_dir,
                task_name=pkg_name)

        if self.global_event:
            fetch_files.connect("start", self.start_download)
            fetch_files.connect("update", self.update_download)
            fetch_files.connect("finish", self.finish_download)
            fetch_files.connect("pause", self.pause_download)
            fetch_files.connect("stop", self.stop_download)
            fetch_files.connect("error", self.download_error)

        self.fetch_files_dict[pkg_name] = {
            "fetch_files" : fetch_files,
            "action_type" : action_type,
            "all_pkg_names": all_pkg_names,
            "all_change_pkgs": all_change_pkgs,
            "status" : "wait"
            }
        self.fetch_service_thread.add_missions([fetch_files,])

    def start_download(self, task, data=None):
        pkg_name = task.task_name
        if self.fetch_files_dict.has_key(pkg_name):
            task_info = self.fetch_files_dict[pkg_name]
            task_info["status"] = "start"
            action_type = task_info["action_type"]

            self.global_event.emit("download-start", pkg_name, action_type)
            if self.verbose:
                self.loginfo("%s download start" % pkg_name)

    def update_download(self, task, data):
        pkg_name = task.task_name
        if self.fetch_files_dict.has_key(pkg_name):
            task_info = self.fetch_files_dict[pkg_name]
            task_info["status"] = "update"
            total = len(task_info["all_change_pkgs"])
            action_type = task_info["action_type"]

            if isinstance(task, MultiTaskObject):
                finish_number = len(task.task_finish_list)
            else:
                finish_number = 0

            self.global_event.emit("download-update", pkg_name, action_type, 
                    (data.progress, data.speed, finish_number, total, data.downloaded,
                    data.filesize))
            if self.verbose:
                self.print_update(task, data)

    def print_update(self, task, data):
        return 
        progress = "%d%%" % data.progress
        speed = parse_bytes(data.speed)
        remaining = parse_time(data.remaining)
        filesize = parse_bytes(data.filesize)
        downloaded = parse_bytes(data.downloaded)

        sys.stdout.flush()
        s = "\r%s: %s/s - %s, progress: %s, total: %s, remaining time: %s"
        print s % (task.task_name, speed, downloaded, progress, filesize, remaining),

    def download_error(self, task, error_info):
        pkg_name = task.task_name
        if self.fetch_files_dict.has_key(pkg_name):
            task_info = self.fetch_files_dict[pkg_name]
            self.fetch_files_dict.pop(pkg_name)
            action_type = task_info["action_type"]

            if isinstance(error_info, list):
                #sub_task = error_info[1]
                error_info = error_info[0]

            self.global_event.emit("download-error", pkg_name, action_type, error_info)
            if self.verbose:
                self.logerror("%s download error: %s" % (pkg_name, error_info))

    def finish_download(self, task, data=None):
        pkg_name = task.task_name
        if self.fetch_files_dict.has_key(pkg_name):
            task_info = self.fetch_files_dict[pkg_name]
            self.fetch_files_dict.pop(pkg_name)
            action_type = task_info["action_type"]
            all_pkg_names = task_info["all_pkg_names"]

            self.global_event.emit("download-finish", pkg_name, action_type,
                    all_pkg_names)
            if self.verbose:
                sys.stdout.flush()
                self.loginfo("%s download finish" % (pkg_name,))

    def pause_download(self, task, data=None):
        pkg_name = task.task_name
        if self.fetch_files_dict.has_key(pkg_name):
            task_info = self.fetch_files_dict[pkg_name]
            task_info["status"] = "stop"
            action_type = task_info['action_type']

            self.global_event.emit("download-stop", pkg_name, action_type)
            if self.verbose:
                self.loginfo("%s download pause" % (pkg_name,))

    def stop_download(self, task, data=None):
        pkg_name = task.task_name
        if self.fetch_files_dict.has_key(pkg_name):
            task_info = self.fetch_files_dict[pkg_name]
            task_info["status"] = "stop"
            action_type = task_info["action_type"]

            self.global_event.emit("download-stop", pkg_name, action_type)
            if self.verbose:
                self.loginfo("%s download stop" % (pkg_name,))

    def stop_wait_download(self, pkg_name):
        if self.fetch_files_dict.has_key(pkg_name):
            self.fetch_files_dict[pkg_name]["fetch_files"].stop()
            self.fetch_files_dict.pop(pkg_name)

if __name__ == "__main__":
    import gtk
    from events import global_event
    gtk.gdk.threads_init()

    download_manager = DownloadManager(global_event=global_event, verbose=True)
    download_manager.add_download("QQ", 1, [
        'http://test.packages.linuxdeepin.com/ubuntu/pool/universe/d/darktable/darktable_1.4-2_amd64.deb',
        'http://test.packages.linuxdeepin.com/ubuntu/pool/universe/f/flickcurl/libflickcurl0_1.25-1ubuntu1_amd64.deb',
        'http://test.packages.linuxdeepin.com/ubuntu/pool/universe/p/prototypejs/libjs-prototype_1.7.1-3_all.deb',
        'http://test.packages.linuxdeepin.com/ubuntu/pool/universe/s/scriptaculous/libjs-scriptaculous_1.9.0-2_all.deb',
        'http://test.packages.linuxdeepin.com/ubuntu/pool/universe/l/lensfun/liblensfun-data_0.2.8-1_all.deb',
        'http://test.packages.linuxdeepin.com/ubuntu/pool/universe/l/lensfun/liblensfun0_0.2.8-1_amd64.deb',
        ], file_save_dir="/tmp")

    gtk.main()
