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
# along with this program.  If not, see <http://www.gnu.org/licenses/>

# Import skin and theme, those must before at any other modules.
# from skin import ui_theme, app_theme
from dtk.ui.skin_config import skin_config
from dtk.ui.theme import Theme, ui_theme
from deepin_utils.file import get_parent_dir
import os

# Init skin config.
skin_config.init_skin(
    "blue",
    os.path.join(get_parent_dir(__file__, 2), "skin"),
    os.path.expanduser("~/.config/deepin-software-center/skin"),
    os.path.expanduser("~/.config/deepin-software-center/skin_config.ini"),
    "deepin-software-center",
    "3.0"
    )

# Create application theme.
app_theme = Theme(
    os.path.join(get_parent_dir(__file__, 2), "app_theme"),
    os.path.expanduser("~/.config/deepin-software-center/theme")
    )

# Set theme.
skin_config.load_themes(ui_theme, app_theme)
