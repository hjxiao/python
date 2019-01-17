""" 
This program outputs a subset of entries from the parsed Excel worksheet that
exactly match the user query. The query consists of an attribute and a value

Matching is case-sensitive.
"""

import argparse
from db_table import db_table

# Global variables
shName = "agenda"
validAttr = ['date', 'time_start', 'time_end', 'title', 'location', 'description']
printSubset = ['title', 'location', 'description']

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

def isValidAttr(attr):
    global validAttr
    return attr in validAttr
    
"""
Purpose: Converts an input string into the corresponding schema column attribute
Args: 
    - s [string] The string to be converted into its corresponding attribute
Returns: string
"""
def convertAttrName(s):
    if s == "time_start":
        return "timeStart"
    elif s == "time_end":
        return "timeEnd"
    elif s == "title":
        return "sessionTitle"
    elif s == "location":
        return "room"
    else:
        return s
    
"""
Purpose: Initializes database with the corresponding schema and name. It is assumed
         that this database was previously created. 
Args: n/a
Returns: db [object] the database
"""
def initDB():
    global shName, schema
    return db_table(shName, schema)
    
"""
Purpose: Given a database and a query, returns a list of database entries
         that exactly match the search criteria.
Args:
    - db [object] the database instance
    - attr [string] the attribute to query
    - val [string] the value of the attribute to query
Returns: list of dictionary objects
"""
def queryDB(db, attr, val):
    global printSubset

    attrToPrint = []
    for item in printSubset:
        attrToPrint.append(convertAttrName(item))

    return db.select(attrToPrint, {convertAttrName(attr): val})
    
"""
Purpose: Formats a data entry [object] with spacing and outputs to terminal
Args:
    - li [list] the list of data entries as objects to print to terminal
Returns: n/a
"""
def prettyPrint(li):
    if len(li) == 0:
        print("No match found. Query is case-sensitive")
        return

    for result in li:
        title = result['sessionTitle']
        room = result['room']
        desc = result['description']
        print("{0:30} {1:30} {2:30}".format(title, room, desc))

######################
# Program entry point
######################
def main():
    parser = argparse.ArgumentParser(description="Return a collection of entries in the Agenda worksheet that exactly match the query")
    parser.add_argument('attribute', metavar="col", type=str, help="The attribute can be one of: date, time_start, time_end, title, location, or description")
    parser.add_argument('value', metavar="val", type=str, nargs="+", help="The value of the attribute that one wishes to filter/search by")
    args = parser.parse_args()
    args = vars(args)
    
    attr = args["attribute"]
    valList = args["value"]
    val = " ".join(valList)
    
    if not isValidAttr(attr):
        raise RuntimeError("The attribute {} is not valid.".format(attr))
    
    db = initDB()
    results = queryDB(db, attr, val)
    prettyPrint(results)
    
    db.close()
    
if __name__ == "__main__":
    main()