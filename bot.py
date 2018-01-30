import discord
import json
import requests
from discord.ext import commands

bot = commands.Bot(command_prefix='!!')
#----
with open('token.json') as fp:
    token = json.load(fp)
#---- getting keys & tokens from not here ----
steam_key = token['s-key']
discord_token = token['d-token']

# test ping command ----
@bot.command()
async def ping(ctx):
    await ctx.send('Pong')

# first iteration of profile-placeholder ----
@bot.command()
async def test(ctx, id: int = None):
    if id is None:
        await ctx.send('heck off, gimme a steamID (the long one please) :frowning:')
        return
    url = (
        'https://api.steampowered.com/ISteamUser/GetPlayer'
        'Summaries/v2/'
    )

    res = requests.get(url, {'key': steam_key, 'steamids': id})
    data = res.json()
    await ctx.send(data)

# ---- I need this to run the bot lol----
bot.run(discord_token)
