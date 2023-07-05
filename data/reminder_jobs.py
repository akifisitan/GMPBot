from config import database_cursor
from dataclasses import dataclass


@dataclass
class ReminderJob:
    id: int
    user_id: int
    channel_id: int
    timestamp: int
    message: str


def create_reminder_job_table() -> None:
    database_cursor.execute(
        "CREATE TABLE IF NOT EXISTS REMINDER_JOBS("
        "job_id SERIAL PRIMARY KEY, channel_id bigint, timestamp bigint, user_id bigint, message varchar(1000)"
        ");"
    )


def get_reminder_jobs() -> dict[int, ReminderJob]:
    database_cursor.execute("SELECT * FROM REMINDER_JOBS")
    reminder_jobs_table = database_cursor.fetchall()
    return_dict = {}
    for job_id, user_id, channel_id, timestamp, message in reminder_jobs_table:
        job = ReminderJob(id=job_id, timestamp=timestamp, user_id=user_id,
                          channel_id=channel_id, message=message)
        return_dict[job.id] = job
    return return_dict


def insert_new_reminder_job(job_tuple: tuple[int, int, int, str]) -> int:
    database_cursor.execute(
        query="INSERT INTO REMINDER_JOBS (user_id, channel_id, timestamp, message) "
              "VALUES (%s, %s, %s, %s) RETURNING job_id;",
        vars=job_tuple
    )
    return database_cursor.fetchone()[0]


def delete_reminder_job(job_id: int) -> None:
    database_cursor.execute(
        query="DELETE FROM REMINDER_JOBS WHERE job_id = %s;",
        vars=[job_id]
    )


create_reminder_job_table()
