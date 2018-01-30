import discord
import json
from discord.ext import commands

bot = commands.Bot(command_prefix='~')


@bot.command()
async def ping(ctx):
    await ctx.send('Pong')

with open('token.json') as fp:
    token = json.load(fp)

discord_token = token['d-token']

bot.run(discord_token)
