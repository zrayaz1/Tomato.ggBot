import requests
from discord.ext import commands
from discord import *
import discord as discord

from fuzzywuzzy import fuzz, process
apiTankData = {}
tankMarkData = {}
tankDataDict = {}
globalTankList = []
masteryCall = []
client = commands.Bot(command_prefix='$')
client.remove_command('help')
colorRatingNew = {
    "very_bad": 0x7d1930,
    "bad": 0xf11919,
    "below_average": 0xff8a00,
    "average": 0xe6df27,
    "above_average": 0x77e812,
    "good": 0x459300,
    "very_good": 0x2ae4ff,
    "great": 0x0077ff,
    "unicum": 0xc64cff,
    "super_unicum": 0x7d2ad8
}

TOKEN = 'Nzk1MTM4MTQ1MTA0MTY2OTEy.X_FAGg.1rqXEp7zGZR-f1jvvFuRH4lKFdE'
localTOKEN = 'Nzg2Njk4ODg1MzI2MzA3MzU4.X9KMbg.ouaG4EF-nQWxt3ACnrpYHLK0zXI'


class botError(Exception):
    pass


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name='$help'))
    r = requests.get("https://api.worldoftanks.com/wot/encyclopedia/vehicles/?application_id=20e1e0e4254d98635796fc71f2dfe741&fields=name%2Cimages").json()
    for x in r["data"]:
        globalTankList.append(r['data'][x]['name'])
        tankDataDict[r['data'][x]['name']] = r['data'][x]['images']['big_icon']

    global apiTankData
    apiTankData = r
    test = requests.get("https://gunmarks.poliroid.ru/api/com/vehicles/65,85,95,100").json()
    global tankMarkData
    tankMarkData = test
    global masteryCall
    masteryCall = requests.get("https://mastery.poliroid.ru/api/com/vehicles").json()




@client.command()
async def help(ctx):
    testembed = Embed()
    testembed.set_footer(text='help')

    testembed.add_field(name='Player Stats', value='`$stats [name] [server]`\n ex. `$stats zrayaz na`')
    await ctx.channel.send(embed=testembed)


def get_wn8_color(wn8: int):
    if wn8 >= 2900:
        WN8Color = colorRatingNew['super_unicum']


    elif wn8 >= 2450:
        WN8Color = colorRatingNew['unicum']

    elif wn8 >= 2000:
        WN8Color = colorRatingNew['great']
    elif wn8 >= 1600:
        WN8Color = colorRatingNew['very_good']
    elif wn8 >= 1200:
        WN8Color = colorRatingNew['good']
    elif wn8 >= 900:
        WN8Color = colorRatingNew['above_average']
    elif wn8 >= 650:
        WN8Color = colorRatingNew['average']
    elif wn8 >= 450:
        WN8Color = colorRatingNew['below_average']
    elif wn8 >= 300:
        WN8Color = colorRatingNew['bad']
    else:
        WN8Color = colorRatingNew['very_bad']
    return WN8Color


def get_short_hand(position):
    shortPositions = {'executive_officer': 'XO',
                      'commander': 'CDR',
                      'personnel_officer': 'PO',
                      'combat_officer': 'CO',
                      'recruitment_officer': 'RO',
                      'intelligence_officer': 'IO',
                      'quartermaster': 'QM',
                      'junior_officer': 'JO',
                      'private': "PVT",
                      'recruit': 'RCT',
                      'reservist': 'RES'
                      }
    return shortPositions[position]


