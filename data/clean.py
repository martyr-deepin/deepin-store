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

import os
from deepin_utils.file import get_current_dir, remove_directory
from deepin_utils.config import Config

current_dir = get_current_dir(__file__)
for dir_name in ["newest", "patch", "update"]:
    remove_directory(os.path.join(current_dir, dir_name))
    
current_data_id_config = Config(os.path.join(current_dir, "data_current_id.ini"))
current_data_id_config.load()
current_data_id_config.set("current", "data_id", "")
current_data_id_config.write()

newest_data_id_config = Config(os.path.join(current_dir, "data_newest_id.ini"))
newest_data_id_config.load()
newest_data_id_config.set("newest", "data_id", "")
newest_data_id_config.write()
    
patch_status_config = Config(os.path.join(current_dir, "patch_status.ini"))
patch_status_config.load()
patch_status_config.set("data_md5", "dsc-search-data", "")
patch_status_config.set("data_md5", "dsc-category-data", "")
patch_status_config.set("data_md5", "dsc-software-data", "")
patch_status_config.set("data_md5", "dsc-home-data", "")
patch_status_config.set("data_md5", "dsc-icon-data", "")
patch_status_config.set("data_md5", "dsc-desktop-data", "")
patch_status_config.write()
