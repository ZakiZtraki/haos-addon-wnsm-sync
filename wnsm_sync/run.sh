#!/bin/bash
set -e

# Dump all environment variables
printenv | sort

# Stay alive so you can inspect the log
sleep 300