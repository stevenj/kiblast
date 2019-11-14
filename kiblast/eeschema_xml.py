# -*- coding: utf-8 -*-
"""KiBlast eeschema xml reading
"""

from lxml import etree
import re
import string


class eeschema_xml:
    def __init__(self, xmlfile, config):
        # Set up the class for a particular eeschame exported XML file.
        self.__eeschema_tree = etree.parse(xmlfile)
        self.__config = config
        self.__all_components = None

    def BoardTitle(self):
        return self.__eeschema_tree.find(
            "./design/sheet[@number='1']/title_block/title"
        ).text

    def Company(self):
        return self.__eeschema_tree.find(
            "./design/sheet[@number='1']/title_block/company"
        ).text

    def BoardRev(self):
        return self.__eeschema_tree.find(
            "./design/sheet[@number='1']/title_block/rev"
        ).text

    def BoardDate(self):
        return self.__eeschema_tree.find(
            "./design/sheet[@number='1']/title_block/date"
        ).text

    def ExportDate(self):
        return self.__eeschema_tree.find("./design/date").text

    @staticmethod
    def __field_to_bool(name):
        return (name.upper() == "YES") or (name.upper() == "TRUE")

    @staticmethod
    def __footprint_to_size(footprint, prefer_metric=False):
        # Extract Library and Footprint name:
        fplib, fpname = footprint.split(":", 1)

        # By Default size is just the footprint name
        size = fpname

        # TODO: Lookup Footprint size in Footprint Size Data
        # Not found in lookup, then try and extract size from footprint

        # Size Extraction 1.
        # IF footprint starts with a letter and underscore, and ends in Metric
        # Extract the Imperial and Metric Sizes
        fp = re.match(r"^.+?_(.+)_(.+)Metric.*$", fpname)
        if fp is not None:
            if prefer_metric:
                size = fp.group(2)
            else:
                size = fp.group(1)

        return size

    def Components(self):
        # Returns an array of components.  Each component being the dict:
        #   {"REF":ref, "VALUE":value, "FP":footprint, "SIZE":size, "PARTS":{variants}}
        #   the variants dict is
        #   {variant_name: {"MFG":..., "MPN":..., "EQUIVOK":..., "Fitted":...}},

        if self.__all_components is None:
            all_components = []

            for component in self.__eeschema_tree.iterfind("./components/comp"):
                this_comp = {
                    "REF": component.get("ref"),
                    "VALUE": component.find("value").text,
                    "FOOTPRINT": component.find("footprint").text,
                }
                this_comp["SIZE"] = self.__footprint_to_size(this_comp["FOOTPRINT"])

                # Parts start out with defaults based on standard part attributes
                # So, MFG is "Generic", MPN comes from the value field, EquivOK and Fitted are True.
                parts = {
                    "COMMON": {
                        "MFG": "Generic",
                        "MPN": this_comp["VALUE"],
                        "EQUIVOK": True,
                        "FITTED": True,
                    }
                }

                for field in component.iterfind("./fields/field"):
                    fieldname = field.get("name").split(".", 1)
                    if len(fieldname) == 1:
                        fieldname.append(
                            "COMMON"
                        )  # Any part fields without a variant are common
                    fieldvalue = field.text

                    if fieldname[0] == self.__config.get("kicad", "mfg_field"):
                        parts[fieldname[1]]["MFG"] = fieldvalue
                    elif fieldname[0] == self.__config.get("kicad", "pn_field"):
                        parts[fieldname[1]]["MPN"] = fieldvalue
                    elif fieldname[0] == self.__config.get("kicad", "equiv_field"):
                        parts[fieldname[1]]["EQUIVOK"] = self.__field_to_bool(
                            fieldvalue
                        )
                    elif fieldname[0] == self.__config.get("kicad", "fitted_field"):
                        parts[fieldname[1]]["FITTED"] = self.__field_to_bool(fieldvalue)
                this_comp["PARTS"] = parts

                all_components.append(this_comp)

            self.__all_components = all_components

        return self.__all_components

    def get_all_variants(self):
        all_components = self.Components()

        all_variants = []
        for comp in all_components:
            all_variants.extend(list(comp["PARTS"].keys()))
        return list(set(all_variants))  # Makes list of variants UNIQUE

    def get_all_refs(self):
        def ref_sorter(key):
            lead = key.rstrip(string.digits)
            count = key[-(len(key) - len(lead)) :]
            newkey = "{:10}{:0>10}".format(lead, count)
            return newkey

        # Returns a SORTED list of unique References
        all_components = self.Components()

        all_refs = []
        for comp in all_components:
            all_refs.append(comp["REF"])

        return sorted(list(set(all_refs)), key=ref_sorter)  # Makes list of refs UNIQUE
