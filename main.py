import nextcord.ext
from nextcord.ext.commands import Bot
from config import BOT_TOKEN, CHECK

# Initialize client
intents = nextcord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = False  # Stop listening to DMs
activity = nextcord.Activity(name="TV", type=nextcord.ActivityType.watching)
bot = Bot(command_prefix="!gmp", intents=intents, activity=activity)


@bot.event
async def on_ready():
    print(f"Connected to bot: {bot.user.name}")


# Run the bot if everything is set up correctly
def main():
    if CHECK:
        bot.run(BOT_TOKEN)


if __name__ == '__main__':
    main()



