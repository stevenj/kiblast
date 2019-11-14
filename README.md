# KiBlast BOM Costing Generator
![KiBlast](resources/logo.png)


From Schematic data and data files and Octopart, cost and generate a bom.

Note, Part Number is supposed to be unique across package options.

1. Read Schematic data from XML file.
2. If a Data directory is defined:
3. Read a Stock File (Multiple Files of name *.stock.csv or *.stock.xls or *.stock.ods (with or without prefix))
        Stock file defines components in local stock:
            - MFG
            - MPN
            - Package
            - Unit Cost
            - Qty On Hand
            - Description
            - Notes - All fields after this are notes, free format
4. Read Equivalents File:
        (*.equiv.csv/xls/ods)
       Defines all equivalent parts
       Each line has a primary identifier MFG,MPN and then an equivalent MFG,MPN that can be used for it.
       The idea is you pick a primary MFG/MPN pair and then define all their equivalents.  The process only looks up the primary
       for equivalents.  This gives you freedom, because you can say a 10uf 6V and 10uf 10V cap are equivalent for BOM purposes
       But the 10uf 10V cap is NOT therefore equivalent to the 10uf 6V.

5. Read Pricing Files:
        (*.price.csv/xls/ods)
        Defines pricing from sources not found on Octopart, such as LSCS or 4UConnector, Aliexpress, etc etc
        MFG,MPN, Link, MOQ, PRICE, MOQ, PRICE, ...
        Must have a separate file per costed source, the source name is derived from the file name LSCS.price.csv is prices for LSCS

6. Read Octopart pricing Cache File
        Octopart.cache.csv
        This contains the following:
        Date/Time Stamp, Source, MFG, MPN, Link, MOQ, PRICE, MOQ, PRICE, MOQ, PRICE, ....

        The Date/Time Stamp is the last time the data was updated from octopart, old data is refreshed as needed.  But never deleted.

        Source is the component source (Digikey/Mouser, etc)

7. Generate a BOM.
        Make a Unique Sorted list of Components by MFG/MPN.  If MPN not Specified/Blank, use Value.  If MFG not specified, use "Generic"
        Generate warnings if components are inconsistent (not using the same footprint, other fields don't match, etc)

        For Each unique component, if NOT IN STOCK, create a list of MFG/MPN, including equivalents we need to cost.

        For Each component to cost, if not in cache or cache too old, add to component query list.

        For Batches of components in component query list, look up data on ocotopart, and update cache with results.  Save Cache.

        For each component in list of MFG/MPN.
            IF in stock, or equivalent in stock, use that.
            Otherwise, find cheapest stocked item from pricing data or octopart cache and use that.

        Emit BOM as CSV/XLS/ODS

NOTE:  First do it all with CSV, but don't preclude option to use XLS or ODS later.

DEVELOPMENT NOTE:

To get the venv for development do this:
```shell
$ poetry shell
$ source ~/.cache/pypoetry/virtualenvs/kiblast-py3.7/bin/activate
```

