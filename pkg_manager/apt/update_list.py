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

import apt
import apt.progress.old
import apt.progress.text
import apt.progress.base
import apt_pkg

from events import global_event
from utils import log
from dtk.ui.thread_pool import MissionThread

from constant import UPDATE_LIST_LOG_PATH

_ = lambda s:s

class AcquireProgress(apt.progress.text.AcquireProgress):
    """AcquireProgress for the text interface."""

    def __init__(self, outfile=None):
        apt.progress.text.AcquireProgress.__init__(self, outfile)
        self.percent = 0
        self.status_message = ''

    def ims_hit(self, item):
        """Called when an item is update (e.g. not modified on the server)."""
        apt.progress.base.AcquireProgress.ims_hit(self, item)
        line = _('Hit ') + item.description
        if item.owner.filesize:
            line += ' [%sB]' % apt_pkg.size_to_str(item.owner.filesize)
        self.status_message = line
        self._write(self.status_message)

    def fail(self, item):
        """Called when an item is failed."""
        apt.progress.base.AcquireProgress.fail(self, item)
        if item.owner.status == item.owner.STAT_DONE:
            self.status_message = _("Ign ") + item.description
            self._write(self.status_message)
        else:
            self.status_message =  _("Err ") + item.description
            self._write(self.status_message)
            self._write("  %s" % item.owner.error_text)

    def fetch(self, item):
        """Called when some of the item's data is fetched."""
        apt.progress.base.AcquireProgress.fetch(self, item)
        # It's complete already (e.g. Hit)
        if item.owner.complete:
            return
        item.owner.id = self._id
        self._id += 1
        line = _("Get:") + "%s %s" % (item.owner.id, item.description)
        if item.owner.filesize:
            line += (" [%sB]" % apt_pkg.size_to_str(item.owner.filesize))

        self.status_message = line
        self._write(self.status_message)

    def pulse(self, owner):
        """Periodically invoked while the Acquire process is underway.

        Return False if the user asked to cancel the whole Acquire process."""
        apt.progress.base.AcquireProgress.pulse(self, owner)
        self.percent = (((self.current_bytes + self.current_items) * 100.0) /
                        float(self.total_bytes + self.total_items))

        global_event.emit("update-list-update", self.percent, self.status_message)
        return True

class UpdateList(MissionThread):
    '''Update package list.'''
	
    def __init__(self, pkg_cache, simulate=False):
        '''Init for UpdateList.'''
        MissionThread.__init__(self)
        self.pkg_cache = pkg_cache
        
    def start_mission(self):
        '''Update package list.'''
        global_event.emit("update-list-start")
        log("Cache update list start!")
        
        log_file = open(UPDATE_LIST_LOG_PATH, 'ab')
        progress = AcquireProgress(log_file)
        try:
            self.pkg_cache.update(progress)
            if int(progress.percent) == 0:
                global_event.emit("update-list-failed")
                log("update list failed!")
            else:
                global_event.emit("update-list-finish")
                log("update list finish")
                self.pkg_cache.open(None)
        except apt.cache.FetchFailedException, e:
            global_event.emit("update-list-failed")
            failed_message = "Cache update list failed: %s" % e
            log(failed_message)
            progress._write(failed_message)
    
if __name__ == "__main__":
    import gtk
    gtk.gdk.threads_init()
    UpdateList().start()
    gtk.main()
