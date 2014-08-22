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

from deepin_storm.logger import Logger

import sys
import dbus

DOWNLOAD_DBUS_NAME = "com.deepin.download.service"
DOWNLOAD_DBUS_PATH = "/com/deepin/download/service"
DOWNLOAD_DBUS_INTERFACE = "com.deepin.download.service"

class DownloadManager(Logger):
    def __init__(self, global_event=None, verbose=False):

        self.global_event = global_event
        self.verbose = verbose

        system_bus = dbus.SystemBus()
        bus_object = system_bus.get_object(DOWNLOAD_DBUS_NAME, DOWNLOAD_DBUS_PATH)
        self.download_dbus_interface = dbus.Interface(bus_object, DOWNLOAD_DBUS_INTERFACE)

        self.download_dbus_interface.connect_to_signal(
                signal_name="Start",
                handler_function=self.start_download
                )
        self.download_dbus_interface.connect_to_signal(
                signal_name="Update",
                handler_function=self.update_download
                )
        self.download_dbus_interface.connect_to_signal(
                signal_name="Finish",
                handler_function=self.finish_download
                )
        self.download_dbus_interface.connect_to_signal(
                signal_name="Stop",
                handler_function=self.stop_download
                )
        self.download_dbus_interface.connect_to_signal(
                signal_name="Pause",
                handler_function=self.pause_download
                )
        self.download_dbus_interface.connect_to_signal(
                signal_name="Error",
                handler_function=self.download_error
                )

        self.download_task_info = {}
        self.task_name_to_id = {}

    def add_download(self,
            task_name,
            action_type,
            download_urls,
            download_sizes=[],
            download_md5s=[],
            all_task_names=[],
            all_change_pkgs=[],
            file_save_dir="/var/cache/apt/archives"
            ):

        task_id = self.download_dbus_interface.AddTask(
            task_name,
            download_urls,
            download_sizes,
            download_md5s,
            file_save_dir,
            )

        self.download_task_info[task_id] = {
            "task_name": task_name,
            "action_type" : action_type,
            "all_task_names": all_task_names,
            "all_change_pkgs": all_change_pkgs,
            "status" : "wait"
            }
        if self.task_name_to_id.has_key(task_name):
            self.logwarn("repeat task name:", task_name)
        self.task_name_to_id[task_name] = task_id

        if self.verbose:
            self.loginfo("Add download for %s urls:" % len(download_urls))
            for url in download_urls:
                self.loginfo(">>> " + url)

    def start_download(self, task_id):
        if self.download_task_info.has_key(task_id):
            task_info = self.download_task_info[task_id]

            task_info["status"] = "start"
            action_type = task_info["action_type"]
            task_name = task_info["task_name"]

            self.global_event.emit("download-start", task_name, action_type)
            if self.verbose:
                self.loginfo("%s download start" % task_name)

    def update_download(self, task_id, progress, speed, finish_number,
            total_number, downloaded_size, total_size):
        if self.download_task_info.has_key(task_id):

            task_info = self.download_task_info[task_id]

            task_info["status"] = "update"
            action_type = task_info["action_type"]
            task_name = task_info["task_name"]

            self.global_event.emit("download-update", task_name, action_type,
                    (progress, speed, finish_number, total_number,
                    downloaded_size, total_size))
            if self.verbose:
                pass

    def download_error(self, task_id, error_code, error_string):
        if self.download_task_info.has_key(task_id):
            task_info = self.download_task_info[task_id]

            action_type = task_info["action_type"]
            task_name = task_info['task_name']

            self.download_task_info.pop(task_id)

            self.global_event.emit("download-error", task_name, action_type,
                    error_string)
            if self.verbose:
                self.logerror("%s download error: %s" % (task_name, error_string))

    def finish_download(self, task_id):
        if self.download_task_info.has_key(task_id):
            task_info = self.download_task_info[task_id]

            action_type = task_info["action_type"]
            all_task_names = task_info["all_task_names"]
            task_name = task_info['task_name']

            self.download_task_info.pop(task_id)

            self.global_event.emit("download-finish", task_name, action_type,
                    all_task_names)
            if self.verbose:
                sys.stdout.flush()
                self.loginfo("%s download finish" % (task_name,))

    def pause_download(self, task_id):
        if self.download_task_info.has_key(task_id):
            task_info = self.download_task_info[task_id]

            task_info["status"] = "stop"
            action_type = task_info['action_type']
            task_name = task_info['task_name']

            self.global_event.emit("download-stop", task_name, action_type)
            if self.verbose:
                self.loginfo("%s download pause" % (task_name,))

    def stop_download(self, task_id):
        if self.download_task_info.has_key(task_id):
            task_info = self.download_task_info[task_id]

            task_info["status"] = "stop"
            action_type = task_info["action_type"]
            task_name = task_info['task_name']

            self.global_event.emit("download-stop", task_name, action_type)
            if self.verbose:
                self.loginfo("%s download stop" % (task_name,))

    def stop_wait_download(self, task_name):
        if self.task_name_to_id.has_key(task_name):
            task_id = self.task_name_to_id[task_name]
            self.download_dbus_interface.StopTask(task_id)
            self.download_task_info.pop(task_id)
            self.task_name_to_id.pop(task_name)

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
