from alert import *
from postgresql import *


class Psql_Alert(Alert):
    def __init__(self, config, db_name):
        super().__init__(config)
        self.db_name = db_name
        self.conn = Psql()
        self.datadir = ""
        self.databases = self.get_databases()

        # self.run()

    def get_databases(self):
        psql_databases = self.conn.run_query("select datname from pg_catalog.pg_database where datname not in ('dba')")
        databases = []
        for db in psql_databases:
            databases.append(db[0])
        return databases

    def get_sub_category(self):
        if has_key(self.config["expected"]):
            return "expected"

    def generic_expected(self):
        return self.conn.run_query(self.config["query"][0][0])

    def get_expected(self, value):
        expected = self.config["expected"]
        if str(expected).isalpha():
            return "OK" if value.upper() == expected.upper() else "NOK"
        elif str(expected).isdigit():
            return "OK" if value == int(expected) else "NOK"
        else:
            return "OK" if value == expected else "NOK"

    def run(self):
        name = self.name
        #method_list = [method for method in dir(self.__class__) if method.startswith('__') is False]
        if self.get_category() == "ok_nok":
            if self.get_sub_category() == "expected":
                print(self.get_expected(generic_expected()))

