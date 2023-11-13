import psycopg2
from helper import file_exists, load_file_to_list


def load_conn_values(port):
    pgpass_list = load_file_to_list("/home/postgres/.pgpass")
    pgpass = False
    for line in pgpass_list:
        if port in line and line.split(":")[0] == "localhost":
            pgpass = line.strip()
    return pgpass





class Psql:
    def __init__(self, port):
        self.pgpass = load_conn_values(port)
        self.host, self.port, self.database, self.user, self.password = self.pgpass.split(":")
        self.conn = psycopg2.connect(
            host=self.host,
            database=self.database,
            port=port,
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
