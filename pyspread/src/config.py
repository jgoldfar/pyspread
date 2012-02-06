#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2011 Martin Manns
# Distributed under the terms of the GNU General Public License

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""
pyspread config file
====================

"""

from getpass import getuser

import wx

from sysvars import get_color, get_font_string

VERSION = "0.2.1"

"""
Program info
============

"""


class DefaultConfig(object):
    """Contains default config for starting pyspread without resource file"""

    def __init__(self):
        # User defined paths
        # ------------------

        standardpaths = wx.StandardPaths.Get()
        self.work_path = standardpaths.GetDocumentsDir()

        # Window configuration
        # --------------------

        self.window_position = "(10, 10)"
        self.window_size = "(wx.GetDisplaySize()[0] * 9 /10," + \
                           " wx.GetDisplaySize()[1] * 9 /10)"

        self.icon_theme = "'Tango'"

        self.help_window_position = "(wx.GetDisplaySize()[0] * 7 / 10, 15)"
        self.help_window_size = "(wx.GetDisplaySize()[0] * 3 /10," + \
                                " wx.GetDisplaySize()[1] * 7 /10)"

        # Grid configuration
        # ------------------

        self.grid_shape = "(1000, 100, 3)"
        self.max_unredo = "5000"

        # Maximum result length in a cell in characters
        self.max_result_length = "1000"

        # Colors
        self.grid_color = repr(get_color(wx.SYS_COLOUR_3DSHADOW))
        self.selection_color = repr(get_color(wx.SYS_COLOUR_HIGHLIGHT))
        self.background_color = repr(get_color(wx.SYS_COLOUR_WINDOW))
        self.text_color = repr(get_color(wx.SYS_COLOUR_WINDOWTEXT))

        # Fonts

        self.font = repr(get_font_string(wx.SYS_DEFAULT_GUI_FONT))

        # Default cell font size

        self.font_default_sizes = "[6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32]"

        # Zoom

        self.minimum_zoom = "0.25"
        self.maximum_zoom = "8.0"

        # Increase and decrease factor on zoom in and zoom out
        self.zoom_factor = "0.05"

        # GPG parameters
        # --------------

        self.gpg_key_uid = repr('None')
        self.gpg_key_passphrase = repr('None')  # Set this individually!

        # CSV parameters for import and export
        # ------------------------------------

        # Number of bytes for the sniffer (should be larger than 1st+2nd line)
        self.sniff_size = "65536"


class Config(object):
    """Configuration class for the application pyspread"""

    # Only keys in default_config are config keys

    def __init__(self, defaults=None):
        self.config_filename = "pyspreadrc"

        # The current version of pyspread
        self.version = VERSION

        if defaults is None:
            self.defaults = DefaultConfig()

        else:
            self.defaults = defaults()

        self.data = DefaultConfig()

        self.cfg_file = wx.Config(self.config_filename)

        self.load()

    def __getitem__(self, key):
        """Main config element read access"""

        if key == "version":
            return self.version

        return eval(getattr(self.data, key))

    def __setitem__(self, key, value):
        """Main config element write access"""

        setattr(self.data, key, value)

    def load(self):
        """Loads configuration file"""

        # Reset data
        self.data.__dict__.update(self.defaults.__dict__)

        for key in self.defaults.__dict__:
            if self.cfg_file.Exists(key):
                setattr(self.data, key, self.cfg_file.Read(key))

    def save(self):
        """Saves configuration file"""

        for key in self.defaults.__dict__:
            self.cfg_file.Write(key, getattr(self.data, key))


config = Config()








