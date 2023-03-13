import httpx
from discord import TextChannel, Forbidden, PermissionOverwrite

from conf import settings as s


async def try_channel(channel: TextChannel) -> bool:
    try:
        await channel.send(s.GREETING_MESSAGE)
        return True
    except Forbidden:
        return False


async def get_server_player_count(bm_id: int) -> dict[str, int]:
    url = f"{s.BM_API_BASE_URL}/{bm_id}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        values = r.json()["data"]["attributes"]
        return {
            "players": values["players"],
            "max_players": values["maxPlayers"],
        }

def get_chanel_overwrites():
    perm_over_everyone = {
        "connect": False,
        "speak": False,
        "stream": False,
        "view_channel": False,

    }
    perm_over_bot = {k: not v for k, v in perm_over_everyone.items()}
    everyone = PermissionOverwrite()
    csm_bot = PermissionOverwrite()
    everyone.update(**perm_over_everyone)
    csm_bot.update(**perm_over_bot)
    return everyone, csm_bot
