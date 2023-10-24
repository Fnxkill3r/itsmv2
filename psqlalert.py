from alert import *
from postgresql import *
from sqlite import Sqlite
import socket
import psutil


def get_databases():
    conn = Psql()
    psql_databases = conn.run_query("select datname from pg_catalog.pg_database where datname not in ('dba')")
    databases = []
    for db in psql_databases:
        databases.append(db[0])
    return databases


def get_data_dir():
    conn = Psql()
    return conn.run_query("select setting from pg_catalog.pg_settings where name='data_directory'")[0][0]


class PsqlAlert(Alert):
    def __init__(self, config, db_name):
        super().__init__(config)
        self.db_name = db_name
        self.conn = Psql()
        self.datadir = ""
        self.databases = get_databases()
        self.run()

        # self.run()

    def run_generic_query(self):
        return self.conn.run_query(self.config["query"])[0][0]

    def run_per_database_query(self):
        database = self.type.split(":")[1]
        self.conn.override_database(database)
        return self.conn.run_query(self.config["query"])[0][0]

    def get_expected(self, value):
        expected = self.config["expected"]
        if str(expected).isalpha():
            return "OK" if value.upper() == expected.upper() else "NOK"
        elif str(expected).isdigit():
            return "OK" if value == int(expected) else "NOK"
        else:
            return "OK" if value == expected else "NOK"

    def set_message(self, value):
        message = self.get_message()
        if len(value) == 1:
            return find_and_replace_multi(message, ["var_value"], value)
        elif len(value) == 2:
            if message.count("var_threshold_value"):
                return find_and_replace_multi(message, ["var_threshold_value", "var_threshold_type"], value)
            else:
                return find_and_replace_multi(message, ["var_database_name", "var_value"], value)
        else:
            return find_and_replace_multi(message, ["var_database_name", "var_threshold_value", "var_threshold_type"],
                                          value)

    #################### Specific functions ########################
    def postgres_uptime(self):
        psql_boot_time_full = self.conn.run_query(self.config["query"])
        psql_boot_time_epoch = int(psql_boot_time_full[0][0].strftime('%s'))
        time = epoch_to_human(psql_boot_time_epoch)

        # print(psql_boot_time_epoch)
        host_db = Sqlite(self.db_name)
        tables_query = "SELECT name FROM sqlite_master WHERE type ='table' AND name NOT LIKE 'sqlite_%';"
        tables = host_db.run_query(tables_query)
        total = 0
        for table in tables:
            if table[0] == "psql":
                total = 1

        if total < 1:
            host_db.run_query("CREATE TABLE psql ( 'port'	TEXT,  'uptime' TEXT);")
            uptime_query = "INSERT INTO psql (port, uptime) VALUES ('{}','{}')".format("50000", psql_boot_time_epoch)
            host_db.write(uptime_query)
            self.state = "OK"
            self.severity = "NORMAL"
            self.message = "First run: No database value yet. Uptime: " + time

        else:
            query = "SELECT uptime FROM psql ORDER BY uptime LIMIT 1"
            saved_uptime = host_db.run_query(query)[0][0]
            saved_uptime = int(float(saved_uptime))
            time = epoch_to_human(saved_uptime)
            self.state = "OK" if saved_uptime >= psql_boot_time_epoch else "NOK"
            self.severity = self.get_severity(self.state)
            self.message = self.set_message([time])

            # host_db.write("psql", "psql_uptime", psql_boot_time_epoch)

    def check_primary_server_name(self):
        host_db = Sqlite(self.db_name)
        query = "SELECT name FROM host ORDER BY uptime LIMIT 1"
        name = host_db.run_query(query)[0][0]
        self.state = "OK" if name == socket.gethostname() else "NOK"
        self.severity = self.get_severity(self.state)
        self.message = self.set_message([name])
        query_host = "delete from host;"
        host_db.write(query_host)
        query_host = "INSERT INTO host (name, uptime) VALUES ('{}','{}')".format(socket.gethostname(), psutil.boot_time())
        host_db.write(query_host)





    def run(self):
        # method_list = [method for method in dir(self.__class__) if method.startswith('__') is False]
        if self.get_category() == "ok_nok":
            if has_key(self.config, "expected") and self.config["group"] == "psql":
                value = self.run_generic_query()
                self.state = self.get_expected(value)
                self.severity = self.get_severity(self.state)
                self.message = self.set_message([value])
            elif self.config["group"] == "per_table":
                value = self.run_per_database_query()
                self.state = self.get_expected(value)
                self.severity = self.get_severity(self.state)
                self.message = self.set_message([self.config["type"].split(":")[1], value])
            elif self.config["alert"] == "postgres_uptime":
                self.postgres_uptime()
            elif self.config["alert"] == "check_primary_server_name":
                self.check_primary_server_name()
            elif self.config["alert"] == "replica_status":
                value = self.run_generic_query()
                self.state = "OK" if value >= 1 else "NOK"
                self.severity = self.get_severity(self.state)
                self.message = self.set_message([value])
            elif has_key(self.config, "file"):
                self.state = "OK" if file_exists(get_data_dir(), self.config["file"]) == self.config["file_existence"] else "NOK"
                self.severity = self.get_severity(self.state)
                self.message = self.config["message"][self.state]

        else:
            if self.config["group"] == "per_database":
                value = self.run_per_database_query()
                self.severity = self.get_severity(value)
                self.state = self.get_state()
                self.message = self.set_message(
                    [self.config["type"].split(":")[1], value, self.config["threshold_type"]])

            # TO DO
            # if self.config["group"] == "ssl":
            #    pass
            # elif has_key(self.config, "expected") and self.config["group"] != "per_table":
            #    value = self.run_per_database_query()

            # if self.config["group"] != "per_database" and self.config["group"] != "per_table":
            #    value = self.run_generic_query()
            #    self.message = self.set_message(value)
            # else:
            #    value = self.run_per_database_query()
            #    self.message = self.set_message(self.value)
