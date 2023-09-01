import nextcord


class RPSGameButton(nextcord.ui.Button):
    def __init__(self, value: str, emoji):
        super().__init__(label="\u200b", emoji=emoji)
        self.value = value

    async def callback(self, interaction: nextcord.Interaction) -> None:
        if (self.view.opponent and interaction.user.id != self.view.opponent.id
                or self.view.player_id == interaction.user.id):
            await interaction.send("You were not challenged.", ephemeral=True)
        else:
            await interaction.send(f"You chose {self.emoji}", ephemeral=True)
            if not self.view.opponent:
                self.view.opponent = interaction.user
            self.view.value = self.value
            self.view.stop()


class RPSGameView(nextcord.ui.View):
    def __init__(self, player_id: int, opponent=None):
        super().__init__(timeout=60)
        self.value = ""
        self.player_id = player_id
        self.opponent = opponent
        for value, emoji in (("rock", "🪨"), ("paper", "📰"), ("scissors", "✂️"), ("random", "🔀")):
            self.add_item(RPSGameButton(value, emoji))


class PaginationView(nextcord.ui.View):
    def __init__(self, embed: nextcord.Embed, pages: list):
        super().__init__(timeout=15)
        self.pages = pages
        self.embed = embed
        self.current_page = 0

    @nextcord.ui.button(label="\u200b", style=nextcord.ButtonStyle.grey, emoji="⬅️")
    async def btn_previous_page(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.current_page -= 1
        if self.current_page < 0:
            self.current_page = len(self.pages) - 1
        self.embed.description = self.pages[self.current_page]
        await interaction.response.edit_message(embed=self.embed, view=self)

    @nextcord.ui.button(label="\u200b", style=nextcord.ButtonStyle.grey, emoji="➡️")
    async def btn_next_page(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.current_page += 1
        if self.current_page > len(self.pages) - 1:
            self.current_page = 0
        self.embed.description = self.pages[self.current_page]
        await interaction.response.edit_message(embed=self.embed, view=self)
