import os
import csv
import xml.etree.ElementTree as ET
import traceback
from os.path import exists

def import_csv():
    try:
        entry_list = []
        with open('file.csv', newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',',quotechar='|')
            for row in spamreader:
                if '169.254.' in row[0]:
                    pass
                else:
                    if row != [] and row[1]!="" and row[0]!="" and row[1]!='EXCLUDEDUSER1' and row[1]!='EXCLUDEDUSER2':
                        entry_list.append(row)
            del entry_list[0]
            return entry_list
    except:
        traceback.print_exc()

def build_XML(entry_list):
    try:
        root = ET.Element('uid-message')
        ver = ET.SubElement(root,"version")
        ver.text = "1.0"
        t = ET.SubElement(root,"type")
        t.text = "update"
        payload = ET.SubElement(root,"payload")
        login = ET.SubElement(payload,"login")
        for userdata in entry_list:
            ET.SubElement(login,'entry name="{}" ip="{}" timeout="300"'.format(userdata[1],userdata[0]))
        tree = ET.ElementTree(root)
        ET.indent(tree, space="\t", level=0)
        tree.write("XMLBuilderoutput.xml")
    except:
        traceback.print_exc()

if __name__ == "__main__":
    if exists('XMLBuilderoutput.xml'):
        os.remove('XMLBuilderoutput.xml')
    el = import_csv()
    build_XML(el)
    os.remove('file.csv')
