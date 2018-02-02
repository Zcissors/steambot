import discord
import json
import requests
from discord.ext import commands

bot = commands.Bot(command_prefix='!!')
# ---- load token.json ----
with open('token.json') as fp:
    token = json.load(fp)

# ---- get the tokens from token.json ----
steam_key = token['s-key']
discord_token = token['d-token']

# ----test ping command ----
@bot.command()
async def ping(ctx):
    await ctx.send('Pong')

# ---- first iteration of profile-placeholder ----
@bot.command()
async def test(ctx, id: int = None):
    if id is None:
        await ctx.send(':bangbang: No valid steamID detected. :bangbang:')
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
