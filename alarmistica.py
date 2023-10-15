from helper import *
from os_alert import Os_Alert
import sqlite


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


os_config_dic_array = json_to_dic("os_alerts.json")
#psql_config_dic_array = json_to_dic("psql_alerts.json")
#filesystem_config_dic_array = set_filesystem_config(json_to_dic("filesystem_alerts.json"))
#send only active and env_type = cenas
#print(psql_config_dic_array[0])

current_os_alerts = []
for cnf in os_config_dic_array:
    print(Os_Alert(cnf, "itsm.db").run())