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
from dtk.ui.utils import get_parent_dir

DSC_SERVICE_NAME = "com.linuxdeepin.softwarecenter"
DSC_SERVICE_PATH = "/com/linuxdeepin/softwarecenter"

DSC_FRONTEND_NAME = "com.linuxdeepin.softwarecenter_frontend"
DSC_FRONTEND_PATH = "/com/linuxdeepin/softwarecenter_frontend"

ICON_DIR = os.path.join(get_parent_dir(__file__, 2), "data", "update_data", "app_icon")
VIEW_PADDING_X = 10
VIEW_PADDING_Y = 10

BUTTON_NORMAL = 1
BUTTON_HOVER = 2
BUTTON_PRESS = 3

ACTION_INSTALL = 1
ACTION_UNINSTALL = 2
ACTION_UPGRADE = 3

CONFIG_DIR =  os.path.join(os.path.expanduser("~"), ".config", "deepin-software-center")
ONE_DAY_SECONDS = 24 * 60 * 60

SCREENSHOT_HOST = "http://package-screenshot.b0.upaiyun.com"
SCREENSHOT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), ".cache", "deepin-software-center", "screenshot")