class Stats:
    def __init__(self, userId: str, server: str, name: str, wotApiKey: str):
        if server == 'com':
            self.defaultTimeOut = 8
        else:
            self.defaultTimeOut = 20
        self.clanApiUrl = f'https://api.worldoftanks.{server}/wot/clans/accountinfo/?application_id={wotApiKey}&account_id={userId}'
        self.apiKey = wotApiKey
        self.server = server
        if self.server == 'com':
            self.parsedServer = 'NA'
        else:
            self.parsedServer = self.server
        self.userName = name
        self.sealClubber = False
        apiUrl = 'https://tomatobackend.herokuapp.com/api/abcd/{}/{}'
        self.userId = userId
        self.userUrl = apiUrl.format(server, userId)

        self.jsonOutput = requests.get(self.userUrl, timeout=self.defaultTimeOut).json()

        self.overallStats = self.jsonOutput['overallStats']
        self.tankWN8 = self.overallStats['tankWN8']
        self.recent24hr = self.jsonOutput['recents']['recent24hr']
        self.recent3days = self.jsonOutput['recents']['recent3days']
        self.recent7days = self.jsonOutput['recents']['recent7days']
        self.recent30days = self.jsonOutput['recents']['recent30days']
        self.recent60days = self.jsonOutput['recents']['recent60days']
        self.recent1000 = self.jsonOutput['recents']['recent1000']
        self.overallWN8 = self.overallStats['overallWN8']
        self.clanId = ''
        self.overallWN8Color = get_wn8_color(self.overallWN8)
        self.oneMarks = 0
        self.twoMarks = 0
        self.threeMarks = 0
        self.tier10ThreeMarks = 0
        self.tier10TwoMarks = 0
        self.tier10OneMarks = 0
        for tank in self.tankWN8:
            if tank['moe'] != 0:
                if tank['moe'] == 1:
                    self.oneMarks += 1
                    if tank['tier'] == 10:
                        self.tier10OneMarks += 1
                elif tank['moe'] == 2:
                    self.twoMarks += 1
                    if tank['tier'] == 10:
                        self.tier10TwoMarks += 1
                elif tank['moe'] == 3:
                    self.threeMarks += 1
                    if tank['tier'] == 10:
                        self.tier10ThreeMarks += 1
        self.startTitleStr = f"{self.userName.capitalize()}'s Stats"
        clanData = requests.get(self.clanApiUrl).json()['data']
        if clanData[str(self.userId)] is None:
            self.isInClan = False
        else:
            self.isInClan = True
            self.clanName = clanData[str(self.userId)]['clan']['tag']
            self.clanIconUrl = clanData[str(self.userId)]['clan']['emblems']['x64']['portal']
            self.clanPosition = clanData[str(self.userId)]['role']
            self.shortClanPosition = get_short_hand(self.clanPosition)

    def get_marks(self):
        embed = Embed(title=f"{self.userName}'s Marks", color=self.overallWN8Color)
        embed.add_field(name='Total Marks',
                        value=f"3 Marks: `{self.threeMarks}`\n2 Marks: `{self.twoMarks}`\n 1 Marks: `{self.oneMarks}`")
        embed.add_field(name='Tier 10 Marks',
                        value=f"3 Marks: `{self.tier10ThreeMarks}`\n2 Marks: `{self.tier10TwoMarks}`\n 1 Marks: `{self.tier10OneMarks}`")
        return embed

    def get_default_stats(self):

        dataList = {"overall": self.overallStats, "24h": self.recent24hr, "7 days": self.recent7days,
                    '30 days': self.recent30days, '60 Days': self.recent60days, '1000 Battles': self.recent1000}
        self.startTitleStr = f"{self.userName.capitalize()}'s Stats"
        if self.isInClan:

            # + ' ' * offset + self.shortClanPosition + ' ' + "at" + " " f"[{self.clanName}]"
            testEmbed = Embed(title=self.startTitleStr,
                              description="**" + self.shortClanPosition + ' ' + "at" + " " f"[{self.clanName}]" + "**",
                              color=self.overallWN8Color,
                              url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}')
            testEmbed.set_thumbnail(url=self.clanIconUrl)



        else:
            testEmbed = Embed(title=self.startTitleStr, colour=self.overallWN8Color,
                              url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}')
        if self.sealClubber:
            testEmbed.set_author(name="🚨WARNING SEALCLUBBER🚨")

        for x in list(dataList.keys()):
            values = list(dict(list(dataList[x].items())[0:4]).values())
            if x == 'overall':
                self.total_battles = self.jsonOutput["overall"]['battles']
                total_wins = self.jsonOutput["overall"]['wins']
                winrate = int(total_wins) / int(self.total_battles)
                winRatePercent = "{:.1%}".format(winrate)
                testEmbed.add_field(name=f"**{x}**",
                                    value=f'Battles: `{values[0]}`\nWN8: `{values[1]}`\nWinRate: `{winRatePercent}`\nAvgTier: `{str(values[2])[0:3]}`',
                                    inline=True)
            else:
                recentBattles = int(values[0])
                recentsWins = dataList[x]['wins']
                if recentBattles != 0:
                    recentWinRate = recentsWins / recentBattles
                    recentWinRatePercent = "{:.1%}".format(recentWinRate)

                else:
                    recentWinRatePercent = '-'
                testEmbed.add_field(name=x,
                                    value=f'Battles: `{values[0]}`\nWN8: `{values[3]}`\nWinRate: `{recentWinRatePercent}`\nAvgTier: `{str(values[2])[0:3]}`')
        testEmbed.set_footer(text='Powered by Tomato.gg',
                             icon_url='https://www.tomato.gg/static/media/smalllogo.70f212e0.png')

        return testEmbed

    def get_tank_stats(self, period):
        dataList = {"OVERALL": self.overallStats, "24H": self.recent24hr, "7DAYS": self.recent7days,
                    '30DAYS': self.recent30days, '60DAYS': self.recent60days, '1000BATTLES': self.recent1000}
        if period.upper() in list(dataList.keys()):
            data = dataList[period.upper()]
            if period.upper() != "OVERALL":
                SortedTankData = sorted(data['tankStats'], key=lambda item: item['battles'], reverse=True)
            else:
                return Embed(title='Soon')
        topSix = SortedTankData[0:6]
        tankEmbed = Embed(title=self.startTitleStr,
                          description=f"**Last {period} Stats**",
                          color=get_wn8_color(data['overallWN8']),
                          url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}')

        for tank in topSix:
            tankEmbed.add_field(name=tank['name'],
                                value=f"Battles: `{tank['battles']}`\nWinRate: `{tank['winrate']}`\nWN8: `{tank['wn8']}`\nDPG: `{tank['dpg']}`")
        return tankEmbed


