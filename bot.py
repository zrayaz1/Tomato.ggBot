import discord as discord
from discord.ext import commands, tasks
from discord_slash.context import ComponentContext
from fuzzywuzzy import process
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils import manage_commands
from discord_slash.utils.manage_components import create_button, create_actionrow, create_select, create_select_option
from discord_slash.model import ButtonStyle
from search_ulitities import Search
from moe_mastery import TankData, TankDataFormatter
from typing import List
from bot_enums import Servers, Recents, Keys
from exceptions import MissingData
from storage import Storage
from player_stats import PlayerStats
from clan_stats import ClanStats

TOKEN = Keys.TOKEN.value
client = commands.Bot(command_prefix='$', activity=discord.Game(name='/'))
slash = SlashCommand(client, sync_commands=True)


@client.event
async def on_ready():
    print('up')


@slash.component_callback(components=["clan", "player"])
async def clan_callback(ctx: ComponentContext) -> None:
    """
    Switch between clan and player embeds on callback
    """
    if ctx.component_id == "clan":
        await ctx.edit_origin(embed=Storage.get_clan_embed(ctx.origin_message_id))
    elif ctx.component_id == "player":
        await ctx.edit_origin(embed=Storage.get_player_embed(ctx.origin_message_id))


@slash.component_callback(components=["timeperiod_selection"])
async def timeperiod_selection(ctx: ComponentContext) -> None:
    if ctx.selected_options[0] in Recents.literal_list():
        recent = Recents.get_class(ctx.selected_options[0])
        instance = Storage.get_instance(ctx.origin_message_id)
        embed = await instance.get_time_stats(recent)
        await ctx.edit_origin(embed=embed)


@slash.slash(name="stats", description='WoT Player Statistics',
             options=[manage_commands.create_option(name=i, description=j, option_type=3, required=h, choices=l) for
                      i, j, h, l in
                      [['user', 'Players Username', True, None],
                       ['server', 'Server To search against', False, Servers.literal_list()],
                       ['timeperiod', 'Detailed Stats for Time Period', False, Recents.literal_list()]]]
             )
async def _stats(ctx: SlashContext, user, server=None, timeperiod=None):
    async def add_clan_buttons():
        buttons = [
            create_button(
                style=ButtonStyle.green,
                label="Clan Stats",
                custom_id='clan'),

            create_button(
                style=ButtonStyle.blurple,
                label='Player Stats',
                custom_id='player')
        ]
        action_row = create_actionrow(*buttons)
        await message.edit(components=[action_row])

    async def add_time_selection():

        select = create_select(options=[create_select_option(i, value=i) for i in Recents.literal_list()],
                               placeholder='Choose Timeperiod', min_values=1, max_values=1,
                               custom_id="timeperiod_selection")
        action_row = create_actionrow(select)
        await message.edit(components=[action_row])

    await ctx.defer()
    api_url = 'https://api.worldoftanks.{}/wot/account/list/?language=en&application_id={}&search={}'
    if server:
        server_name = Servers.get_class(server)
        server_extension = Servers.get_extension(server_name)
        id_search = await Search.async_search(api_url.format(server_extension.value, Keys.WOT.value, user))
        if id_search['status'] == "error" or id_search['meta']['count'] == 0:
            await ctx.send('Missing api data: Invalid username?')
            return
        else:
            user_id = id_search['data'][0]['account_id']
    else:
        user_id, server_name = await Search.get_user_server(user)

    user_instance_cached: PlayerStats = PlayerStats(f"{user_id}", server_name, user, Keys.WOT.value, cached=True)
    user_instance: PlayerStats = PlayerStats(f"{user_id}", server_name, user, Keys.WOT.value, cached=False)

    if timeperiod is not None:
        timeperiod = Recents.get_class(timeperiod)
        try:
            await user_instance_cached.set_default_stats()
            cached_sent = True
            message = await ctx.send(embed=await user_instance_cached.get_time_stats(timeperiod))
        except MissingData:
            cached_sent = False

        await user_instance.set_default_stats()
        if cached_sent:
            await message.edit(embed=await user_instance.get_time_stats(timeperiod))
        else:
            await ctx.send(embed=await user_instance.get_time_stats(timeperiod))

    else:
        try:
            await user_instance_cached.set_default_stats()
            message = await ctx.send(embed=await user_instance_cached.generate_default_embed())
            cached_sent = True
        except MissingData:
            cached_sent = False
        user_instance = PlayerStats(f"{user_id}", server_name, user, Keys.WOT.value, cached=False)
        await user_instance.set_default_stats()
        fetched_embed = await user_instance.generate_default_embed()
        if cached_sent:
            await message.edit(embed=fetched_embed)
        else:
            message = await ctx.send(embed=fetched_embed)
        Storage.player_embeds[message.id] = fetched_embed
        clan_id = user_instance.player_data.clan_data['clan']['clan_id']
        clan_tag = user_instance.player_data.clan_data['clan']['tag']
        clan_instance = ClanStats(clan_tag, server_name)
        clan_embed = await clan_instance.create_embed(clan_id, clan_tag)
        Storage.clan_embeds[message.id] = clan_embed
    Storage.instances[message.id] = user_instance
    if timeperiod is None and user_instance.player_data.isInClan:
        await add_clan_buttons()
    if timeperiod:
        await add_time_selection()


@slash.slash(name='marks', description='WoT Tank MoE and Mastery',
             options=[
                 manage_commands.create_option(name='tank', description='Name of Tank', option_type=3, required=True),
                 manage_commands.create_option(name='server', description='Options: na, eu, asia. Defaults to na',
                                               choices=Servers.literal_list(), option_type=3,
                                               required=False)]
             )
async def _marks(ctx: SlashContext, tank: str, server='NA'):
    server_obj = Servers.get_class(server.upper())
    sent_tank_name = tank.upper()
    short_tank_list, short_and_long_list, short_to_long_dict = TankData.get_tank_list(server_obj)
    tank_guess: List[str, int] = process.extractOne(sent_tank_name, list(short_and_long_list))
    tank_name = tank_guess[0]  # extractOne produces a list only need the match itself
    if tank_name in short_tank_list:
        tank_name = short_to_long_dict[tank_name]
    user_tank = TankDataFormatter(tank_name, server=server_obj)
    await ctx.send(embed=user_tank.get_moe_embed())


@slash.slash(name='ClanStats', description="WoT Clan Statistics",
             options=[manage_commands.create_option(name='clan', description='Clan Name', option_type=3, required=True),
                      manage_commands.create_option(name='server', description='Server To search against.',
                                                    choices=Servers.literal_list(), option_type=3,
                                                    required=True)])
async def _clan_stats(ctx: SlashContext, clan, server):
    await ctx.defer()  # interaction will drop in 3 seconds unless deferred
    server = Servers.get_class(server)
    clan_instance = ClanStats(clan, server)
    search_response = await clan_instance.find_clan()
    clan_id = search_response['data'][0]['clan_id']
    clan_tag = search_response['data'][0]['tag']
    clan_embed = await clan_instance.create_embed(clan_id, clan_tag)
    await ctx.send(embed=clan_embed)


@tasks.loop(hours=12)
async def update_marks():
    client.loop.create_task(TankData.get_data())


if __name__ == "__main__":
    update_marks.start()
    client.run(TOKEN)
