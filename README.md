# yac - portable services

# Requirements

* Docker engine
(That's it!)

# Quick Start

Install the **yac** cli by:

    # source /dev/stdin  <<<  "$(curl --header "PRIVATE-TOKEN: sAd7ckLs4VkdaMxH8oC2" "https://gitlab.nordstrom.com/api/v4/projects/288/repository/files/.yac/raw?ref=master")"

This installs **yac** as a shell function in your current shell session.

NOTE: you can set the desired version via the YACVER environment variable. Type **yac** for help and to verify the version installed.

# Docs

Full documentation for yac is [available on Confluence](https://confluence.nordstrom.net/display/YAC/yac+-+your+automated+cloud)


# Typical Workflows

Ready to get up to speed on yac? Run:

        $ yac grok

Deploy a service your team owns?

        $ yac deploy <abs or rel path>/service.yaml

Want to test drive an engineering platform service archetype?

Find a service archetype of interest:

        $ yac service --find=platformengineering

Give it a spin:

        $ yac deploy platformengineering/stateless:1.0


# Why yac?

To provide a paved road to the cloud for Nordstrom application teams.

Have a containerized app? yac makes it easy to deploy to the engineering platform.

Using Kubernetes? yac also makes it easy to deploy via k8s resource templates (no Helm required!).

Using AWS? yac makes it easy to deploy via cloudformation templates.

Using GCP? native support is not yet availbale, but yac makes it easy for teams to add support themselves via the yac api incubation process.

# What is yac?

*  A workflow system that does for services what docker did for applications

    *  docker helped make it easy to find, run, define, and share individual applications
    *  yac does the same for services via the **Servicefile**
    *  a **Servicefile** is to a yac service what a **Dockerfile** is to an app

*  An operator engine for service providers

    * yac services include configuration+code
    * service code allows operational best practices to be codified and shared

*  A harness for integration tests

    * yac **Servicefiles** can include a suite of artillery-based integration tests
    * tests help ensure your service is functional and performant

*  A pipeline

    * yac **Servicefiles** can include a pipeline definition
    * build and test your service via yac in a given stage
    * yac orchestrates the promotion to the next stage

*  A cli app that lets you easily find, run, define, and share **Servicefiles**

    *  yac registry works just like the docker registry
    *  services are defined in **Servicefiles** in json
    *  **Servicefiles** can be browsed and instantiated via the yac registry

*  A happy place for service developers, cloud administrators, and service providers


# How does yac work?

Coding infrastructure is all about managing cloud provider apis, templates, and template variables.

The **yac** Servicefile allows you to leverage provider-native templates and makes it easy to blend variables from multiple sources, including:

* static parameters
* secrets in vaults
* calculations
* user prompts

The Servicefile allows you to define a pipeline that the **yac** cli uses to instantiate your service to your cloud provider.

The Servicefile provide a portable definition of the infrastructure needs of your service, just like a Dockerfile provides a portable definition of your service.


# What is a service?

*  An application that provides some useful function
*  An application that can be implemented using cloud infrastructure


# Want to contribute?

Building and testing yac is simple because the development environment leverages the yac container image (no python virtual environment required!!)

## Build Image

to build the yac image, update the major or minor version in the Makefile, then run the following from your mac prompt in the repo root ...

    $ make image

this will build the image then test each yac unit within the container image

## Run Locally

ready to develop a new yac feature?

run yac in a container while mounting your local yac sources to try out yac use cases that exercise your feature.

make sure you have a local container image per the 'Build Image' step above, then, from repo root, run ...

    $ make local

to end the session type 'exit' or cntl-d to exit from the container

note: want your bash prompt to show your yac repo branch? run the following from the bash prompt inside the yac container:

    $ source ~/.bash_profile

## Releasing

releasing the image will push the versioned image to docker hub and update the 'latest' tag to match. run the following from your mac prompt ...

    $ make release
