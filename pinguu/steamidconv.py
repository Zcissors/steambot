#!/usr/bin/env python
# -*- coding: utf-8 -*-
# References:
#     github.com/moshferatu/Steam-ID-Converter/blob/master/SteamIDConverter.py

__all__ = ('community_to_steam', 'steam_to_community')


base = 76561197960265728


def community_to_steam(id: int) -> str:
    return f'STEAM_0:{(id - base) % 2}:{(id - base) >> 1}'


def steam_to_community(id: str) -> int:
    _, first, second = id.split(':')
    return (int(second) << 1) + int(first) + base
