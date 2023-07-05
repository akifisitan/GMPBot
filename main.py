from os import listdir
import nextcord
from nextcord.ext.commands import Bot
from config import BOT_TOKEN

# Initialize client
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = False  # Stop listening to DMs
activity = nextcord.Activity(name="TV", type=nextcord.ActivityType.watching)
bot = Bot(command_prefix="?", intents=intents, activity=activity)
bot.remove_command("help")


# Notify when bot is ready
@bot.event
async def on_ready():
    print(f"Connected to bot: {bot.user.name}")


# Load extensions & run the bot
def main():
    extensions_list = listdir("extensions")
    for extension in filter(lambda x: x.endswith(".py"), extensions_list):
        bot.load_extension(f"extensions.{extension[:-3]}")
    bot.run(BOT_TOKEN)


if __name__ == '__main__':
    main()
