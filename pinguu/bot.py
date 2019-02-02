#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
import asyncio
import logging
import json
import random
import subprocess
import time
import requests

import aiohttp
import bs4
import discord
from discord.ext import commands

from . import profilestates
from . import appids
from . import pinguucmds
from . import steamidconv

appid_cache = appids.AppIdCacher()

logging.basicConfig(level='INFO')
# DEBUG < INFO < WARNING < ERROR < FATAL
logger = logging.getLogger('Pinguu')

# ---- bot prefix ----
bot = commands.Bot(
    command_prefix='!sl',
    owner_id=95721165607141376
)
bot.remove_command('help')
bot.load_extension('pinguu.pinguuhelp')


def command(**kwargs):
    kwargs.setdefault('cls', pinguucmds.PinguuCommand)

    def decorator(coro):
        cmd = commands.command(**kwargs)(coro)
        bot.add_command(cmd)
        return cmd

    return decorator


def group(**kwargs):
    kwargs.setdefault('cls', pinguucmds.PinguuGroup)

    def decorator(coro):
        cmd = commands.command(**kwargs)(coro)
        bot.add_command(cmd)
        return cmd

    return decorator


# ---- load token.json ----
with open('token.json') as fp:
    token = json.load(fp)

# ---- get the tokens from token.json ----
steam_key = token['s-key']
discord_token = token['d-token']
bot_token = token['b-token']
ladder_key = token['ladder-key']


@bot.listen()
async def on_ready():
    await bot.change_presence(
        # game=...
        # 7/4/2018 - 404 - Changed from `game' to `activity' as the API has
        #                  been changed.
        activity=discord.Game(name=f"{bot.command_prefix}help")
    )

@bot.listen()
async def on_reaction_add(reaction, user):
    if(user.id==bot.owner_id):
        if reaction.emoji == "❎":
            await reaction.message.delete()

@commands.is_owner()
@bot.command(brief='list servers')
async def servers(ctx):
    pag = commands.Paginator()

    for i, guild in enumerate(ctx.bot.guilds):
        owner = guild.owner

        pag.add_line(f'{i + 1:04}  {guild} | {owner} | {guild.id}')

    for page in pag.pages:
        await ctx.send(page)




@commands.is_owner()
@command(brief='Make an invite link.')
async def invite(ctx):
    """
    A command to get an invite link for the bot.
    """
    await ctx.author.send(
        'here is a link you can use to invite me to your Discord '
        'guild! \N{SMILING FACE WITH OPEN MOUTH}'
        ' \nhttps://discordapp.com/oauth2/authorize?client_id'
        f'={bot_token}&scope=bot')


# ----test ping command ----
@commands.is_owner()
@command(
    brief='Prints the latency.',
    hidden=True)
async def ping(ctx):
    """
    Tests that the bot is not dead.
    """
    await ctx.send(f'Pong @ {ctx.bot.latency * 1000:,.2f} ms.')

# ---- say command ----
@commands.is_owner()
@command(hidden=True)
async def say(ctx, *, message):
    await ctx.send(message)

