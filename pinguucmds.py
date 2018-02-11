"""
Default command implementation.
"""
import datetime
import logging
import traceback
import typing

from discord.ext import commands


class PinguuMixin:
    name: str
    before_invoke: typing.Callable

    def __init__(self):
        self.logger = logging.getLogger(f'{type(self).__name__} {self.name}')
        self.before_invoke(self.before_invoke_do)

    @staticmethod
    async def before_invoke_do(ctx):
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
            cog, ctx, error = args
        else:
            ctx, error = args
            cog = None

        self.logger.warning(f'{type(error).__name__}: {str(error)!r} occurred.')
        traceback.print_exception(type(error), error, error.__traceback__)

        try:
            await ctx.send('\N{FROWNING FACE WITH OPEN MOUTH}')
        finally:
            return


class PinguuCommand(commands.Command, PinguuMixin):
    def __init__(self, name, callback, **kwargs):
        commands.Command.__init__(self, name, callback, **kwargs)
        PinguuMixin.__init__(self)


class PinguuGroup(commands.Group, PinguuMixin):
    def __init__(self, name, callback, **kwargs):
        commands.Group.__init__(self, name, callback, **kwargs)
        PinguuMixin.__init__(self)


def command(**kwargs):
    kwargs.setdefault('cls', PinguuCommand)
    return commands.command(**kwargs)


def group(**kwargs):
    kwargs.setdefault('cls', PinguuGroup)
    return commands.group(**kwargs)
