#! /usr/bin/env python

###############################################################################
#
#  Created:    30.03.2020
#  Authors:    Marian Majan, IBL
#              Tom Kralidis, Meteorological Service of Canada
#
###############################################################################


import csv
import os
import glob
from xml.dom import minidom
import xml.etree.ElementTree as ET

rootElement = "dataroot"
# recordElement set as a filename
# recordElement = "BUFRCREX_33_0_0_CodeFlag_en"

csv.register_dialect('custom',
                     delimiter=',',
                     doublequote=True,
                     escapechar=None,
                     quotechar='"',
                     quoting=csv.QUOTE_MINIMAL,
                     skipinitialspace=False)

files = glob.glob("txt/*.txt")

for filePathName in files:
    dirName, fileName = os.path.split(filePathName)
    baseFileName, fileExtension = os.path.splitext(fileName)
    recordElement = baseFileName

    with open(filePathName) as ifile:
        data = csv.reader(ifile, dialect='custom')
        header = next(data, None)
 
        xmlFile = ET.Element(rootElement)
        no = 0
        for record in data:
          if record != header and record.__len__() != 0 :
            r = ET.SubElement(xmlFile, recordElement)
#            no = no + 1
#            ET.SubElement(r,"No").text = str(no)
            for i, field in enumerate(record):
                if not "10**" in field:
                    field = field.replace("*","")
                if field != "" and field != " ":
                    ET.SubElement(r, header[i].replace(' ', '-')).text = field
 
        tree = ET.ElementTree(xmlFile)
        tree.write("xml/" + baseFileName + ".xml")
    

        rough_string = ET.tostring(xmlFile, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        with open("xml/" + baseFileName + ".xml", 'w') as fh:
            fh.write(reparsed.toprettyxml(indent="  "))
