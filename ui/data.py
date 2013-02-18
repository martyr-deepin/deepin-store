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
from deepin_utils.file import get_parent_dir
from deepin_utils.config import Config

data_init_flag = False

DATA_DIR = os.path.join(get_parent_dir(__file__, 2), "data")
DATA_NEWEST_ID_CONFIG_FILE = os.path.join(DATA_DIR, "data_newest_id.ini")
DATA_CURRENT_ID_CONFIG_FILE = os.path.join(DATA_DIR, "data_current_id.ini")
DATA_ID = None

def data_init():
    global data_init_flag
    global DATA_ID
    
    if not data_init_flag:
        print "data init"
        data_init_flag = True
        
        data_newest_id_config = Config(DATA_NEWEST_ID_CONFIG_FILE)
        data_newest_id_config.load()
        DATA_ID = data_newest_id_config.get("newest", "data_id")
        
        data_current_id_config = Config(DATA_CURRENT_ID_CONFIG_FILE)
        data_current_id_config.load()
        data_current_id_config.set("current", "data_id", DATA_ID)
        data_current_id_config.write()
    
data_init()    

def data_exit():
    data_current_id_config = Config(DATA_CURRENT_ID_CONFIG_FILE)
    data_current_id_config.load()
    data_current_id_config.set("current", "data_id", "")
    data_current_id_config.write()
