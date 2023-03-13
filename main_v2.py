from typing import Any

from discord import TextChannel, Intents, Message, Guild
from discord.ext import tasks
from conf import settings as s

# This example requires the 'message_content' intent.

import discord

from utils.persistent_properties import PersistentProperties, GuildProperty
from utils.guild_utils import try_channel
from utils.setup_manager import SetupManager

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)


class Client(discord.Client):
    def __init__(self, *, intents: Intents, **options: Any):
        super().__init__(intents=intents, options=options)
        self.guilds_in_setup: dict[Guild, GuildProperty] = {}
        self.guilds_properties_mapping: dict[Guild, GuildProperty] = {}

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        print("Loading properties")
        pp_manager = PersistentProperties()
        guilds_data: dict[int, GuildProperty] = {
            g.guild_id: g for g in await pp_manager.load_all()
        }
        self.guilds_properties_mapping = {
            guild: guilds_data.get(guild.id) for guild in self.guilds
        }
        print("Properties loaded")
        await self.background_loop.start()

    async def on_message(self, message: Message):
        if message.author == self.user:
            return
        if message.guild in self.guilds_in_setup:
            if message.content.startswith("/csm"):
                manager = self.guilds_in_setup[message.guild]
                is_setup_done = await manager.process_command(message.content)
                if is_setup_done:
                    self.guilds_in_setup.pop(message.guild)

    async def on_guild_join(self, guild):
        print(f"Joined guild {guild}")

        if guild in self.guilds_properties_mapping:
            return

        guild_service_channel = guild.system_channel  # hidden on noxs server
        guild_text_channels = [
            ch for ch in guild.channels if isinstance(ch, TextChannel)
        ]
        # service_channel = list(guild.channels)[13]  # temporary hardcode
        guild_setup_channel = None
        if await try_channel(guild_service_channel):
            guild_setup_channel = guild_service_channel
        else:
            for ch in guild_text_channels:
                # looking for first good channel
                if await try_channel(ch):
                    guild_setup_channel = guild_service_channel
                    break
        if not guild_setup_channel:
            # bot cannot talk, so it gets upset and leaves
            await guild.leave()

        sm = SetupManager(guild=guild, setup_channel=guild_setup_channel)
        await sm.help()
        self.guilds_in_setup[guild] = sm
        print(f"setup channel = {guild_setup_channel}")

    async def _add_role_if_not_exist(self, guild: Guild, props: GuildProperty):
        role = discord.utils.find(
            lambda rl: rl.id == props.channel_category_id, guild.categories
        )
        changed = False
        if not role:
            role = await guild.create_role(name="CSM-Bot")
            props.role_id = role.id
            changed = True
        return changed

    async def _create_channel_if_not_exists(self, guild: Guild, props: GuildProperty):
        changed = False
        cat = discord.utils.find(
            lambda cat: cat.id == props.channel_category_id, guild.categories
        )
        if not cat:
            cat = await guild.create_category_channel(
                name="Bot channels",
                reason="Bot stuff",
                position=0,
            )
            props.channel_category_id = cat.id
            changed = True
        channel = discord.utils.find(
            lambda ch: ch.id == props.channel_id, guild.channels
        )
        if not channel:
            channel = await guild.create_voice_channel(
                name="test_channel",
                reason="Bot stuff",
                category=cat,
                position=0,
                # overwrites=...,  # TODO role should block this channel joining
            )
            props.channel_id = channel.id
            changed = True
        return changed

    @tasks.loop(seconds=s.BACKGROUND_CYCLE)
    async def background_loop(self):
        props_with_updates: list[GuildProperty] = []
        # TODO add context manager with properties to this loop
        for guild, props in self.guilds_properties_mapping.items():
            role_changed = await self._add_role_if_not_exist(guild, props)
            channels_changed = await self._create_channel_if_not_exists(guild, props)
            if role_changed or channels_changed:
                props_with_updates.append(props)

        if props_with_updates:
            pp = PersistentProperties()
            await pp.update_guilds(props_with_updates)

    # async def get_tartar_pc(self) -> str:
    #     async with httpx.AsyncClient() as client:
    #         r = await client.get("https://api.battlemetrics.com/servers/19247858")
    #         values = r.json()["data"]["attributes"]
    #         return f"{values['players']}/{values['maxPlayers']}"


client_instance = Client(intents=intents)
client_instance.run(s.BOT_SECRET_KEY)

# @client.event
# async def on_ready():
#     print(f"We have logged in as {client.user}")
#     # task_loop.start()
#
#
# @client.event
# async def on_message(message):
#     if message.author == client.user:
#         return
#     if re.findall(r"517417011727302658|Конец|конец", message.content):
#         await message.channel.send("Конец тебе, конец!")
#
# @client.event
# async def on_guild_join(guild):
#     channel = guild.system_channel  # hidden on noxs server
#     channel = list(guild.channels)[13]  # temporary hardcode
#
#
# async def get_tartar_pc() -> str:
#     async with httpx.AsyncClient() as client:
#         r = await client.get("https://api.battlemetrics.com/servers/19247858")
#         values = r.json()["data"]["attributes"]
#         return f"{values['players']}/{values['maxPlayers']}"


# @tasks.loop(seconds=10)
# async def task_loop():
#     pc_str = await get_tartar_pc()
#     await client.change_presence(
#         status=discord.Status.dnd,
#         activity=discord.Activity(
#             type=discord.ActivityType.watching, name=f"{pc_str} on Tartar"
#         ),
#     )
#
#
# client.run(s.BOT_SECRET_KEY)
