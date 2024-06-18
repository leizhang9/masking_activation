#!/usr/bin/env python3

import sqlite3
import binascii
import argparse


###############################################################################################################################################
# argparse
parser = argparse.ArgumentParser(description="blah")
parser.add_argument("-d", "--database", type=str, help="database aisec format", required=True)
namespace = parser.parse_args()


###############################################################################################################################################
conn = sqlite3.connect(namespace.database)
c = conn.cursor()

keys = []

for row in c.execute("SELECT k FROM traces WHERE k IN (SELECT k FROM traces GROUP BY k HAVING COUNT(*)>1)"):
    keys.append(row[0])


key_set = set()

for key in keys:
    key_set.add(binascii.hexlify(keys[0]).decode("utf-8"))


if len(key_set) != 1:
    print("irgendwas stimmt nicht mit dem key es gibt mehrere die doppelt vor kommen")

print(list(key_set)[0])

conn.close()
###############################################################################################################################################
