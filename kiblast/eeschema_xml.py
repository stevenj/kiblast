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
        # TODO:  Read extra components from the extra components data files.
        # Include them in the BOM as if they are in the XML Spreadsheet.
        # Typically these are hardware components or PCBs.  Anything we need
        # for the BOM but doesn't appear as a "Part" on the pcb design.

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

    @staticmethod
    def decode_ref(ref):
        # Return the class designator and ref index
        class_designator = ref.rstrip(string.digits)
        ref_index = ref[-(len(ref) - len(class_designator)) :]

        return (class_designator, ref_index)

    def get_all_refs(self):
        def ref_sorter(key):
            class_designator, ref_index = self.decode_ref(key)
            return "{:10}{:0>10}".format(class_designator, ref_index)

        # Returns a SORTED list of unique References
        all_components = self.Components()

        all_refs = []
        for comp in all_components:
            all_refs.append(comp["REF"])

        return sorted(list(set(all_refs)), key=ref_sorter)  # Makes list of refs UNIQUE

    def get_component(self, ref):
        # Get the component with the specified reference.
        # If the reference is not unique, return ALL components with that reference.
        found_component = []
        all_components = self.Components()
        for component in all_components:
            if component["REF"] == ref:
                found_component.extend(component)
        return found_component

    def get_all_mfg_mpn(self):
        # Return all components with the specified Manufacturer and Part Number
        # and optionally size
        found_mfg_mpn = []
        all_components = self.Components()
        for component in all_components:
            for variant in component["PARTS"]:
                if component["PARTS"][variant]["FITTED"]:
                    found_mfg_mpn.append(
                        (
                            component["PARTS"][variant]["MFG"],
                            component["PARTS"][variant]["MPN"],
                        )
                    )
        return list(set(found_mfg_mpn))

    def check_equivok(self, mfg_mpn):
        # Check if the specified mfg_mpn is ok to lookup equivalents as well.
        all_components = self.Components()
        for component in all_components:
            for variant in component["PARTS"]:
                if (
                    component["PARTS"][variant]["FITTED"]
                    and component["PARTS"][variant]["MFG"] == mfg_mpn[0]
                    and component["PARTS"][variant]["MPN"] == mfg_mpn[1]
                    and component["PARTS"][variant]["EQUIVOK"]
                ):
                    return True
        return False
