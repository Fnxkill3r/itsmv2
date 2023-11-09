import sys
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


def run(port):
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

    if file_exists("postgresalert.py") and file_exists("postgres_alerts.json") and is_primary(port):
        for a in run_psql(port, alarmistic_type, sqlite_db):
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
            check_pgpass = load_conn_values(port)
            if check_pgpass == "":
                print("No pgpass line for localhost and setted port")
            else:
                run(port)
        else:
            print("First arg must be Port number")