# ---- steamladder position ----
@command(
    brief="Displays the requested players "
          "position on the steamladder.com ladder"
)
async def position(ctx, steamid=None):
    """Displays the requested players position on the steamladder.com ladder"""
    if steamid is None:
        await ctx.send(
            "\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64/"
            "customurl to work.")
        return
    async with aiohttp.ClientSession() as session:
        if not steamid.isdigit():
            url = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
            params = {
                'key': steam_key,
                'format': 'json',
                'url_type': 1,
                'vanityurl': steamid
            }
            resp = await session.get(url, params=params)
            data = await resp.json()

            if data['response']['success'] != 1:
                return await ctx.send(data['response']['message'])
            steamid = data['response']['steamid']

        # url of the API we're getting stuff from

        url = requests.get(
            f'https://steamladder.com/api/v1/profile/{steamid}/',
            headers={'Authorization': f'Token {ladder_key}'}
        )


        data = url.json()

    # variables that go into the message we're sending.
    name = data['steam_user']['steam_name']
    profileurl = data['steam_user']['steamladder_url']
    avatar_img = data['steam_user']['steam_avatar_src']
    ladderpos = data['ladder_rank']['worldwide_xp']
    laddergc = data['ladder_rank']['worldwide_games']
    ladderpt = data['ladder_rank']['worldwide_playtime']


    embed = discord.Embed(title=f'{name}', url=f'{profileurl}',
                          colour=random.randint(0, 0xFFFFFF))
    embed.set_thumbnail(url=avatar_img)
    embed.add_field(name='World Ranks:', value=f'Level Rank: #{ladderpos:,}\n'
                                               f'Playtime Rank: #{ladderpt:,}\n'
                                               f'Game Count Rank: #{laddergc:,}'
                    , inline=False)
    embed.set_footer(text="Data collected from steamladder.com")
    await ctx.send(embed=embed)

# ---- steamladder ladder ----
@command(brief="Displays the Top 10 profiles on the steamladder.com ladder")
async def ladder(ctx):
    async with aiohttp.ClientSession() as session:
        resp = requests.get(
            f'https://steamladder.com/api/v1/ladder/xp/',
            headers={'Authorization': f'Token {ladder_key}'}
        )
        data = resp.json()['ladder']

        embed = discord.Embed(title='Steamladder Top 10 Profiles',
                              url='https://steamladder.com/',
                              color=random.randint(0, 0xFFFFFF))
        embed.set_thumbnail(
            url="https://steamladder.com/static/img/new_logo.png"
        )
        embed.set_footer(
            text="Data collected from steamladder.com"
        )

        for i, value in enumerate(data):
            if i >= 10:
                break

            display_name = value['steam_user']['steam_name']
            url = value['steam_user']['steamladder_url']
            country_code = value['steam_user']['steam_country_code']
            link = f'[{display_name}]({url})'
            games_count = value['steam_stats']['games']
            badge_count = value['steam_stats']['badges']
            level = value['steam_stats']['level']
            xp = value['steam_stats']['xp']


            string = f'{link}  \n' \
                     f'Country: {country_code} \n' \
                     f' Level: {level} \n' \
                     f' XP: {xp:,} \n'
                     # f' Games: {games_count} \n' \
                     # f' Badges: {badge_count}'


            embed.add_field(name=f'#{i+1}', value=string, inline=True)
        await ctx.send(embed=embed)


# ---- getting profile and player info ----
@command(
    brief='Displays the profile of the user belonging to the steamid/customurl'
          ' provided')
