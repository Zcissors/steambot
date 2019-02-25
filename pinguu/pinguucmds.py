#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Default command implementation.
"""
import datetime
import logging
import traceback
import typing

from discord.ext import commands as _commands
from discord.ext.commands import *


class PinguuMixin:
    name: str
    before_invoke: typing.Callable

    def __init__(self):
        self.logger = logging.getLogger(f'{type(self).__name__} {self.name}')
        self.before_invoke(self.before_invoke_do)

    @staticmethod
    async def before_invoke_do(*args):
        if len(args) == 1:
            cog, ctx = None, args[0]
        else:
            cog, ctx = args

        cmd: 'PinguuMixin' = ctx.command
        # Logs when the command is invoked.
        cmd.logger.info(
            f'{datetime.datetime.now()} :: '
            f'{ctx.author} in {ctx.guild if ctx.guild else "DMs"} '
            f'in channel {ctx.channel} just called '
            f'{ctx.message.content}')

    async def on_error(self, *args):

        # Makes sure this will work in cogs also.
        if len(args) == 3:
            _unused_cog, ctx, error = args
        else:
            ctx, error = args

        self.logger.warning(f'{type(error).__name__}: {str(error)!r} occurred.')
        traceback.print_exception(type(error), error, error.__traceback__)

        try:
            await ctx.send('\N{FROWNING FACE WITH OPEN MOUTH}')
        finally:
            return


class Command(_commands.Command, PinguuMixin):
    def __init__(self, callback, **kwargs):
        _commands.Command.__init__(self, callback, **kwargs)
        PinguuMixin.__init__(self)


class Group(_commands.Group, PinguuMixin):
    def __init__(self, callback, **kwargs):
        _commands.Group.__init__(self, callback, **kwargs)
        PinguuMixin.__init__(self)


def command(*args, **kwargs):
    kwargs.setdefault('cls', Command)
    return _commands.command(*args, **kwargs)


def group(*args, **kwargs):
    kwargs.setdefault('cls', Group)
    return _commands.group(*args, **kwargs)
