#!/usr/bin/python
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

import os
from deepin_utils.file import get_parent_dir, remove_file, remove_path
from deepin_utils.config import Config
import uuid
import tarfile

DATA_DIR = os.path.join(get_parent_dir(__file__), "data")
UPDATE_DATE = "2013-03-25"

data_origin_dir = os.path.join(DATA_DIR, "origin")
data_newest_dir = os.path.join(DATA_DIR, "newest")
data_patch_dir = os.path.join(DATA_DIR, "patch")
data_patch_config_filepath = os.path.join(DATA_DIR, "patch_status.ini")
data_newest_id_path = os.path.join(DATA_DIR, "data_newest_id.ini")

def run():
    if not os.path.exists(data_newest_id_path):
        newest_data_id_config = Config(data_newest_id_path)
        newest_data_id_config.load()
        newest_data_id_config.set("newest", "data_id", "")
        newest_data_id_config.set("newest", "update_date", "")
        newest_data_id_config.write()
        
    # Extract data if current directory is not exists.
    newest_data_id_config = Config(data_newest_id_path)
    newest_data_id_config.load()

    try:
        update_date = newest_data_id_config.get("newest", "update_date")
    except Exception:
        update_date = ""

    if newest_data_id_config.get("newest", "data_id") == "" or update_date != UPDATE_DATE:
        clean()
        newest_data_id = str(uuid.uuid4())
        newest_data_dir = os.path.join(DATA_DIR, "update", newest_data_id)
        
        print "进行第一次数据解压..."
        for data_file in os.listdir(data_origin_dir):
            with tarfile.open(os.path.join(data_origin_dir, data_file), "r:gz") as tar_file:
                tar_file.extractall(newest_data_dir)
        print "进行第一次数据解压完成"
        
        newest_data_id_config.set("newest", "data_id", newest_data_id)
        newest_data_id_config.set("newest", "update_date", UPDATE_DATE)
        newest_data_id_config.write()

def clean():
    remove_file(os.path.join(DATA_DIR, "patch_status.ini"))
    for dir_name in os.listdir(DATA_DIR):
        if dir_name in ["newest", "update", "patch"]:
            remove_path(os.path.join(DATA_DIR, dir_name))

if __name__ == "__main__":
    run()
