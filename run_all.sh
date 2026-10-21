#!/bin/bash
# Runs all four scripts together; Ctrl+C stops them all. Output is prefixed with the script name.
cd "$(dirname "$0")"
trap 'kill 0' EXIT
for s in door_sensor light_control fan_control water_level; do
    python3 -u -W ignore $s.py 2>&1 | sed -u "s/^/[$s] /" &
done
wait
