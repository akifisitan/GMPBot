from helpers.colors import random_color
from data.servers import SERVER_IDS
from data.reminder_jobs import ReminderJob, get_reminder_jobs, insert_new_reminder_job, delete_reminder_job
import nextcord
from nextcord import slash_command, Interaction, SlashOption
from nextcord.ext.commands import Cog, Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

reminders = get_reminder_jobs()
print("Reminders:", reminders)


class ReminderCommands(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        for job in reminders.values():
            self.scheduler.add_job(self.remind_user, 'date', run_date=datetime.fromtimestamp(job.timestamp),
                                   args=[job])

    async def remind_user(self, job: ReminderJob):
        embed = nextcord.Embed(description=job.message, color=random_color())
        embed.set_author(name="Reminder", icon_url=self.bot.user.avatar.url)
        await self.bot.get_channel(job.channel_id).send(content=f"<@{job.user_id}>", embed=embed)
        if job.id in reminders:
            reminders.pop(job.id)
        delete_reminder_job(job.id)

    @slash_command(name="reminder", guild_ids=SERVER_IDS)
    async def reminder(self, interaction: Interaction):
        pass

    @reminder.subcommand(name="set", description="Set a reminder to be reminded of sometime")
    async def reminder_set(self, interaction: Interaction,
                           message: str = SlashOption(description="What do you want to be reminded of?",
                                                      max_length=1000),
                           time: str = SlashOption(description="How much time from now? (10s, 10m, 10h)",
                                                   min_length=2, max_length=3),
                           ):
        if not time[:-1].isdigit() or time[-1] not in ("s", "m", "h"):
            await interaction.send("Please specify a valid time.", ephemeral=True)
            return
        seconds = int(time[:-1]) if time[-1] == "s" else 0
        minutes = int(time[:-1]) if time[-1] == "m" else 0
        hours = int(time[:-1]) if time[-1] == "h" else 0
        if seconds <= 10 and minutes == 0 and hours == 0:
            await interaction.send("Please specify a time longer than 10 seconds.", ephemeral=True)
            return
        await interaction.send("Setting reminder...", ephemeral=True)
        try:
            timestamp = int(datetime.timestamp(datetime.now() + timedelta(seconds=seconds,
                                                                          minutes=minutes, hours=hours)))
            date = datetime.fromtimestamp(timestamp)
            job_id = insert_new_reminder_job((interaction.user.id, interaction.channel.id, timestamp, message))
            job = ReminderJob(id=job_id, timestamp=timestamp, user_id=interaction.user.id,
                              channel_id=interaction.channel.id, message=message)
            self.scheduler.add_job(self.remind_user, 'date', run_date=date, args=[job], id=str(job.id))
            reminders[job.id] = job
            await interaction.edit_original_message(content=f"Reminder set for <t:{timestamp}>")
        except Exception as e:
            print(f"Failed to set reminder: {e}")
            await interaction.edit_original_message(content="Failed to set reminder.")

    @reminder.subcommand(name="list", description="List all your reminders")
    async def reminder_list(self, interaction: Interaction):
        await interaction.send("Loading...", ephemeral=True)
        embed = nextcord.Embed(title="Your Reminders", color=random_color())
        for job in reminders.values():
            if job.user_id == interaction.user.id:
                embed.add_field(name=f"Job Id: {job.id} Timestamp: <t:{job.timestamp}>",
                                value=job.message, inline=False)
        if len(embed.fields) == 0:
            await interaction.edit_original_message(content="You have no reminders.")
        else:
            await interaction.edit_original_message(content=None, embed=embed)

    @reminder.subcommand(name="delete", description="Delete a reminder you have set")
    async def reminder_delete(self, interaction: Interaction,
                              job_id: str = SlashOption(description="The id of the reminder to delete")
                              ):
        await interaction.send("Deleting reminder...", ephemeral=True)
        int_job_id = int(job_id)
        if int_job_id not in reminders:
            await interaction.edit_original_message(content="This reminder does not exist.")
            return
        if reminders[int_job_id].user_id != interaction.user.id:
            await interaction.edit_original_message(content="You can only delete your own reminders.")
            return
        try:
            self.scheduler.remove_job(job_id)
            reminders.pop(int_job_id)
            delete_reminder_job(int_job_id)
            await interaction.edit_original_message(content="Reminder deleted.")
        except Exception as e:
            print("Failed to delete reminder: ", e)
            await interaction.edit_original_message(content=f"Failed to delete reminder.")


def setup(bot):
    bot.add_cog(ReminderCommands(bot))
