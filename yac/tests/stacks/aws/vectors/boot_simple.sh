#!/bin/bash

# these values should get rendered in
NTP_SERVERS=123

PHOBIAS=spiders

# format volumes as an ext4 fs
mkfs -t ext4 /dev/xvdc
mkfs -t ext4 /dev/xvdd