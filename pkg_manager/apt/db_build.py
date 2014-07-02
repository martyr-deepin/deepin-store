#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011~2013 Deepin, Inc.
#               2011~2013 Kaisheng Ye
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
import sqlite3
from deepin_utils.file import get_parent_dir, remove_file, touch_file_dir
import locale
locale.setlocale(locale.LC_ALL, '')

class BuildSoftwareDB(object):
    def __init__(self, cache):
        self.cache = cache
        self.db_path = os.path.join(get_parent_dir(__file__, 3), 
                "data/cache_soft.db")

        remove_file(self.db_path)
        touch_file_dir(self.db_path)

        self.connect = sqlite3.connect(self.db_path)
        self.cursor = self.connect.cursor()

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS software (\
            pkg_name PRIMARY KEY NOT NULL, short_desc, long_desc, version, \
            homepage, size)")

        for pkg in self.cache:
            try:
                self.cursor.execute(
                    "INSERT INTO software VALUES(?,?,?,?,?,?)",
                    (pkg.name, 
                    unicode(pkg.candidate.summary),
                    unicode(pkg.candidate.description),
                    unicode(pkg.candidate.version),
                    unicode(pkg.candidate.homepage),
                    unicode(pkg.candidate.size)
                    ))
            except Exception, e:
                print "Error in db_build: %s %s" % (e, pkg.name)

        self.connect.commit()
        self.connect.close()

if __name__ == '__main__':
    import apt
    cache = apt.Cache()
    db = BuildSoftwareDB(cache)
