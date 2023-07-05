from config import database_cursor
from dataclasses import dataclass


@dataclass
class RPSPlayer:
    id: str
    user_id: int
    server_id: int
    username: str
    elo: int
    wins: int
    losses: int
    draws: int


def create_rps_table() -> None:
    database_cursor.execute(
        "CREATE TABLE IF NOT EXISTS RPS(user_id bigint, server_id bigint, username varchar(255), elo int, "
        "wins int, losses int, draws int, PRIMARY KEY (user_id, server_id)"
        ");"
    )
# "FOREIGN KEY(user_id) REFERENCES USERS(user_id), FOREIGN KEY(server_id) REFERENCES SERVERS(server_id));"


def get_rps_players() -> dict[str, RPSPlayer]:
    database_cursor.execute("SELECT * FROM RPS")
    rps_table = database_cursor.fetchall()
    return_dict = {}
    for user_id, server_id, username, elo, wins, draws, losses in rps_table:
        player = RPSPlayer(f"{user_id}.{server_id}", user_id, server_id, username, elo, wins, losses, draws)
        return_dict[player.id] = player
    return return_dict


def insert_new_player(player: RPSPlayer) -> None:
    database_cursor.execute(
        query="INSERT INTO RPS (user_id, server_id, username, elo, wins, losses, draws) "
              "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        vars=(player.user_id, player.server_id, player.username, player.elo, player.wins, player.losses, player.draws))


def update_player(player: RPSPlayer) -> None:
    database_cursor.execute(
        query="UPDATE RPS SET username = %s, elo = %s, wins = %s, losses = %s, draws = %s "
              "WHERE user_id = %s AND server_id = %s",
        vars=(player.username, player.elo, player.wins, player.losses, player.draws, player.user_id, player.server_id)
    )


create_rps_table()
