import requests
from discord.ext import commands
from discord import *



client = commands.Bot(command_prefix='$')
colorRatingNew = {
    "very_bad": 0xBAAAAD,
    "bad": 0xf11919,
    "below_average": 0xff8a00,
    "average": 0xe6df27,
    "above_average": 0x77e812,
    "good": 0x459300,
    "very_good": 0x2ae4ff,
    "great": 0x00a0b8,
    "unicum": 0xc64cff,
    "super_unicum": 0x8225ad
}

TOKEN = 'Nzk1MTM4MTQ1MTA0MTY2OTEy.X_FAGg.SBmQ2z-jPUZ-5wmAULCumUvjYQg'
localTOKEN = 'Nzg2Njk4ODg1MzI2MzA3MzU4.X9KMbg.qxs696oJSbqaxbJGtWrnMlnLwgw'

def get_wn8_color(wn8: int, tier: float):
    sealClubber = False

    tier = float(tier)
    if wn8 >= 2900:
        WN8Color = colorRatingNew['super_unicum']
        if tier <= 7:
            sealClubber = True

    elif wn8 >= 2450:
        WN8Color = colorRatingNew['unicum']
        if tier <= 7:
            sealClubber = True
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
    return WN8Color, sealClubber
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
    def __init__(self, userId: str, server: str, name: str,wotApiKey: str):

        self.clanApiUrl = f'https://api.worldoftanks.{server}/wot/clans/accountinfo/?application_id={wotApiKey}&account_id={userId}'
        self.apiKey = wotApiKey
        self.server = server
        if self.server == 'com':
            self.parsedServer ='NA'
        else:
            self.parsedServer = self.server
        self.userName = name
        self.sealClubber = False
        apiUrl = 'https://tomatobackend-oswt3.ondigitalocean.app/api/abcd/{}/{}'
        self.userId = userId
        self.userUrl = apiUrl.format(server, userId)
        self.jsonOutput = requests.get(self.userUrl).json()
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
        self.overallWN8Color, self.sealClubber = get_wn8_color(self.overallWN8, self.overallStats['avgTier'])
        if self.recent1000['overallWN8'] != '-' and self.recent1000['tier'] != '-':
            self.recent1000Color, self.rSealClubber = get_wn8_color(self.recent1000['overallWN8'],
                                                                    self.recent1000['tier'])
        else:
            self.recent1000Color = self.overallWN8Color
            self.rSealClubber = self.sealClubber
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

        clanData = requests.get(self.clanApiUrl).json()['data']
        if clanData[str(self.userId)] is None:
            self.isInClan = False
        else:
            self.isInClan = True
            self.clanName = clanData[str(self.userId)]['clan']['tag']
            self.clanIconUrl = clanData[str(self.userId)]['clan']['emblems']['x195']['portal']
            self.clanPosition = clanData[str(self.userId)]['role']
            self.shortClanPosition = get_short_hand(self.clanPosition)
    def get_marks(self):
        embed = Embed(title=f"{self.userName}'s Marks", color=self.recent1000Color)
        embed.add_field(name='Total Marks',
                        value=f"3 Marks: `{self.threeMarks}`\n2 Marks: `{self.twoMarks}`\n 1 Marks: `{self.oneMarks}`")
        embed.add_field(name='Tier 10 Marks',
                        value=f"3 Marks: `{self.tier10ThreeMarks}`\n2 Marks: `{self.tier10TwoMarks}`\n 1 Marks: `{self.tier10OneMarks}`")
        return embed



    def get_default_stats(self):

        dataList = {"overall": self.overallStats, "24h": self.recent24hr, "7 days": self.recent7days,
                    '30 days': self.recent30days, '60 Days': self.recent60days, '1000 Battles': self.recent1000}
        startTitleStr = f"{self.userName.capitalize()}'s Stats"
        if self.isInClan:
            offset = 40 - len(startTitleStr)
            fullStr = startTitleStr + ' ' * offset + self.shortClanPosition + ' ' + "at" + " " f"[{self.clanName}]"
            testEmbed = Embed(title=fullStr,
                              color=self.recent1000Color,url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}')
            testEmbed.set_thumbnail(url=self.clanIconUrl)
        else:
            testEmbed = Embed(title=startTitleStr,color=self.recent1000Color,url=f'http://tomato.gg/stats/{self.parsedServer}/{self.userName}={self.userId}')
        for x in list(dataList.keys()):
            values = list(dict(list(dataList[x].items())[0:4]).values())
            if x == 'overall':
                total_battles = self.jsonOutput["overall"]['battles']
                total_wins = self.jsonOutput["overall"]['wins']
                winrate = int(total_wins) / int(total_battles)
                winRatePercent = "{:.1%}".format(winrate)
                testEmbed.add_field(name=x,
                                    value=f'Battles: `{values[0]}`\nWN8: `{values[1]}`\nWinRate: `{winRatePercent}`\nAvgTier: `{str(values[2])[0:3]}`',
                                    inline=True)
            else:
                recentBattles = int(values[0])
                recentsWins = dataList[x]['wins']
                if recentBattles != 0:
                    recentWinRate = recentsWins / recentBattles
                    recentWinRatePercent = "{:.0%}".format(recentWinRate)

                else:
                    recentWinRatePercent = '-'
                testEmbed.add_field(name=x,
                                    value=f'Battles: `{values[0]}`\nWN8: `{values[3]}`\nWinRate: `{recentWinRatePercent}`\nAvgTier: `{str(values[2])[0:3]}`')
        testEmbed.set_footer(text='Powered by Tomato.gg',
                             icon_url='https://www.tomato.gg/static/media/smalllogo.70f212e0.png')

        return testEmbed


@client.command(alais='stat')
async def stats(ctx, *args: str):
    apiKey = '20e1e0e4254d98635796fc71f2dfe741'
    apiUrl = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'


    sentChannel = ctx.channel
    serverList = ['na', 'eu', 'asia', 'ru']
    if args:
        name = args[0]
        server = [i for i in args if i in serverList]
        if server:
            print(server)
            print(server[0])
            if server[0] == 'na':
                userServer = 'com'
            else:
                userServer = server[0]
        else:
            userServer = 'com'

        searchForIdJson = requests.get(apiUrl.format(userServer, apiKey, name)).json()

        if searchForIdJson['status'] == "error" or searchForIdJson['meta']['count'] == 0:
            await sentChannel.send("Invalid Username")
        else:
            userId = searchForIdJson['data'][0]['account_id']

            userInstance = Stats(userId, userServer, name,apiKey)
            if any(item.startswith('--') for item in args):
                sentFlags = [i for i in args if i.startswith('--')]
                if '--marks' in sentFlags or '--all' in sentFlags:
                    embed = userInstance.get_marks()
                    await sentChannel.send(embed=embed)
            if "--all" in args or not any(item.startswith("--") for item in args):
                myEmbed = userInstance.get_default_stats()
                await sentChannel.send(embed=myEmbed)
    else:
        await sentChannel.send("Usage: $stats [user] [server] --flags")


client.run(TOKEN)