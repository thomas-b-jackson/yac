# yac - services overview

# Requirements

* Docker engine
(That's it!)


# Setting Up an EC2 Runner
Create a runner in an arbitrary AWS account:

Create credentials for account you want the stack in.
	$ yac creds services/container-builder.yaml aws -o
	
	It will prompt you for the name of the AWS account.

	$ yac stack services/yac-runner.yaml --alias [INPUT ALIAS]

This will prompt you for the following:

	1. Environment (dev || stage || prod)
	2. Runner Registration Token (generated at group or project level in CI/CD setting tab)
	2. SSH key pair (e.g. Gitlab-DOTS)
	3. GitLab host (e.g. https://gitlab.nordstrom.com)
	4. Version of GitLab (e.g. 10.8.2)

Confirm via GitLab UI that Runner is registered and ready for use

Create a sample .gitlab-ci.yml in a new or existing project



# yac Container Builder

	Create a container image stack for building Docker images in EC2 instance using AWS account (e.g. NORD-NonProd_DOTS-DevUsers-Team).
	
	1. Create credentials for account you want the stack in.
		$ yac creds services/container-builder.yaml aws -o
		
		It will prompt you for the name of the AWS account.
	
	2. Build stack usingg the below command.
		$ yac stack services/container-builder.yaml
		
	
# yac registry

