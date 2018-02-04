# The user's current status. 0 - Offline, 1 - Online, 2 - Busy, 3 - Away, 4 - Snooze,
# 5 - looking to trade, 6 - looking to play. If the player's profile is private, this
# will always be "0", except if the user has set their status to looking to trade or
# looking to play, because a bug makes those status appear even if the profile is private.
import collections

ProfileState = collections.namedtuple('ProfileState', 'id name colour emote')
# Allows you to just str() the tuple and get the name.
ProfileState.__str__ = lambda ps: ps.name
# Allows you to do id(AWAY) and get 3
ProfileState.__hash__ = lambda ps: ps.name

# Makes AWAY == 3, and AWAY == 'aWaY'
def __eq__(self, other):
    if isinstance(other, int):
        return id(self) == other
    elif isinstance(other, str):
        return str(self).lower() == other.lower()
ProfileState.__eq__ = __eq__
del __eq__


OFFLINE = ProfileState(
    id=0,
    name='Offline',
    colour=0x736f6e,
    emote='\N{black heart}')

ONLINE = ProfileState(
    id=1,
    name='Online',
    colour=0x00ff00,
    emote='\N{green heart}')

BUSY = ProfileState(
    id=2,
    name='Busy',
    colour=0xff0000,
    # Actually red but whatever discord.
    emote='\N{heavy black heart}')

AWAY = ProfileState(
    id=3,
    name='Away',
    colour=0xffff00,
    emote='\N{yellow heart}')

SNOOZE = ProfileState(
    id=4,
    name='Snooze',
    colour=0x8e35ef,
    emote='\N{purple heart}')

LTT = ProfileState(
    id=5,
    name='Looking to trade',
    colour=0x54c571,
    emote='\N{heart with ribbon}')

LTP = ProfileState(
    id=6,
    name='Looking to play',
    colour=0x1589ff,
    emote='\N{revolving hearts}')

states = (OFFLINE, ONLINE, BUSY, AWAY, SNOOZE, LTT, LTP)
str2state = {s.name.lower(): s for s in states}
