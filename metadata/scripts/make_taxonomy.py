#! /usr/bin/python
#
"""
a script that reads taxonomy terms from an Excel spreadsheet and write them 
out into a structured JSON document.

The input Excel file is expected contain the taxonomy in the first tab.  The 
first row is a header line that should be ignored.  The subsequent rows 
contain the 3 levels of terms in the first three columns.  The first column is 
the top tier term; if the first column is blank, the second tier value in the 
second or third column is expected to be a sub-term of the term given in the 
last non-blank value of column 1.  Similarly, an empty second column indicates
the the 3rd column is a 3rd-tier term wihtin second tier, as given by the last 
non-blank 2nd column value.  

The output is a JSON array.
"""
import openpyxl as xl
import os, sys, re, json
from argparse import ArgumentParser
from collections import OrderedDict

prog=sys.argv[0]
description = \
"""convert a multi-tiered vocabulary from an Excel spreadsheet to a JSON array"""

epilog=None

class VocabFormatError(Exception):
    """
    an error indicating unexpected formatting in the input vocabulary file.
    """
    def __init__(self, msg=None, rowdata=None, lineno=None):
        self.row = rowdata
        self.lineno = lineno
        if not msg:
            msg = "Input spreadsheet formatting error" 
        super(VocabFormatError, self).__init__(msg)

    def __str__(self):
        msg = self.message
        if isinstance(self.lineno, int):
            msg += " at " + str(self.lineno)
        if self.row is not None:
            msg += ":\n   " + str([cell.value for cell in self.row[:3]])
        return msg

def get_vocab_data(filename):
    wb = xl.load_workbook(filename=filename)
    sheets = wb.get_sheet_names()
    if len(sheets) < 1:
        raise VocabFormatError("No sheets found in Excel spreadsheet")
    return wb.get_sheet_by_name(sheets[0])

def make_term(cells):
    if not cells:
        return None
    out = OrderedDict()
    if len(cells) > 1:
        out['parent'] = ": ".join(cells[0:-1])
    out['term'] = cells[-1]
    out['level'] = len(cells)
    return out

def fill(thisrow, lastrow):
    out = []
    for cell in reversed(thisrow):
        if not out and not cell:
            continue
        out.append(cell)
    out.reverse()

    for i in range(len(out)):
        if isinstance(out[i], (str, unicode)):
            out[i] = out[i].strip()
        if not out[i] and i < len(lastrow):
            out[i] = lastrow[i]
        else:
            break
    return out

def get_header():
    taxfile = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           "model", "theme-taxonomy.json")
    header = {}
    try:
        if os.path.exists(taxfile):
            with open(taxfile) as fd:
                header = json.load(fd, object_pairs_hook=OrderedDict)
    except Exception, ex:
        pass
    
    header['vocab'] = []
    return header
        

def main(infile):

    levels = 3

    basedata = get_header()

    ws = get_vocab_data(infile)
    lastrow = []
    thisrow = []
    out = []
    pastheader = False
    for cells in ws.iter_rows():
        if not pastheader:
            pastheader = True
            continue

        thisrow = [c.value for c in cells[0:levels]]
        thisrow = fill(thisrow, lastrow)
        term = make_term(thisrow)
        if term:
            out.append(term)
        lastrow = thisrow

    basedata['vocab'] = out
    json.dump(basedata, sys.stdout, indent=4, separators=(',', ': '))

if __name__ == '__main__':
#    try:
        main(sys.argv[-1])
#    except Exception, ex:
#        sys.stderr.write(prog+": "+str(ex)+"\n")
#        sys.exit(1)

