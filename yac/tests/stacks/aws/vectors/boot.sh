#!/bin/bash

# these values should get rendered in
NTP_SERVERS={{yac-ref:param1}}

PHOBIAS={{yac-ref:param2}}

# format volumes as an ext4 fs
mkfs -t ext4 /dev/xvdc
mkfs -t ext4 /dev/xvdd