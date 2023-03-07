import os
import nextcord.ext
from nextcord.ext.commands import Bot
from config import BOT_TOKEN, CHECK

# Initialize client
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = False  # Stop listening to DMs
activity = nextcord.Activity(name="TV", type=nextcord.ActivityType.watching)
bot = Bot(command_prefix="?", intents=intents, activity=activity)
bot.remove_command("help")


@bot.event
async def on_ready():
    print(f"Connected to bot: {bot.user.name}")


def main():
    if not CHECK:
        return
    for extension in filter(lambda x: x.endswith(".py"), os.listdir("extensions")):
        bot.load_extension(f"extensions.{extension[:-3]}")
    bot.run(BOT_TOKEN)


if __name__ == '__main__':
    main()



