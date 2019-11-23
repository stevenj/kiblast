# -*- coding: utf-8 -*-
"""KiBlast Data File Handling
"""
import os
import sys
import appdirs
from .defs import defs
import csv


class DataTableFile:

    DATA_DIRS = [
        os.path.join(os.getcwd(), "." + defs.appname()),
        appdirs.user_data_dir(defs.APPNAME, defs.APPAUTHOR),
        appdirs.site_data_dir(defs.APPNAME, defs.APPAUTHOR),
    ]

    __data = []

    def __init__(self, base_name, defaults):
        # Read in Data tables that match the base name
        # and the columns and their defaults.
        # Blank rows are skipped.
        # Rows with the column names matching (EXACTLY) are skipped
        # if base_name begins with a . then we look for all files that end in the base name
        data_files = []
        for path in self.DATA_DIRS:
            if os.path.isdir(path):
                with os.scandir(path) as entries:
                    for datafile in sorted(entries, key=lambda file: file.name):
                        if self._chk_loadable(datafile, base_name):
                            data_files.append(os.path.join(path, datafile))

        priority = 0
        for data in data_files:
            self._load_data(data, defaults, priority)
            priority += 1

    @staticmethod
    def _chk_loadable(data_file, base_name):
        if data_file.is_dir():
            return False

        if base_name.startswith("."):
            if str(data_file.name).endswith(base_name + ".csv"):
                return True
            if str(data_file.name).endswith(base_name + ".xlsx"):
                return True
            base_name = base_name[1:]
        if str(data_file.name) == base_name + ".csv":
            return True
        if str(data_file.name) == base_name + ".xlsx":
            return True
        return False

    def _load_data(self, filename, defaults, priority):
        if filename.endswith(".csv"):
            self._load_data_csv(filename, defaults, priority)
        elif filename.endswith(".xlsx"):
            self._load_data_xlsx(filename, defaults, priority)

    def _load_data_csv(self, filename, defaults, priority):
        # We load the csv, row at a time into the data store.
        # We add the "PRIORITY" field, to encode what level of file it is.
        # We strip any headers, or blank rows.
        def isRowHeader(row):
            for column in defaults.keys():
                if (
                    (row[column] != column)
                    and (row[column] is not None)
                    and (row[column] != "")
                ):
                    return False
            return True

        def setRowDefaults(row):
            for column in defaults.keys():
                if (row[column] is None) or (row[column] == ""):
                    row[column] = defaults[column]
                # Make sure columns that should be bools, are bools.
                if isinstance(defaults[column], bool):
                    row[column] = self.dataToBool(row[column])

            if "COMMENT" in row:
                row["COMMENT"] = ", ".join(row["COMMENT"])
            else:
                row["COMMENT"] = ""

            row["PRIORITY"] = priority
            return row

        with open(filename, newline="") as csvfile:
            datareader = csv.DictReader(
                csvfile,
                fieldnames=list(defaults.keys()),
                restkey="COMMENT",
                dialect="excel",
                skipinitialspace=True,
                escapechar="\\",
            )
            for row in datareader:
                if row["REF"].startswith("#"):
                    continue  # This is a comment line, so ignore it.

                if isRowHeader(row):
                    continue  # This is just a header row, so ignore it.

                row = setRowDefaults(row)
                self.__data.append(row)

    def _load_data_xlsx(self, filename, columns, priority):
        pass

    def dumpAllData(self):
        if len(self.__data) > 0:
            # csv writer, which dumps to the terminal
            dumper = csv.writer(sys.stdout, dialect="excel", escapechar="\\")

            dumper.writerow(self.__data[0].keys())

            columns = self.__data[0].keys()
            for row in self.__data:
                row_data = []
                for column in columns:
                    row_data.append(row[column])
                dumper.writerow(row_data)
        else:
            print("No Data")

    def getAllData(self):
        return self.__data

    @staticmethod
    def dataToBool(
        value,
        truthTable=[
            "TRUE",
            "YES",
            "YEA",
            "AYE",
            "OK",
            "OKAY",
            "AFFIRMATIVE",
            "CERTAINLY",
            "DEFINITELY",
        ],
    ):
        return str(value).upper() in truthTable


class PartCache:
    __COLUMNS = [""]

    def __init__(self):
        pass


class StockData:
    def __init__(self):
        pass


class EquivalentsData:
    def __init__(self):
        pass


class PricingData:
    def __init__(self):
        pass


class ExtraParts:
    __DEFAULTS = {
        "REF": None,
        "VARIANT": "COMMON",
        "MFG": "Generic",
        "MPN": None,
        "SIZE": None,
        "EQUIVOK": True,
        "FITTED": False,
        "DESC": None,
    }

    def __init__(self):
        self.__data = DataTableFile(".parts", self.__DEFAULTS)

    def getParts(self, variant=None, known_refs=[]):
        # Get the unique extra parts list for the named variant.
        # only gets parts whose ref is not already known.
        def add_extra_parts(variant):
            for row in self.__data.getAllData():
                if row["VARIANT"] == variant:
                    if row["REF"] not in known_refs:
                        known_refs.append(row["REF"])
                        parts.append(row)

        parts = []
        add_extra_parts(variant)
        add_extra_parts(self.__DEFAULTS["VARIANT"])

        return parts

    def getExtraVariants(self, known_variants=[]):
        extra_variants = []
        for row in self.__data.getAllData():
            if row["VARIANT"] not in known_variants:
                known_variants.append(row["VARIANT"])
                extra_variants.append(row["VARIANT"])

        return extra_variants

    def dumpAll(self):
        self.__data.dumpAllData()


class AllData:
    part_cache = PartCache()
    stock = StockData()
    equivalents = EquivalentsData()
    pricings = PricingData()
    extras = ExtraParts()

    def __init__(self):
        pass
