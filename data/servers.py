from config import database_cursor


def create_servers_table():
    database_cursor.execute(
        "CREATE TABLE IF NOT EXISTS SERVERS(server_id bigint PRIMARY KEY, server_name varchar(255));"
    )


def get_servers() -> dict[int, str]:
    database_cursor.execute("SELECT * FROM Servers")
    servers_table = database_cursor.fetchall()
    return_dict = {}
    for server_id, server_name in servers_table:
        return_dict[server_id] = server_name
    return return_dict


def insert_new_server(server_id: int, server_name: str):
    database_cursor.execute(
        query="INSERT INTO Servers (server_id, server_name) VALUES (%s, %s)",
        vars=(server_id, server_name)
    )


def delete_server_from_database(server_id: int):
    database_cursor.execute(
        query="DELETE FROM Servers WHERE server_id = %s",
        vars=[server_id]
    )


create_servers_table()
SERVER_IDS = list(get_servers().keys())
# If there are no servers in the database, add the server IDs of the servers you want to use the bot in
# SERVER_IDS.extend([])
