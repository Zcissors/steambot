#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
# The user's current status. 0 - Offline, 1 - Online, 2 - Busy, 3 - Away,
# 4 - Snooze, 5 - looking to trade, 6 - looking to play. If the player's
# profile is private, this will always be "0", except if the user has set
# their status to looking to trade or looking to play, because a bug makes
# those status appear even if the profile is private.
import dataclasses


@dataclasses.dataclass(frozen=True, eq=False, init=True, repr=True, unsafe_hash=False)
class ProfileState:
    """Python3.7 dataclass descriptor of a profile state."""

    id: int
    name: str
    colour: int
    emote: str

    def __eq__(self, other):
        if isinstance(other, int):
            return id(self) == other
        elif isinstance(other, str):
            return str(self).casefold() == other.casefold()
        else:
            return False

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.id)


_member_map_ = dict(
    OFFLINE=ProfileState(
        id=0,
        name='Offline',
        colour=0x736f6e,
        emote='\N{black heart}'),

    ONLINE=ProfileState(
        id=1,
        name='Online',
        colour=0x00ff00,
        emote='\N{green heart}'),

    BUSY=ProfileState(
        id=2,
        name='Busy',
        colour=0xff0000,
        # Actually red but whatever discord.
        emote='\N{heavy black heart}'),

    AWAY=ProfileState(
        id=3,
        name='Away',
        colour=0xffff00,
        emote='\N{yellow heart}'),

    SNOOZE=ProfileState(
        id=4,
        name='Snooze',
        colour=0x8e35ef,
        emote='\N{purple heart}'),

    LTT=ProfileState(
        id=5,
        name='Looking to trade',
        colour=0x54c571,
        emote='\N{heart with ribbon}'),

    LTP=ProfileState(
        id=6,
        name='Looking to play',
        colour=0x1589ff,
        emote='\N{revolving hearts}')
)


def __getattr__(name):
    return _member_map_[name]


def find_name_casefold(item):
    """Insensitive lookup."""
    for k, v in _member_map_.items():
        if k.casefold() == item.casefold() or v.name.casefold() == item.casefold():
            return v
    raise KeyError(item)


def find_by_id(id):
    for item in _member_map_.values():
        if item.id == id:
            return item
    raise KeyError(id)