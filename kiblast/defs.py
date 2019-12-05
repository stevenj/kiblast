# -*- coding: utf-8 -*-
""" Definitions for KiBlast

SPDX-License-Identifier: GPL-3.0-or-later
Copyright © 2019 Steven Johnson
"""
from kiblast import __version__


class defs:
    APPNAME = "KiBlast"
    APPAUTHOR = "Sakura Industries Limited"
    FULLVERSION = APPNAME + " " + __version__
    SHORTVERSION = __version__

    @classmethod
    def appname(cls):
        return cls.APPNAME.lower()
