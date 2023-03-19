import nextcord
from nextcord import slash_command, SlashOption, user_command
from nextcord.ext import commands
from nextcord.ext.commands import Cog
from config import DATABASE, SERVER_IDS
import random

database = DATABASE["participants"]
giveaway_channels = {1074886518969204748}

class Giveaway:
    def __init__(self, message_id, num_winners=1):
        self.message_id = message_id
        self.participants = set()
        self.num_winners = num_winners
        self.winners = set()

    def get_winner(self):
        if len(self.participants) < self.num_winners:
            return None
        while len(self.winners) < self.num_winners:
            self.winners.add(random.choice(list(self.participants)))
        return self.winners


class Giveaways(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.giveaways = {}

    @slash_command(name="giveaway", guild_ids=SERVER_IDS,
                   default_member_permissions=nextcord.Permissions(manage_messages=True))
    async def giveaway(self, interaction):
        pass

    # Slash command that starts a giveaway
    @giveaway.subcommand(name="start", description="Start a giveaway")
    async def giveaway_start(self, interaction,
                             prize: str = SlashOption(description="Giveaway prize"),
                             winners: int = SlashOption(description="Number of winners", min_value=1),
                             end: int = SlashOption(description="Unix timestamp for ending", min_value=1),
                             giveaway_text: str = SlashOption(description="Giveaway text", required=False)
                             ):
        await interaction.send(content="Loading...", ephemeral=True)
        embed = nextcord.Embed(title=prize, color=0x03fcdf, timestamp=nextcord.utils.utcnow())
        embed.description = (f"React with 🎉 to enter!\n\n**Prize:** {prize}\n**Ends:** <t:{end}:R>"
                             f"\n**Winners:** {winners}")
        giveaway_message = await interaction.channel.send(embed=embed)
        await giveaway_message.add_reaction("🎉")
        giveaway = Giveaway(message_id=giveaway_message.id, num_winners=winners)
        self.giveaways[giveaway_message.id] = giveaway
        await interaction.edit_original_message(content="Giveaway started!")

    # Slash command that ends a giveaway
    @giveaway.subcommand(name="end", description="End a giveaway")
    async def giveaway_end(self, interaction):
        await interaction.send(content="Loading...", ephemeral=True)
        if interaction.channel.last_message.id in self.giveaways:
            giveaway = self.giveaways[interaction.channel.last_message.id]
            winner = giveaway.get_winner()
            await interaction.channel.send(f"The winner is {winner.mention}!")
            del self.giveaways[interaction.channel.last_message.id]
        else:
            await interaction.edit_original_message(content="There is no giveaway to end!")

    # Voting
    @commands.Cog.listener('on_raw_reaction_add')
    async def reaction_add(self, payload):
        # Ignore reactions from the bot itself
        if payload.user_id == self.bot.user.id:
            return
        # Only allow reactions in the giveaway channel Return if the message is not a giveaway message
        if payload.message_id not in self.giveaways or payload.channel_id not in giveaway_channels:
            return
        message_id = payload.message_id
        giveaway = self.giveaways[message_id]
        # Reaction user's id
        user_id = payload.user_id
        # Remove reaction from the reacted message
        # message = await self.bot.get_channel(payload.channel_id).fetch_message(message_id)
        # await message.remove_reaction(payload.emoji, payload.member)
        # Check if the user has already reacted to the message
        if user_id not in giveaway.participants:
            giveaway.participants.add(user_id)

    # Voting
    @commands.Cog.listener('on_raw_reaction_remove')
    async def reaction_remove(self, payload):
        # Ignore reactions from the bot itself
        if payload.user_id == self.bot.user.id:
            return
        # Only allow reactions in the giveaway channel Return if the message is not a giveaway message
        if payload.message_id not in self.giveaways or payload.channel_id not in giveaway_channels:
            return
        message_id = payload.message_id
        giveaway = self.giveaways[message_id]
        # Reaction user's id
        user_id = payload.user_id
        # Check if the user has already reacted to the message
        if user_id in giveaway.participants:
            giveaway.participants.remove(user_id)


def setup(bot):
    bot.add_cog(Giveaways(bot))
