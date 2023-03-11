import discord
import httpx
from discord.ext import tasks

intents = discord.Intents.default()
client = discord.Client(intents=intents)
intents.message_content = True
# BM_URL = "https://example.com" # <- в это значение нужно проставить адрес сервера на батлметрике
BM_URL = "https://api.battlemetrics.com/servers/19247858"  # например так


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    task_loop.start()


async def get_tartar_pc() -> str:
    async with httpx.AsyncClient(headers={"Connection": "close"}) as bm_client:
        r = await bm_client.get(BM_URL)
        values = r.json()["data"]["attributes"]
        return f"{values['players']}/{values['maxPlayers']}"


async def get_time() -> str:
    async with httpx.AsyncClient() as time_client:
        r = await time_client.get(
            "https://www.timeapi.io/api/Time/current/zone?timeZone=Europe/Minsk"
        )
    values = r.json()
    return values["time"]


@tasks.loop(seconds=90)
async def task_loop():
    pc_str = await get_tartar_pc()
    time_str = await get_time()
    await client.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name=f": {pc_str} | {time_str} ",
        ),
    )


# example token
# token = 'MTA4MzQHTzQwMTUxLLU9NTY0Mg.G332Qtp.vkf8uCbreWXb42СЕАREuGdqu-HJvCygk__80mx'
client.run("token")  # вот сюда вставить токен бота
