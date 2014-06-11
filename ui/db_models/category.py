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
db_path = os.path.join(root_path, "data/category/category.db")

#category_db = peewee.SqliteDatabase(db_path, autocommit=False)
category_db = peewee.SqliteDatabase(db_path)

class FirstCategory(peewee.Model):
    name = peewee.CharField()
    alias_name = peewee.CharField()
    order = peewee.IntegerField(default=0)

    class Meta:
        database = category_db

class SecondCategory(peewee.Model):
    name = peewee.CharField()
    alias_name = peewee.CharField()
    order = peewee.IntegerField(default=0)
    first_category = peewee.ForeignKeyField(FirstCategory, related_name="first_category")

    class Meta:
        database = category_db

if __name__ == "__main__":
    FirstCategory.create_table(fail_silently=True)
    SecondCategory.create_table(fail_silently=True)
    from desktop import Package
    n = 0
    for pkg in Package.select():
        first_category_name = pkg.first_category_name
        second_category_name = pkg.second_category_name
        if first_category_name == "" or second_category_name == "":
            continue
        try:
            first_obj = FirstCategory.select().where(FirstCategory.name==first_category_name).get()
        except:
            first_obj = FirstCategory(name=first_category_name, alias_name=first_category_name)
            first_obj.save()

        try:
            second_obj = SecondCategory.select().where(SecondCategory.name==second_category_name).get()
        except:
            second_obj = SecondCategory(name=second_category_name, alias_name=second_category_name, first_category=first_obj)
            second_obj.save()
        n += 1
        print "\rNumber: %i" % n,


