#!/usr/bin/env python3.6
import json
import profilestates
import random
import time
import logging
import functools
import aiohttp

import bs4
import discord
import requests
import asyncio
from discord.ext import commands

import appids

appid_cache = appids.AppIdCacher()

logging.basicConfig(level='INFO')
# DEBUG < INFO < WARNING < ERROR < FATAL
logger = logging.getLogger('Pinguu')

def log_who(coro):
    @functools.wraps(coro)
    async def command(ctx, *args, **kwargs):
        # Forgot what the logger variable was called
        logger.info(f' {ctx.author} in #{ctx.channel} in guild {ctx.guild if ctx.guild else "DMs"} '
                     f'invoked {ctx.invoked_with} with args {args} {kwargs}')
        return await coro(ctx, *args, **kwargs)
    return command

class PinguuCommand(commands.Command):
    async def on_error(self, cog, ctx, error):
        import traceback
        err = traceback.format_exception(type(error), error,
                                         error.__traceback__)
        # noinspection PyBroadException
        traceback.print_exception(type(error), error, error.__traceback__)

        await ctx.send(f'An error occurred:\n{"".join(err)}')


# ---- bot prefix ----
bot = commands.Bot(command_prefix='!!')
# ---- load token.json ----
with open('token.json') as fp:
    token = json.load(fp)

# ---- get the tokens from token.json ----
steam_key = token['s-key']
discord_token = token['d-token']
bot_token = token['b-token']


@bot.command(cls=PinguuCommand)
@log_who
async def invite(ctx):
    """
    A command to get an invite link for the bot.
    """
    await ctx.send(f'here is a link you can use to invite me to your Discord guild! \N{SMILING FACE WITH OPEN MOUTH}'
                   ' \nhttps://discordapp.com/oauth2/authorize?client_id={bot_token}&scope=bot')

# ----test ping command ----
@bot.command(
    name='ping',  # this overrides the function name if you wanted
    aliases=['pong', 'beep'],
    brief='Ping pong hong kong long dong')
@log_who
async def ass_feck(ctx):
    """
    This is your docstring for the ass_feck function.
    Discord.py uses this as an extended description.
    """
    await ctx.send('Pong')


