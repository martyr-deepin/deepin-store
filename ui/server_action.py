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

import threading as td
import urllib2
import urllib
import json
from constant import SERVER_ADDRESS, POST_TIMEOUT
from events import global_event

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
            
            urllib2.urlopen(
                "%s/softcenter/v1/analytics" % (SERVER_ADDRESS),
                data=urllib.urlencode(args),
                timeout=POST_TIMEOUT
                )
            print "Send download count (%s) successful." % (self.pkgName)
        except Exception, e:
            print "Send download count (%s) failed." % (self.pkgName)
            print "Error: ", e
