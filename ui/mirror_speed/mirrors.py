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

import os
from deepin_utils.file import get_parent_dir
from deepin_utils.config import Config
from urlparse import urlparse

root_dir = get_parent_dir(__file__, 3)
mirrors_dir = os.path.join(root_dir, 'mirrors')

class Mirror(object):
    def __init__(self, ini_file):
        self.ini_file = ini_file
        self.config = Config(ini_file)
        self.config.load()
        deepin_url = self.get_repo_urls()[1]
        self._url_parse = urlparse(deepin_url)
        self._hostname = self._url_parse.scheme + "://" + self._url_parse.netloc
    
    @property
    def host(self):
        return self._url_parse.netloc

    @property
    def hostname(self):
        return self._hostname

def get_mirrors():
    mirrors_list = []
    for ini_file in os.listdir(mirrors_dir):
        m = Mirror(os.path.join(mirrors_dir, ini_file))
        mirrors_list.append(m)
    return mirrors_list

if __name__ == "__main__":
    mirrors_list = []
    for ini_file in os.listdir(mirrors_dir):
        m = Mirror(os.path.join(mirrors_dir, ini_file))
        print m.host
