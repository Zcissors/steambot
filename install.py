#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
"""
Installs any dependencies
"""
import pip


with open('dependencies.txt') as fp:
    dependencies = fp.readlines()


for d in dependencies:
    print(f'Installing/updating {d}')
    pip.main(f'install -U {d}'.split(' '))


print('Finished.')
