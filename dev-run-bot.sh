#!/bin/bash

pip install -e . --no-deps

export $(grep -v '^#' .env | xargs)

timekiller "telepostkeeper" --timeout 20

telepostkeeper-frontend
