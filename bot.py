#!/usr/bin/env python3

from os import environ
import discord
from discord.ext import commands
import asyncio

from massmove import MassMove
# from snooper import Snooper

# Documentation used: https://discordpy.readthedocs.io/en/latest/api.html

# Token is stored in Heroku environment to avoid
# the vulnerability of private Discord bot key exposed to public

with open('../token2_BHL_DS.txt') as f:
    TOKEN = f.read().strip()
print(discord.__version__)
intents = discord.Intents.default()
intents.members = True
intents.reactions = True
intents.guilds = True
client = commands.Bot(command_prefix = '.', intents = intents)
client.add_cog(MassMove(client))
# Run bot
client.run(TOKEN)
