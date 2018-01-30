import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='?')


@bot.command()
async def ping(ctx):
    await ctx.send('Pong')

with open('token.txt') as fp:
    token = fp.read().strip()

bot.run(token)
