# -*- coding: utf-8 -*-
"""KiBlast Configuration Handling

SPDX-License-Identifier: GPL-3.0-or-later
Copyright © 2019 Steven Johnson
"""
from .defs import defs

import os
import appdirs
import tomlkit
import inspect
import pygments
from pygments.lexers.configs import TOMLLexer
from pygments.formatters import TerminalFormatter, NullFormatter


class KiBlastConfig:
    CFG_NAME = defs.appname() + "_cfg.toml"
    CFG_NAMES = [
        (os.path.join(os.getcwd(), "." + defs.appname(), CFG_NAME), "LOCAL"),
        (
            os.path.join(
                appdirs.user_config_dir(defs.APPNAME, defs.APPAUTHOR), CFG_NAME
            ),
            "USER",
        ),
        (
            os.path.join(
                appdirs.site_config_dir(defs.APPNAME, defs.APPAUTHOR), CFG_NAME
            ),
            "SYSTEM",
        ),
    ]

    # This is the default TOML Configuration File.
    # We will ONLY read information from config files also found here.
    DEFAULT_CFG = """
    # This is the TOML Formatted configuration file for KiBlast
    # It should be called "{}"
    title = "KiBlast Configuration File"

    #---Options related to KiCad----------------------------------
    [kicad]
    # Name of Manufacturer field
    mfg_field = "MFG"

    # Name of Part Number field
    pn_field  = "MPN"

    # Name of Equivalent Use OK field
    equiv_field  = "EQUIVOK"

    # Name of the part fitted or not field.  If no field, defaults to fitted.
    fitted_field = "FITTED"

    #---Options related to Querying Octopart-----------------------
    ["www.octopart.com"]
    # The apikey to access octopart web api - Get it from Octopart
    apikey = ""

    # Maximum Number of components to get per API query.
    batch_size = 20

    # Maximum Number of queries to octopart per second.
    rate_limit = 3

    # Limit part searches to these Distributors.
    distributors = ["element14 APAC", "Digi-Key", "Mouser"]

    # Currency to return search data in.
    currency = "USD"

    # Country code to search within.
    country = "US"

    # maximum number of hours we will cache octopart results for.
    cache_age = 48
    """.format(
        CFG_NAME
    )

    def __init__(self, default_only=False):
        # Initialise the configurations

        # Read the defaults first.
        self.__cfg = tomlkit.parse(inspect.cleandoc(self.DEFAULT_CFG))

        cfg_files = []
        for cfg_file_name in self.CFG_NAMES:
            try:
                with open(cfg_file_name[0]) as f:
                    cfg_files.append((tomlkit.parse(f.read()), cfg_file_name[1]))
            except IOError:
                cfg_files.append(None)

        if not default_only:
            for group in self.__cfg.keys():
                if group != "title":
                    for item in self.__cfg[group]:
                        # Add Default comment to ALL entries.
                        self.__cfg[group][item].comment("DEFAULT")

                        # Find config in files, in reverse order of importance.
                        for cfg in reversed(cfg_files):
                            if cfg is not None:
                                # If the file updates the cfg item, set its new value
                                # and update the comment to say where it came from.
                                if (group in cfg[0]) and (item in cfg[0][group]):
                                    self.__cfg[group][item] = cfg[0][group][item]
                                    self.__cfg[group][item].comment(cfg[1])

    def dump(self, color=0):
        if color == 0:
            formatter = TerminalFormatter(bg="dark")
        elif color == 1:
            formatter = TerminalFormatter(bg="light")
        else:
            formatter = NullFormatter()

        print(pygments.highlight(tomlkit.dumps(self.__cfg), TOMLLexer(), formatter))

    def get(self, group, item):
        # Get the configuration
        return self.__cfg[group][item]
