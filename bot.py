#!/usr/bin/env python3.6
import json
import random
import time

import discord
import requests
from discord.ext import commands
# ---- bot prefix ----
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
async def profile(ctx, id: int = None):
    if id is None:
        await ctx.send(':bangbang: No valid steamID detected. :bangbang:')
        return

    url1 = (
        'https://api.steampowered.com/ISteamUser/GetPlayer'
        'Summaries/v2/'
    )
    url2 = (
        'https://api.steampowered.com/IPlayerService/GetBadges/v1/'
    )

# You will eventually not want to do it like this, as there is a much
# faster way.
    resp1 = requests.get(url1, {'key': steam_key, 'steamids': id})
    resp2 = requests.get(url2, {'key': steam_key, 'steamid': id})

    # This will probably error if an invalid key was given. You eventually
    # want to do some kind of error checking here.
    data1 = resp1.json()['response']['players'][0]
    # Looks like you forgot to do this one.
    data2 = resp2.json()['response']

    # Store the info you want in variables
    name = data1['personaname']
    profile_url = data1['profileurl']
    avatar_img = data1['avatarmedium']
    created_on = str(time.gmtime(data1['timecreated']))
    # Generates a flag emote. I think this will work.
    if 'loccountrycode' in data1:
        country_emote = ' ' + chr(0x1f1e6 + ord(data1['loccountrycode'][0]) - ord('A')) + chr(0x1f1e6 + ord(data1['loccountrycode'][1]) - ord('A')) + ' '
    else:
        country_code = '\N{BLACK QUESTION MARK ORNAMENT}'
    xp = data2['player_xp']
    level = data2['player_level']
    xp_needed = data2['player_xp_needed_to_level_up']


    embed=discord.Embed(title=f'Steam Profile of {name}', url=profile_url, color=random.randint(0, 0xFFFFFF))
    embed.set_thumbnail(url=avatar_img)
    embed.add_field(name='Current Steam Level:', value=level, inline=False)
    embed.add_field(name='Current XP', value=xp, inline=False)
    embed.add_field(name='XP Needed To Reach Next Level', value=xp_needed, inline=False)
    embed.set_footer(text="Made with \N{HEAVY BLACK HEART} by Vee#4012")
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
    response = data['response']
    output = f'Lvl. {response["player_level"]}, {response["player_xp"]}XP and {response["player_xp_needed_to_level_up"]}XP needed to level up'
    await ctx.send(output)
# ---- I need this to run the bot lol----
bot.run(discord_token)
