#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import random
import subprocess
import time
import requests

import aiohttp
import bs4
import discord

from pinguu import profilestates, steamidconv
from . import pinguucmds as commands


class SteamLadderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(
            # game=...
            # 7/4/2018 - 404 - Changed from `game' to `activity' as the API has
            #                  been changed.
            activity=discord.Game(name=f"{self.bot.command_prefix}help")
        )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user: discord.User):
        cross = "\N{NEGATIVE SQUARED CROSS MARK}"
        if all((user.id == self.bot.owner_id, reaction.message.author == self.bot.user,
                reaction.emoji == cross)):
            await reaction.message.delete()

    # ---- steamladder position ----
    @commands.command(brief="Displays the requested players position on the steamladder.com ladder")
    async def position(self, ctx, steamid=None):
        """Displays the requested players position on the steamladder.com ladder"""
        config = ctx.bot.configuration
        steam_key, ladder_key = config.steam_key, config.ladder_key

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
        embed.add_field(
            name='World Ranks:',
            value='\n'.join((
                f'Level Rank: #{ladderpos:,}',
                f'Playtime Rank: #{ladderpt:,}',
                f'Game Count Rank: #{laddergc:,}',
            )),
            inline=False)
        embed.set_footer(text="Data collected from steamladder.com")
        await ctx.send(embed=embed)

    # ---- steamladder ladder ----
    @commands.command(brief="Displays the Top 10 profiles on the steamladder.com ladder")
    async def ladder(self, ctx):
        ladder_key = ctx.bot.configuration.ladder_key

        async with aiohttp.ClientSession() as session:
            resp = await session.get(f'https://steamladder.com/api/v1/ladder/xp/',
                                     headers={'Authorization': f'Token {ladder_key}'})
            resp.raise_for_status()
            data = await resp.json()
            data = data['ladder']

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
                level = value['steam_stats']['level']
                xp = value['steam_stats']['xp']
                if country_code is not None:
                    country_code = chr(
                        0x1f1e6 + ord(value['steam_user']['steam_country_code'][0]) - ord(
                            'A')) + chr(
                        0x1f1e6 + ord(value['steam_user']['steam_country_code'][1]) - ord(
                            'A')) + ' '
                else:
                    country_code = discord.utils.get(ctx.bot.emojis, name="missingflag")

                string = '\n'.join((
                    link,
                    f'Country: {country_code}',
                    f'Level: {level:,}',
                    f'XP: {xp:,}'
                ))

                embed.add_field(name=f'#{i + 1}', value=string, inline=True)
            await ctx.send(embed=embed)

    # ---- getting profile and player info ----
    @commands.command(
        brief='Displays the profile of the user belonging to the steamid/customurl provided')
    async def profile(self, ctx, steamid=None):
        """
        Displays the profile of the user belonging to the steamid provided.

        !slprofile steamid/customurl
        """
        steam_key = ctx.bot.configuration.steam_key

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
                resp.raise_for_status()
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

        community_banned = data4['CommunityBanned']
        vac_banned = data4['VACBanned']
        economy_banned = data4['EconomyBan']

        # Takes an int and gets the profile state object
        state = profilestates.find_by_id(data1['personastate'])
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
            embed.add_field(name='Total Playtime:', value=f'{tpt / 60:,.0f} hours')

        if data3 is not None:
            embed.add_field(name='Playtime Last 2 Weeks:',
                            value=f'{apt / 60:,.0f} hours')

        if xp_needed is not None:
            embed.add_field(name='To Reach Next Level',
                            value=f'{xp_needed:,}'
                            f' XP ({xp_needed // 100 + 1} badges.)')

        if 'loccountrycode' in data1:
            country_emote = 'Country: ' + chr(
                0x1f1e6 + ord(data1['loccountrycode'][0]) - ord('A')) + chr(
                0x1f1e6 + ord(data1['loccountrycode'][1]) - ord('A')) + ' '
            embed.add_field(name=country_emote, value='\u200b')

        if created_on is not None:
            embed.add_field(name='Profile created', value=created_on)

        embed.add_field(
            name='Community Status',
            value='\n'.join((
                f'**Community Banned**: {community_banned}',
                f'**VAC Banned**: {vac_banned}',
                f'**Market Bans**: {economy_banned}'
            )),
            inline=False)

        embed.add_field(
            name="SteamID's",
            value='\n'.join((
                '**SteamID64**:',
                str(steamid),
                '**SteamID**:',
                str(steam_id)
            ))
        )

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
    @commands.command(brief='Shows the avatar of a given steamid/profile')
    async def avatar(self, ctx, steamid=None):
        """
        Shows the avatar of a given steamid/profile.

        !slavatar username
        """
        steam_key = ctx.bot.configuration.steam_key

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
                resp.raise_for_status()
                data = await resp.json()
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
            state = profilestates.find_by_id(data1['personastate'])

        # variables that go into the message we're sending.
        avatar_img = data1['avatarfull']

        embed = discord.Embed(colour=state.colour)
        embed.set_image(url=avatar_img)
        await ctx.send(embed=embed)

    # ---- profile status ----
    @commands.command(brief='Gets the current status of a requested profile.')
    async def status(self, ctx, steamid=None):
        """
        Gets the current status of a requested profile.

        !slstatus steamid/customurl
        """
        steam_key = ctx.bot.configuration.steam_key

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
                resp.raise_for_status()
                data = await resp.json()
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
        state = profilestates.find_by_id(data1['personastate'])

        print(f'{name} is {state}.')
        if 'gameextrainfo' in data1:
            current_game = data1['gameextrainfo']
            await ctx.send(
                f'{name} is currently {state} and playing {current_game}.')
        else:
            await ctx.send(f'{name} is currently {state}.')

    # ---- Level command ---
    @commands.command(brief='Provides a small info card with a players level')
    async def level(self, ctx, steamid=None):
        """
        Shows the avatar of a given steamid/profile.

        !slavatar username
        """
        steam_key = ctx.bot.configuration.steam_key

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
                resp.raise_for_status()
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

            state = profilestates.find_by_id(data1['personastate'])

        # variables that go into the message we're sending.
        name = data1['personaname']
        profileurl = data1['profileurl']
        avatar_img = data1['avatarfull']

        embed = discord.Embed(title=f'{name}', url=f'{profileurl}', colour=state.colour)
        embed.set_thumbnail(url=avatar_img)

        if 'player_level' in data2 is not None:
            level = data2['player_level']
        else:
            level = 0

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

            embed.add_field(
                name='Level Info',
                value=f'\nLevel: {level} || XP: {xp:,}\n `{bar}` {level_progress * 100:.0F}%',
                inline=False
            )
        else:
            embed.add_field(name='Level Info', value='\nPrivate', inline=False)
        await ctx.send(embed=embed)

    # ---- game info ----
    @commands.command(brief='Provides information about a game.')
    async def game(self, ctx, *, content):
        """
        Provides information about a game given the title or Appid.

        !slgame appid/name of game
        """
        if content.isdigit():
            app_id = int(content)
            # This just means the text is formatted the way steam does it.
            game_name = await ctx.bot.app_id_cache.lookup_id(app_id)
        else:
            app_id = await ctx.bot.app_id_cache.lookup_name(content)
            game_name = None if app_id is None else await ctx.bot.app_id_cache.lookup_id(
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
                session.get(url2, params={'key': ctx.bot.configuration.steam_key, 'appid': app_id})
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




def setup(bot):
    bot.add_cog(SteamLadderCog(bot))
