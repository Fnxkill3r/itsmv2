import sys
from helper import *
from osalert import OsAlert
from psqlalert import PsqlAlert, get_databases
from podmanalert import PodmanAlert
from filesystemalert import FilesystemAlert
from sqlite import Sqlite
import psutil
import socket
import subprocess
import json

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


def set_filesystem_config(dic_array):
    template = get_dict_from_array(dic_array, "template")
    filesystems = []
    for dic in dic_array:
        if not has_key(dic, "template"):
            for current_fs in dic["filesystems"]:
                if has_key(dic, "use_template"):
                    thresholds, threshold_type = template["thresholds"], template["threshold_type"]
                else:
                    thresholds, threshold_type = dic["thresholds"], dic["threshold_type"]

                filesystems.append({"alert": template["alert"], "environment": template["environment"],
                                    "type": template["type"] + ":" + current_fs, "description": template["description"],
                                    "group": template["group"], "message": template["message"],
                                    "thresholds": thresholds, "threshold_type": threshold_type, "active": True})
    return filesystems


def set_pods_config(dic_array):
    result = subprocess.getoutput('podman ps -a --format json')
    my_dic = json.loads(result)
    specific_pod = []
    pods = []
    template = get_dict_from_array(dic_array, "template")
    for dic in dic_array:
        if not has_key(dic, "template"):
            for name in dic["names"]:
                specific_pod.append([name, dic["severity"]])
    for mpod in my_dic:
        position = 0
        exists = False
        for i in range(0, len(specific_pod)):
            if specific_pod[i][0] == mpod["Names"][0]:
                exists = True
                position = i

        severity = specific_pod[position][1] if exists else template["severity"]
        pods.append({"alert": template["alert"], "environment": template["environment"],
                     "type": template["type"] + ":" + mpod["Names"][0], "description": template["description"],
                     "group": template["group"], "message": template["message"],
                     "severity": severity, "active": True, "rstate": mpod["State"], "rstatus": mpod["Status"]})
    return pods


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


def run(port):


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
        for a in run_psql(port):
            all_alerts.append(a)

    for alert in all_alerts:
        print(alert)


if __name__ == '__main__':
    args = len(sys.argv) - 1
    if args == 0:
        print("No port set")
    else:
        if sys.argv[1].isdigit():
            port = sys.argv[1]
            # pgp = load_file("/home/postgres/.pgpass").split(":")[1]
            pgp = "localhost:50000:postgres:postgres:NzljOGRiYmNjZThiNWZhYjYxZDhlNzc1".split(":")[1]
            if port == pgp:
                print("Running")
                run(port)
            else:
                print("No pgpass found for setted port")


        else:
            print("First arg must be Port number")
        first_run()
#
#    for alert in run_pods():
#        print(alert)
