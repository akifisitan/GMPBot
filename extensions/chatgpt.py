from config import OPENAI_API_KEY, SERVER_IDS
import asyncio
import aiohttp
import json
from nextcord import SlashOption, slash_command
from nextcord.ext.commands import Cog


async def get_usage(date):
    url = f"https://api.openai.com/v1/usage?date={date}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=30) as resp:
            return await resp.json()


# Non-blocking version of the API request
async def create_completion(model, messages, *, temperature=0.7, presence_penalty=0.6,
                            frequency_penalty=0.6, max_tokens=400):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
        "max_tokens": max_tokens
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=json.dumps(payload), timeout=30) as resp:
            return await resp.json()


# Takes the question, the current dialog, and the mode (0 = normal, 1 = remember, 2 = remember and use)
# Sends the question to the API, and returns the response and the number of tokens used
async def gpt_dialog(question: str, current_dialog=None, mode=0, max_tokens=400) -> tuple[str, int]:
    current_dialog = current_dialog if current_dialog else []
    if mode == 0:
        current_dialog.clear()
    current_dialog.append({"content": question, "role": "user"})
    print(f"Current dialog is: {current_dialog}")
    try:
        response = await create_completion(model="gpt-3.5-turbo", messages=current_dialog, max_tokens=max_tokens,
                                           temperature=0.7, presence_penalty=0.6, frequency_penalty=0.6)
    except asyncio.TimeoutError:
        return "Request timed out!", 0
    except Exception as e:
        print(e)
        return "Error: API request failed", 0
    # Ensures ChatGPT remembers the answers it gave, but uses a lot more tokens
    if mode == 2:
        current_dialog.append({"content": response['choices'][0]['message']['content'],
                               "role": response['choices'][0]['message']['role']})
    return response['choices'][0]['message']['content'], int(response['usage']['total_tokens'])


# Sends a message to the channel ignoring any errors
async def send_message(interaction, message: str):
    try:
        await interaction.channel.send(content=message)
    except Exception as e:
        print(e)


class ChatGPT(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_sessions = set()

    """
    @Cog.listener("on_message")
    async def chatgpt(self, message):
        if message.author.id not in self.active_sessions:
            return
        if message.content.lower() in {"exit", "quit", "stop", "end"}:
            self.active_sessions.remove(message.author.id)
        async with message.channel.typing():
            response = await gpt_dialog(message.content)
        if len(response[0]) <= 2000:
            await send_message(message, response[0])
        else:
            paragraphs = response[0].split("\n\n")
            for paragraph in paragraphs:
                await send_message(message, paragraph)
    """
    @slash_command(name="usage", description="Learn usage", guild_ids=SERVER_IDS)
    async def usage_chatgpt(self, interaction,
                            day: int = SlashOption(min_value=1, max_value=31,
                                                   description="The date to check usage for (YYYY-MM-DD)"),
                            month: int = SlashOption(min_value=1, max_value=12,
                                                     description="The date to check usage for (YYYY-MM-DD)"),
                            year: int = SlashOption(min_value=2022, max_value=2024, default="2023",
                                                    description="The date to check usage for (YYYY-MM-DD)")
                            ):
        await interaction.send(content="Getting usage...", ephemeral=True)
        try:
            usage = await get_usage(f"{year}-{month}-{day}")
        except Exception as e:
            print(e)
            return await interaction.edit_original_message(content="Error: API request failed")
        used_tokens, n_requests = 0, 0
        for entry in usage['data']:
            used_tokens += entry['n_generated_tokens_total']
            n_requests += entry['n_requests']
        print(f"Used tokens: {used_tokens}, Number of requests: {n_requests}")
        await interaction.edit_original_message(content=f"You have used {used_tokens} tokens in {day}/{month}/{year}")

    @slash_command(name="chatgpt", description="Ask ChatGPT anything", guild_ids=SERVER_IDS)
    async def ask_chatgpt(self, interaction,
                          mode: int = SlashOption(
                              description="The mode to use (Default is incomplete)",
                              choices={"Incomplete": 0, "Semi-Complete": 1, "Complete": 2},
                              default=0),
                          max_tokens: int = SlashOption(
                              description="The maximum amount of tokens to use (Default is 400)",
                              choices=[30, 50, 100, 200, 300, 400, 500, 750, 1000],
                              default=400)
                          ):
        if interaction.user.id in self.active_sessions:
            return await interaction.send(
                content="You already have a session running! Type exit or wait for it to time out.", ephemeral=True)
        await interaction.send(content="Starting a new session...", ephemeral=True)
        current_dialog, used_tokens, busy, num_questions = [], 0, False, 0
        self.active_sessions.add(interaction.user.id)
        await interaction.channel.send(f"Hey {interaction.user.mention}! How can I assist you today?")

        def check(message):
            return message.author.id == interaction.user.id and message.channel.id == interaction.channel.id \
                and not busy

        while True:
            try:
                question = await self.bot.wait_for('message', timeout=300, check=check)
            except asyncio.TimeoutError:
                question = None
            except Exception as e:
                self.active_sessions.remove(interaction.user.id)
                return await interaction.edit_original_message(content=f"Error: {e}")
            if not question or question.content.lower() in {"exit", "quit", "stop", "end"}:
                self.active_sessions.remove(interaction.user.id)
                print(f"Session stats for {interaction.user}: {used_tokens} tokens used, "
                      f"{num_questions} messages sent.")
                await interaction.edit_original_message(content="Session ended!")
                return await send_message(interaction, "Bye!")
            async with interaction.channel.typing():
                busy = True
                response = await gpt_dialog(question.content, current_dialog, mode, max_tokens=max_tokens)
                num_questions += 1
                used_tokens += response[1]
            if len(response[0]) <= 2000:
                await send_message(interaction, response[0])
            else:
                paragraphs = response[0].split("\n\n")
                for paragraph in paragraphs:
                    await send_message(interaction, paragraph)
            busy = False
            print(f"Used tokens: {used_tokens} (+{response[1]})")


def setup(bot):
    bot.add_cog(ChatGPT(bot))
