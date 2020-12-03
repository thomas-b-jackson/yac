#!/bin/bash

# *****************************************************************
# Script for booting a new host
# *****************************************************************

# generate format date and time
echo_with_time () {
  echo $(date "+%m-%d-%Y %H:%M:%S") $1
}

# log stdout and stderr from this script to a boot log
# You can troubleshoot boot issues by inspecting this log file.
logfile=/tmp/boot.log
exec > $logfile 2>&1

# you can use any yac instrincs supported by yac templating (see 'yac templates' in wiki)
AMI_ID={{yac-ref:ami-id}}

echo_with_time "This EC2 is using ami: $AMI_ID"

# you can render in cf resources like so
SG_NAME={"Ref": "MyAppSG"}
echo_with_time "This EC2 is subject to security group: $SG_NAME"