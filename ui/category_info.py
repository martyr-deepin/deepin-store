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
    "internet" : _("Internet"),
    "browser" : _("Browser"),
    "instant_messaging" : _("Instant messaging"),
    "email" : _("Email"),
    "file_transfer" : _("File transfer"),
    "news" : _("News"),
    "remote_access" : _("Remote access"),
    "security" : _("Security"),
    "miscellaneous" : _("Miscellaneous"),
    "multimedia" : _("Multimedia"),
    "audiovideo" : _("Audiovideo"),
    "audiovideo_editing" : _("Media Editing"),
    "disc_burner" : _("Disc burner"),
    "midi" : _("MIDI"),
    "mixer" : _("Mixer"),
    "player" : _("Player"),
    "recorder" : _("Recorder"),
    "sequencer" : _("Sequencer"),
    "tuner" : _("Tuner"),
    "games" : _("Games"),
    "action_games" : _("Action games"),
    "advernture_games" : _("Advernture games"),
    "arcade_games" : _("Arcade games"),
    "board_games" : _("Board games"),
    "card_games" : _("Card games"),
    "emulator" : _("Emulator"),
    "kids_games" : _("Kids games"),
    "logic_games" : _("Logic games"),
    "puzzle_games" : _("Puzzle games"),
    "role_playing_games" : _("Role-playing games"),
    "sports_games" : _("Sports games"),
    "strategy_games" : _("Strategy games"),
    "graphics" : _("Graphics"),
    "2d_graphics" : _("2D graphics"),
    "3d_graphics" : _("3D graphics"),
    "image_processing" : _("Image processing"),
    "photography" : _("Photography"),
    "vector_graphics" : _("Vector graphics"),
    "viewer" : _("Viewer"),
    "productivity" : _("Productivity"),
    "office" : _("Office"),
    "scanning_printing" : _("Scanning printing"),
    "industry" : _("Industry"),
    "engineering" : _("Engineering"),
    "finance" : _("Finance"),
    "ham_radio" : _("Ham radio"),
    "medical" : _("Medical"),
    "publishing" : _("Publishing"),
    "education" : _("Science Education"),
    "languages" : _("Languages"),
    "religion" : _("Religion"),
    "science" : _("Science"),
    "development" : _("Development"),
    "database" : _("Database"),
    "debugging" : _("Debugging"),
    "ide" : _("IDE"),
    "software_development" : _("Software development"),
    "version_control" : _("Version control"),
    "web_development" : _("Web development"),
    "system" : _("System"),
    "desktop_environment" : _("Desktop environment"),
    "monitor" : _("Monitor"),
    "network" : _("Network"),
    "package_manager" : _("Package manager"),
    "settings" : _("Settings"),
    "virtualization" : _("Virtualization"),
    "window_manager" : _("Window manager"),
    "utilities" : _("Utilities"),
    "accessories" : _("Accessories"),
    "archiving" : _("Archiving"),
    "emulation" : _("Emulation"),
    "file_manager" : _("File manager"),
    "screensaver" : _("Screensaver"),
    "terminal_emulator" : _("Terminal emulator"),
    "text_editor" : _("Text editor"),
}

def get_category_name(category_id):
    return category_info[category_id]
