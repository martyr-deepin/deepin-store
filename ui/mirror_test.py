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

import time
import threading
import aptsources
import aptsources.distro
from aptsources.sourceslist import SourcesList
import urllib2
import os
from deepin_utils.file import get_parent_dir
from deepin_utils.config import Config
from constant import LANGUAGE
from urlparse import urlparse

root_dir = get_parent_dir(__file__, 2)
mirrors_dir = os.path.join(root_dir, 'mirrors')

class Mirror(object):
    def __init__(self, ini_file):
        self.config = Config(ini_file)
        self.config.load()
        deepin_url = self.get_repo_urls()[1]
        _url_parse = urlparse(deepin_url)
        self._hostname = _url_parse.scheme + "://" + _url_parse.netloc
        self._priority = int(self.config.get("mirror", "priority")) if self.config.has_option("mirror", "priority") else 100
    
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

class MirrorTest(threading.Thread):
    """Determines the best mirrors by perfoming ping and download test."""

    def __init__(self, mirrors, test_file):
        threading.Thread.__init__(self)
        self.action = ''
        self.progress = (0, 0, 0.0) # cur, max, %
        self.best = None
        self.test_file = test_file
        self.mirrors = mirrors
        self.running = False
        self.terminated = False

    def report_action(self, text):
        self.action = text

    def report_progress(self, current, max):
        self.progress = (current, 
                         max,
                         current*1.0/max)

    def run_full_test(self):
        results = self.run_download_test(self.mirrors)

        if not results:
            return None
        else:
            for r in results:
                print "mirror: %s - time: %s" % (r[1].hostname, r[0])
            print "winner:", results[0][1].hostname

            return results[0]

    def run_download_test(self, mirrors=None):

        def test_download_speed(mirror):
            url = "%s/%s" % (mirror.get_repo_urls()[0],
                             self.test_file)
            self.report_action("正在测试: %s" % mirror.get_repo_urls()[0])
            start = time.time()
            try:
                urllib2.urlopen(url, timeout=2).read(102400)
                return time.time() - start
            except:
                return 0

        if mirrors == None:
            mirrors = self.mirrors
        results = []

        for m in mirrors:
            if self.terminated:
                return []
            download_time = test_download_speed(m)
            if download_time > 0:
                results.append([download_time, m])
            self.report_progress(mirrors.index(m) + 1, len(mirrors))
        results.sort()
        return results

    def run(self):
        """Complete test exercise, set self.best when done"""
        self.running = True
        self.best = self.run_full_test()
        self.running = False

def test_mirrors(mirrors_list):
    distro = aptsources.distro.get_distro()
    distro.get_sources(SourcesList())
    pipe = os.popen("dpkg --print-architecture")
    arch = pipe.read().strip()
    test_file = "dists/%s/%s/binary-%s/Packages.gz" % \
                (
                #distro.source_template.name,
                "quantal",
                distro.source_template.components[0].name,
                arch)

    app = MirrorTest(mirrors_list,
                     test_file,
                     )
    results = app.run_download_test()
    winner = [100, None]
    print results
    for r in results:
        if r[0] < winner[0]:
            winner = r
    return winner

if __name__ == "__main__":
    mirrors_list = []
    for ini_file in os.listdir(mirrors_dir):
        m = Mirror(os.path.join(mirrors_dir, ini_file))
        mirrors_list.append(m)
    print test_mirrors(mirrors_list)
