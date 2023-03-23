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
        async with session.get(url, headers=headers, timeout=180) as response:
            return await response.json()


# Non-blocking version of the API request
async def create_completion(model, messages, *, temperature=0.7, presence_penalty=0.6,
                            frequency_penalty=0.6, max_tokens=400, timeout=180):
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
        async with session.post(url, headers=headers, data=json.dumps(payload), timeout=timeout) as response:
            return await response.json()


# Takes the question, the current dialog, and the mode (0 = forget all, 1 = remember only user input, 2 = remember all)
# Sends the question to the API, then returns the response and the number of tokens used
async def gpt_request(question: str, current_dialog, mode=0, max_tokens=400, timeout=180) -> tuple[str, int]:
    if len(current_dialog) > 0 and mode == 0:
        current_dialog.clear()
    current_dialog.append({"content": question, "role": "user"})
    # print(f"Current dialog is: {current_dialog}")
    try:
        response = await create_completion(model="gpt-3.5-turbo", messages=current_dialog,
                                           max_tokens=max_tokens, timeout=timeout)
    except asyncio.TimeoutError:
        return "Request timed out!", 0
    except Exception as e:
        print(e)
        return "Error: API request failed", 0
    # Ensures ChatGPT remembers the answers it gave, but uses a lot more tokens
    if mode == 2:
        current_dialog.append({"content": response['choices'][0]['message']['content'],
                               "role": response['choices'][0]['message']['role']})
    print(current_dialog)
    return response['choices'][0]['message']['content'], int(response['usage']['total_tokens'])


# async def gpt_dialog

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

    @slash_command(name="chatgpt", guild_ids=SERVER_IDS)
    async def chatgpt(self, interaction):
        pass

    # Ask ChatGPT a single question
    @chatgpt.subcommand(name="ask", description="Ask ChatGPT a question")
    async def chatgpt_ask(self, interaction):
        await interaction.send(content=f"How can I assist you today?", ephemeral=True)

        def check(message):
            return message.author.id == interaction.user.id and message.channel.id == interaction.channel.id

        try:
            question = await self.bot.wait_for('message', timeout=300, check=check)
        except Exception as e:
            return await interaction.edit_original_message(content=f"Error: {e}")
        async with interaction.channel.typing():
            response = await gpt_request(question.content)
        if len(response[0]) <= 2000:
            await send_message(interaction, response[0])
        else:
            paragraphs = response[0].split("\n\n")
            for paragraph in paragraphs:
                await send_message(interaction, paragraph)
        await interaction.edit_original_message(content=f"Thanks for using ChatGPT!")

    # Have a dialog with ChatGPT (Admin only for now)
    @chatgpt.subcommand(name="dialog", description="Have a dialog with ChatGPT")
    async def chatgpt_dialog(self, interaction,
                             mode: int = SlashOption(
                                 description="The mode to use (Default is incomplete)",
                                 choices={"Incomplete": 0, "Semi-Complete": 1, "Complete": 2},
                                 default=0),
                             max_tokens: int = SlashOption(
                                 description="The maximum amount of tokens to use (Default is 400)",
                                 choices=[30, 50, 100, 200, 300, 400, 500, 750, 1000],
                                 default=400),
                             timeout: int = SlashOption(
                                 description="The amount of time to wait for a response (Default is 180 seconds)",
                                 default=180,
                                 min_value=30,
                                 max_value=270)
                             ):
        if interaction.user.id not in {434647152552312853, 238479694423392256}:
            return await interaction.send(content="Use /chatgpt ask for now.", ephemeral=True)
        if interaction.user.id in self.active_sessions:
            return await interaction.send(
                content="You already have a session running! Type exit or wait for it to time out.", ephemeral=True)
        if mode != 0 and interaction.user.id not in {434647152552312853, 238479694423392256}:
            return await interaction.send(content="You don't have permission to use this mode!", ephemeral=True)
        await interaction.send(content=f"How can I assist you today?", ephemeral=True)
        current_dialog, used_tokens, busy, num_questions = [], 0, False, 0
        self.active_sessions.add(interaction.user.id)

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
                return await interaction.edit_original_message(content="Session ended!")
            async with interaction.channel.typing():
                busy = True
                response = await gpt_request(question.content, current_dialog, mode=mode,
                                             max_tokens=max_tokens, timeout=timeout)
                num_questions += 1
                used_tokens += response[1]
            if len(response[0]) <= 2000:
                await send_message(interaction, response[0])
            else:
                paragraphs = response[0].split("\n\n")
                for paragraph in paragraphs:
                    await send_message(interaction, paragraph)
            busy = False
            # print(f"Used tokens: {used_tokens} (+{response[1]})")

    @chatgpt.subcommand(name="usage", description="Check token usage by date")
    async def chatgpt_usage(self, interaction,
                            day: int = SlashOption(min_value=1, max_value=31,
                                                   description="The day to check usage for (01-31)"),
                            month: int = SlashOption(min_value=1, max_value=12,
                                                     description="The month to check usage for (01-12)"),
                            ):
        if interaction.user.id not in {434647152552312853, 238479694423392256}:
            return await interaction.send(content="You do not have permission to use this command.", ephemeral=True)
        await interaction.send(content="Getting usage...", ephemeral=True)
        try:
            usage = await get_usage(f"2023-{month}-{day}")
        except Exception as e:
            return await interaction.edit_original_message(content=f"Error: {e}")
        used_tokens, n_requests = 0, 0
        for entry in usage['data']:
            used_tokens += entry['n_generated_tokens_total']
            n_requests += entry['n_requests']
        # print(f"Used tokens: {used_tokens}, Number of requests: {n_requests}")
        await interaction.edit_original_message(
            content=f"```Usage ({day}/{month}/2023)\nUsed tokens: {used_tokens}\nNumber of requests: {n_requests}```")


def setup(bot):
    bot.add_cog(ChatGPT(bot))
