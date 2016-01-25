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
from deepin_utils.file import get_parent_dir

import time
from Queue import Queue
from threading import Thread

from data import DATA_ID
from constant import LANGUAGE
from category import CATEGORY_TYPE_DICT

UPDATE_DATA_DIR = os.path.join(get_parent_dir(__file__, 2), "data", "update", DATA_ID)
CACHE_SOFT_DB_PATH = os.path.join(get_parent_dir(__file__, 2), "data", "cache_soft.db")

DATA_SUPPORT_LANGUAGE = ['en_US', 'zh_CN', 'zh_TW']

class SqliteMultithread(Thread):
    """
    Wrap sqlite connection in a way that allows concurrent requests from multiple threads.

    This is done by internally queueing the requests and processing them sequentially
    in a separate thread (in the same order they arrived).

    """
    def __init__(self, filename, autocommit=False, journal_mode="OFF"):
        super(SqliteMultithread, self).__init__()
        self.filename = filename
        self.autocommit = autocommit
        self.journal_mode = journal_mode
        self.reqs = Queue() # use request queue of unlimited size
        self.setDaemon(True) # python2.5-compatible
        self.start()

    def run(self):
        if self.autocommit:
            conn = sqlite3.connect(self.filename, isolation_level=None, check_same_thread=False)
        else:
            conn = sqlite3.connect(self.filename, check_same_thread=False)
        conn.execute('PRAGMA journal_mode = %s' % self.journal_mode)
        conn.text_factory = str
        cursor = conn.cursor()
        cursor.execute('PRAGMA synchronous=OFF')
        while True:
            req, arg, res = self.reqs.get()
            if req == '--close--':
                break
            elif req == '--commit--':
                conn.commit()
            else:
                cursor.execute(req, arg)
                if res:
                    for rec in cursor:
                        res.put(rec)
                    res.put('--no more--')
                if self.autocommit:
                    conn.commit()
        conn.close()

    def execute(self, req, arg=None, res=None):
        """
        `execute` calls are non-blocking: just queue up the request and return immediately.

        """
        self.reqs.put((req, arg or tuple(), res))

    def executemany(self, req, items):
        for item in items:
            self.execute(req, item)

    def select(self, req, arg=None):
        """
        Unlike sqlite's native select, this select doesn't handle iteration efficiently.

        The result of `select` starts filling up with values as soon as the
        request is dequeued, and although you can iterate over the result normally
        (`for res in self.select(): ...`), the entire result will be in memory.

        """
        res = Queue() # results of the select will appear as items in this queue
        self.execute(req, arg, res)
        while True:
            rec = res.get()
            if rec == '--no more--':
                break
            yield rec

    def select_one(self, req, arg=None):
        """Return only the first row of the SELECT, or None if there are no matching rows."""
        try:
            return iter(self.select(req, arg)).next()
        except StopIteration:
            return None

    def commit(self):
        self.execute('--commit--')

    def close(self):
        self.execute('--close--')

def db_path_exists(path):
    if not os.path.exists(path):
        print "Database not exist:", path
        sys.exit(1)

class DataManager(object):
    def __init__(self, bus_interface, debug_flag=False):
        '''
        init docs
        '''
        self.bus_interface = bus_interface
        self.debug_flag = debug_flag

        self.language = LANGUAGE if LANGUAGE in DATA_SUPPORT_LANGUAGE else 'en_US'

        software_db_path = os.path.join(UPDATE_DATA_DIR, "software", self.language, "software.db")
        db_path_exists(software_db_path)
        self.software_db_cursor = SqliteMultithread(software_db_path)

        desktop_db_path = os.path.join(UPDATE_DATA_DIR, "desktop", "desktop2014.db")
        db_path_exists(desktop_db_path)
        self.desktop_db_cursor = SqliteMultithread(desktop_db_path)

        category_db_path = os.path.join(UPDATE_DATA_DIR, "category", "category.db")
        db_path_exists(category_db_path)
        self.category_db_cursor = SqliteMultithread(category_db_path)

        self.icon_data_dir = os.path.join(UPDATE_DATA_DIR, "icon")

        self.category_dict = {}
        self.category_name_dict = {}

    def get_software_info(self, pkg_name):
        req = "SELECT pkg_name, alias_name, short_desc, long_desc FROM software WHERE pkg_name=?"
        return self.software_db_cursor.select_one(req, (pkg_name,))

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
        req = "SELECT pkg_name FROM software WHERE pkg_name LIKE ?"
        input_string = input_string.lower()
        search_key = "%" + unicode(input_string) + "%"

        cache_info = self.get_info_from_cache_soft_db([req, (search_key, )])
        if cache_info:
            pkg_names = map(lambda s: s[0], cache_info)
        else:
            res = self.software_db_cursor.select(req, (search_key, ))
            pkg_names = map(lambda s: s[0], res)

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
        req = "SELECT start_pkg_names FROM package WHERE pkg_name=?"
        start_pkg_names = self.desktop_db_cursor.select_one(req, (pkg_name,))
        if start_pkg_names != None:
            start_pkg_names = start_pkg_names[0]
        else:
            start_pkg_names = ""
        self.bus_interface.get_pkg_start_status(pkg_name, start_pkg_names,
                reply_handler=lambda r: callback(r, True),
                error_handler=lambda e: callback(e, False))

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
        req = "SELECT first_category_name, second_category_name FROM package WHERE pkg_name=?"
        category_names = self.desktop_db_cursor.select_one(req, (pkg_name,))
        if category_names and category_names[0] and category_names[1]:
            result['category'] = category_names

        # get long_desc, version, homepage, alias_name
        soft = self.get_software_info(pkg_name)
        if soft:
            result["alias_name"] = soft[1]
            result["long_desc"] = soft[3]

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
        result = self.get_software_info(pkg_name)

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
            return (result[1], result[2], result[3], 5.0)

    def get_item_pkg_info(self, pkg_name):
        info = self.get_software_info(pkg_name)
        if info and info[2] != "":
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
        req = "SELECT id FROM package WHERE pkg_name=?"
        res = self.desktop_db_cursor.select_one(req, (pkg_name,))
        if res:
            return True
        else:
            if pkg_name.endswith(":i386"):
                pkg_name = pkg_name[:-5]
                return bool(self.desktop_db_cursor.select_one(req, (pkg_name,)))
            else:
                return False

    def get_display_flag(self, pkg_name):
        req = "SELECT display_flag, first_category_name FROM package WHERE pkg_name=?"
        res = self.desktop_db_cursor.select_one(req, (pkg_name,))
        return bool(res) and bool(res[0]) and bool(res[1])

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

    def get_first_category(self):
        return CATEGORY_TYPE_DICT.keys()

    def get_second_category(self, first_category_name):
        return CATEGORY_TYPE_DICT.get(first_category_name).keys()

    def get_first_category_packages(self, first_category_name):
        req = "SELECT pkg_name FROM package WHERE first_category_name=? ORDER BY pkg_name"
        res = self.desktop_db_cursor.select(req, (first_category_name,))
        return map(lambda s: s[0], res)

    def get_second_category_packages(self, second_category_name):
        req = "SELECT pkg_name FROM package WHERE second_category_name=? ORDER BY pkg_name"
        res = self.desktop_db_cursor.select(req, (second_category_name,))
        return map(lambda s: s[0], res)

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
    start = time.time()
    print data_manager.get_item_pkg_info("evince")
    print time.time() - start
