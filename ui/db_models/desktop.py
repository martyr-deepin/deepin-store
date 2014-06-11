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
import peewee

root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
db_path = os.path.join(root_path, "data/desktop/desktop2014.db")

#desktop_db = peewee.SqliteDatabase(db_path)
desktop_db = peewee.SqliteDatabase(db_path, autocommit=False)

class Package(peewee.Model):
    pkg_name = peewee.CharField()
    display_flag = peewee.BooleanField()
    first_category_name = peewee.CharField()
    second_category_name = peewee.CharField()
    start_pkg_names = peewee.CharField()

    class Meta:
        database = desktop_db

class Desktop(peewee.Model):
    desktop_path = peewee.CharField()
    desktop_name = peewee.CharField()
    pkg_names = peewee.CharField()
    first_category_name = peewee.CharField()

    class Meta:
        database = desktop_db

class PackageDesktop(peewee.Model):
    package = peewee.ForeignKeyField(Package, related_name="package")
    desktop  = peewee.ForeignKeyField(Desktop, related_name="desktop")

    class Meta:
        database = desktop_db

if __name__ == "__main__":
    print Package.select().count()
