import httpx
from discord import TextChannel, Guild

from utils.persistent_properties import PersistentProperties, GuildProperty

INSTRUCTIONS = (
    "Now bot needs to collect data for its setup. Next messages would be instructions",
    r"/csm setup_status <- this is to show status of setup, what is to be done",
    r"/csm bot_name \"name\" <- this is to set the bot name command on server",
    r"/csm server_id \"123123\" <- this is to set the id of the conan server on battlemetrics",
    r"/csm confirm_server_id <- this is to confirm the server id on battlemetrics",
    r"/csm help <- this is to show these tips",
)


class SetupManager:
    setup_channel: TextChannel
    guild_id: int
    bot_name: str = None
    server_id: int = None
    server_id_candidate: int = None
    bm_api_default_url = "https://api.battlemetrics.com/servers"

    def __init__(
        self, guild: Guild, setup_channel: TextChannel, internal: bool = False
    ):
        self.guild_id = guild.id
        self.setup_channel = setup_channel

    async def help(self):
        async with self.setup_channel.typing():
            for inst in INSTRUCTIONS:
                await self.setup_channel.send(inst)

    async def process_command(self, raw_command: str, *args, **kwargs):
        command_and_content = raw_command.split(maxsplit=2)
        command_and_content.pop(0)  # remove /csm
        match command_and_content[0]:
            case "bot_name":
                self.bot_name = command_and_content[1].strip('"')
            case "server_id":
                await self.set_server_id(command_and_content[1].strip('"'))
            case "confirm_server_id":
                await self.confirm_server_id()
            case "setup_status":
                await self.get_setup_status(send_message=True)
            case "help":
                await self.help()
            case _:
                print(f"unrecognized input {command_and_content}")
                return

        if await self.get_setup_status():
            await self.setup_channel.send("Setup has been completed")
            guild_properties = await self._form_guild_properties()
            pp_manager = PersistentProperties()
            await pp_manager.add_guild(new_gp=guild_properties)
            return True

    async def get_setup_status(self, send_message: bool = False):
        if not send_message:
            return self.bot_name and self.server_id

        if self.bot_name and self.server_id:
            # probably it should not ever be called
            await self.setup_channel.send("All is set!")
            return True

        bot_name = self.bot_name or "<Not set>"
        server_id = self.server_id or "<Not set>"

        message = (
            f"Settings to be set: Bot name: '{bot_name}'; server_id: '{server_id}'. "
            "Fill the corresponding fields"
        )
        await self.setup_channel.send(message)
        return False

    async def set_server_id(self, bm_server_id):
        api_url = f"{self.bm_api_default_url}/{bm_server_id}"
        async with httpx.AsyncClient(headers={"Connection": "close"}) as bm_client:
            r: dict = (await bm_client.get(api_url)).json()
            if not await self.is_conan_server(r):
                await self.setup_channel.send(
                    "Incorrect battlemetric conan server ID, "
                    "please provide correct one with the same command"
                )
                return
        self.server_id_candidate = bm_server_id
        await self.setup_channel.send(
            f"You've selected server '{r['data']['attributes']['name']}'. Is that correct?"
        )

    @staticmethod
    async def is_conan_server(js_response: dict) -> bool:
        # for now we will track only conan servers
        # but it could be tweaked to any other game tracked on battlemetrics
        try:
            is_conan = (
                js_response["data"]["relationships"]["game"]["data"]["id"]
                == "conanexiles"
            )
        except KeyError:
            is_conan = False
        is_error = js_response.get("errors", False)
        return is_conan and not is_error

    async def confirm_server_id(self):
        self.server_id = self.server_id_candidate
        await self.setup_channel.send("Server is set")

    async def _form_guild_properties(self) -> GuildProperty:
        return GuildProperty(
            guild_id=self.guild_id,
            bot_name=self.bot_name,
            server_id=self.server_id,
        )