async def profile(ctx, steamid=None):
    """
    Displays the profile of the user belonging to the steamid provided.

    !slprofile steamid/customurl
    """
    if steamid is None:
        await ctx.send(
            "\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64/"
            "customurl to work.")
        return
    async with aiohttp.ClientSession() as session:
        if not steamid.isdigit():
            url = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
            params = {
                'key': steam_key,
                'format': 'json',
                'url_type': 1,
                'vanityurl': steamid
            }
            resp = await session.get(url, params=params)
            data = await resp.json()

            if data['response']['success'] != 1:
                return await ctx.send(data['response']['message'])
            steamid = data['response']['steamid']

        # url's of the API we're getting stuff from
        url1 = (
            'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/'
        )
        url2 = (
            'https://api.steampowered.com/IPlayerService/GetBadges/v1/'
        )
        url3 = (
            'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/'
        )
        url4 = (
            'https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/'
        )

        resp1, resp2, resp3, resp4 = await asyncio.gather(
            session.get(url1, params={'key': steam_key, 'steamids': steamid}),
            session.get(url2, params={'key': steam_key, 'steamid': steamid}),
            session.get(url3, params={'key': steam_key, 'steamid': steamid}),
            session.get(url4, params={'key': steam_key, 'steamids': steamid})
        )
        data1, data2, data3, data4 = await asyncio.gather(
            resp1.json(), resp2.json(), resp3.json(), resp4.json()
        )
        data1 = data1['response']['players'][0]
        data2 = data2['response']
        data3 = data3['response'].get('games')
        data4 = data4['players'][0]

    # Variables that go into the message we're sending.
    # Store the info you want in variables
    name = data1['personaname']
    profile_url = data1['profileurl']
    avatar_img = data1['avatarmedium']
    # ----
    if 'timecreated' in data1:
        created_on = time.strftime('%A, %d %B %Y ',
                                   time.gmtime(data1['timecreated']))
    else:
        created_on = None
    # ----
    badge_count = len(data2.get('badges', []))
    # ----
    if 'realname' in data1:
        real_name = data1['realname']
    else:
        real_name = '\N{ZERO WIDTH SPACE}'
    # ----
    if 'gameextrainfo' in data1:
        current_game = data1['gameextrainfo']
    else:
        current_game = None
    # ----
    xp = data2.get('player_xp')
    level = data2.get('player_level')
    xp_needed = data2.get('player_xp_needed_to_level_up')

    if data3 is not None:
        tpt = 0
        for game in data3:
            tpt += game['playtime_forever']
    else:
        tpt = None

    if data3 is not None:
        apt = 0
        for game in data3:
            apt += game.get('playtime_2weeks', 0)
    else:
        apt = None

    CommunityBanned = data4['CommunityBanned']
    VACBanned = data4['VACBanned']
    EconomyBan = data4['EconomyBan']

    # Takes an int and gets the profile state object
    state = profilestates.states[data1['personastate']]
    steam_id = steamidconv.community_to_steam(int(steamid))
    # ---- embed stuff ----
    embed = discord.Embed(title=f'Steam Profile of {name}', url=profile_url,
                          colour=state.colour)
    embed.set_thumbnail(url=avatar_img)
    if name is not None:
        embed.add_field(name='Profile Name', value=name)

    if real_name is not None:
        real_name = real_name.strip()
        embed.add_field(name='Real Name', value=real_name)


    if current_game is not None:
        embed.add_field(name='Currently In Game', value=current_game)

    if level is not None:
        embed.add_field(name='Current Steam Level', value=f'{level:,}')

    if badge_count:
        embed.add_field(name='Number of Badges', value=f'{badge_count:,}')

    if xp is not None:
        embed.add_field(name='Current XP', value=f'{xp:,}')

    if data3 is not None:
        embed.add_field(name='Total Playtime:', value=f'{tpt/60:,.0f} hours')

    if data3 is not None:
        embed.add_field(name='Playtime Last 2 Weeks:',
                        value=f'{apt/60:,.0f} hours')

    if xp_needed is not None:
        embed.add_field(name='To Reach Next Level',
                        value=f'{xp_needed:,}'
                              f' XP ({xp_needed // 100+1} badges.)')

    if 'loccountrycode' in data1:
        country_emote = 'Country: ' + chr(
            0x1f1e6 + ord(data1['loccountrycode'][0]) - ord('A')) + chr(
            0x1f1e6 + ord(data1['loccountrycode'][1]) - ord('A')) + ' '
        embed.add_field(name=country_emote, value='\u200b')

    if created_on is not None:
        embed.add_field(name='Profile created', value=created_on)

    embed.add_field(name='Community Status', value=f'**Community Banned**:'
                                                   f' {CommunityBanned}\n '
                                                   f'**VAC Banned**:'
                                                   f' {VACBanned}\n '
                                                   f'**Market Bans**:'
                                                   f' {EconomyBan}',
                    inline=False)
    embed.add_field(name="SteamID's", value=f'**SteamID64**:\n{steamid}\n'
                                            f'**SteamID**:\n{steam_id}')

    if len(embed.fields) == 0:
        embed.add_field(name='Private profile',
                        value='I can\'t read any info about you. \nDo you '
                              'have a private profile?')
    # NO! THIS IS FOR DISCORD.PY V0
    # await self.bot.say(embed=embed)
    # do this:
    print('Name:', name, 'State:', state, 'Level:', level, 'Badge count:',
          badge_count, 'Created on:', created_on)
    await ctx.send(embed=embed)


