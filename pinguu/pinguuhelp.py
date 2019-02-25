#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Wasn't happy with the default help manager for the bot, so I stole
the one Neko uses. This has a whole load of dependencies though, so they
are all going to be dumped in this file until I can be bothered to rewrite
it properly.

- Espeonageon (taken from the first iteration of the Neko bot. This module
    is deprecated, buggy and poorly engineered. Please don't hate me).
"""
import asyncio
import collections
import re
import traceback
import typing

import discord

from . import pinguucmds as commands


# Dodger blue.
default_color = 0x391841

Page = discord.Embed


def replace_recursive(text, to_match, repl=''):
    """
    Works the same as str.replace, but recurses until no matches can be found.
    Thus, ``replace_recursive('hello_wooorld', 'oo', '')`` would replace
    ``wooorld`` with ``woorld`` on the first pass, and ``woorld`` with
    ``world`` on the second.
    Note that ``str.replace`` only performs one pass, so
    ``'wooorld'.replace('oo', 'o')`` would return ``woorld``.
    :param text: the text to operate on.
    :param to_match: the text to match.
    :param repl: what to replace any matches with.
    :return: text, guaranteed to not contain ANY instances of ``to_match``.
    """
    while to_match in text:
        text = text.replace(to_match, repl)
    return text


def capitalise(string):
    """
    Capitalises the first character of a string and returns the string.
    """
    # We don't use a single index, as if the string is zero length, this
    # would raise an out of bounds exception. Instead, using ranges of indexes
    # will only output the maximum length string possible.
    return string[:1].upper() + string[1:]


# Americans GTFO
capitalize = capitalise


def pascal_to_space(text):
    """
    Takes a string in PascalCaseFormatting and attempts to detect
    any word boundaries. Spaces are inserted in detected word boundaries
    and the modified string is returned.
    """
    # We only match if we have a lowercase letter followed by an uppercase one.
    # We do not account for internal spaces existing.
    result = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text, flags=re.U | re.M)
    return result.title()


def underscore_to_space(text):
    """
    Takes a string of underscore separated words and converts it into
    space separated words.
    """
    # Replace multiple underscores recursively until no more exist.
    # We could use regex, but that is going at it with a hammer.
    # str.replace(self, text, repl) only performs a single pass.

    return replace_recursive(text, '__', '_').replace('_', ' ').title()


def pluralise(cardinality, *args, method='app'):
    """
    Pluralises the given measurement.
    e.g.
          pluralise(12, 'echo', 'es') => '12 echoes'
          pluralise(1, 'echo', 'es') => '1 echo'
          pluralise(1, 'request', method='per append') => 'per request'
          pluralise(32, 'request', method='per append') => 'per 34 requests'
    Do not rely on this in a performance-critical situation. It is slow and
    inefficient; however, for most day-to-day occasional uses, this overhead
    is negligible.
    :param cardinality: numeric value.
    :param args: zero or more arguments, depending on the specified method.
    :param method: the method to pluralise by.
    Methods
    -------
    - **'app[end]'** (default)
        args[0]: singular name (e.g. pass)
        args[1]: plural: what to append on the end (e.g. 'es')
        If cardinality == 1, the singular is used.
        If cardinality != 1, the plural is appended to the singular.
        If args[1] is not specified, it defaults to 's'.
    - **'repl[ace]'**
        args[0]: singular name (e.g. goose)
        args[1]: plural name (e.g. geese)
        If cardinality == 1, the singular is used.
        If cardinality != 1, the plural is used.
    - **'per app[end]'**
        See 'append' for arguments and rules.
        Appends "per " to the start of the result.
        Additionally, if cardinality == 1, the cardinality is omitted from the
        output.
    - **'per repl[ace]'**
        See 'replace' for arguments and rules.
        Appends "per " to the start of the result.
        Additionally, if cardinality == 1, the cardinality is omitted from the
        output.
    - **'th'**
        Expects NO additional arguments.
        Expects cardinality to be an integer. Will not accept a float, or a
        negative integer.
        Assuming the `x` in the following is replaced with the cardinality...
        If cardinality == 0, 4, 5, 6, 10, 11, 12, 13, 14, 15, .. 20, 30, .. etc
            return 'xth'
        If cardinality == 1, 21, 31, .., 101, 121, .. etc
            return 'xst'
        If cardinality == 2, 22, 32, .. etc
            return 'xnd'
        If cardinality == 3, 23, 33, .. etc
            return 'xrd'
    """
    # Make life a bit easier.
    method = method.lower()

    def replace(s, p):
        return f'{cardinality} {s if cardinality == 1 else p}'

    def per_replace(s, p):
        if cardinality - 1:
            return f'per {cardinality} {p}'
        else:
            return f'per {s}'

    try:
        if method.startswith('app'):
            singular = args[0]
            plural = args[1] if len(args) > 1 else 's'
            replacement = singular + plural
            return replace(singular, replacement)
        elif method.startswith('repl'):
            return replace(*args)
        elif method.startswith('per app'):
            singular = args[0]
            plural = args[1] if len(args) > 1 else 's'
            replacement = singular + plural
            return per_replace(singular, replacement)
        elif method.startswith('per repl'):
            return per_replace(*args)
        elif method == 'th':
            if not isinstance(cardinality, int) or cardinality < 0:
                raise TypeError('This method only works with an integer '
                                'cardinality that is greater than or equal '
                                'to zero.')
            tens = cardinality % 100
            units = cardinality % 10
            if tens // 10 == 1 or units > 3 or units == 0:
                return f'{cardinality}th'
            elif units == 1:
                return f'{cardinality}st'
            elif units == 2:
                return f'{cardinality}nd'
            elif units == 3:
                return f'{cardinality}rd'
            else:
                assert False, f'Algorithm won\'t handle input {cardinality}'
        else:
            raise ValueError(f'Unexpected method {method} for args {args}')
    except IndexError:
        raise TypeError('Incorrect number of arguments...')


# Again, damn 'muricans.
pluralize = pluralise


def remove_single_lines(text):
    """
    Replaces single line breaks with spaces. Double line breaks
    are kept as they are. If the text param is None, it is substituted with
    an empty string.
    """
    # To make line sizes a bit easier to handle, we remove single line breaks
    # and replace them with a space, similar to what markdown does. To put a
    # single line break in explicitly, add "\r".
    if text is None:
        text = ''

    d = '\n\n'.join(line.replace('\n', ' ') for line in text.split('\n\n'))
    d = d.replace('\r\n', '\n')
    return d


def ellipses(text: str, max_length: int):
    """
    Takes text as input, and returns it as long as it is less than
    max_length. If it is over this, then ellipses are placed over the last
    three characters and the substring from the start to the boundary is
    returned.
    This makes arbitrarily long text blocks safe to place in messages and
    embeds.
    """
    if len(text) > max_length:
        ellipse = '...'
        return text[0:max_length - len(ellipse)] + ellipse
    else:
        return text


def parse_quotes(string, quotes=None, delimit_on=None):
    """
    Delimits the given string using a quotation mark parser.
    :param string: the string to parse. Go figure!
    :param quotes: the quotation marks to delemit on. Defaults to single
            and double quotations.
    :param delimit_on: the characters to usually separate on. Defaults
            to space characters
    """
    if not quotes:
        quotes = {'\'', '"'}
    elif isinstance(quotes, str):
        quotes = {quotes}

    if not delimit_on:
        delimit_on = {' '}
    elif isinstance(delimit_on, str):
        delimit_on = {delimit_on}

    # Holds parsed strings.
    stack = None
    strs = []
    current_str = []

    def empty_current():
        """
        Clears the current string if it is not empty, and places it in
        the results list.
        """
        if current_str:
            # Push the current string onto the strs list.
            strs.append(''.join(current_str))
            current_str.clear()

    while string:
        # Stores whether we have mutated the string already in this iteration.
        has_mutated = False
        for quote in quotes:
            if string.startswith(f'\\{quote}'):
                current_str.append(quote)
                string = string[1 + len(quote):]
                # Onto the next character.
                has_mutated = True

            # If the string starts with a quotation, and the stack is either
            # holding the same character (thus a closing quotation), or the
            # stack is empty (thus an opening quotation while not in existing
            #  quotations).
            elif string.startswith(quote) and (quote == stack or stack is None):
                if stack == quote:
                    stack = None
                    empty_current()
                else:
                    stack = quote

                # Onto the next character.
                string = string[len(quote):]
                has_mutated = True

        if has_mutated:
            continue
        elif stack is None:
            for delimiter in delimit_on:
                if string.startswith(delimiter):
                    empty_current()
                    has_mutated = True
                    string = string[len(delimiter):]
            if has_mutated:
                continue
        # Else, just shift the first character.
        current_str.append(string[0])
        string = string[1:]

    # Empty the string if it is not empty.
    empty_current()

    # If the stack is not empty, we have an issue.
    if stack is not None:
        raise ValueError(f'Expected closing {stack} character.')

    return strs


class PatternCollection(collections.MutableSet):
    """
    Implements a set of patterns. These can be strings or regular expressions.
    """

    def __init__(self, *args):
        self._set = set()
        [self.add(arg) for arg in args]

    class _MatchableString:
        """Wrapper for a string that has a match method."""

        def __init__(self, string):
            self.string = string

        def __get__(self, instance, owner):
            return self.string

        def __missing__(self, key):
            return getattr(self.string, key)

        def __str__(self):
            return self.string

        def __repr__(self):
            return self.string

        # Compatibility with regex pattern object.

        @property
        def pattern(self):
            return self.string

        def match(self, other):
            return other == self.string

    def add(self, value):
        assert isinstance(value, (str, type(re.compile(''))))
        if isinstance(value, str):
            value = self._MatchableString(value)
        self._set.add(value)

    def discard(self, value):
        self._set.discard(value)

    def __iter__(self):
        return iter(self._set)

    def __contains__(self, item):
        for patt in self:
            if patt.match(item):
                return True
        return False

    def __eq__(self, other):
        return all(other_el in self for other_el in other)

    def __str__(self):
        return ', '.join(str(pat.pattern) for pat in self)

    def __len__(self):
        return len(self._set)

    def __missing__(self, key):
        return getattr(self._set, key)


DEV = False

# For debugging. If DEV is a global and is set to True, then
# any coroutine that is called using this ensure_future signature
# will be gathered rather than the future being ensured. This has
# the side effect of running "synchronously". The reason for
# wanting such a function is that any exceptions will propagate
# fully out of gather, whereas they are just printed and ignored
# in asyncio.ensure_future. This is a pain when trying to debug
# any issues, as we cannot get a full traceback.
if DEV:
    def ensure_future(coro, *_):
        return coro
else:
    ensure_future = asyncio.ensure_future


class Button:
    """
    A button for a book. This should decorate a coroutine to perform when
    clicked.
    """
    __slots__ = (
        'invoke',
        'emoji',
        'always_show'
    )

    def __new__(cls, emoji: str, show_if_one_page=True):
        """
        Generates a new button.
        :param emoji: the emoji to decorate the button with.
        :param show_if_one_page: defaults to True. If False, then the button
                is only displayed if more than one page is present in the
                pagination.
        :return: a decorator for a coroutine describing what to do when
                the button is clicked. The first parameter is the parent
                book object, the second is the current page, which is an
                embed.
        """
        if len(emoji) != 1:
            raise ValueError('Emoji must be a single character.')
        else:
            def decorator(coro: typing.Callable[['Book', 'Page'], None]):
                btn = object.__new__(cls)

                setattr(btn, 'emoji', emoji)
                setattr(btn, 'invoke', coro)
                setattr(btn, 'always_show', show_if_one_page)

                return btn

            return decorator


class Book:
    """
    A book is a collection of pages, along with an associated page number.
    """
    __slots__ = (
        'pages',  # Collection of embeds.
        '_page_index',  # 0-based page index. Access via `index` or `page_no`.
        'buttons',  # Collection of buttons.
        '_ctx',  # The context to reply to.
        '_msg',  # The message containing the current page. This is set on send.
        'timeout'  # How long to idle for before destroying pagination.
    )

    def __init__(self,
                 ctx: commands.Context,
                 timeout: float = 120,
                 buttons: typing.Iterable = None):
        """
        Initialises the pages.
        :param ctx: the message context we are replying to.
        :param buttons: the buttons to display on the Book. If none, default
                buttons are generated instead.
        :param timeout: time to wait before destroying pagination.
                Defaults to 120 seconds.
        """
        self.pages = []
        self._page_index = 0

        if timeout <= 0:
            raise ValueError('Timeout must be positive and nonzero.')

        self.timeout = timeout

        if buttons is None:
            buttons = self.generate_buttons()

        self.buttons: typing.Dict[str, Button] = {}

        for button in buttons:
            if not isinstance(button, Button):
                raise TypeError('Each button must be a Button object.')
            else:
                self.buttons[button.emoji] = button

        self._ctx = ctx

    @property
    def context_invoked_from(self) -> commands.Context:
        """Gets the context we were invoked from."""
        return self._ctx

    @property
    def response_message(self) -> typing.Optional[discord.Message]:
        """Gets the response message we sent."""
        return self._msg

    @property
    def index(self):
        """Gets the page index. This is a zero-based index."""
        return self._page_index

    @index.setter
    def index(self, new):
        """
        Sets the page index. This is a zero-based index, but will wrap
        around relative to the start/end of the pages, thus -1 would be
        the same as setting the last page, etc.
        """
        # Wraps the index around at the front and rear.
        while new < 0:
            new += len(self)
        while new >= len(self):
            new -= len(self)

        self._page_index = new

    @property
    def page_no(self):
        """Gets the page number. This is a one-based index."""
        return self._page_index + 1

    @page_no.setter
    def page_no(self, new):
        """
        Sets the page number. This is a one-based index and does not wrap
        around like index does.
        """
        if 0 < new <= len(self.pages):
            self._page_index = new - 1
        else:
            raise IndexError(
                f'Page number {new} is outside range [1...{len(self.pages)}]'
            )

    @property
    def page(self) -> Page:
        """Gets the current page."""
        return self.pages[self._page_index]

    def add_page(self, *, index=None, **kwargs) -> discord.Embed:
        """
        Attempts to create an embed from the given kwargs, adding it
        to the page collection.
        If you have pre-made an embed, then just call `btn.pages.append()`
        instead.
        If index is None, it is added to the end of the collection, otherwise,
        it is inserted at the given index into the list.
        The embed is then returned.
        """
        embed = discord.Embed(**kwargs)

        if index is None:
            self.append(embed)
        else:
            self.insert(index, embed)

        return embed

    def __iter__(self):
        """Iterates across each page in order."""
        yield from self.pages

    def __len__(self):
        """Counts the pages."""
        return len(self.pages)

    def __contains__(self, item):
        """True if the given item is a page in the collection."""
        return item in self.pages

    def __getitem__(self, index: int):
        """Gets the page at the given zero-based index."""
        return self.pages[index]

    def __iadd__(self, other: Page):
        """
        If a Page (a discord Embed) is given, we append the page to the end
        of the collection of pages.
        """
        if not isinstance(other, Page):
            raise TypeError('Expected embed.')
        else:
            self.pages.append(other)
            return self

    def append(self, page: Page):
        """Appends the page."""
        if not isinstance(page, Page):
            raise TypeError('Expected embed.')
        else:
            self.pages.append(page)

    def insert(self, index, page):
        """
        Inserts the page at a given 0-based index.
        """
        index = int(index)
        if not isinstance(page, Page):
            raise TypeError('Expected embed.')
        elif not 0 <= index <= len(self.pages):
            raise IndexError(
                f'Page number {index} is outside range [0,{len(self.pages)}]'
            )
        else:
            self.pages.insert(index, page)

    async def send(self):
        """
        Sends the message and waits for a reaction.
        The button coroutine is performed for any
        reaction added by the sender of the context passed
        to the constructor.
        If nothing is done for timeout seconds, the pagination
        is cleared and this element becomes decayed. This is to
        prevent the application from having an increasing
        number of co-routines in the event loop idling, as this
        will consume more and more memory over time, and likely
        degrade performance.
        """
        if len(self.pages) == 0:
            page = Page(
                title='*HISS*',
                description='Seems there is nothing to see here. This is '
                            'probably an oversight, or just laziness on '
                            'the developer\'s behalf.\n\nYou know what? I '
                            'will go punish him right now.\n\n'
                            '*Shotgun barrel clicks*')

            page.set_footer(text='No pinguus were hurt in the making of this '
                                 'embed. A duck was shot, and a cat got sick, '
                                 'but that was about it.')

            await self._ctx.send(embed=page, delete_after=10)
        else:
            ensure_future(self._send_loop())

    async def _send_loop(self):
        # If no page has been shown yet, send a placeholder message.
        if not hasattr(self, '_msg') or self._msg is None:
            msg = await self._ctx.send('Loading pagination...')
            setattr(self, '_msg', msg)

            ensure_future(self._reset_buttons())

        ensure_future(self._update_page())

        try:
            def check(_react, _user):
                return (_react.emoji in self.buttons.keys()
                        and _react.message.id == self._msg.id
                        and _user.id in (
                            self._ctx.author.id, self._ctx.bot.owner_id))

            react, member = await self._ctx.bot.wait_for(
                'reaction_add',
                timeout=self.timeout,
                check=check
            )

            ensure_future(self._msg.remove_reaction(react.emoji, member))
        except asyncio.TimeoutError:
            # Kills the pagination.
            self.decay()
        else:
            await self.buttons[react.emoji].invoke(self, self.page)

    async def _reset_buttons(self):
        """
        Clears all reactions and displays the
        current buttons in insertion order.
        """
        await self._msg.clear_reactions()
        # Must await to ensure correct ordering.
        if len(self) > 1:
            [await self._msg.add_reaction(btn) for btn in self.buttons]
        else:
            for emoji, btn in self.buttons.items():
                if btn.always_show:
                    await self._msg.add_reaction(emoji)

    async def _msg_content(self):
        """
        Gets a string to display for the message content.
        This does not call another coroutine. However, it exists to be
        await-able in order to allow overriding this message.
        """
        return f'Page {self.page_no} of {len(self)}'

    async def _update_page(self):
        """
        Forces the current page to be edited to reflect the current page
        in this Book. This will not touch reactions.
        """
        try:
            await self._msg.edit(
                content=await self._msg_content(),
                embed=self.page
            )
        except discord.HTTPException:
            traceback.print_exc()
            await self._msg.edit(
                content='Amazon seem to have lost your package in transit. '
                        'Please accept this basket of sympathy oranges. '
                        'https://thumbs.dreamstime.com/b/basket-oranges'
                        '-12173131.jpg')
            await self._msg.clear_reactions()
            await asyncio.sleep(10)
            await self._msg.delete()

    def decay(self):
        """
        Makes the pagination decay into an embed. This effectively
        finalises this element.
        """
        ensure_future(self._msg.clear_reactions())
        ensure_future(self._msg.edit(content=''))

    @staticmethod
    def generate_buttons() -> typing.List[Button]:
        """
        Generates default buttons.
        |<< - Goes to the first page.
         <  - Decrements the page number.
        123 - Takes the page number as input.
         >  - Increments the page number.
        >>| - Goes to the last page.
         X  - Kills the pagination.
        Bin - Kills the embed and original message.
        """

        @Button(
            '\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}',
            False)
        async def first_page(book: Book, __: Page):
            book.index = 0
            await book._send_loop()

        @Button('\N{BLACK LEFT-POINTING TRIANGLE}', False)
        async def previous_page(book: Book, __: Page):
            book.index -= 1
            await book._send_loop()

        @Button('\N{INPUT SYMBOL FOR NUMBERS}', False)
        async def page_picker(book: Book, __: Page):
            prompt = await book._ctx.send(
                'Please enter a page number/offset to go to.'
            )

            try:
                def check(message):
                    ctx = book.context_invoked_from
                    return (
                            message.channel == ctx.channel and
                            message.author.id == ctx.author.id
                    )

                while True:
                    reply = await book._ctx.bot.wait_for(
                        'message',
                        timeout=30,
                        check=check
                    )
                    try:
                        await reply.delete()
                        reply.content = reply.content.strip()
                        i = int(reply.content)
                        is_offset = reply.content.startswith('+') or i < 0
                        if is_offset:
                            book.index += i
                        else:
                            if i < 1 or i > len(book):
                                raise ValueError()
                            else:
                                book.page_no = i
                        await prompt.delete()
                        break
                    except ValueError:
                        await book._ctx.send(
                            'Invalid input. Try again.',
                            delete_after=10
                        )
            except asyncio.TimeoutError:
                await book._ctx.send(
                    'Took too long.',
                    delete_after=10
                )
            finally:
                await book._send_loop()

        @Button('\N{BLACK RIGHT-POINTING TRIANGLE}', False)
        async def next_page(book: Book, __: Page):
            book.index += 1
            await book._send_loop()

        @Button('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}',
                False)
        async def last_page(book: Book, __: Page):
            book.index = -1
            await book._send_loop()

        @Button('\N{SQUARED OK}')
        async def close_book(b: Book, __: Page):
            # Doesn't need to do anything apart from remove the page number and
            # the reactions.
            b.decay()

        @Button('\N{PUT LITTER IN ITS PLACE SYMBOL}')
        async def close_and_delete(b: Book, __: Page):
            await b.response_message.delete()
            await b.context_invoked_from.message.delete()

        return [
            first_page,
            previous_page,
            page_picker,
            next_page,
            last_page,
            close_book,
            close_and_delete
        ]


async def should_show(cmd, ctx):
    """
    Logic to determine whether to include a given page in the help.
    This filters out all disabled, hidden and unrunnable commands except if
    the ctx was invoked by the bot owner; in this case, everything is
    displayed regardless.
    :param cmd: command to verify.
    :param ctx: context to check against.
    :return: true if we should show it, false otherwise.
    """
    if ctx.author.id == ctx.bot.owner_id:
        return True
    else:
        # noinspection PyBroadException
        try:
            can_run = await cmd.can_run(ctx)
        except BaseException:
            return False
        else:
            is_hidden = cmd.hidden
            is_enabled = cmd.enabled
            return can_run and not is_hidden and is_enabled


class HelpCog(commands.Cog):
    """Provides the inner methods with access to bot directly."""

    def __init__(self, bot):
        """
        Initialises the cog.
        :param bot: the bot.
        """
        self.bot = bot

    @commands.command(
        name='help',
        brief='Shows help for the available bot commands.',
        usage='|command|group command')
    async def help_command(self, ctx, *, query=None):
        """
        Shows a set of help pages outlining the available commands, and
        details on how to operate each of them.
        If a command name is passed as a parameter (`help command`) then the
        parameter is searched for as a command name and that page is opened.
        """
        # TODO: maybe try to cache this! It's a fair amount of work each time.

        # Generates the book
        bk = Book(ctx)

        # Maps commands to pages, so we can just jump to the page
        command_to_page = {}

        bk += await self.gen_front_page(ctx)
        command_to_page[None] = 0

        # Walk commands
        all_cmds = sorted(set(self.bot.walk_commands()),
                          key=lambda c: c.qualified_name)

        # We offset each index in the enumeration by this to get the
        # correct page number.
        offset = len(bk)

        # Strip out any commands we don't want to show.
        cmds = [cmd for cmd in all_cmds if await should_show(cmd, ctx)]

        page_index = None
        for i, cmd in enumerate(cmds):

            bk += await self.gen_spec_page(ctx, cmd)

            if page_index is None and query == cmd.qualified_name:
                # I assume checking equality of commands is slower
                # than checking for is None each iteration.
                page_index = i + offset

        # Set the page
        if page_index is None and query:
            await ctx.send(f'I could not find a command called {query}!',
                           delete_after=10)
        else:
            if page_index is None:
                page_index = 0

            bk.index = page_index
            await bk.send()

    async def gen_front_page(self, ctx) -> Page:
        """
        Generates an about page. This is the first page of the help
        pagination.
        :param ctx: the command context.
        """

        embed = discord.Embed(
            title=f'Helpful Information',
            description='Created by: Vee\n'
                        'This bot is was made to provide\n'
                        'information about Steam accounts and games',
            color=default_color
        )

        embed.set_thumbnail(url=ctx.bot.user.avatar_url)

        embed.set_footer(
            text='Made with \N{HEAVY BLACK HEART} by Vee#4012')

        # Walk commands into a set to omit aliases.
        cmds = sorted({*self.bot.walk_commands()},
                      key=lambda c: c.qualified_name)
        cmds = [await self.format_command_name(cmd, ctx, is_full=True)
                for cmd in cmds if await should_show(cmd, ctx)]

        embed.add_field(
            name='Available commands',
            value='\n'.join(f'`!sl`{c}' for c in cmds),
            inline=False
        )

        return embed

    # noinspection PyUnusedLocal
    async def gen_spec_page(self, ctx, cmd):
        """
        Given a context and a command, generate a help page entry for the
        command.
        :param ctx: the context to use to determine if we can run the command
                here.
        :param cmd: the command to generate the help page for.
        :return: a book page.
        """
        pfx = self.bot.user.mention
        fqn = await self.format_command_name(cmd, ctx, is_full=True)
        brief = cmd.brief if cmd.brief else 'Whelp! No info here!'
        doc_str = remove_single_lines(cmd.help)
        usages = cmd.usage.split('|') if cmd.usage else ''
        usages = map(lambda u: f'• {pfx} {cmd.qualified_name} {u}', usages)
        usages = '\n'.join(sorted(usages))
        aliases = sorted(cmd.aliases)
        cooldown = getattr(cmd, '_buckets')

        if cooldown:
            cooldown: commands.Cooldown = getattr(cooldown, '_cooldown')

        if cmd.parent:
            super_command = await self.format_command_name(cmd.parent, ctx)
        else:
            super_command = None

        # noinspection PyUnresolvedReferences
        can_run = await cmd.can_run(ctx)

        if isinstance(cmd, commands.Group):
            async def sub_cmd_map(c):
                c = await self.format_command_name(c, ctx, is_full=True)
                c = f'• {c}'
                return c

            # Cast to a set to prevent duplicates for aliases. Hoping this
            # fixes #9 again.
            # noinspection PyUnresolvedReferences
            sub_commands = {*cmd.walk_commands()}
            sub_commands = [await sub_cmd_map(c) for c in sub_commands]
            sub_commands = sorted(sub_commands)
        else:
            sub_commands = []

        if getattr(cmd, 'enabled', False) and can_run:
            color = default_color
        elif not can_run:
            color = 0xFFFF00
        else:
            color = 0xFF0000

        page = Page(
            title=await self.format_command_name(cmd, ctx, is_full=True),
            description=brief,
            color=color
        )

        if doc_str:
            page.add_field(
                name='More info',
                value=doc_str,
                inline=False
            )

        if usages:
            page.add_field(
                name='Usage',
                value=usages,
                inline=False
            )

        if aliases:
            page.add_field(
                name='Aliases',
                value=', '.join(aliases)
            )

        if cooldown:
            timeout = cooldown.per
            if timeout.is_integer():
                timeout = int(timeout)

            string = (
                f'{capitalise(cooldown.type.name)}-scoped '
                f'{pluralise(cooldown.rate, "request", method="per app")} '
                f'with timeout of {pluralise(timeout, "second")}.')

            page.add_field(
                name='Cooldown policy',
                value=string
            )

        if sub_commands:
            page.add_field(
                name='Child commands',
                value='\n'.join(sub_commands)
            )

        if super_command:
            page.add_field(
                name='Parent command',
                value=super_command
            )

        if not can_run and cmd.enabled:
            page.set_footer(
                text='You do not hve permission to run the command here... '
                     'Sorry!'
            )
        elif not cmd.enabled:
            page.set_footer(
                text='This command has been disabled globally by the dev.'
            )

        return page

    @staticmethod
    async def format_command_name(cmd,
                                  ctx,
                                  *,
                                  is_full=False) -> str:
        """
        Formats the given command using it's name, in markdown.
        If the command is disabled, it is crossed out.
        If the command is a group, it is proceeded with an asterisk.
            This is only done if the command has at least one sub-command
            present.
        If the command is hidden, it is displayed in italics.
        :param cmd: the command to format.
        :param ctx: the command context.
        :param is_full: defaults to false. If true, the parent command is
                    prepended to the returned string first.
        """
        if is_full:
            name = f'{cmd.full_parent_name} {cmd.name}'.strip()
        else:
            name = cmd.name

        if not cmd.enabled or not await cmd.can_run(ctx):
            name = f'~~{name}~~'

        if cmd.hidden:
            name = f'*{name}*'

        if isinstance(cmd, commands.Group) and getattr(cmd, 'commands'):
            name = f'{name}\*'

        return name


def setup(bot):
    bot.add_cog(HelpCog(bot))
