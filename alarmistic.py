import sys
import os
from helper import *
from osalert import run_os
from postgresalert import is_primary, run_psql
from podmanalert import run_pods
from filesystemalert import run_filesystem
from sqlite import Sqlite
from postgresql import *
import psutil
import socket
from loguru import logger


#logger.add("itsm.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", rotation="12:00")


class Alarmistic:
    def __init__(self, port):
        self.port = port
        self.hostname = socket.gethostname()
        self.conf_dir = str(os.getcwd()) + "/" + str(port) + "/confs/"
        self.db_dir = str(os.getcwd()) + "/" + str(port) + "/db/"
        self.logs_dir = str(os.getcwd()) + "/" + str(port) + "/logs/"
        self.config = False
        self.type = False
        self.sqlite_db = False
        self.active_modules = []
        self.is_blackout = False
        self.errors = []
        self.all_alerts = False

    def load_config(self):
        full_path = self.conf_dir + "config.json"
        config = load_json(read_file(full_path))
        if config:
            return config
        else:
            self.errors.append("FileNotFoundError")
            return False


    def setup(self):
        self.config = self.load_config()
        if self.config:
            self.type = self.config["type"]
            self.sqlite_db = self.config["sqlite_db"]
            self.active_modules = [key for key in self.config["active"] if self.config["active"][key]]
            self.is_blackout = self.config["blackout"]

            for module in self.active_modules:
                module_name = str(module) + "alert"
                module_conf = str(module) + "_alerts.json"
                if module_name not in sys.modules:
                    self.errors.append('You have not imported the {} module'.format(module_name))
                if not file_exists(self.conf_dir + module_conf):
                    self.errors.append('You have not created the {} configutsion file.'.format(module_conf))


            if not file_exists( self.db_dir + self.sqlite_db):
                self.first_run()
        else:
            return False

    def first_run(self):
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)
            #add_to_log
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
            # add_to_log

        sqlite_db_path = self.db_dir + self.sqlite_db
        boot_time = int(psutil.boot_time())
        sqlite_conn = Sqlite(sqlite_db_path)
        sqlite_conn.run_query("CREATE TABLE host ( 'name'	TEXT,  'uptime' INTEGER);")
        query_host = "INSERT INTO host (name, uptime) VALUES ('{}','{}')".format(self.hostname, boot_time)
        sqlite_conn.write(query_host)


    def get_alerts(self):
        all_alerts = []

        for a in run_os(self.conf_dir + "os_alerts.json", self.db_dir + self.sqlite_db):
            all_alerts.append(a)
        for a in run_filesystem(self.conf_dir + "filesystem_alerts.json"):
            all_alerts.append(a)
        for a in run_pods(self.conf_dir + "podman_alerts.json"):
            all_alerts.append(a)

        if  is_primary(port):
            #Postgres alerts run only on primary servers
            for a in run_psql(port, self.conf_dir + "postgres_alerts.json", self.type, self.db_dir + self.sqlite_db):
                all_alerts.append(a)
        return all_alerts

    def run(self):
        self.setup()
        print(self.errors)
        if not len(self.errors):
            print(self.active_modules)
            self.all_alerts = self.get_alerts()
            for alert in self.all_alerts:
                print(alert)




if __name__ == '__main__':
    args = len(sys.argv) - 1
    if args == 0:
        print("No port set")
    else:
        if sys.argv[1].isdigit():
            port = sys.argv[1]
            check_pgpass = load_conn_values(port)
            if not check_pgpass:
                print("No pgpass line for localhost and setted port")
            else:
                run = Alarmistic(port)
                run.run()
        else:
            print("First arg must be Port number")