@client.command(aliases=["stat", "Stats", 'Stat', 'ZrayWantsToDie'])
async def stats(ctx, *args):
    print('Stats Called by ' + str(ctx.guild) + " " + str(ctx.message.author) + f" Called on {args[0]}")
    apiKey = '20e1e0e4254d98635796fc71f2dfe741'
    apiUrl = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'

    sentChannel = ctx.channel
    serverList = ['na', 'eu', 'asia', 'ru']

    def find_server(username):

        searchNA = requests.get(apiUrl.format('com', apiKey, username)).json()

        if searchNA['status'] != "error" and searchNA['meta']['count'] != 0:
            userId = searchNA['data'][0]['account_id']

            return userId, 'com'
        else:

            searchEU = requests.get(apiUrl.format('eu', apiKey, username)).json()

            if searchEU['status'] != "error" and searchEU['meta']['count'] != 0:
                userId = searchEU['data'][0]['account_id']

                return userId, 'eu'
            else:

                searchASIA = requests.get(apiUrl.format('asia', apiKey, username)).json()
                if searchASIA['status'] != "error" and searchASIA['meta']['count'] != 0:
                    userId = searchASIA['data'][0]['account_id']
                    return userId, 'asia'
                else:
                    raise Exception

    if args:
        timePeriods = ["OVERALL", "24H", "7DAYS", '30DAYS', '60DAYS', '1000BATTLES']
        name = args[0]
        server = [i for i in args if i in serverList]
        time = [i for i in args if i.upper() in timePeriods]
        if server:
            serverPassed = True
            if server[0] == 'na':
                userServer = 'com'
            else:
                userServer = server[0]
        else:
            serverPassed = False

        if serverPassed:
            searchForIdJson = requests.get(apiUrl.format(userServer, apiKey, name)).json()
            if searchForIdJson['status'] == "error" or searchForIdJson['meta']['count'] == 0:
                await ctx.channel.send('Invalid Username1')
            else:
                userId = searchForIdJson['data'][0]['account_id']
        else:
            try:
                userId, userServer = find_server(name)

            except Exception:
                await sentChannel.send('Invalid Username (All servers)')
                return

        try:

            userInstance = Stats(userId, userServer, name, apiKey)
        except requests.exceptions.Timeout:
            await sentChannel.send('api timeout: invalid user?')
            return
        except Exception:
            await sentChannel.send('UwU sumthwing bworke UwU')

        if any(item.startswith('-') for item in args):
            sentFlags = [i for i in args if i.startswith('-')]
            if '-marks' in sentFlags or '-all' in sentFlags:
                embed = userInstance.get_marks()
                await sentChannel.send(embed=embed)
        if time:
            time = time[0]
            await sentChannel.send(embed=userInstance.get_tank_stats(time))
            return
        if "-all" in args or not any(item.startswith("-") for item in args):
            myEmbed = userInstance.get_default_stats()

            await sentChannel.send(embed=myEmbed)
    else:

        await sentChannel.send("Usage: $stats [user] -flags")


@client.command()
async def wotlabs(ctx):
    await ctx.channel.send(embed=Embed(title='Wotlabs Sucks'))


class TankData:
    def __init__(self, senttank, *args):
        self.tank = senttank
        self.args = args

        for x in apiTankData['data']:

            if apiTankData['data'][x]['name'] == self.tank:

                self.tankId = x
                for x in tankMarkData['data']:
                    if str(x['id']) == str(self.tankId):

                        self.markData = x['marks']
        self.moeEmbed = Embed(title=f"{self.tank} Marks")
        for tank in masteryCall['data']:
            if tank['id'] == int(self.tankId):
                self.masteryData = tank['mastery']


    def getMoeEmbed(self):

        self.moeEmbed.add_field(name='Marks',value=f"1 Mark: `{self.markData['65']}`\n2 Mark: `{self.markData['85']}`\n3 Mark: `{self.markData['95']}`\n100% MoE: `{self.markData['100']}`")
        self.moeEmbed.add_field(name='Mastery',value=f"3st Class: `{self.masteryData[0]}`\n2st Class: `{self.masteryData[1]}`\n1st Class: `{self.masteryData[2]}`\nMastery: `{self.masteryData[3]}`")
        url = tankDataDict[self.tank]
        self.moeEmbed.set_thumbnail(url=url)
        return self.moeEmbed


@client.command(aliases=['tankstats', 'tanks', 'Tank'])
async def marks(ctx, *args):
    if args:
        nameStr = ""
        for x in args:
            nameStr += str(x)

        guessStr = process.extractOne(str(nameStr), globalTankList)
        try:
            userTank = TankData(guessStr[0])
        except botError:
            await ctx.channel.send('Invalid Tank Name')
            return
        await ctx.channel.send(embed=userTank.getMoeEmbed())

client.run(TOKEN)