# ---- first iteration of profile-placeholder ----
@bot.command(cls=PinguuCommand)
@log_who
async def profile(ctx, id=None):
    """
    Displays the profile of the user belonging to the steamid provided
    """
    if id is None:
        await ctx.send(
            "\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64 to work.")
        return
    async with aiohttp.ClientSession() as session:
        if not id.isdigit():
            url = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
            params = {
                'key': steam_key,
                'format': 'json',
                'url_type': 1,
                'vanityurl': id
            }
            resp = await session.get(url, params=params)
            data = await resp.json()

            if data['response']['success'] != 1:
                return await ctx.send(data['response']['message'])
            id = data['response']['steamid']

        # url's of the API we're getting stuff from
        url1 = (
            'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/'
        )
        url2 = (
                'https://api.steampowered.com/IPlayerService/GetBadges/v1/'
        )

        resp1, resp2 = await asyncio.gather(
            session.get(url1, params={'key': steam_key, 'steamids': id}),
            session.get(url2, params={'key': steam_key, 'steamid': id})
        )
        data1, data2 = await asyncio.gather(
            resp1.json(), resp2.json()
        )
        data1 = data1['response']['players'][0]
        data2 = data2['response']
    # Variables that go into the message we're sending.
    # Store the info you want in variables
    name = data1['personaname']
    profile_url = data1['profileurl']
    avatar_img = data1['avatarfull']
    # ----
    if 'timecreated' in data1:
        created_on = time.strftime('%A, %d %B %Y at %I:%M%p', time.gmtime(data1['timecreated']))
    else:
        created_on = None
    # ----
    badge_count = len(data2.get('badges', []))
    # ----
    if 'realname' in data1:
        real_name = data1['realname']
    else:
        real_name = None
    # ----
    if 'gameextrainfo' in data1:
        current_game = data1['gameextrainfo']
    else:
        current_game = None
    # ----
    xp = data2.get('player_xp')
    level = data2.get('player_level')
    xp_needed = data2.get('player_xp_needed_to_level_up')

    # Takes an int and gets the profile state object
    state = profilestates.states[data1['personastate']]
    # ---- embed stuff ----
    embed = discord.Embed(title=f'Steam Profile of {name}', url=profile_url,
                          colour=state.colour)
    embed.set_thumbnail(url=avatar_img)
    if name is not None:
        embed.add_field(name='Profile Name:', value=name, inline=False)
    if real_name is not None:
        embed.add_field(name='Real Name:', value=real_name, inline=False)
    if current_game is not None:
        embed.add_field(name='Currently In Game:', value=current_game,
                        inline=False)
    if level is not None:
        embed.add_field(name='Current Steam Level:', value=f'{level:,}',
                        inline=False)
    if badge_count:
        embed.add_field(name='Number of Badges:', value=f'{badge_count}',
                        inline=False)
    if xp is not None:
        embed.add_field(name='Current XP', value=f'{xp:,}', inline=False)
    if xp_needed is not None:
        embed.add_field(name='XP Needed To Reach Next Level',
                        value=f'{xp_needed:,}', inline=False)
    if created_on is not None:
        embed.add_field(name='Profile created:', value=created_on, inline=True)
    if 'loccountrycode' in data1:
        country_emote = 'Country:  ' + chr(
            0x1f1e6 + ord(data1['loccountrycode'][0]) - ord('A')) + chr(
            0x1f1e6 + ord(data1['loccountrycode'][1]) - ord('A')) + ' '
        embed.add_field(name=country_emote, value='\u200b', inline=False)
    if len(embed.fields) == 0:
        embed.add_field(name='Private profile',
                        value='I can\'t read any info about you. \nDo you have a private profile?')
    embed.set_footer(text="Made with \N{HEAVY BLACK HEART} by Vee#4012")
    # NO! THIS IS FOR DISCORD.PY V0
    # await self.bot.say(embed=embed)
    # do this:
    print('Name:', name, 'State:', state, 'Level:', level, 'Badge count:',
          badge_count, 'Created on:', created_on)
    print(created_on)
    await ctx.send(embed=embed)


# ---- simple profile ----
@bot.command(enabled=False, cls=PinguuCommand)
@log_who
async def simpprofile(ctx, id=None):
    """
    Displays simplified information belonging to the steamid provided
    """
    if id is None:
        await ctx.send(
            "\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64 to work.")
        return

    if not id.isdigit():
        url = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
        params = {
            'key': steam_key,
            'format': 'json',
            'url_type': 1,
            'vanityurl': id
        }

        resp = requests.get(url, params=params)
        data = resp.json()
        if data['response']['success'] != 1:
            return await ctx.send(data['response']['message'])
        id = data['response']['steamid']

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
        country_emote = '' + chr(
            0x1f1e6 + ord(data1['loccountrycode'][0]) - ord('A')) + chr(
            0x1f1e6 + ord(data1['loccountrycode'][1]) - ord('A')) + ' '
    else:
        country_emote = 'N/A'
        # Takes an int and gets the profile state object
    state = profilestates.states[data1['personastate']]

    output_str = (f'Profile Name: {name}, state: {state}, Current Steam Level: '
                  f'{level:,}, Number of Badges: {badge_count:,}, xp: {xp:,}, '
                  f'XP Needed To Reach Next Level: {xp_needed:,}, Country: '
                  f'{country_emote}.')
    await ctx.send(output_str)


