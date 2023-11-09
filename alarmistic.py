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

logger.add("itsm.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}", rotation="12:00")


class Alarmistic:
    def __init__(self, port):
        self.port = port
        self.hostname = socket.gethostname()
        self.conf_dir = str(os.getcwd()) + "/" + str(port) + "/confs"
        self.db_dir = str(os.getcwd()) + "/" + str(port) + "/db"
        self.logs_dir = str(os.getcwd()) + "/" + str(port) + "/logs"
        self.config = False
        self.type = False
        self.sqlite_db = False
        self.active_modules = []
        self.is_blackout = False
        self.errors = []

    def load_config(self):
        config = json_to_dic("/config.json", self.conf_dir)
        if config == "FileNotFoundError":
            self.errors.append("FileNotFoundError")
            return False
        else:
            return config

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
                if not file_exists(module_conf, self.conf_dir):
                    self.errors.append('You have not created the {} module'.format(module_conf))


            if not file_exists(self.sqlite_db, self.db_dir):
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

        sqlite_db_full_path = self.db_dir + "/" + self.sqlite_db
        boot_time = int(psutil.boot_time())
        sqlite_conn = Sqlite(sqlite_db_full_path)
        sqlite_conn.run_query("CREATE TABLE host ( 'name'	TEXT,  'uptime' INTEGER);")
        query_host = "INSERT INTO host (name, uptime) VALUES ('{}','{}')".format(self.hostname, boot_time)
        sqlite_conn.write(query_host)


    def get_alerts(self):
        all_alerts = []


        for a in run_os(file_exists("os_alerts.json",self.conf_dir), self.sqlite_db):
            all_alerts.append(a)
        if file_exists("filesystemalert.py") and file_exists("filesystem_alerts.json", self.conf_dir):
            for a in run_filesystem():
                all_alerts.append(a)
        if file_exists("podmanalert.py") and file_exists("podman_alerts.json", self.conf_dir):
            for a in run_pods():
                all_alerts.append(a)

        if file_exists("postgresalert.py") and file_exists("postgres_alerts.json", self.conf_dir) and is_primary(port):
            for a in run_psql(port, self.type, self.sqlite_db):
                all_alerts.append(a)

    def run(self):
        self.setup()
        print(self.errors)
        if not len(self.errors):
            print(self.active_modules)
            self.get_alerts()




if __name__ == '__main__':
    args = len(sys.argv) - 1
    if args == 0:
        print("No port set")
    else:
        if sys.argv[1].isdigit():
            port = sys.argv[1]
            check_pgpass = load_conn_values(port)
            if check_pgpass == "":
                print("No pgpass line for localhost and setted port")
            else:
                run = Alarmistic(port)
                run.run()
        else:
            print("First arg must be Port number")
