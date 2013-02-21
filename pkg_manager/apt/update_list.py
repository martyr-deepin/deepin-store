#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 ~ 2012 Deepin, Inc.
#               2011 ~ 2012 Wang Yong
# 
# Author:     Wang Yong <lazycat.manatee@gmail.com>
# Maintainer: Wang Yong <lazycat.manatee@gmail.com>
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

from apt.progress.old import FetchProgress
from deepin_utils.net import is_network_connected
import threading as td
from events import global_event
import time

class UpdateListProgress(FetchProgress):
    """ Ready to use progress object for terminal windows """

    def __init__(self):
        super(UpdateListProgress, self).__init__()

    def pulse(self):
        """Called periodically to update the user interface.

        Return True to continue or False to cancel.
        """
        try:
            self.percent = (((self.currentBytes + self.currentItems) * 100.0) /
                            float(self.totalBytes + self.totalItems))
            if self.currentCPS > 0:
                self.eta = ((self.totalBytes - self.currentBytes) /
                            float(self.currentCPS))
                
            global_event.emit("update-list-update", self.percent)
        except Exception, e:
            print "UpdateListProgress.pulse(): %s" % (e)
        
        return True
    
class UpdateList(td.Thread):
    '''Update package list.'''
	
    def __init__(self, pkg_cache, simulate=False):
        '''Init for UpdateList.'''
        td.Thread.__init__(self)
        self.setDaemon(True) # make thread exit when main program exit
        
        self.pkg_cache = pkg_cache
        self.simulate = simulate
        
        self.simulate_update_counter = 0
        self.simulate_update_delay = 0.01 # milliseconds
        # self.simulate_update_delay = 0.1 # milliseconds
        
    def run(self):
        '''Update package list.'''
        if is_network_connected():
            try:
                global_event.emit("update-list-start")
                
                if self.simulate:
                # if True:
                    while self.simulate_update_counter <= 100:
                        global_event.emit("update-list-update", self.simulate_update_counter)
                        
                        time.sleep(self.simulate_update_delay)
                        
                        self.simulate_update_counter += 1
                else:
                    progress = UpdateListProgress()
                    self.pkg_cache.cache.update(progress)
                
                global_event.emit("update-list-finish")
            except Exception, e:
                print "UpdateList.run(): %s" % (e)
                
                global_event.emit("update-list-failed")
    
if __name__ == "__main__":
    import gtk
    gtk.gdk.threads_init()
    
    UpdateList().start()

    gtk.main()
