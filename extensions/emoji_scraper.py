from data.servers import SERVER_IDS
import os
import zipfile
import asyncio
import nextcord
from nextcord import slash_command
from nextcord.ext.commands import Cog
import logging


async def get_emojis_from_server(server):
    return server.emojis


async def emoji_save_zip_delete(emoji, zip_file, num) -> str:
    file = f"{emoji.name}_{num}.gif" if emoji.animated else f"{emoji.name}_{num}.png"
    await emoji.save(file)
    logging.info(f"Saved {file} to disk")
    zip_file.write(file)
    logging.info(f"Added {file} to zip file")
    os.remove(file)
    logging.info(f"Deleted {file}")
    return file


class EmojiScraper(Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="scrape", description="Scrape emojis from all servers", guild_ids=SERVER_IDS,
                   default_member_permissions=nextcord.Permissions(manage_messages=True))
    async def slash_scrape(self, interaction):
        await interaction.response.send_message("Scraping emojis...")
        emojis = self.bot.emojis
        await interaction.edit_original_message(content=f"Found {len(emojis)} emojis, zipping...")
        # Create the zip file
        with zipfile.ZipFile("emojis.zip", "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Save the emojis to files and add them to the zip file asynchronously
            coroutines = [asyncio.create_task(
                emoji_save_zip_delete(emoji, zip_file, idx)) for idx, emoji in enumerate(emojis)]
            await asyncio.gather(*coroutines)
        # Send the zip file and delete it
        await interaction.edit_original_message(content=f"Zipping complete, sending the file...")
        await interaction.channel.send(file=nextcord.File("emojis.zip"))
        os.remove("emojis.zip")
        await interaction.edit_original_message(content=f"Successfully sent {len(emojis)} emojis as a zip file.")


def setup(bot):
    bot.add_cog(EmojiScraper(bot))