# --- getting a profile picture/avatar ---
@command(brief='Shows the avatar of a given steamid/profile')
async def avatar(ctx, steamid=None):
    """
    Shows the avatar of a given steamid/profile.

    !slavatar username
    """
    if steamid is None:
        await ctx.send(
            "\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64/"
            "customurl to work.")
        return

    async with aiohttp.ClientSession() as session:
        if not steamid.isdigit():
            url = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
            params = {
                'key': steam_key,
                'format': 'json',
                'url_type': 1,
                'vanityurl': steamid
            }

            data = await (await session.get(url, params=params)).json()
            if data['response']['success'] != 1:
                return await ctx.send(data['response']['message'])
            steamid = data['response']['steamid']

        # url of the API we're getting stuff from
        url1 = (
            'https://api.steampowered.com/ISteamUser/GetPlayer'
            'Summaries/v2/'
        )

        resp = await session.get(url1,
                                 params={'key': steam_key, 'steamids': steamid})
        data1 = (await resp.json())['response']['players'][0]
        state = profilestates.states[data1['personastate']]

    # variables that go into the message we're sending.
    avatar_img = data1['avatarfull']
    # gstate = profilestates.states[data1['personastate']]

    embed = discord.Embed(colour=state.colour)
    embed.set_image(url=avatar_img)
    await ctx.send(embed=embed)


# ---- profile status ----
@command(brief='Gets the current status of a requested profile.')
async def status(ctx, steamid=None):
    """
    Gets the current status of a requested profile.

    !slstatus steamid/customurl
    """
    if steamid is None:
        await ctx.send(
            "\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64/"
            "customurl to work.")
        return

    async with aiohttp.ClientSession() as session:
        if not steamid.isdigit():
            url = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
            params = {
                'key': steam_key,
                'format': 'json',
                'url_type': 1,
                'vanityurl': steamid
            }

            data = await (await session.get(url, params=params)).json()
            if data['response']['success'] != 1:
                return await ctx.send(data['response']['message'])
            steamid = data['response']['steamid']

        # url of the API we're getting stuff from.
        url1 = (
            'https://api.steampowered.com/ISteamUser/GetPlayer'
            'Summaries/v2/'
        )
        # gets stuff from the url in an 'easy to get' layout.
        resp = await session.get(url1,
                                 params={'key': steam_key, 'steamids': steamid})
        data1 = (await resp.json())['response']['players'][0]
    # variables that go into the message we're sending.

    name = data1['personaname']
    state = profilestates.states[data1['personastate']]

    print(f'{name} is {state}.')
    if 'gameextrainfo' in data1:
        current_game = data1['gameextrainfo']
        await ctx.send(
            f'{name} is currently {state} and playing {current_game}.')
    else:
        await ctx.send(f'{name} is currently {state}.')

