#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from discord.ext import commands

from . import appids
from . import pinguucmds
from . import config
from . import singleton


logging.basicConfig(level='INFO')
# DEBUG < INFO < WARNING < ERROR < FATAL
logger = logging.getLogger('Pinguu')


class Bot(commands.Bot, metaclass=singleton.SingletonMeta):
    def __init__(self):
        self.configuration = config.Config()
        self.app_id_cache = appids.AppIdCacherSingleton()
        super().__init__(command_prefix=self.configuration.command_prefix,
                         owner_id=self.configuration.owner_id)

    def command(self, *args, **kwargs):
        """A shortcut decorator that invokes :func:`.command` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_command`.
        """

        def decorator(func):
            kwargs.setdefault('parent', self)
            result = pinguucmds.command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    def group(self, *args, **kwargs):
        """A shortcut decorator that invokes :func:`.group` and adds it to
        the internal command list via :meth:`~.GroupMixin.add_command`.
        """

        def decorator(func):
            kwargs.setdefault('parent', self)
            result = pinguucmds.group(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return decorator

    def run(self):
        # Config is singleton, so we just initialize it each time we want to use it.
        # it will only load the config the first time :)
        token = self.configuration.bot_token
        return super().run(token)
