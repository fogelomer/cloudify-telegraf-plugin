#!/bin/bash

set -e

sudo service docker start
sudo docker run hello-world
