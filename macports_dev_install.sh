#!/bin/sh

/Applications/MacPorts/"Python 3.13"/IDLE.app/Contents/MacOS/Python -m ensurepip

/Applications/MacPorts/"Python 3.13"/IDLE.app/Contents/MacOS/Python -m pip install --upgrade pip

/Applications/MacPorts/"Python 3.13"/IDLE.app/Contents/MacOS/Python -m pip install --upgrade pip setuptools wheel

#--no-warn-script-location # to avoid warning about scripts not being on PATH


# Install the required packages for the mi_companion project using MacPorts Python 3.13
export SUBMODULE_DIRECTORY=/Users/maha/Projects/mi_companion

/Applications/MacPorts/"Python 3.13"/IDLE.app/Contents/MacOS/Python -m pip install -r /Users/maha/Projects/mi_companion/mi_companion/requirements.txt