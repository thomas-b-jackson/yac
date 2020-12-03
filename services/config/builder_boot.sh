#!/bin/bash

# *****************************************************************
# For booting a new container builder host.
# *****************************************************************

# generate format date and time
echo_with_time () {
  echo $(date "+%m-%d-%Y %H:%M:%S") $1
}

# log stdout and stderr from this script to a boot log
# You can troubleshoot boot issues by inspecting this log file.
logfile=/tmp/boot.log
exec > $logfile 2>&1

# set time zone to Pacific
sudo timedatectl set-timezone America/Los_Angeles

# enables docker's remote API
# note: per instructions here
# https://medium.com/@sudarakayasindu/enabling-and-accessing-docker-engine-api-on-a-remote-docker-host-on-ubuntu-16-04-2c15f55f5d39

sudo sed -i 's/$DOCKER_OPTS/-H tcp:\/\/0.0.0.0:5555 $DOCKER_OPTS/g' /lib/systemd/system/docker.service

# reload and restart docker to pick up with the new proxy and docker configurations
sudo systemctl daemon-reload
sudo systemctl restart docker

# Open up any inbound ports we require, then enable firewall
# Note: Port 22 is open by default via the ami source image (hardened ubuntu).
sudo ufw allow 5555
sudo ufw --force enable

echo $(date "+%m-%d-%Y %H:%M:%S") "Remote api setup complete ..."
