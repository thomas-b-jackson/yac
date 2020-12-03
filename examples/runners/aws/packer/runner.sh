#!/bin/bash

# *****************************************************************
# Script for creating an AMI for a GitLab runner host.
# *****************************************************************

# When using the CIS Ubuntu image, the update manager starts running as soon as the instance is created.
# This causes "Could not get lock /var/lib/dpkg/lock" errors for the apt-get commands run.
# A workaround is to introduce a 2 min delay so that the automatic updates can complete running
#  apt-get's.
echo "*****Pausing for 2 min to let the system fully initialize..."
sleep 2m

# clear out the dpkg lock.
sudo dpkg --configure -a

sudo apt-get update --quiet

# upgrade packages on the system to ensure is is up-to-date.
yes | sudo DEBIAN_FRONTEND=noninteractive apt-get -y upgrade

sudo apt-get -y install curl

# install the runner pacakge
sudo curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | sudo bash

# install docker to container images builds
sudo apt-get -y install docker.io

# install the aws cli for aws builds
sudo apt-get -y install awscli

# cleanup any unnecessary packages.
# sudo apt-get -y autoremove