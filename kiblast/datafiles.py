# -*- coding: utf-8 -*-
"""KiBlast Data File Handling
"""
import os
import sys
import appdirs
from .defs import defs
import csv


class DataTableFile:

    __DATA_DIRS = [
        os.path.join(os.getcwd(), "." + defs.appname()),
        appdirs.user_data_dir(defs.APPNAME, defs.APPAUTHOR),
        appdirs.site_data_dir(defs.APPNAME, defs.APPAUTHOR),
    ]

    def __init__(self, basename, defaults):
        # Read in Data tables that match the base name
        # and the columns and their defaults.
        # Blank rows are skipped.
        # Rows with the column names matching (EXACTLY) are skipped
        # if base_name begins with a . then we look for all files that end in the base name
        self.__BASENAME = basename
        self.__DEFAULTS = defaults

        # Initialise Instance Variables
        self.__data = []

        data_files = []
        for path in self.__DATA_DIRS:
            if os.path.isdir(path):
                with os.scandir(path) as entries:
                    for datafile in sorted(entries, key=lambda file: file.name):
                        if self._chk_loadable(datafile, self.__BASENAME):
                            data_files.append(os.path.join(path, datafile))

        priority = 0
        for data in data_files:
            self._load_data(data, self.__DEFAULTS, priority)
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

            if "EXTRA" in row:
                row["EXTRA"] = ", ".join(row["EXTRA"])
            else:
                row["EXTRA"] = ""

            row["PRIORITY"] = priority
            row["SOURCE"] = sourcename
            return row

        with open(filename, newline="") as csvfile:
            rawfilename = os.path.basename(filename)
            if rawfilename.endswith(
                self.__BASENAME + ".csv"
            ) and self.__BASENAME.startswith("."):
                sourcename = rawfilename[0 : -(len(self.__BASENAME) + 4)]
            else:
                sourcename = "COMMON"

            datareader = csv.DictReader(
                csvfile,
                fieldnames=list(defaults.keys()),
                restkey="EXTRA",
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


class StockData(DataTableFile):
    def __init__(self):
        super().__init__(
            ".stock",
            {
                "MFG": None,
                "MPN": None,
                "SIZE": None,
                "COST": None,
                "COST_QTY": None,
                "QTY_ON_HAND": 0,
                "DESCRIPTION": None,
            },
        )


class EquivalentsData(DataTableFile):
    def __init__(self):
        super().__init__(".equiv", {"MFG": None, "MPN": None})
        # EXTRA is a list of "MFG,MPN" pairs which declare the equivalent parts to the master part


class PricingData(DataTableFile):
    def __init__(self):
        super().__init__(".price", {"MFG": None, "MPN": None, "LINK": None})
        # EXTRA is a list of "MOQ,PRICE" pairs which declare the price at various MOQ's


class ExtraParts(DataTableFile):
    def __init__(self):
        super().__init__(
            ".parts",
            {
                "REF": None,
                "VARIANT": "COMMON",
                "MFG": "Generic",
                "MPN": None,
                "SIZE": None,
                "EQUIVOK": True,
                "FITTED": False,
                "DESC": None,
            },
        )

    def getParts(self, variant=None, known_refs=[]):
        # Get the unique extra parts list for the named variant.
        # only gets parts whose ref is not already known.
        def add_extra_parts(variant):
            for row in self.getAllData():
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
        for row in self.getAllData():
            if row["VARIANT"] not in known_variants:
                known_variants.append(row["VARIANT"])
                extra_variants.append(row["VARIANT"])

        return extra_variants


class AllData:
    def __init__(self):
        # part_cache = PartCache()
        self.stock = StockData()
        self.equivalents = EquivalentsData()
        self.pricings = PricingData()
        self.extras = ExtraParts()
