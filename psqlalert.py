from alert import *
from postgresql import *
from sqlite import Sqlite
import socket
import psutil
import subprocess


def get_databases(port):
    conn = Psql(port)
    psql_databases = conn.run_query("select datname from pg_catalog.pg_database where datname not in ('dba')")
    databases = []
    for db in psql_databases:
        databases.append(db[0])
    return databases


def get_data_dir(port):
    conn = Psql(port)
    return conn.run_query("select setting from pg_catalog.pg_settings where name='data_directory'")[0][0]


def is_primary(port):
    conn = Psql(port)
    return True if not conn.run_query("select pg_is_in_recovery()")[0][0] else False


def run_psql(port, alarmistic_type, sqlite_db):
    psql_config_dic_array = json_to_dic("psql_alerts.json")
    current_psql_alerts = []
    psql_databases = get_databases(port)

    for cnf in psql_config_dic_array:
        if alarmistic_type.lower() == "single" and cnf["environment"].lower() != "all":
            cnf["active"] = False
        if alarmistic_type.lower() == "replica":
            pass

        if cnf["active"]:
            if cnf["group"] != "per_database" and cnf["group"] != "per_table":
                current_psql_alerts.append(PsqlAlert(cnf, sqlite_db, port))
            else:
                conf = cnf["type"]
                query = cnf["query"]
                for db in psql_databases:
                    cnf.update({"type": conf + ":" + db})
                    cnf.update({"query": query.replace("var_database_name", db, 1)})
                    current_psql_alerts.append(PsqlAlert(cnf, sqlite_db, port))
    return current_psql_alerts


class PsqlAlert(Alert):
    def __init__(self, config, db_name, port):
        super().__init__(config)
        self.port = port
        self.db_name = db_name
        self.conn = Psql(port)
        self.datadir = ""
        self.databases = get_databases(port)
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
            total = 1 if table[0] == "psql" else 0
        if total < 1:
            host_db.run_query("CREATE TABLE psql ( 'port'	TEXT,  'uptime' TEXT);")
            uptime_query = "INSERT INTO psql (port, uptime) VALUES ('{}','{}')".format(self.port, psql_boot_time_epoch)
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
        self.message = self.set_message([socket.gethostname()])
        query_host = "delete from host;"
        host_db.write(query_host)
        query_host = "INSERT INTO host (name, uptime) VALUES ('{}','{}')".format(socket.gethostname(),
                                                                                 psutil.boot_time())
        host_db.write(query_host)

    def replica_status(self):
        value = self.run_generic_query()
        self.state = "OK" if value >= 1 else "NOK"
        self.severity = self.get_severity(self.state)
        self.message = self.set_message([value])

    def replica_lsn_delay(self):
        value = self.run_generic_query()
        self.state = self.get_expected(value)
        self.severity = self.get_severity(self.state)
        self.message = self.set_message([value]) if self.state == "NOK" else self.config["message"]["OK"]

    def replica_process_running(self):
        value = self.run_generic_query()
        self.state = "OK" if value >= 1 else "NOK"
        self.severity = self.get_severity(self.state)
        self.message = self.config["message"][self.state]

    def certificate_expiration_time(self):
        data_dir = get_data_dir(self.port)
        path = data_dir + "/" + self.config["file"]
        full_string = "openssl x509 -enddate -noout -in" + path
        result = subprocess.getoutput(full_string)
        print(result)

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
                self.replica_status()
            elif self.config["alert"] == "replica_lsn_delay":
                self.replica_lsn_delay()
            elif self.config["alert"] == "replica_process_running":
                self.replica_process_running()
            elif has_key(self.config, "file"):
                self.state = "OK" if file_exists(get_data_dir(self.port), self.config["file"]) == self.config[
                    "file_existence"] else "NOK"
                self.severity = self.get_severity(self.state)
                self.message = self.config["message"][self.state]
            self.run_timestamp = self.get_run_timestamp()
        else:
            if self.config["group"] == "per_database":
                value = self.run_per_database_query()
                self.severity = self.get_severity(value)
                self.state = self.get_state()
                self.message = self.set_message(
                    [self.config["type"].split(":")[1], value, self.config["threshold_type"]])
                self.run_timestamp = self.get_run_timestamp()

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
