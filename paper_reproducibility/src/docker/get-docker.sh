#!/bin/sh
set -e
# Docker Engine for Linux installation script.
#
# This script is intended as a convenient way to configure docker's package
# repositories and to install Docker Engine, This script is not recommended
# for production environments. Before running this script, make yourself familiar
# with potential risks and limitations, and refer to the installation manual
# at https://docs.docker.com/engine/install/ for alternative installation methods.
#
# The script:
#
# - Requires `root` or `sudo` privileges to run.
# - Attempts to detect your Linux distribution and version and configure your
#   package management system for you.
# - Doesn't allow you to customize most installation parameters.
# - Installs dependencies and recommendations without asking for confirmation.
# - Installs the latest stable release (by default) of Docker CLI, Docker Engine,
#   Docker Buildx, Docker Compose, containerd, and runc. When using this script
#   to provision a machine, this may result in unexpected major version upgrades
#   of these packages. Always test upgrades in a test environment before
#   deploying to your production systems.
# - Isn't designed to upgrade an existing Docker installation. When using the
#   script to update an existing installation, dependencies may not be updated
#   to the expected version, resulting in outdated versions.
#
# Source code is available at https://github.com/docker/docker-install/
#
# Usage
# ==============================================================================
#
# To install the latest stable versions of Docker CLI, Docker Engine, and their
# dependencies:
#
# 1. download the script
#
#   $ curl -fsSL https://get.docker.com -o install-docker.sh
#
# 2. verify the script's content
#
#   $ cat install-docker.sh
#
# 3. run the script with --dry-run to verify the steps it executes
#
#   $ sh install-docker.sh --dry-run
#
# 4. run the script either as root, or using sudo to perform the installation.
#
#   $ sudo sh install-docker.sh
#
# Command-line options
# ==============================================================================
#
# --version <VERSION>
# Use the --version option to install a specific version, for example:
#
#   $ sudo sh install-docker.sh --version 23.0
#
# --channel <stable|test>
#
# Use the --channel option to install from an alternative installation channel.
# The following example installs the latest versions from the "test" channel,
# which includes pre-releases (alpha, beta, rc):
#
#   $ sudo sh install-docker.sh --channel test
#
# Alternatively, use the script at https://test.docker.com, which uses the test
# channel as default.
#
# --mirror <Aliyun|AzureChinaCloud>
#
# Use the --mirror option to install from a mirror supported by this script.
# Available mirrors are "Aliyun" (https://mirrors.aliyun.com/docker-ce), and
# "AzureChinaCloud" (https://mirror.azure.cn/docker-ce), for example:
#
#   $ sudo sh install-docker.sh --mirror AzureChinaCloud
#
# --setup-repo
#
# Use the --setup-repo option to configure Docker's package repositories without
# installing Docker packages. This is useful when you want to add the repository
# but install packages separately:
#
#   $ sudo sh install-docker.sh --setup-repo
#
# Automatic Service Start
#
# By default, this script automatically starts the Docker daemon and enables the docker
# service after installation if systemd is used as init.
#
# If you prefer to start the service manually, use the --no-autostart option:
#
#   $ sudo sh install-docker.sh --no-autostart
#
# Note: Starting the service requires appropriate privileges to manage system services.
#
# ==============================================================================


# Git commit from https://github.com/docker/docker-install when
