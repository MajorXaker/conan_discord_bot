import json
from typing import Optional

import aiofiles

from conf import settings as s
from pydantic import BaseModel
import os
from pathlib import Path


class GuildProperty(BaseModel):
    guild_id: int
    bot_name: str
    server_id: int

    channel_id: Optional[int]  # TODO this could be a list someday
    channel_category_id: Optional[int]
    role_id: int | None

    @classmethod
    def from_data(
        cls,
        guild_id: str,
        bot_name: str,
        server_id: int,
    ):
        return cls(guild_id=guild_id, bot_name=bot_name, server_id=server_id)


class PersistentProperties:
    def __init__(self):
        self.file = s.PROPERTIES_FILE
        if not os.path.isfile(self.file):
            Path(self.file).touch()
            with open(self.file, mode="w") as f:
                f.write("[]")

    async def load_all(self) -> list[GuildProperty]:
        async with aiofiles.open(self.file, mode="r") as f:
            contents = await f.read()
        return [GuildProperty(**entry) for entry in json.loads(contents)]

    async def update_guild(self, new_gp: GuildProperty):
        current_entries = await self.load_all()
        if new_gp.guild_id not in (x.guild_id for x in current_entries):
            raise KeyError("Given guild does not exist in properties")

        cleared_vals = [gp for gp in current_entries if gp.guild_id != new_gp.guild_id]
        await self._add_data_to_json(old_data=cleared_vals, new_gp=new_gp)

    async def add_guild(self, new_gp: GuildProperty):
        current_properties = await self.load_all()
        if new_gp.guild_id in (x.guild_id for x in current_properties):
            raise ValueError("Cannot add existing guild")
        await self._add_data_to_json(old_data=current_properties, new_gp=new_gp)

    async def _add_data_to_json(self, old_data: list, new_gp: GuildProperty):
        old_data.append(new_gp)
        old_data = json.dumps([x.dict() for x in old_data])
        async with aiofiles.open(self.file, mode="w") as f:
            await f.write(old_data)

    async def update_guilds(self, new_data: list[GuildProperty]):
        current_entries = await self.load_all()
        new_data_ids = [
            guild.guild_id
            if guild not in current_entries
            else print("ERROR: Guild does not exist in properties")
            for guild in new_data
        ]
        untouched_properties = [
            entry for entry in current_entries if entry.guild_id not in new_data_ids
        ]
        prepared_data = json.dumps(
            [x.dict() for x in [*untouched_properties, *new_data]]
        )

        async with aiofiles.open(self.file, mode="w") as f:
            await f.write(prepared_data)
