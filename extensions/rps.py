from data.servers import SERVER_IDS
from data.rps_players import get_rps_players, RPSPlayer, update_player, insert_new_player
from utils.colors import random_color
from utils.ui import RPSGameView, PaginationView
import nextcord
from nextcord import slash_command, SlashOption
from nextcord.ext.commands import Cog
import random as rnd
from io import StringIO


rps_players = get_rps_players()
print("RPS Players:", rps_players)
rps_table = {"rock": 0, "paper": 1, "scissors": 2}


def rps_result(player1_choice: str, player2_choice: str) -> int:
    if player1_choice == player2_choice:
        return 0
    return (rps_table[player1_choice] - rps_table[player2_choice]) % 3


def update_ratings(player1: RPSPlayer, player2: RPSPlayer, result: int) -> dict:
    if result == 1:
        winner = player1
        loser = player2
    elif result == 2:
        winner = player2
        loser = player1
    else:
        print(f"Result is: {result}")
        raise Exception("invalid result, must be either 1 or 2")
    winner_payout = rnd.randint(25, 35)
    winner.wins += 1
    winner.elo += winner_payout
    loser_payout = rnd.randint(20, 25)
    loser.losses += 1
    loser.elo -= loser_payout
    update_player(winner)
    update_player(loser)
    return {"Winner": f"+{winner_payout}", "Loser": f"-{loser_payout}"}


