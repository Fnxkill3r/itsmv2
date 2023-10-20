import psqlalert
from helper import *
from osalert import OsAlert
from psqlalert import PsqlAlert
from filesystemalert import FilesystemAlert
from sqlite import Sqlite
import psutil
import os

sqlite_db = "itsm.db"


def first_run():
    if not file_exists(sqlite_db):
        hostname = os.name
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
                                    "thresholds": thresholds, "active": True})
    return filesystems


first_run()

os_config_dic_array = json_to_dic("os_alerts.json")
psql_config_dic_array = json_to_dic("psql_alerts.json")
filesystem_config_dic_array = set_filesystem_config(json_to_dic("filesystem_alerts.json"))

# TO DO
# send only active and env_type = cenas and active = true
# print(psql_config_dic_array[0])

# Set Up parte

current_os_alerts = []
for cnf in os_config_dic_array:
    current_os_alerts.append(OsAlert(cnf, "itsm.db"))

#PSQL
current_psql_alerts = []
psql_databases = psqlalert.get_databases()

for cnf in psql_config_dic_array:
    if cnf["group"] != "per_database" and cnf["group"] != "per_table":
        current_psql_alerts.append(PsqlAlert(cnf, "itsm.db"))
    else:
        conf = cnf["type"]
        query = cnf["query"]
        for db in psql_databases:
            cnf.update({"type": conf + ":" + db})
            cnf.update({"query": query.replace("var_database_name", db, 1)})
            current_psql_alerts.append(PsqlAlert(cnf, "itsm.db"))

#Filesystems
current_filesystem_alerts = []
for cnf in filesystem_config_dic_array:
    current_filesystem_alerts.append(FilesystemAlert(cnf))

# The print part

for alert in current_os_alerts:
    print(alert)

for alert in current_psql_alerts:
    print(alert)

for alert in current_filesystem_alerts:
    print(alert)
