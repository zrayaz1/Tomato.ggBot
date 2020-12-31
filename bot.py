import requests
import discord
from discord.ext import commands
import random
from discord import *

# first arg must be name, second must be server if used.
# "10s" get tier 10 list
# "rwn8" get recent wn8
# "10wn8" get tier 10 wn8
# "10rwn8" get tier 10 rwn8
# none gives default output probably like recent overall and avgerage tier
#
# https://tomatobackend-oswt3.ondigitalocean.app/api/abcd/{server}/{id}
# get tier 10 list
# get recent tier 10 wn8
# get recent wn8
# api_url = 'https://api.worldoftanks.com/wot/account/list/?language=en&application_id=20e1e0e4254d98635796fc71f2dfe741&search={}'
TOKEN = "Nzg2Njk4ODg1MzI2MzA3MzU4.X9KMbg.qxs696oJSbqaxbJGtWrnMlnLwgw"
client = commands.Bot(command_prefix='$')


class Stats:
    def __init__(self, userId: str, server: str):
        apiUrl = 'https://tomatobackend-oswt3.ondigitalocean.app/api/abcd/{}/{}'
        self.userId = userId
        self.userUrl = apiUrl.format(server, userId)
        self.jsonOutput = requests.get(self.userUrl).json()



@client.command(alais='stat')
async def stats(ctx, *args: str):
    apiUrl = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id=20e1e0e4254d98635796fc71f2dfe741&search={}'
    sentChannel = ctx.channel
    serverList = ['na', 'eu', 'asia', 'ru']
    if args:
        server = [i for i in args if i in serverList]
        if server:
            if server[0] == 'na':
                server = 'com'
            else:
                server = server[0]
        else:
            server = 'com'

        searchForIdJson = requests.get(apiUrl.format(server, args[0])).json()

        if searchForIdJson['status'] == "error" or searchForIdJson['meta']['count'] == 0:
            await sentChannel.send("Invalid Username")
        else:
            userId = searchForIdJson['data'][0]['account_id']
            user = Stats(userId, "com")



    else:
        await sentChannel.send("Usage: $stats {name} {server} {stat type}")


client.run(TOKEN)
