from discord import TextChannel, Forbidden
from conf import settings as s


async def try_channel(channel: TextChannel) -> bool:
    try:
        await channel.send(s.GREETING_MESSAGE)
        return True
    except Forbidden:
        return False
