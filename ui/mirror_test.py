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
import sys
import threading
import aptsources
import aptsources.distro
import urllib2
import time
from urlparse import urlparse
import traceback

from deepin_utils.file import get_parent_dir
from deepin_utils.config import Config

from constant import LANGUAGE
from logger import Logger

root_dir = get_parent_dir(__file__, 2)
mirrors_dir = os.path.join(root_dir, 'mirrors')

def get_mirrors():
    mirrors = []
    for f in os.listdir(mirrors_dir):
        if f.endswith(".ini"):
            ini_file = os.path.join(mirrors_dir, f)
            m = Mirror(ini_file)
            mirrors.append(m)
    return mirrors

class Mirror(object):
    def __init__(self, ini_file):
        self.config = Config(ini_file)
        self.config.load()
        deepin_url = self.get_repo_urls()[1]
        _url_parse = urlparse(deepin_url)
        self._hostname = _url_parse.scheme + "://" + _url_parse.netloc
        self._priority = float(self.config.get("mirror", "priority")) if self.config.has_option("mirror", "priority") else 100
    
    @property
    def hostname(self):
        return self._hostname

    @property
    def name(self):
        if self.config.has_option('mirror', 'name[%s]' % LANGUAGE):
            return self.config.get('mirror', 'name[%s]' % LANGUAGE)
        else:
            return self.config.get('mirror', 'name[%s]' % 'en_US')

    @property
    def priority(self):
        return self._priority

    def get_repo_urls(self):
        return (self.config.get('mirror', 'ubuntu_url'), self.config.get('mirror', 'deepin_url'))

class MirrorTest(Logger):
    def __init__(self, hostnames):
        self.hostnames = hostnames
        self._stop = False
        self._cancel = False
        self._mirrors = []

    def cancel(self):
        self._cancel = True

    def init_mirrors(self):
        all_mirrors_list = get_mirrors()
        for hostname in self.hostnames:
            url = "http://" + hostname
            for m in all_mirrors_list:
                if url in m.hostname:
                    self._mirrors.append(m)

    def timer_out_callback(self):
        self._stop = True

    def run(self):
        self.init_mirrors()
        result = []
        for m in self._mirrors:
            if self._cancel:
                return ""
            speed = self.get_speed(m)
            result.append((speed, m.hostname))
        sorted_result = sorted(result, key=lambda r: r[0])
        best_hostname = sorted_result[-1][-1]
        self.loginfo("Best hostname: %s" % best_hostname)
        return best_hostname

    def get_speed(self, mirror):
        deepin_url = mirror.get_repo_urls()[1]
        if deepin_url.endswith("/"):
            deepin_url = deepin_url[:-1]
        distro = aptsources.distro.get_distro()
        download_url = "%s/dists/%s/Contents-amd64" % (deepin_url, distro.codename)
        request = urllib2.Request(download_url, None)
        try:
            conn = urllib2.urlopen(request, timeout=10)
        except Exception, e:
            self.logerror("Error for host: %s %s" % (mirror.hostname, e))
            return 0
        total_data = ""
        self._stop = False
        self._timer = threading.Timer(10, self.timer_out_callback)
        self._timer.start()
        start_time = time.time()
        try_times = 6
        while not self._cancel and try_times > 0:
            try:
                data = conn.read(1024)
                if len(data) == 0 or self._stop:
                    break
                else:
                    total_data += data
            except:
                try_times -= 1
        if self._timer.isAlive():
            self._timer.cancel()
        self._timer = None
        total_time = time.time() - start_time
        speed = len(total_data)/total_time
        self.loginfo("Speed for host: %s %s" % (mirror.hostname, speed))
        return speed

if __name__ == "__main__":
    now = time.time()
    t = MirrorTest([u'mirrors.hust.edu.cn', u'packages.linuxdeepin.com', u'mirrors.ustc.edu.cn', u'test.packages.linuxdeepin.com', u'mirrors.jstvu.edu.cn'])
    print t.run()
    print "Total Time:", time.time() - now
