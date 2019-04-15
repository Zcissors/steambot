#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess

from . import pinguucmds as commands


class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ----server list----
    @commands.command(brief='list servers')
    async def servers(self, ctx):
        pag = commands.Paginator()

        for i, guild in enumerate(ctx.bot.guilds):
            owner = guild.owner

            pag.add_line(f'{i + 1:04}  {guild} | {owner} | {guild.id} | {guild.member_count}')

            for page in pag.pages:
                await ctx.send(page)

    # ----make an invite----
    @commands.command(brief='Make an invite link.')
    async def invite(self, ctx):
        """
        A command to get an invite link for the bot.
        """
        await ctx.author.send(
            'here is a link you can use to invite me to your Discord '
            'guild! \N{SMILING FACE WITH OPEN MOUTH}'
            ' \nhttps://discordapp.com/oauth2/authorize?client_id'
            f'={self.bot.bot_token}&scope=bot')

    # ----test ping command ----
    @commands.command(brief='Prints the latency.', hidden=True)
    async def ping(self, ctx):
        """
        Tests that the bot is not dead.
        """
        await ctx.send(f'Pong @ {ctx.bot.latency * 1000:,.2f} ms.')

    # ---- say command ----
    @commands.command(hidden=True)
    async def say(self, ctx, *, message):
        await ctx.send(message)

    # ----update command----
    @commands.command(name='update',
                      brief='Executes git-pull on the repository, and DMs you the output.')
    async def git_pull(self, ctx, *extra_args):
        """
        If you call this with the `--force` flag, then we will force-update and
        overwrite the existing code with the upstream branch.

        This blocks the event loop.
        """
        # noinspection PyBroadException
        try:
            if '--force' in extra_args:
                output: str = subprocess.check_output(
                    [
                        '/bin/bash', '-c',
                        'git fetch --all && git reset --hard origin/'
                        '$(git rev-parse --abbrev-ref HEAD); exit 0'
                    ],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True)
            else:
                output: str = subprocess.check_output(
                    ['/bin/bash', '-c', 'git pull; exit 0'],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )

        except BaseException:
            import traceback
            output = traceback.format_exc()

        pag = commands.Paginator()
        for line in output.split('\n'):
            pag.add_line(line)

        for page in pag.pages:
            await ctx.author.send(page)

    @commands.command(name='stop', brief='Stops the bot.')
    async def stop(self, ctx):
        await ctx.send('Goodbye.')
        await ctx.bot.logout()

    async def cog_check(self, ctx):
        return ctx.author.id == ctx.bot.owner_id


def setup(bot):
    bot.add_cog(AdminCog(bot))
