from config import OPENAI_API_KEY
from data.servers import SERVER_IDS
from nextcord import SlashOption, slash_command, Interaction
from nextcord.ext.commands import Cog
import aiohttp
import json


# Non-blocking version of the API request
async def generate_image(prompt: str, *, number_of_images: int = 1, size="1024x1024", timeout=180):
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    payload = {
        "prompt": prompt,
        "n": number_of_images,
        "size": size
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=json.dumps(payload), timeout=timeout) as response:
            return await response.json()


# Sends the prompt to the API, then returns the image url
async def image_request(prompt: str, size="256x256", timeout=180) -> str:
    response = None
    try:
        response = await generate_image(prompt=prompt, size=size, timeout=timeout)
        return response['data'][0]['url']
    except Exception as e:
        print(f"Exception: {e}\nResponse: {response}")
        return "Sorry, either your prompt is bad or I have a skill issue."


class ImageGeneration(Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(guild_ids=SERVER_IDS)
    async def image(self, interaction):
        pass

    # Generate a single image from a prompt
    @image.subcommand(name="generate", description="Create an image using OpenAI's image generation API")
    async def image_generate(self, interaction: Interaction,
                             prompt: str = SlashOption(
                                 description="What do you want to generate?",
                                 max_length=500,
                             ),
                             size: str = SlashOption(
                                 description="What size do you want the image to be?",
                                 choices=["256x256", "512x512", "1024x1024"],
                                 default="256x256"
                             )):
        if size != "256x256":
            return await interaction.send(content=f"Only staff can generate images larger than 256x256 for now.",
                                          ephemeral=True)
        await interaction.send(content=f"Generating image with prompt: {prompt}")
        try:
            response: str = await image_request(prompt=prompt, size=size, timeout=180)
        except Exception as e:
            print(f"Image generation exception : {e}")
            return await interaction.edit_original_message(content=f"Something went wrong. Please try again later.")
        await interaction.edit_original_message(content=response)


def setup(bot):
    bot.add_cog(ImageGeneration(bot))
