from discord import Embed
from typing import Dict
from player_stats import PlayerStats


class Storage:
    """
    this should be a database. Too bad!
    """
    player_embeds = {}
    clan_embeds = {}
    instances: Dict[int, PlayerStats] = {}

    @classmethod
    def get_instance(cls, message_id) -> PlayerStats:
        return cls.instances[message_id]

    @classmethod
    def get_player_embed(cls, message_id) -> Embed:
        return cls.player_embeds[message_id]

    @classmethod
    def get_clan_embed(cls, message_id) -> Embed:
        return cls.clan_embeds[message_id]
