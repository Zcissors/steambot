#!/usr/bin/env python3.6
import json
import profilestates
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
        await ctx.send("\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64 to work.")
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
    data2 = resp2.json()['response']

    # Store the info you want in variables
    name = data1['personaname']
    profile_url = data1['profileurl']
    avatar_img = data1['avatarmedium']
    created_on = str(time.gmtime(data1['timecreated']))
    xp = data2['player_xp']
    level = data2['player_level']
    xp_needed = data2['player_xp_needed_to_level_up']


            # Takes an int and gets the profile state object
    state = profilestates.states[data1['personastate']]




    embed=discord.Embed(title=f'Steam Profile of {name}', url=profile_url, colour=state.colour)
    embed.set_thumbnail(url=avatar_img)
    embed.add_field(name='Current Steam Level:', value=level, inline=False)
    embed.add_field(name='Current XP', value=xp, inline=False)
    embed.add_field(name='XP Needed To Reach Next Level', value=xp_needed, inline=False)
    if 'loccountrycode' in data1:
        country_emote = 'Country:  ' + chr(0x1f1e6 + ord(data1['loccountrycode'][0]) - ord('A')) + chr(0x1f1e6 + ord(data1['loccountrycode'][1]) - ord('A')) + ' '
        embed.add_field(name=country_emote, value='\u200b', inline=False)
    embed.set_footer(text="Made with \N{HEAVY BLACK HEART} by Vee#4012")
            # NO! THIS IS FOR DISCORD.PY V0
            # await self.bot.say(embed=embed)
            # do this:
    await ctx.send(embed=embed)


# ---- I need this to run the bot lol----
bot.run(discord_token)
