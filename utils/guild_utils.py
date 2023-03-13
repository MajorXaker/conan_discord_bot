import httpx
from discord import TextChannel, Forbidden

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
