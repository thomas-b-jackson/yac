# yac base image

The yac base image includes core binaries used by yac, including
    * python
    * python packages
    * artillery
    * kubectl
    * kubelogin
    * packer
    * misc linux utilities

Most yac features live in the yac image rather than the yac base image, so separating the two ensures fast yac image builds.

## Build Image

to build the yac base image and push it to docker hub, update the major or minor version in the Makefile, then run the following from the repo root ...

    $ make
