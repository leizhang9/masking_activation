#!/bin/bash
sqlite3 $1 <<EOF
SELECT hex(k) FROM traces LIMIT 20;

EOF
