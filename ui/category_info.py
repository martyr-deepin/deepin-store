#!/usr/bin/env python
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

from nls import _

category_info = {
    "internet" : _("internet"),
    "browser" : _("browser"),
    "instant_messaging" : _("instant_messaging"),
    "email" : _("email"),
    "file_transfer" : _("file_transfer"),
    "news" : _("news"),
    "remote_access" : _("remote_access"),
    "security" : _("security"),
    "miscellaneous" : _("miscellaneous"),
    "multimedia" : _("multimedia"),
    "audiovideo" : _("audiovideo"),
    "audiovideo_editing" : _("audiovideo_editing"),
    "disc_burner" : _("disc_burner"),
    "midi" : _("midi"),
    "mixer" : _("mixer"),
    "player" : _("player"),
    "recorder" : _("recorder"),
    "sequencer" : _("sequencer"),
    "tuner" : _("tuner"),
    "games" : _("games"),
    "action_games" : _("action_games"),
    "advernture_games" : _("advernture_games"),
    "arcade_games" : _("arcade_games"),
    "board_games" : _("board_games"),
    "card_games" : _("card_games"),
    "emulator" : _("emulator"),
    "kids_games" : _("kids_games"),
    "logic_games" : _("logic_games"),
    "puzzle_games" : _("puzzle_games"),
    "role_playing_games" : _("role_playing_games"),
    "sports_games" : _("sports_games"),
    "strategy_games" : _("strategy_games"),
    "graphics" : _("graphics"),
    "2d_graphics" : _("2d_graphics"),
    "3d_graphics" : _("3d_graphics"),
    "image_processing" : _("image_processing"),
    "photography" : _("photography"),
    "vector_graphics" : _("vector_graphics"),
    "viewer" : _("viewer"),
    "productivity" : _("productivity"),
    "office" : _("office"),
    "scanning_printing" : _("scanning_printing"),
    "industry" : _("industry"),
    "engineering" : _("engineering"),
    "finance" : _("finance"),
    "ham_radio" : _("ham_radio"),
    "medical" : _("medical"),
    "publishing" : _("publishing"),
    "education" : _("education"),
    "languages" : _("languages"),
    "religion" : _("religion"),
    "science" : _("science"),
    "development" : _("development"),
    "database" : _("database"),
    "debugging" : _("debugging"),
    "ide" : _("ide"),
    "software_development" : _("software_development"),
    "version_control" : _("version_control"),
    "web_development" : _("web_development"),
    "system" : _("system"),
    "desktop_environment" : _("desktop_environment"),
    "monitor" : _("monitor"),
    "network" : _("network"),
    "package_manager" : _("package_manager"),
    "settings" : _("settings"),
    "virtualization" : _("virtualization"),
    "window_manager" : _("window_manager"),
    "utilities" : _("utilities"),
    "accessories" : _("accessories"),
    "archiving" : _("archiving"),
    "emulation" : _("emulation"),
    "file_manager" : _("file_manager"),
    "screensaver" : _("screensaver"),
    "terminal_emulator" : _("terminal_emulator"),
    "text_editor" : _("text_editor"),
}

def get_category_name(category_id):
    return category_info[category_id]
