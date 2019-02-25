#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from . import singleton


class Config(metaclass=singleton.SingletonMeta):
    def __init__(self):
        with open('token.json') as fp:
            contents = json.load(fp)

        self.steam_key = contents['s-key']
        self.bot_token = contents['d-token']
        self.bot_id = contents['b-token']
        self.ladder_key = contents['ladder-key']
        # TODO: put this in your token.json :)
        self.owner_id = 95721165607141376
        # TODO: put this in your token.json :)
        self.command_prefix = '!sl'
