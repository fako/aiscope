#!/usr/bin/env bash

# Load environment variables similar to how docker does it
export $(cat .env | xargs)

# Activate virtual environment
poetry shell