# --- getting a profile picture/avatar ---
@bot.command(cls=PinguuCommand)
@log_who
async def avatar(ctx, id=None):
    """
    Shows the avatar of a given steamid.
    """
    if id is None:
        await ctx.send('\N{FACE WITH OPEN MOUTH AND COLD SWEAT} '
                       'I need a steamid64 to work.')
        return

    if not id.isdigit():
        url = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
        params = {
            'key': steam_key,
            'format': 'json',
            'url_type': 1,
            'vanityurl': id
        }

        resp1 = requests.get(url, params=params)
        data = resp1.json()
        if data['response']['success'] != 1:
            return await ctx.send(data['response']['message'])
        id = data['response']['steamid']

    # url of the API we're getting stuff from
    url1 = (
        'https://api.steampowered.com/ISteamUser/GetPlayer'
        'Summaries/v2/'
    )

    async with aiohttp.ClientSession() as session:
        resp = await session.get(url1, params={'key': steam_key, 'steamids': id})
        data1 = (await resp.json())['response']['players'][0]

    # variables that go into the message we're sending.
    avatar_img = data1['avatarfull']
    state = profilestates.states[data1['personastate']]

    await ctx.send(avatar_img)


# ---- profile status ----
@bot.command(cls=PinguuCommand)
@log_who
async def status(ctx, id=None):
    """
    Gets the current status of a requested profile.
    """
    if id is None:
        await ctx.send(
            "\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64 to work.")
        return

    if not id.isdigit():
        url = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
        params = {
            'key': steam_key,
            'format': 'json',
            'url_type': 1,
            'vanityurl': id
        }

        resp = requests.get(url, params=params)
        data = resp.json()
        if data['response']['success'] != 1:
            return await ctx.send(data['response']['message'])
        id = data['response']['steamid']

    # url of the API we're getting stuff from.
    url1 = (
        'https://api.steampowered.com/ISteamUser/GetPlayer'
        'Summaries/v2/'
    )
    # gets stuff from the url in an 'easy to get' layout.
    async with aiohttp.ClientSession() as session:
        resp = await session.get(url1, params={'key': steam_key, 'steamids': id})
        data1 = (await resp.json())['response']['players'][0]
    # variables that go into the message we're sending.
    name = data1['personaname']
    state = profilestates.states[data1['personastate']]

    print(f'{name} is {state}.')
    await ctx.send(f'{name} is currently {state}.')


# ---- game info ----
@bot.command(cls=PinguuCommand)
@log_who
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
        game_name = None if app_id is None else await appid_cache.lookup_id(
            app_id)

    if app_id is None or game_name is None:
        await ctx.send('No match')
        return
    url1 = (
        'http://store.steampowered.com/api/appdetails'
    )
    url2 = (
        'https://api.steampowered.com/ISteamUserStats/'
        'GetNumberOfCurrentPlayers/v1/'
    )
    # gets stuff from the url in an 'easy to get' layout.
    async with aiohttp.ClientSession() as session:
        resp1, resp2 = await asyncio.gather(
            session.get(url1, params={'appids': app_id}),
            session.get(url2, params={'key': steam_key, 'appid': app_id})
        )
        data1, data2 = await asyncio.gather(
            resp1.json(), resp2.json()
        )
    data1 = data1[str(app_id)]['data']
    data2 = data2['response']

    desc = data1['short_description']
    clean_text = bs4.BeautifulSoup(desc, 'html.parser').text
    release_date = data1['release_date']['date']
    developers = data1['developers'][0]
    store = data1['support_info']['url']
    cc_players = data2['player_count']
    # app_id holds the app id now
    # game_name holds the game name string now

    embed = discord.Embed(title=game_name, color=random.randint(0, 0xFFFFFF))
    embed.add_field(name='Game Title:', value=game_name, inline=False)
    embed.add_field(name='Appid:', value=app_id, inline=False)
    if cc_players is not None:
        embed.add_field(name='Total Current Players:', value=f'{cc_players:,}',
                        inline=False)
    if developers is not None:
        embed.add_field(name='Developed by: ', value=developers, inline=False)
    if release_date is not None:
        embed.add_field(name='Released:', value=release_date, inline=False)
    if clean_text:
        embed.add_field(name='Description', value=clean_text, inline=False)
    if store:
        embed.add_field(name='Store Page:',
                        value=f'http://steamcommunity.com/app/{app_id}',
                        inline=False)
    embed.set_footer(text="Made with \N{HEAVY BLACK HEART} by Vee#4012")

    await ctx.send(embed=embed)


# ---- I need this to run the bot lol----
bot.run(discord_token)
