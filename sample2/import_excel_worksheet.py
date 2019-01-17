""" 
This program imports the document agenda.xls, parses the contents, and stores it
inside a SQLite database. 
"""

import xlrd
import argparse
from db_table import db_table

# Global variables
fileToParse = ""
shName = ""         ## name of worksheet to parse

numRows = 0         ## number of entries 
numCols = 0         ## number of attributes 
attrIndex = 12      ## row containing attribute names
rowStartIndex = 13  ## start parsing from this row

# The following schema enables duplicate entries. It appears
# idiomatic in SQLite to denote "id" as the primary key. Ideally
# I would create a primary key set consisting of the required fields
# to prevent duplicate entries. 
schema = {"id": "integer PRIMARY KEY", 
            "date": "text NOT NULL", 
            "timeStart":"text NOT NULL", 
            "timeEnd":"text NOT NULL", 
            "sessionTitle":"text NOT NULL", 
            "room":"text", 
            "description":"text"}

###################
# Helper Functions
###################

"""
Purpose: Opens the file specified @ fileDir and initializes global 
         variables numRows & numCols for other methods to use
Args:
    - fileDir [string]: The directory of file to be parsed
Returns: 
    - sh [object]: The object representation of the first Excel worksheet 
"""
def initBook(fileDir): 
    global shName, numRows, numCols
    
    try:
        book = xlrd.open_workbook(fileToParse)
    except FileNotFoundError as e:
        raise RuntimeError("Unable to open the file {} or it does not exist".format(fileToParse))
    sh = book.sheet_by_index(0)
    
    shName = sh.name.lower()
    numRows = sh.nrows
    numCols = sh.ncols
    print("The worksheet {0} contains {1} rows and {2} columns".format(shName, numRows, numCols))
    
    return sh
    
"""
Purpose: Initializes the database instance with the provided schema
Args:
    - schema [dict]: The schema by which data is organized and stored
Returns: 
    - db [object]: The database object initialized with the provided schema
"""
def initDB(schema): 
    global shName
    
    db = db_table(shName, schema)
    return db
    
"""
Purpose: Returns the list of all attributes that describe each entry in the
         given worksheet. Attributes are cleaned of extraneous characters such
         as ' * '
Args:
    - sh [object]: The object representation of the first Excel worksheet
    - index [integer]: The row in the Excel worksheet containing the attributes
Returns: list of string
"""
def getAttrNames(sh, index): 
    names = []
    for name in sh.row_values(index):
        names.append(cleanupName(name))
    return names
    
"""
Purpose: (1) Trims and return strings containing a leading asterisk
         (2) Splits strings by "/" and returns the letters to the left of "/"
         (3) Trims interior spaces and returns string in lower camel case
Args:
    - s [str]: String to be cleaned and returned
Returns: string
"""
def cleanupName(s): 
    if s.startswith("*"):
        return cleanupName(s[1:].lower())
    elif not s.find("/") == -1:
        ss = s.split("/")
        return cleanupName(ss[0].lower())
    else:
        return toLowerCamelCase(s.lower().split(" "))
        
"""
Purpose: Given a list of strings, returns a single string in lower camel case that
         is the concatenation of the list of strings
Args:
    - ss [list]: List of strings
Returns: string
Example:
"""
def toLowerCamelCase(ss): 
    ret = ""
    for i, s in enumerate(ss):
        if i == 0:
            ret += s
        else:
            ret += s[0].upper() + s[1:]
    return ret
    
"""
Purpose: Iterates through the Excel worksheet row-wise and adds each entry to database
         starting from rowStartIndex to end
Args:
    - sh [object]: The object representation of the first Excel worksheet
    - db [object]: The SQLite instance of the database
Returns: n/a
"""
def parseWorksheet(sh, db): 
    global numRows, attrIndex
    
    attrNames = getAttrNames(sh, attrIndex)
    
    for i in range(rowStartIndex, numRows):
        dataObj = parseEntry(sh.row_values(i), attrNames)
        db.insert(dataObj)
        
"""
Purpose: Given a row of raw Excel data, constructs a dictionary object 
         suitable for storage in a SQLite database 
Args:
    - entry [list]: A row of data retrieved from an Excel document
    - attribute [list]: A list of all attributes that describe a data entry
Returns: n/a
Example:
"""
def parseEntry(data, attributes): 
    entry = {}
    for i, attr in enumerate(attributes):
        entry[attr] = data[i].replace("'", "''")
    return entry
    
######################
# Program entry point
######################
def main():
    global fileToParse, attrIndex, schema

    parser = argparse.ArgumentParser(description="Parse a document and dump contents into SQLite database")
    parser.add_argument('fileName', metavar="f", type=str, help="The file location of the Excel doc to be parsed")
    args = parser.parse_args()
    fileToParse = vars(args)["fileName"]
    
    sh = initBook(fileToParse)
    db = initDB(schema)
    
    # Parse worksheet and load contents into database
    parseWorksheet(sh, db)
    print("Finished parsing worksheet and loading contents into database")
    
    db.close()
    
if __name__ == "__main__":
    main()