class RPSGame(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_games = set()

    @slash_command(name="rps", guild_ids=SERVER_IDS)
    async def rps(self, interaction: nextcord.Interaction):
        pass

    @rps.subcommand(name="vs", description="Challenge a user to Rock-Paper-Scissors")
    async def rps_vs(self, interaction: nextcord.Interaction,
                     choice: str = SlashOption(
                         description="Choose one",
                         choices=("Rock", "Paper", "Scissors", "Random")),
                     p2: nextcord.Member = SlashOption(
                         name="user",
                         description="Choose a user to challenge",
                         default=None
                     )):
        choice = choice.lower()
        p1 = interaction.user
        if p1 == p2:
            await interaction.send("You can't challenge yourself!", ephemeral=True)
            return
        if p2 and p2.bot:
            await interaction.send("You can't challenge a bot!", ephemeral=True)
            return
        if p1.id in self.current_games:
            await interaction.send("You already have a game running, wait for it to finish.", ephemeral=True)
            return
        await interaction.send("Challenge sent!", ephemeral=True)
        self.current_games.add(p1.id)
        embed = nextcord.Embed(title="Rock-Paper-Scissors Challenge!", color=random_color())
        embed.set_author(name=p1.display_name, icon_url=p1.avatar.url if p1.avatar else None)
        if p2:
            player_mention = p2.mention
            embed.description = (f"{p2.mention} you have been challenged by {p1.mention} to play RPS!\n"
                                 f"Pick your choice within the next minute to play.")
            view = RPSGameView(player_id=p1.id, opponent=p2)
        else:
            player_mention = None
            embed.description = (f"{p1.mention} has sent a challenge to play RPS!\n"
                                 f"Pick your choice within the next minute to play.")
            view = RPSGameView(player_id=p1.id)
        game_msg = await interaction.channel.send(content=player_mention, embed=embed, view=view)
        # Wait for opponent to interact or the view to timeout
        if await view.wait():
            self.current_games.remove(p1.id)
            embed.description = f"Challenge timed out."
            await game_msg.edit(content=None, embed=embed, view=None)
            await game_msg.delete(delay=10)
            await interaction.edit_original_message(content=f"Challenge timed out.")
            return
        opponent = view.opponent
        opponent_choice = view.value
        # Challenge accepted, set players
        player1 = f"{p1.id}.{interaction.guild.id}"
        # Add player1 to database if not already there
        if player1 not in rps_players:
            rps_players[player1] = RPSPlayer(id=player1, user_id=p1.id, server_id=interaction.guild.id,
                                             username=p1.name, elo=1000, wins=0, losses=0, draws=0)
            insert_new_player(rps_players[player1])
        # Set player2 to the responding user, if the user did not specifically challenge a player
        p2 = opponent
        player2 = f"{p2.id}.{interaction.guild.id}"
        # Add player2 to database if not already there
        if player2 not in rps_players:
            rps_players[player2] = RPSPlayer(id=player2, user_id=p2.id, server_id=interaction.guild.id,
                                             username=p2.name, elo=1000, wins=0, losses=0, draws=0)
            insert_new_player(rps_players[player2])
        # Set choices and calculate game result
        p1_choice = rnd.choice(["rock", "paper", "scissors"]) if choice == "random" else choice
        p2_choice = rnd.choice(["rock", "paper", "scissors"]) if opponent_choice == "random" else opponent_choice
        # Format embed according to player choices
        p1_format = f"{p1_choice.upper()} 🔀" if choice == "random" else p1_choice.upper()
        p2_format = f"{p2_choice.upper()} 🔀" if opponent_choice == "random" else p2_choice.upper()
        embed.add_field(name=p1.display_name, value=f"**{p1_format}**")
        embed.add_field(name="VS", value="\u200b")
        embed.add_field(name=p2.display_name, value=f"**{p2_format}**")
        result = rps_result(p1_choice, p2_choice)
        if result == 0:
            embed.add_field(name="Result", value="Draw", inline=False)
            rps_players[player1].draws += 1
            rps_players[player2].draws += 1
            await game_msg.delete()
            await interaction.channel.send(embed=embed, delete_after=30)
            self.current_games.remove(p1.id)
            await interaction.edit_original_message(content="Game completed successfully.")
            return
        # Calculate ELO for players, update player stats and store the ELO gains in a dictionary for later use
        gains = update_ratings(rps_players[player1], rps_players[player2], result)
        # Show results and finish the game
        p1_result = "Winner" if result == 1 else "Loser"
        p2_result = "Loser" if result == 1 else "Winner"
        embed.add_field(name=p1_result, value=f"{p1.mention}\nElo: {rps_players[player1].elo} ({gains[p1_result]})")
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name=p2_result, value=f"{p2.mention}\nElo: {rps_players[player2].elo} ({gains[p2_result]})")
        await game_msg.delete()
        await interaction.channel.send(embed=embed, delete_after=30)
        self.current_games.remove(p1.id)
        await interaction.edit_original_message(content="Game completed successfully.")

    @rps.subcommand(name="leaderboard", description="View the Rock-Paper-Scissors leaderboard")
    async def rps_leaderboard(self, interaction: nextcord.Interaction,
                              hidden: bool = SlashOption(
                                  description="If the leaderboard is shown to everyone or just you",
                                  default=False)
                              ):
        await interaction.send("Loading leaderboard...", ephemeral=hidden)
        dict_to_sort = {
            player_id: rps_players[player_id].elo
            for player_id in rps_players if rps_players[player_id].server_id == interaction.guild.id
        }
        players_sorted = sorted(dict_to_sort, key=dict_to_sort.get, reverse=True)
        leaderboard = StringIO()
        player_list = []
        for ranking, player_id in enumerate(players_sorted):
            stats = (f"Elo: ``{rps_players[player_id].elo}`` | "
                     f"Wins: ``{rps_players[player_id].wins}`` | "
                     f"Losses: ``{rps_players[player_id].losses}`` | "
                     f"Draws: ``{rps_players[player_id].draws}``\n")
            leaderboard.write(f"#**{ranking + 1}** <@{rps_players[player_id].user_id}>\n{stats}\n")
            if ranking % 5 == 4:
                player_list.append(leaderboard.getvalue())
                leaderboard = StringIO()
        embed = nextcord.Embed(color=random_color())
        embed.set_author(name="RPS Leaderboard", icon_url=self.bot.user.avatar.url)
        if len(player_list) == 0:
            embed.description = leaderboard.getvalue()
            await interaction.edit_original_message(content=None, embed=embed)
            return
        embed.description = player_list[0]
        pagination_view = PaginationView(embed=embed, pages=player_list)
        await interaction.edit_original_message(content=None, embed=embed, view=pagination_view)
        if await pagination_view.wait():
            if not hidden:
                await interaction.delete_original_message()
            else:
                await interaction.edit_original_message(view=None)

    @rps.subcommand(name="stats", description="Check a user's RPS stats")
    async def rps_stats(self, interaction: nextcord.Interaction,
                        user: nextcord.Member = SlashOption(
                            description="User to check stats for (Default: yourself)",
                            default=None)
                        ):
        user = user if user else interaction.user
        player_id = f"{user.id}.{interaction.guild.id}"
        if player_id not in rps_players:
            await interaction.send(f"{user.mention} hasn't played Rock-Paper-Scissors yet!", ephemeral=True)
            return
        stats = (f"```Elo: {rps_players[player_id].elo}\nWins: {rps_players[player_id].wins}\n"
                 f"Losses: {rps_players[player_id].losses}\nDraws: {rps_players[player_id].draws}```")
        embed = nextcord.Embed(description=f"{user.mention}{stats}", color=random_color())
        embed.set_author(name=user.name, icon_url=user.avatar.url)
        await interaction.send(embed=embed, ephemeral=True)

    @rps.subcommand(name="reset", description="Reset the game state in case of errors")
    async def rps_reset(self, interaction: nextcord.Interaction):
        await interaction.send("Resetting game state...", ephemeral=True)
        try:
            global rps_players
            self.current_games.clear()
            rps_players.clear()
            rps_players = get_rps_players()
            await interaction.edit_original_message(content="Reset successfully.")
        except Exception as e:
            print(f"Error resetting RPS game state: {e}")
            await interaction.edit_original_message(content="Error resetting game state.")


def setup(bot):
    bot.add_cog(RPSGame(bot))