# ---- Level command ---
@command(brief='Provides a small info card with a players level')
async def level(ctx, steamid=None):
    """
    Shows the avatar of a given steamid/profile.

    !slavatar username
    """
    if steamid is None:
        await ctx.send(
            "\N{FACE WITH OPEN MOUTH AND COLD SWEAT} I need a steamid64/"
            "customurl to work.")
        return
    async with aiohttp.ClientSession() as session:
        if not steamid.isdigit():
            url = 'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/'
            params = {
                'key': steam_key,
                'format': 'json',
                'url_type': 1,
                'vanityurl': steamid
            }
            resp = await session.get(url, params=params)
            data = await resp.json()

            if data['response']['success'] != 1:
                return await ctx.send(data['response']['message'])
            steamid = data['response']['steamid']

        # url of the API we're getting stuff from
        url1 = (
            'https://api.steampowered.com/ISteamUser/GetPlayer'
            'Summaries/v2/'
        )
        url2 = (
            'https://api.steampowered.com/IPlayerService/GetBadges/v1/'
        )

        resp1, resp2 = await asyncio.gather(
            session.get(url1, params={'key': steam_key, 'steamids': steamid}),
            session.get(url2, params={'key': steam_key, 'steamid': steamid})
        )
        data1, data2 = await asyncio.gather(
            resp1.json(), resp2.json()
        )
        data1 = data1['response']['players'][0]
        data2 = data2['response']

        state = profilestates.states[data1['personastate']]

    # variables that go into the message we're sending.
    name = data1['personaname']
    profileurl = data1['profileurl']
    avatar_img = data1['avatarfull']

    embed = discord.Embed(title=f'{name}', url=f'{profileurl}', colour=state.colour)
    embed.set_thumbnail(url=avatar_img)

    if 'player_level' in data2 is not None:
        level = data2['player_level']
    if 'player_xp' in data2 is not None:
        xp = data2['player_xp']
        # ---- bar calculation
        current_total_xp = data2['player_xp']
        remaining_to_level_up = data2['player_xp_needed_to_level_up']
        current_level_xp_base = data2['player_xp_needed_current_level']

        xp_points_since_level_up = current_total_xp - current_level_xp_base

        level_total_xp = xp_points_since_level_up + remaining_to_level_up
        level_progress = xp_points_since_level_up / level_total_xp
        max_bar_width = 20
        bar_length = int(level_progress * max_bar_width)

        space = max_bar_width - bar_length

        bar = '[' + ('#' * bar_length) + (u'\u2002' * space) + ']'
    # ---- end bar calculation

        embed.add_field(name='Level Info', value=f'\nLevel: {level} || XP: {xp:,}\n '
                        f'`{bar}` {level_progress*100:.0F}%', inline=False)
    else:
        embed.add_field(name='Level Info', value='\nPrivate', inline=False)
    await ctx.send(embed=embed)


# ---- game info ----
@command(brief='Provides information about a game.')
async def game(ctx, *, content):
    """
    Provides information about a game given the title or Appid.

    !slgame appid/name of game
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
    header_img = data1['header_image']
    cc_players = data2['player_count']


    if 'price_overview' in data1:
        data = data1['price_overview']
        price = data['final'] / 100
        currency = data['currency']
        price = f'{price} {currency}'
    else:
        price = 'Free'

    # price = round(price, 2)
    # app_id holds the app id now
    # game_name holds the game name string now

    embed = discord.Embed(title=game_name, color=random.randint(0, 0xFFFFFF))
    embed.set_image(url=header_img)
    embed.add_field(name='Game Title:', value=game_name)
    embed.add_field(name='Appid:', value=str(app_id))
    if cc_players is not None:
        embed.add_field(name='Total Current Players:', value=f'{cc_players:,}')
    if developers is not None:
        embed.add_field(name='Developed by: ', value=developers)
    if price is not None:
        embed.add_field(name='Price: ', value=f'{price}')
    else:
        embed.add_field(name='Price:', value='Free')
    if release_date is not None:
        embed.add_field(name='Released:', value=release_date)
    if clean_text:
        embed.add_field(name='Description', value=clean_text, inline=False)
    embed.add_field(name='Store Page:',
                    value=f'https://store.steampowered.com/app/{app_id}',
                    inline=False)

    await ctx.send(embed=embed)

@commands.is_owner()
@command(name='update',
         brief='Executes git-pull on the repository, and DMs you the output.')
async def git_pull(ctx, *extra_args):
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


@commands.is_owner()
@command(name='stop', brief='Stops the bot.')
async def stop(ctx):
    await ctx.send('Goodbye.')
    await bot.logout()


# ---- I need this to run the bot lol----
bot.run(discord_token)
