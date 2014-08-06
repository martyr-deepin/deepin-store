#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
#               2012 ~ 2013 Kaisheng Ye
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
#             Kaisheng Ye <kaisheng.ye@gmail.com>
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
import gio
import sys
import sqlite3
import xappy
from collections import OrderedDict
from deepin_utils.file import get_parent_dir
import threading as td

from data import DATA_ID
from constant import LANGUAGE
from category import CATEGORY_TYPE_DICT

import peewee
from db_models.software import Software
from db_models.software import Language as SoftwareLanguage

UPDATE_DATA_DIR = os.path.join(get_parent_dir(__file__, 2), "data", "update", DATA_ID)
CACHE_SOFT_DB_PATH = os.path.join(get_parent_dir(__file__, 2), "data", "cache_soft.db")

DATA_SUPPORT_LANGUAGE = ['en_US', 'zh_CN', 'zh_TW']

def db_path_exists(path):
    if not os.path.exists(path):
        print "Database not exist:", path
        sys.exit(1)

class DataManager(td.Thread):
    def __init__(self, bus_interface, debug_flag=False):
        '''
        init docs
        '''
        self.bus_interface = bus_interface
        self.debug_flag = debug_flag

        self.language = LANGUAGE if LANGUAGE in DATA_SUPPORT_LANGUAGE else 'en_US'

        software_db_path = os.path.join(UPDATE_DATA_DIR, "software", "software.db")
        software_db = peewee.SqliteDatabase(software_db_path, check_same_thread=False)
        Software._meta.database = software_db
        SoftwareLanguage._meta.database = software_db
        self.default_lang_obj = SoftwareLanguage.select().where(SoftwareLanguage.language_code=="en_US").get()
        self.current_lang_obj = SoftwareLanguage.select().where(SoftwareLanguage.language_code==self.language).get()

        self.init_cache_soft_db()

        desktop_db_path = os.path.join(UPDATE_DATA_DIR, "desktop", "desktop2014.db")
        db_path_exists(desktop_db_path)
        self.desktop_db_connect = sqlite3.connect(desktop_db_path, check_same_thread = False)
        self.desktop_db_cursor = self.desktop_db_connect.cursor()
        
        category_db_path = os.path.join(UPDATE_DATA_DIR, "category", "category.db")
        db_path_exists(category_db_path)
        self.category_db_connect = sqlite3.connect(category_db_path, check_same_thread = False)
        self.category_db_cursor = self.category_db_connect.cursor()

        self.icon_data_dir = os.path.join(UPDATE_DATA_DIR, "icon")
        
        self.category_dict = {}
        self.category_name_dict = {}
        
        #self.build_category_dict()

    def get_software_obj(self, pkg_name):
        try:
            soft = Software.select().where(Software.pkg_name == pkg_name, Software.language == self.current_lang_obj).get()
        except:
            soft = None
        return soft

    def init_cache_soft_db(self):
        if self.is_cache_soft_db_exists() and not hasattr(self, 'cache_soft_db_cursor'):
            self.cache_soft_db_connect = sqlite3.connect(CACHE_SOFT_DB_PATH, check_same_thread = False)
            self.cache_soft_db_cursor = self.cache_soft_db_connect.cursor()

    def is_cache_soft_db_exists(self):
        return os.path.exists(CACHE_SOFT_DB_PATH)

    def get_info_from_cache_soft_db(self, argv):
        if self.is_cache_soft_db_exists():
            if not hasattr(self, 'cache_soft_db_cursor'):
                self.cache_soft_db_connect = sqlite3.connect(CACHE_SOFT_DB_PATH, check_same_thread = False)
                self.cache_soft_db_cursor = self.cache_soft_db_connect.cursor()
            self.cache_soft_db_cursor.execute(*argv)
            return self.cache_soft_db_cursor.fetchall()
        else:
            return []

    def get_pkgs_match_input(self, input_string):
        # Select package name match input string.

        input_string = input_string.lower()
        pkg_names = []
        argv = [
            "SELECT pkg_name FROM software WHERE pkg_name LIKE ?",
            ("%" + unicode(input_string) + "%",)
            ]

        cache_info = self.get_info_from_cache_soft_db(argv)
        if cache_info:
            for (pkg_name, ) in cache_info:
                pkg_names.append(pkg_name)
        else:
            search_key = "*%s*" % input_string
            software_list = Software.select().where(Software.pkg_name % search_key, Software.language==self.default_lang_obj)
            for soft in software_list:
                pkg_names.append(soft.pkg_name)

        # Sort package name.
        pkg_names = sorted(
            pkg_names,
            cmp=lambda pkg_name_a, pkg_name_b: self.sort_match_pkgs(pkg_name_a, pkg_name_b, input_string))    
            
        return pkg_names
    
    def sort_match_pkgs(self, pkg_name_a, pkg_name_b, input_string):
        start_with_a = pkg_name_a.startswith(input_string)
        start_with_b = pkg_name_b.startswith(input_string)
        
        if start_with_a and start_with_b:
            return cmp(pkg_name_a, pkg_name_b)
        elif start_with_a:
            return -1
        else:
            return 1

    def get_pkg_download_size(self, pkg_name, callback):
        self.bus_interface.get_download_size(
                pkg_name,
                reply_handler=lambda r: callback(r, True),
                error_handler=lambda e: callback(e, False)
                )
    def get_pkg_icon_path(self, pkg_name):
        pass
        
    def get_search_pkgs_info(self, pkg_names):
        pkg_infos = []
        for (index, pkg_name) in enumerate(pkg_names):
            self.desktop_db_cursor.execute(
                "SELECT desktop_path, icon_name, display_name FROM desktop WHERE pkg_name=?", [pkg_name])    
            desktop_infos = self.desktop_db_cursor.fetchall()
            pkg_infos.append([pkg_name, desktop_infos])
        
        return pkg_infos
    
    def get_pkg_desktop_info(self, desktops):
        app_infos = []
        all_app_infos = gio.app_info_get_all()
        for desktop in desktops:
            app_info = gio.unix.desktop_app_info_new_from_filename(desktop)
            if app_info:
                for item in all_app_infos:
                    if app_info.get_commandline() == item.get_commandline():
                        app_infos.append(app_info)
        return app_infos
    
    def get_pkg_installed(self, pkg_name, callback):
        self.desktop_db_cursor.execute("SELECT start_pkg_names FROM package WHERE pkg_name=?", (pkg_name,))
        start_pkg_names = self.desktop_db_cursor.fetchone()
        if start_pkg_names:
            start_pkg_names = start_pkg_names[0]
        else:
            start_pkg_names = ""
        self.bus_interface.get_pkg_start_status(pkg_name, start_pkg_names,
                reply_handler=lambda r: callback(r, True),
                error_handler=lambda e: callback(e, False)
                )
        
    def get_pkg_detail_info(self, pkg_name):
        result = {
                'category': None,
                'recommend_pkgs': [],
                'long_desc': 'Unknown',
                'version': 'Unknown',
                'homepage': '',
                'alias_name': pkg_name,
                }

        # get category, recommend_pkgs
        self.desktop_db_cursor.execute(
            "SELECT first_category_name, second_category_name FROM package WHERE pkg_name=?", [pkg_name])
        category_names = self.desktop_db_cursor.fetchone()
        if category_names and category_names[0] and category_names[1]:
            result['category'] = category_names

        # get long_desc, version, homepage, alias_name
        soft = self.get_software_obj(pkg_name)
        if soft:
            result["long_desc"] = soft.long_desc
            result["alias_name"] = soft.alias_name

        cache_info = self.get_cache_info(pkg_name)
        if cache_info:
            if result['long_desc'] == 'Unknown':
                result['long_desc'] = cache_info[0][0]
            result['version'] = cache_info[0][1]
            result['homepage'] = cache_info[0][2]
        return result

    def get_cache_info(self, pkg_name):
        cache_info = None
        for name in [pkg_name, pkg_name + ":i386"]:
            cache_info = self.get_info_from_cache_soft_db([
                "SELECT long_desc, version, homepage FROM software WHERE pkg_name=?",
                [name]])
            if cache_info:
                return cache_info
        return cache_info
        
    def get_pkg_search_info(self, pkg_name):
        result = self.get_software_obj(pkg_name)

        if result == None:
            cache_info = self.get_info_from_cache_soft_db([
                "SELECT short_desc, long_desc FROM software WHERE pkg_name=?",
                [pkg_name]])
            if cache_info:
                (short_desc, long_desc) = cache_info[0]
                return (pkg_name, short_desc, long_desc, 5.0)
            else:
                return (pkg_name, "FIXME", "FIXME", 5.0)
        else:
            #(alias_name, short_desc, long_desc) = result
            return (result.alias_name, result.short_desc, result.long_desc, 5.0)
    
    def get_item_pkg_info(self, pkg_name):
        result = self.get_software_obj(pkg_name)
        if result:
            info = [result.pkg_name, result.alias_name, result.short_desc, result.long_desc]
        else:
            info = None


        if info != None and info[2] != "":
            return info
        else:
            r = self.get_info_from_cache_soft_db(["SELECT short_desc, long_desc FROM software WHERE pkg_name=?", (pkg_name, )])
            if r:
                return [pkg_name, pkg_name, r[0][0], r[0][1]]
            else:
                return [pkg_name, pkg_name, "", ""]
    
    def get_item_pkgs_info(self, pkg_names):
        infos = []
        for (index, pkg_name) in enumerate(pkg_names):
            infos.append(self.get_item_pkg_info(pkg_name))
        return infos    
    
    def is_pkg_have_desktop_file(self, pkg_name):
        self.desktop_db_cursor.execute(
            "SELECT id FROM package WHERE pkg_name=?", [pkg_name])
        r = self.desktop_db_cursor.fetchone()
        if r:
            return True
        else:
            if pkg_name.endswith(":i386"):
                pkg_name = pkg_name[:-5]
                self.desktop_db_cursor.execute(
                    "SELECT id FROM package WHERE pkg_name=?", [pkg_name])
                return self.desktop_db_cursor.fetchone()
            else:
                return False

    def get_display_flag(self, pkg_name):
        self.desktop_db_cursor.execute(
            "SELECT display_flag, first_category_name FROM package WHERE pkg_name=?", (pkg_name, ))
        r = self.desktop_db_cursor.fetchone()
        if r:
            return r[0] and r[1]
        else:
            return False

    def is_pkg_display_in_uninstall_page(self, pkg_name):
        if self.get_display_flag(pkg_name):
            return True
        else:
            if pkg_name.endswith(":i386"):
                pkg_name = pkg_name[:-5]
                return self.get_display_flag(pkg_name)
            else:
                return False
    
    def get_album_info(self):
        self.album_db_cursor.execute(
            "SELECT album_id, album_name, album_summary FROM album ORDER BY album_id")
        return self.album_db_cursor.fetchall()
    
    def get_download_rank_info(self, pkg_names):
        infos = []

        for pkg_name in pkg_names:
            info =self.get_software_obj(pkg_name)

            if info:
                alias_name = info.alias_name
                self.desktop_db_cursor.execute(
                    "SELECT desktop_path, icon_name, display_name FROM desktop WHERE pkg_name=?", [pkg_name])    
                desktop_infos = self.desktop_db_cursor.fetchall()
                
                infos.append([pkg_name, alias_name, 5.0, desktop_infos])
            
        return infos

    def get_recommend_info(self):
        pkgs = []
        with open(self.recommend_db_path) as fp:
            for line in fp:
                pkgs.append(line.strip())
        return pkgs

    def get_slide_info(self):
        pkgs = []
        with open(self.slide_db_path) as fp:
            for line in fp:
                pkgs.append(line.strip())
        return pkgs
    
    def build_category_dict(self):
        # Build OrderedDict of first category.
        self.category_db_cursor.execute(
            "SELECT DISTINCT first_category_name FROM category_name ORDER BY first_category_index")
        self.category_dict = OrderedDict(map(lambda names: (names[0], []), self.category_db_cursor.fetchall()))
        
        # Build list of second category. 
        self.category_db_cursor.execute(
            "SELECT DISTINCT first_category_name, second_category_name FROM category_name ORDER BY second_category_index")
        for (first_category, second_category) in self.category_db_cursor.fetchall():
            self.category_dict[first_category] = self.category_dict[first_category] + [(second_category, OrderedDict())]
            
        # Bulid OrderedDict of second category.
        for (first_category, second_category_list) in self.category_dict.items():
            self.category_dict[first_category] = OrderedDict(second_category_list)

        # Fill data into category dict.
        self.category_name_dict = OrderedDict()
        self.category_db_cursor.execute(
            "SELECT first_category_index, second_category_index, first_category_name, second_category_name FROM category_name")
        for (first_category_index, second_category_index, first_category, second_category) in self.category_db_cursor.fetchall():
            self.category_name_dict[(first_category_index, second_category_index)] = (first_category, second_category)

    def get_first_category(self):
        return CATEGORY_TYPE_DICT.keys()

    def get_second_category(self, first_category_name):
        return CATEGORY_TYPE_DICT.get(first_category_name).keys()

    def get_first_category_packages(self, first_category_name):
        self.desktop_db_cursor.execute(
            "SELECT pkg_name FROM package WHERE first_category_name=? ORDER BY pkg_name", (first_category_name,))
        r = self.desktop_db_cursor.fetchall()
        return map(lambda s: s[0], r)

    def get_second_category_packages(self, second_category_name):
        self.desktop_db_cursor.execute(
            "SELECT pkg_name FROM package WHERE second_category_name=? ORDER BY pkg_name", (second_category_name,))
        r = self.desktop_db_cursor.fetchall()
        return map(lambda s: s[0], r)
                
    def search_query(self, keywords):
        '''
        init docs
        '''
        # Init search connect.
        search_db_path = os.path.join(UPDATE_DATA_DIR, "search", "zh_CN", "search_db")
        sconn = xappy.SearchConnection(search_db_path)
        
        # Do search.
        search = ' '.join(keywords).lower()
        q = sconn.query_parse(search, default_op=sconn.OP_AND)
        results = sconn.search(q, 0, sconn.get_doccount(), sortby="have_desktop_file")
        
        all_results = map(lambda result: result.data["pkg_name"][0], results)
        for keyword in keywords:
            match_names = self.get_pkgs_match_input(keyword)
            for name in match_names:
                if name not in all_results:
                    all_results.append(name)
        return all_results

    def change_source_list(self, repo_urls, reply_handler, error_handler):
        self.bus_interface.change_source_list(repo_urls,
                reply_handler=reply_handler, 
                error_handler=error_handler)
        
if __name__ == "__main__":
    import dbus
    from constant import DSC_SERVICE_NAME, DSC_SERVICE_PATH
    system_bus = dbus.SystemBus()
    bus_object = system_bus.get_object(DSC_SERVICE_NAME, DSC_SERVICE_PATH)
    bus_interface = dbus.Interface(bus_object, DSC_SERVICE_NAME)

    data_manager = DataManager(bus_interface)
