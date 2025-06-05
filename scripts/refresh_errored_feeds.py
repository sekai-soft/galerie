import os
import sys
import miniflux
import psycopg2
from dotenv import load_dotenv


load_dotenv()


def refresh_errored_feeds(miniflux_username: str, miniflux_password: str):
    client = miniflux.Client(
        username=miniflux_username,
        password=miniflux_password,
        base_url=os.getenv("MINIFLUX_BASE_URL"),
        timeout=5,
    )
    total_count = 0
    success_count = 0
    for feed in client.get_feeds():
        if feed["parsing_error_count"] == 0:
            continue
        print(f"Refreshing errored feed, id={feed['id']}, title={feed['title']}")
        try:
            client.refresh_feed(feed["id"])
            print(f"Successfully refreshed feed, id={feed['id']}, title={feed['title']}")
            success_count += 1
        except Exception as e:
            print(f"Failed to refresh feed, id={feed['id']}, title={feed['title']}")
            print(e)
        total_count += 1
    print(f"Refreshed {success_count}/{total_count} errored feeds.")


def main(username: str):
    conn = None
    try:
        conn = psycopg2.connect(os.getenv("SQLALCHEMY_DATABASE_URI"))
        cur = conn.cursor()
        cur.execute("SELECT miniflux_password FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        if result:
            refresh_errored_feeds(username, result[0])
        else:
            return f"No user found with username: {username}"
    except Exception as e:
        return f"Database error: {str(e)}"
    finally:
        if conn:
            cur.close()
            conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python refresh_errored_feeds.py <username>")
        sys.exit(1)
    username = sys.argv[1]
    main(username)
