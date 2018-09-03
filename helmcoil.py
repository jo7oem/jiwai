#!/bin/python3
# -*- coding: utf-8 -*-
import visa
import time
import os
import sys
import datetime

rm = visa.ResourceManager()
gauss = rm.open_resource("ASRL3::INSTR")
power = rm.open_resource("GPIB0::4::INSTR")

