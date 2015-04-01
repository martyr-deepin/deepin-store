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
import apt.progress.text
import apt.progress.base
import apt_pkg

from events import global_event
import utils
from dtk.ui.thread_pool import MissionThread

from constant import UPDATE_LIST_LOG_PATH

_ = lambda s:s

class AcquireProgress(apt.progress.base.AcquireProgress):
    """AcquireProgress for the text interface."""

    def __init__(self, outfile=None):
        apt.progress.base.AcquireProgress.__init__(self)
        self.percent = 0
        self.status_message = ''
        self._id = long(1)

    def ims_hit(self, item):
        """Called when an item is update (e.g. not modified on the server)."""
        apt.progress.base.AcquireProgress.ims_hit(self, item)
        line = _('Hit ') + item.description
        if item.owner.filesize:
            line += ' [%sB]' % apt_pkg.size_to_str(item.owner.filesize)
        self.status_message = line

    def fail(self, item):
        """Called when an item is failed."""
        apt.progress.base.AcquireProgress.fail(self, item)
        if item.owner.status == item.owner.STAT_DONE:
            self.status_message = _("Ign ") + item.description
        else:
            self.status_message =  _("Err ") + item.description

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

    def pulse(self, owner):
        """Periodically invoked while the Acquire process is underway.

        Return False if the user asked to cancel the whole Acquire process."""
        apt.progress.base.AcquireProgress.pulse(self, owner)
        self.percent = (((self.current_bytes + self.current_items) * 100.0) /
                        float(self.total_bytes + self.total_items))

        end = ""
        if self.current_cps:
            eta = long(float(self.total_bytes - self.current_bytes) /
                        self.current_cps)
            end = " %sB/s %s" % (apt_pkg.size_to_str(self.current_cps),
                                 apt_pkg.time_to_str(eta))

        global_event.emit("update-list-update", self.percent, self.status_message, end)
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
        utils.set_last_update_time()
        utils.logger.info("Cache update list start!")

        log_file = open(UPDATE_LIST_LOG_PATH, 'ab')
        progress = AcquireProgress(log_file)
        try:
            self.pkg_cache.update(progress)
            if int(progress.percent) == 0:
                global_event.emit("update-list-failed")
                utils.logger.error("update list failed!")
            else:
                self.pkg_cache.open(None)
                global_event.emit("update-list-finish")
                utils.logger.info("update list finish")
        except Exception, e:
            global_event.emit("update-list-failed")
            failed_message = "Cache update list failed: %s" % e
            utils.logger.error(failed_message)

if __name__ == "__main__":
    import gtk
    gtk.gdk.threads_init()
    UpdateList().start()
    gtk.main()
