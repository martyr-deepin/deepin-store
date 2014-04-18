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

from collections import OrderedDict

CATEGORY_TYPE_DICT = OrderedDict(
    [("internet", OrderedDict([
                    ("browser", []),
                    ("instant_messaging", []),
                    ("email", []),
                    ("file_transfer", []),
                    ("news", []),
                    ("remote_access", []),
                    ("security", []),
                    ("miscellaneous", []),
                    ])),
     ("multimedia", OrderedDict([
                    ("audiovideo", []),
                    ("audiovideo_editing", []),
                    ("disc_burner", []),
                    ("midi", []),
                    ("mixer", []),
                    ("player", []),
                    ("recorder", []),
                    ("sequencer", []),
                    ("tuner", []),
                    ])),
     ("games", OrderedDict([
                    ("action_games", []),
                    ("advernture_games", []),
                    ("arcade_games", []),
                    ("board_games", []),
                    ("card_games", []),
                    ("emulator", []),
                    ("kids_games", []),
                    ("logic_games", []),
                    ("puzzle_games", []),
                    ("role_playing_games", []),
                    ("sports_games", []),
                    ("strategy_games", []),
                    ])),
     ("graphics", OrderedDict([
                    ("2d_graphics", []),
                    ("3d_graphics", []),
                    ("image_processing", []),
                    ("photography", []),
                    ("vector_graphics", []),
                    ("viewer", []),
                    ])),
     ("productivity", OrderedDict([
                    ("office", []),
                    ("scanning_printing", []),
                    ])),
     ("industry", OrderedDict([
                    ("engineering", []),
                    ("finance", []),
                    ("ham_radio", []),
                    ("medical", []),
                    ("publishing", []),
                    ])),
     ("education", OrderedDict([
                    ("languages", []),
                    ("religion", []),
                    ("science", []),
                    ])),
     ("development", OrderedDict([
                    ("database", []),
                    ("debugging", []),
                    ("ide", []),
                    ("software_development", []),
                    ("version_control", []),
                    ("web_development", []),
                    ])),
     ("system", OrderedDict([
                    ("desktop_environment", []),
                    ("monitor", []),
                    ("network", []),
                    ("package_manager", []),
                    ("settings", []),
                    ("virtualization", []),
                    ("window_manager", []),
                    ])),
     ("utilities", OrderedDict([
                    ("accessories", []),
                    ("archiving", []),
                    ("emulation", []),
                    ("file_manager", []),
                    ("screensaver", []),
                    ("terminal_emulator", []),
                    ("text_editor", []),
                    ])),
     ])
