#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pinguu.bot


bot = pinguu.bot.Bot()

bot.load_extension('pinguu.steamladdercog')
bot.load_extension('pinguu.admincog')
bot.remove_command('help')
bot.load_extension('pinguu.pinguuhelp')
bot.load_extension('libneko.extras.superuser')

bot.run()
