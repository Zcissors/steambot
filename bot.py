#!/usr/bin/env python3.6
import json
import profilestates
import random
import time
import logging


import discord
import requests
from discord.ext import commands

import appids
appid_cache = appids.AppIdCacher()

logging.basicConfig(level='WARNING')
# DEBUG < INFO < WARNING < ERROR < FATAL
logger = logging.getLogger('Pinguu')
# ---- bot prefix ----
bot = commands.Bot(command_prefix='!!')
# ---- load token.json ----
with open('token.json') as fp:
    token = json.load(fp)

# ---- get the tokens from token.json ----
steam_key = token['s-key']
discord_token = token['d-token']

# ----test ping command ----
@bot.command(
    name='ping',    # this overrides the function name if you wanted
    aliases=['pong', 'beep'],
    brief='Ping pong hong kong long dong')
async def ass_feck(ctx):
    """
    This is your docstring for the ass_feck function.
    Discord.py uses this as an extended description.
    """
    await ctx.send('Pong')

# ---- first iteration of profile-placeholder ----
@bot.command()
async def profile(ctx, id: int = None):
    """
    Displays the profile of the user belonging to the steamid provided
    """
    if id is None:
        await ctx.send("\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64 to work.")
        return
    # url's of the API we're getting stuff from
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

    # Variables that go into the message we're sending.
    # Store the info you want in variables
    name = data1['personaname']
    profile_url = data1['profileurl']
    avatar_img = data1['avatarfull']
    created_on = str(time.gmtime(data1['timecreated']))
    badge_count = len(data2['badges'])
    xp = data2['player_xp']
    level = data2['player_level']
    xp_needed = data2['player_xp_needed_to_level_up']

            # Takes an int and gets the profile state object
    state = profilestates.states[data1['personastate']]
# ---- embed stuff ----
    embed=discord.Embed(title=f'Steam Profile of {name}', url=profile_url, colour=state.colour)
    embed.set_thumbnail(url=avatar_img)
    embed.add_field(name='Current Steam Level:', value=f'{level:,}', inline=False)
    embed.add_field(name='Number of Badges:', value=f'{badge_count}', inline=False)
    embed.add_field(name='Current XP', value=f'{xp:,}', inline=False)
    embed.add_field(name='XP Needed To Reach Next Level', value=f'{xp_needed:,}', inline=False)
    if 'loccountrycode' in data1:
        country_emote = 'Country:  ' + chr(0x1f1e6 + ord(data1['loccountrycode'][0]) - ord('A')) + chr(0x1f1e6 + ord(data1['loccountrycode'][1]) - ord('A')) + ' '
        embed.add_field(name=country_emote, value='\u200b', inline=False)
    embed.set_footer(text="Made with \N{HEAVY BLACK HEART} by Vee#4012")
            # NO! THIS IS FOR DISCORD.PY V0
            # await self.bot.say(embed=embed)
            # do this:
    print(f'name: {name},', f'state: {state},', f'level: {level:,},', f'badge count: {badge_count:,},',
    f'xp: {xp:,},', f'next level xp: {xp_needed:,}.')
    await ctx.send(embed=embed)

# ---- simple profile ----
@bot.command()
async def simpprofile(ctx, id: int = None):
    """
    Displays simplified information belonging to the steamid provided
    """
    if id is None:
        await ctx.send("\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64 to work.")
        return
    # url's of the API we're getting stuff from
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

    # Variables that go into the message we're sending.
    # Store the info you want in variables
    name = data1['personaname']
    profile_url = data1['profileurl']
    avatar_img = data1['avatarfull']
    created_on = str(time.gmtime(data1['timecreated']))
    badge_count = len(data2['badges'])
    xp = data2['player_xp']
    level = data2['player_level']
    xp_needed = data2['player_xp_needed_to_level_up']
    if 'loccountrycode' in data1:
        country_emote = '' + chr(0x1f1e6 + ord(data1['loccountrycode'][0]) - ord('A')) + chr(0x1f1e6 + ord(data1['loccountrycode'][1]) - ord('A')) + ' '
    else:
        country_emote = 'N/A'
            # Takes an int and gets the profile state object
    state = profilestates.states[data1['personastate']]

    output_str = f'Profile Name: {name}, state: {state}, Current Steam Level: {level:,}, Number of Badges: {badge_count:,}, xp: {xp:,}, XP Needed To Reach Next Level: {xp_needed:,}, Country: {country_emote}.'
    await ctx.send(output_str)

# --- getting a profile picture/avatar ---
@bot.command()
async def avatar(ctx, id: int = None):
    """
    Shows the avatar of a given steamid.
    """
    if id is None:
        await ctx.send("\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64 to work.")
        return
    # url of the API we're getting stuff from
    url1 = (
        'https://api.steampowered.com/ISteamUser/GetPlayer'
        'Summaries/v2/'
    )

    resp1 = requests.get(url1, {'key': steam_key, 'steamids': id})
    data1 = resp1.json()['response']['players'][0]
    # variables that go into the message we're sending.
    avatar_img = data1['avatarfull']
    state = profilestates.states[data1['personastate']]

    await ctx.send(avatar_img)


@bot.command()
async def status(ctx, id: int = None):
    """
    Gets the current status of a requested profile.
    """
    if id is None:
        await ctx.send("\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64 to work.")
        return
    # url of the API we're getting stuff from.
    url1 = (
        'https://api.steampowered.com/ISteamUser/GetPlayer'
        'Summaries/v2/'
    )
    # gets stuff from the url in an 'easy to get' layout.
    resp1 = requests.get(url1, {'key': steam_key, 'steamids': id})
    data1 = resp1.json()['response']['players'][0]
    # variables that go into the message we're sending.
    name = data1['personaname']
    state = profilestates.states[data1['personastate']]

    await ctx.send(f'{name} is currently {state}.')

@bot.command()
async def gameinfo(ctx, *, content):
    """
    Provides information about a game or AppId
    """
    if content.isdigit():
        app_id = int(content)
        # This just means the text is formatted the way steam does it.
        game_name = await appid_cache.lookup_id(app_id)
    else:
        app_id = await appid_cache.lookup_name(content)
        game_name = None if app_id is None else await appid_cache.lookup_id(app_id)

    if app_id is None or game_name is None:
        await ctx.send('No match')
        return

    # app_id holds the app id now
    # game_name holds the game name string now
    await ctx.send(f'{game_name} belongs to appid {app_id}.')


# ---- I need this to run the bot lol----
bot.run(discord_token)
