# GET IT TWISTED
import nextcord
from nextcord import slash_command, SlashOption
from nextcord.ext.commands import Cog
import random as rnd
import asyncio
from config import SERVER_IDS, participants

# TODO: Add a way to view the leaderboard
# TODO: Add a way to view the stats of a player


def add_participant(user_id, username, *, elo=1000, wins=0, losses=0, draws=0) -> None:
    try:
        if participants.count_documents({"_id": user_id}, limit=1) != 0:
            return
        participants.insert_one(
            {"_id": user_id, "name": username, "elo": elo,
             "wins": wins, "losses": losses, "draws": draws}
        )
    except Exception as e:
        print(e)


def calc_rps_result(player1_choice, player2_choice) -> int:
    if player1_choice == player2_choice:
        return 0
    rps_idx = {"rock": 0, "paper": 1, "scissors": 2}
    return (rps_idx[player1_choice] - rps_idx[player2_choice]) % 3


def update_elo_rating(player1_id: int, player2_id: int, result: int) -> dict:
    if result not in {1, 2}:
        print(f"Result is: {result}")
        raise Exception("invalid result, must be either 1 or 2")
    winner_id = player1_id if result == 1 else player2_id
    winner_payout = rnd.randint(25, 35)
    winner_elo = participants.find_one_and_update(
        {"_id": winner_id}, {"$inc": {"elo": winner_payout, "wins": 1}})["elo"] + winner_payout
    loser_id = player2_id if result == 1 else player1_id
    loser_payout = rnd.randint(25, 35)
    loser_elo = participants.find_one_and_update(
        {"_id": loser_id}, {"$inc": {"elo": -1*loser_payout, "losses": 1}})["elo"] - loser_payout
    return {"Winner": f"+{winner_payout}", "Loser": f"-{loser_payout}", "WinnerElo": winner_elo, "LoserElo": loser_elo}


class RPSGame(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_games = set()

    @slash_command(name="rps", guild_ids=SERVER_IDS)
    async def rps(self, interaction: nextcord.Interaction):
        pass

    # Play RPS against a user
    @rps.subcommand(name="vs", description="Challenge a user to Rock-Paper-Scissors")
    async def rps_vs(self, interaction: nextcord.Interaction,
                     choice: str = SlashOption(
                         description="Choose one",
                         choices={"Rock": "rock", "Paper": "paper", "Scissors": "scissors", "Random": "random"}
                     ),
                     p2: nextcord.Member = SlashOption(
                         name="user",
                         description="Choose a user to challenge",
                         default=None
                     )):
        p1 = interaction.user
        if p1 == p2:  # and not TESTING:
            await interaction.send("You can't challenge yourself!", ephemeral=True)
            return
        if p2 and p2.bot:
            await interaction.send("You can't challenge a bot!", ephemeral=True)
            return
        if p1.id in self.current_games:
            await interaction.send("You already have a game running, wait for it to finish.", ephemeral=True)
            return
        # Send challenge message
        await interaction.send("Challenge sent!", ephemeral=True)
        self.current_games.add(p1.id)
        embed = nextcord.Embed(title="Rock-Paper-Scissors Challenge!", color=nextcord.Color.blurple())
        embed.set_author(name=p1.display_name, icon_url=p1.avatar.url if p1.avatar else None)
        player_mention = p2.mention if p2 else None
        embed.description = (f"{p2.mention} you have been challenged by {p1.mention} to play RPS!\n"
                             f"React with your choice within the next 120 seconds to play.") if p2 else (
            f"{p1.mention} has sent a challenge to play RPS!\n" 
            f"React with your choice within the next 120 seconds to play.")

        game_msg = await interaction.channel.send(content=player_mention, embed=embed)

        def check(reaction, user):
            return (user == p2) and (str(reaction.emoji) in {"🪨", "📰", "✂️", "🔀"}) if p2 else \
                (not user.bot) and (user != p1) and (str(reaction.emoji) in {"🪨", "📰", "✂️", "🔀"})

        for _ in ("🪨", "📰", "✂️", "🔀"):
            await game_msg.add_reaction(_)
        try:
            user_reaction, reaction_user = await self.bot.wait_for('reaction_add', timeout=120, check=check)
        except asyncio.TimeoutError:
            embed.description = f"Challenge timed out."
            await game_msg.clear_reactions()
            await game_msg.edit(content=None, embed=embed)
            await game_msg.delete(delay=10)
            self.current_games.remove(p1.id)
            await interaction.edit_original_message(content=f"Challenge timed out.")
            return

        def final_embed(in_embed: nextcord.Embed, game_result: int, gains_dict: dict) -> nextcord.Embed:
            in_embed.add_field(name=p1.display_name, value=f"**{p1_choice.upper()}**")
            in_embed.add_field(name="VS", value="**---**")
            in_embed.add_field(name=p2.display_name, value=f"**{p2_choice.upper()}**")
            # Draw
            if game_result not in {1, 2}:
                return in_embed
            p1_result = "Winner" if game_result == 1 else "Loser"
            p2_result = "Loser" if game_result == 1 else "Winner"
            in_embed.add_field(
                name=p1_result, value=f"{p1.mention}\nElo: {gains_dict[f'{p1_result}Elo']} ({gains_dict[p1_result]})")
            in_embed.add_field(name="**---**", value="**---**")
            in_embed.add_field(
                name=p2_result, value=f"{p2.mention}\nElo: {gains_dict[f'{p2_result}Elo']} ({gains_dict[p2_result]})")
            return in_embed

        # Challenge accepted, delete challenge message and set players
        await game_msg.clear_reactions()
        add_participant(p1.id, p1.name)
        # Set player2 to the reactor if the user did not specifically challenge a player
        p2 = p2 if p2 else reaction_user
        add_participant(p2.id, p2.name)
        # Set choices and calculate game result
        p1_choice = choice if choice != "random" else rnd.choice(["rock", "paper", "scissors"])
        emoji = str(user_reaction.emoji)
        emoji_to_choice = {"🪨": "rock", "📰": "paper", "✂️": "scissors"}
        p2_choice = emoji_to_choice[emoji] if emoji in emoji_to_choice else rnd.choice(["rock", "paper", "scissors"])
        result = calc_rps_result(p1_choice, p2_choice)
        # If result is a draw, no calculations done, show result and return
        if result == 0:
            embed = final_embed(embed, result, {})
            embed.add_field(name="Result", value="Draw", inline=False)
            await game_msg.delete()
            await interaction.channel.send(embed=embed, delete_after=30)
            self.current_games.remove(p1.id)
            participants.update_one({"_id": p1.id}, {"$inc": {"draws": 1}})
            participants.update_one({"_id": p2.id}, {"$inc": {"draws": 1}})
            await interaction.edit_original_message(content="Game completed successfully.")
            return
        # Calculate ELO for players, update player stats and store the ELO gain
        gains = update_elo_rating(p1.id, p2.id, result)
        # Show results and finish the game
        embed = final_embed(embed, result, gains)
        await game_msg.delete()
        await interaction.channel.send(embed=embed, delete_after=30)
        self.current_games.remove(p1.id)
        await interaction.edit_original_message(content="Game completed successfully.")

    # RPS RESET
    @rps.subcommand(name="reset", description="Reset the game in case of errors")
    async def rps_reset(self, interaction: nextcord.Interaction):
        await interaction.send("Reloading...", ephemeral=True)
        self.current_games.clear()
        await interaction.edit_original_message(content="Reloaded successfully.")


def setup(bot):
    bot.add_cog(RPSGame(bot))
