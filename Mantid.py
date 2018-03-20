#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 20 22:27:24 2018

@author: lass
"""

import subprocess


mantidPath = str(subprocess.check_output("dpkg -L Mantid |grep mantidpython", shell=True)[:-1])

print(subprocess.check_output(mantidPath+' mantidtest.py',shell=True))