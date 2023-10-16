import psycopg2
from helper import file_exists, load_file


def load_conn_values():
    # pgpass = load_file( / home / postgres /.pgpass)
    # for testes
    pgpass = "192.168.56.170:50000:postgres:postgres:NjRkZDkwMThkZjY0MzdjNTRjYmZiYmYz"
    ##
    return pgpass.split(":")


class Psql:
    def __init__(self):
        self.host, self.port, self.database, self.user, self.password = load_conn_values()
        self.conn = psycopg2.connect(
            host=self.host,
            database=self.database,
            port=self.port,
            user=self.user,
            password=self.password
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def override_database(self, database_name):
        self.close()
        self.database = database_name
        self.conn = psycopg2.connect(
            host=self.host,
            database=self.database,
            port=self.port,
            user=self.user,
            password=self.password
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()

    def run_query(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.conn.close()
