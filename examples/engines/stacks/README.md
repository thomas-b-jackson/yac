# Stack Engine Incubator Starter Kit

Starter kit for creating a new stack engine incubator

# Overview

The image directory has a Makefile and sources for a skeletal GCPStack implementation.

The sources inlude the following files:
* stack.py: GCPStack builder
* stack.json: GCPStack schema
* tests/* : unit tests for GCPStack builder

# Build Steps

## Image Build

Makefile is in the image dir

Build your yac image by running the 'make image' target as:

```
$ cd image
$ make image
```

## Service Build

Return to root dir and uncomment the Stack stanza in service.yaml.

Next, do a dryrun build as ...

```
$ cd ..
$ source .yac
$ yac stack service.yaml -d
```

Iterate on the image until you are happy with your stack implementation.

## Image Release

Release your yac image as:

```
$ cd image
$ make release
```
