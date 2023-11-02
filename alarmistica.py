import sys
from helper import *
from osalert import OsAlert
from psqlalert import PsqlAlert, get_databases
from podmanalert import PodmanAlert, set_pods_config
from filesystemalert import FilesystemAlert, set_filesystem_config
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


def run_os():
    os_config_dic_array = json_to_dic("os_alerts.json")
    current_os_alerts = []
    for cnf in os_config_dic_array:
        if cnf["active"]:
            current_os_alerts.append(OsAlert(cnf, "itsm.db"))
    return current_os_alerts


def run_psql(port):
    psql_config_dic_array = json_to_dic("psql_alerts.json")
    current_psql_alerts = []
    psql_databases = get_databases(port)

    for cnf in psql_config_dic_array:
        if alarmistic_type.lower() == "single" and cnf["environment"].lower() != "all":
            cnf["active"] = False

        if cnf["active"]:
            if cnf["group"] != "per_database" and cnf["group"] != "per_table":
                current_psql_alerts.append(PsqlAlert(cnf, "itsm.db", port))
            else:
                conf = cnf["type"]
                query = cnf["query"]
                for db in psql_databases:
                    cnf.update({"type": conf + ":" + db})
                    cnf.update({"query": query.replace("var_database_name", db, 1)})
                    current_psql_alerts.append(PsqlAlert(cnf, "itsm.db", port))
    return current_psql_alerts


def run_filesystem():
    filesystem_config_dic_array = set_filesystem_config(json_to_dic("filesystem_alerts.json"))
    current_filesystem_alerts = []
    for cnf in filesystem_config_dic_array:
        current_filesystem_alerts.append(FilesystemAlert(cnf))
    return current_filesystem_alerts


def run_pods():
    podman_config_dic_array = set_pods_config(json_to_dic("podman_alerts.json"))
    current_pod_alerts = []
    for cnf in podman_config_dic_array:
        current_pod_alerts.append(PodmanAlert(cnf))
    return current_pod_alerts


def run(psqlport):
    first_run()
    all_alerts = []

    if file_exists("osalert.py") and file_exists("os_alerts.json"):
        for a in run_os():
            all_alerts.append(a)
    if file_exists("filesystemalert.py") and file_exists("filesystem_alerts.json"):
        for a in run_filesystem():
            all_alerts.append(a)
    if file_exists("podmanalert.py") and file_exists("podman_alerts.json"):
        for a in run_pods():
            all_alerts.append(a)

    if file_exists("psqlalert.py") and file_exists("psql_alerts.json"):
        for a in run_psql(psqlport):
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
                psq = Psql(port)
                is_standby = psq.run_query("select pg_is_in_recovery()")[0][0]
                if not is_standby:
                    run(port)
            else:
                print("No pgpass found for setted port")
        else:
            print("First arg must be Port number")


