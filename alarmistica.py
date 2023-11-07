import sys
from helper import *
from osalert import run_os
from psqlalert import is_primary, run_psql
from podmanalert import run_pods
from filesystemalert import run_filesystem
from sqlite import Sqlite
from postgresql import *
import psutil
import socket

sqlite_db = "itsm.db"
setup = json_to_dic("config.json")
alarmistic_type = setup["type"]


def first_run():
    if not file_exists(sqlite_db):
        hostname = socket.gethostname()
        boot_time = int(psutil.boot_time())
        host_db = Sqlite(sqlite_db)
        host_db.run_query("CREATE TABLE host ( 'name'	TEXT,  'uptime' INTEGER);")
        query_host = "INSERT INTO host (name, uptime) VALUES ('{}','{}')".format(hostname, boot_time)
        host_db.write(query_host)


def run(psql_port):
    first_run()
    all_alerts = []

    if file_exists("osalert.py") and file_exists("os_alerts.json"):
        for a in run_os(sqlite_db):
            all_alerts.append(a)
    if file_exists("filesystemalert.py") and file_exists("filesystem_alerts.json"):
        for a in run_filesystem():
            all_alerts.append(a)
    if file_exists("podmanalert.py") and file_exists("podman_alerts.json"):
        for a in run_pods():
            all_alerts.append(a)

    if file_exists("psqlalert.py") and file_exists("psql_alerts.json") and is_primary(psql_port):
        for a in run_psql(psql_port, alarmistic_type, sqlite_db):
            all_alerts.append(a)

    for alert in all_alerts:
        full_csv = "SERVIDOR: " + get_hostname() + "; SITE:" + get_site() + "; AMBIENTE:" + get_environment() + ";" + alert.return_csv()
        print(full_csv)


if __name__ == '__main__':
    args = len(sys.argv) - 1
    if args == 0:
        print("No port set")
    else:
        if sys.argv[1].isdigit():
            port = sys.argv[1]
            pgp = load_file(".pgpass", "/home/postgres").split(":")[1]

            if port == pgp:
                run(port)
            else:
                print("No pgpass found for setted port")
        else:
            print("First arg must be Port number")
