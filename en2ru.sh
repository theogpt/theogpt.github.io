#!/bin/bash
DIR=$(dirname "$0")
source $DIR/_openai/venv/bin/activate
python3 $DIR/_openai/en2ru.py "$@"
