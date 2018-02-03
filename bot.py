#!/usr/bin/env python3.6
import json
import random

import discord
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
    url2 = (
        'https://api.steampowered.com/IPlayerService/GetBadges/v1/'
    )

    res = requests.get(url, {'key': steam_key, 'steamids': id})
    data = res.json()
    response = data['response']
    players = response['players']

    response2 = requests.get(url2, {'key': steam_key, 'steamid': id})
    data2 = response2.json()
    player_xp = data2['response']['player_xp']
    player_level = data2['response']['player_level']
    player_xp_needed_to_level_up = data2['response']['player_xp_needed_to_level_up']

    for player in players:
        print(response)
        embed=discord.Embed(title=f'Steam Profile of {player["personaname"]}', url=player['profileurl'], color=random.randint(0, 0xFFFFFF))
        embed.set_thumbnail(url=player['avatarfull'])
        embed.add_field(name='Level',  value=player['player_level'], inline=False)
        embed.add_field(name='XP', value=player['player_xp'] , inline=False)
        embed.add_field(name='XP to next level', value=player['player_xp_needed_to_level_up'], inline=False)
        embed.set_footer(text="Made with :heart: by Vee#4012")
        # NO! THIS IS FOR DISCORD.PY V0
        # await self.bot.say(embed=embed)
        # do this:
        await ctx.send(embed=embed)

@bot.command()
async def test2(ctx, id: int = None):
    if id is None:
        await ctx.send(':bangbang: No valid steamID detected. :bangbang:')
        return

    url = (
        'https://api.steampowered.com/IPlayerService/GetBadges/v1/'
    )

    res = requests.get(url, {'key': steam_key, 'steamid': id})
    data = res.json()
    await ctx.send(data)
# ---- I need this to run the bot lol----
bot.run(discord_token)
