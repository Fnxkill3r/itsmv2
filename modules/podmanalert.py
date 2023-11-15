import subprocess
import json
from modules.alert import *
from modules.helpers.helper import *


def run_pods(json_path):
    podman_config_dic_array = set_pods_config(load_json(read_file(json_path)))
    current_pod_alerts = []
    for cnf in podman_config_dic_array:
        current_pod_alerts.append(PodmanAlert(cnf))
    return current_pod_alerts


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


class PodmanAlert(Alert):
    def __init__(self, config):
        super().__init__(config)
        self.run()

    def set_message(self, values):
        message = self.get_message()
        return find_and_replace_multi(message, ["var_value", "var_value"], values)

    def run(self):
        self.name = self.config["alert"]
        self.state = "OK" if self.config["rstate"] == 'running' else "NOK"
        self.severity = self.get_severity(self.state)
        self.message = self.set_message([self.config["rstate"], self.config["rstatus"]])
