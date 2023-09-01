from utils.colors import random_color
from data.servers import SERVER_IDS
from data.reminder_jobs import ReminderJob, get_reminder_jobs, insert_new_reminder_job, delete_reminder_job
import nextcord
from nextcord import slash_command, Interaction, SlashOption, Message, Embed
from nextcord.ext.commands import Cog, Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta


def create_embed(message: Message) -> Embed:
    embed = Embed(color=random_color())

    return embed


class Logging(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.log_channel = None

    async def log(self, content: str = None, embed: Embed = None):
        if not self.log_channel:
            self.log_channel = self.bot.get_channel(1121024973847416865)
        try:
            await self.log_channel.send(content=content, embed=embed)
        except Exception as e:
            print(e)

    @Cog.listener("on_message_delete")
    async def deleted_messages(self, message: Message):
        embed = Embed(color=random_color(),
                      description=f"Message deleted in {message.channel.mention}")
        embed.set_author(name=message.author.name, icon_url=message.author.avatar.url)
        embed.add_field(name="Content", value=message.content, inline=False)
        embed.add_field(name="Date", value=f"<t:{int(nextcord.utils.utcnow().timestamp())}:R>")
        embed.add_field(name="ID", value=f"```User = {message.user_id}\nMessage = {message.id}```")
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        await self.log(embed=embed)

    @Cog.listener("on_message_edit")
    async def edited_messages(self, before: Message, after: Message):
        message = before
        embed = Embed(color=random_color(),
                      description=f"{message.author.name} updated their message in {message.channel.mention}",
                      timestamp=nextcord.utils.utcnow())
        embed.set_author(name=message.author.name, icon_url=message.author.avatar.url)
        embed.add_field(name="Channel",
                        value=f"{message.channel.mention} ({message.channel.name})\n"
                              f"[Go To Message]({message.jump_url})")
        embed.add_field(name="Now", value=after.content, inline=False)
        embed.add_field(name="Previous", value=before.content, inline=False)
        embed.add_field(name="ID", value=f"```User = {message.user_id}\nMessage = {message.id}```")
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar.url)
        await self.log(embed=embed)


def setup(bot: Bot):
    bot.add_cog(Logging(bot))
