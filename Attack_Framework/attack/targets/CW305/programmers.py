# -*- coding: utf-8 -*-
#
# Copyright (c) 2014, NewAE Technology Inc
# All rights reserved.
#
# Authors: Colin O'Flynn
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, http://www.assembla.com/spaces/chipwhisperer
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
# =================================================
import logging
from . import util


from functools import wraps

_logger = logging.getLogger(__name__)


class Programmer(object):
    lastFlashedFile = "unknown"
    _scope = None
    pin_setup = {}

    def __init__(self):
        self.newTextLog = util.Signal()
        self._scope = None

    @property
    def scope(self):
        if self._scope:
            return self._scope

        # No scope object so we won't toggle pins
        return None

    @scope.setter
    def scope(self, value):
        self._scope = value

    def save_pin_setup(self):
        self.pin_setup["pdic"] = self.scope.io.pdic
        self.pin_setup["pdid"] = self.scope.io.pdid
        self.pin_setup["nrst"] = self.scope.io.nrst

    def restore_pin_setup(self):
        self.scope.io.pdic = self.pin_setup["pdic"]
        self.scope.io.pdid = self.pin_setup["pdid"]
        self.scope.io.nrst = self.pin_setup["nrst"]

    def set_pins(self):
        raise NotImplementedError

    def setUSBInterface(self, iface):
        raise DeprecationWarning("find method now includes what setUSBInterface did")

    def find(self):
        raise NotImplementedError

    def program(self, filename, memtype="flash", verify=True):
        raise NotImplementedError

    def erase(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def log(self, text):
        """Logs the text and broadcasts it"""
        _logger.info(text)
        self.newTextLog.emit(text)

    def autoProgram(self, hexfile, erase, verify, logfunc, waitfunc):
        raise NotImplementedError
