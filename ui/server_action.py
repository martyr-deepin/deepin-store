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
import threading as td
import urllib2
import urllib
import json
from constant import SERVER_ADDRESS, POST_TIMEOUT
from events import global_event
import traceback
from deepin_utils.file import create_directory
from utils import get_recommend_mode

DEBUG = False

BAIDU_SERVER_ADDRESS = 'http://dschomedata.duapp.com/' if not DEBUG else 'http://127.0.0.1:8000/'
UPYUN_SERVER_ADDRESS = 'http://dsc-home-data.b0.upaiyun.com/'

CACHE_DIR = os.path.join(os.path.expanduser("~"), '.cache', 'deepin-software-center')
create_directory(CACHE_DIR)

status = get_recommend_mode()

class FetchAlbumData(td.Thread):

    def __init__(self, language, debug_flag=False):
        td.Thread.__init__(self)
        self.language = language
        self.album_data_url = BAIDU_SERVER_ADDRESS + "album/"
        self.data = {
                'hl': language if language != 'zh_HK' else 'zh_TW',
                'status': status,
                }
        self.setDaemon(True)

    def run(self):
        json_data = None
        try:
            query = urllib.urlencode(self.data)
            request_url = ("%s?%s") % (self.album_data_url, query)
            connection = urllib2.urlopen(
                request_url,
                timeout=POST_TIMEOUT,
            )
            json_data = json.loads(connection.read())            
        except Exception, e:
            traceback.print_exc(file=sys.stdout)
            print "Fetch album data failed: %s." % (e)
        global_event.emit("download-album-infos-finish", json_data)

class FetchHomeData(td.Thread):

    def __init__(self, language, callback_method=None):
        td.Thread.__init__(self)
        self.callback_method = callback_method
        self.language = language
        self.home_data_url = BAIDU_SERVER_ADDRESS + "home/"
        self.data = {
                'hl': language if language != 'zh_HK' else 'zh_TW',
                'status': status,
                }
        self.setDaemon(True)

    def run(self):
        json_data = None
        try:
            query = urllib.urlencode(self.data)
            request_url = ("%s?%s") % (self.home_data_url, query)
            connection = urllib2.urlopen(
                request_url,
                timeout=POST_TIMEOUT,
            )
            json_data = json.loads(connection.read())            
            if self.callback_method:
                self.callback_method(json_data)
        except Exception, e:
            if self.callback_method:
                self.callback_method(None)
            traceback.print_exc(file=sys.stdout)
            print "Fetch home data failed: %s." % (e)
        global_event.emit("download-home-infos-finish", json_data)

class FetchImageFromUpyun(td.Thread):
    
    def __init__(self, image_path, callback_method=None):
        td.Thread.__init__(self)
        self.callback_method = callback_method
        self.remote_url = UPYUN_SERVER_ADDRESS + image_path
        self.local_path = os.path.join(CACHE_DIR, image_path)
        create_directory(os.path.dirname(self.local_path))
        self.setDaemon(True)

    def run(self):
        if os.path.exists(self.local_path):
            self.callback_method(self.local_path)
            return
        try:
            urllib.urlretrieve(self.remote_url, self.local_path)
            self.callback_method(self.local_path)

        except Exception, e:
            traceback.print_exc(file=sys.stdout)
            print "Download image error: %s" % e

class FetchVoteInfo(td.Thread):
    '''Fetch vote.'''

    def __init__(self, pkgName, updateVoteCallback):
        '''Init for fetch vote.'''
        td.Thread.__init__(self)
        self.setDaemon(True) # make thread exit when main program exit

        self.pkgName = pkgName
        self.updateVoteCallback = updateVoteCallback

    def run(self):
        '''Run.'''
        try:
            args = {'n' : self.pkgName, "t" : "vote"}
            connection = urllib2.urlopen(
                "%s/softcenter/v1/mark" % (SERVER_ADDRESS),
                data=urllib.urlencode(args),
                timeout=POST_TIMEOUT
                )
            voteJson = json.loads(connection.read())            
            self.updateVoteCallback(voteJson[self.pkgName])
        except Exception, e:
            print "Fetch vote data failed: %s." % (e)

class SendVote(td.Thread):
    '''Vote'''

    def __init__(self, name, vote):
        '''Init for vote.'''
        td.Thread.__init__(self)
        self.setDaemon(True) # make thread exit when main program exit
        self.name = name
        self.vote = vote

    def run(self):
        '''Run'''
        try:
            args = {'n' : self.name, 'm' : self.vote}
            urllib2.urlopen(
                "%s/softcenter/v1/mark" % (SERVER_ADDRESS),
                data=urllib.urlencode(args),
                timeout=POST_TIMEOUT
                )
            global_event.emit('vote-send-success', self.name)
        except Exception, e:
            global_event.emit('vote-send-failed', self.name)
            print "Error: ", e

class SendUninstallCount(td.Thread):
    '''Send uninstall count.'''
	
    def __init__(self, pkgName):
        '''Init for vote.'''
        td.Thread.__init__(self)
        self.setDaemon(True)
        self.pkgName = pkgName

    def run(self):
        '''Run'''
        try:
            args = {'a' : 'u', 'n' : self.pkgName}
            
            urllib2.urlopen(
                "%s/softcenter/v1/analytics" % (SERVER_ADDRESS),
                data=urllib.urlencode(args),
                timeout=POST_TIMEOUT
                )
            print "Send uninstall count (%s) successful." % (self.pkgName)
        except Exception, e:
            print "Send uninstall count (%s) failed." % (self.pkgName)
            print "Error: ", e


class SendDownloadCount(td.Thread):
    '''Send download count.'''
	
    def __init__(self, pkgName):
        '''Init for vote.'''
        td.Thread.__init__(self)
        self.setDaemon(True) # make thread exit when main program exit 
        self.pkgName = pkgName

    def run(self):
        '''Run'''
        try:
            args = {
                'a' : 'd', 
                'n' : self.pkgName}
            
            result = urllib2.urlopen(
                "%s/softcenter/v1/analytics" % (SERVER_ADDRESS),
                data=urllib.urlencode(args),
                timeout=POST_TIMEOUT
                )
            print "Send download count (%s) successful." % (self.pkgName)
            print "Result:", result.read()
        except Exception, e:
            print "Send download count (%s) failed." % (self.pkgName)
            print "Error: ", e

class FetchPackageInfo(td.Thread):
    def __init__(self, pkg_name, callback_method):
        td.Thread.__init__(self)
        self.setDaemon(True)
        self.pkg_name = pkg_name
        self.callback_method = callback_method

    def run(self):
        try:
            con = urllib2.urlopen(
                    "%s/softcenter/v1/soft?a=info&r=%s" % (SERVER_ADDRESS, self.pkg_name),
                    timeout=POST_TIMEOUT
                    )
            r = con.read()
            self.callback_method(json.loads(r))
        except Exception, e:
            print 'Get %s info failed.' % self.pkg_name
            print 'Error Info:', e
