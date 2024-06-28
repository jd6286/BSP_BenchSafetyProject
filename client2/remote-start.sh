#!/bin/bash
cd /home/pi/openvino-project/client2/
source .venv/bin/activate
export DISPLAY=:0
python3 main.py
