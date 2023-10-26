import subprocess
import json
from helper import *

result = subprocess.getoutput('podman ps -a --format json')
my_dic = json.loads(result)
# print(my_dic)


podman_config_dic_array = json_to_dic("podman_alerts.json")


def get_pods(dic_array):
    specific_pod = []
    pods = []
    template = get_dict_from_array(dic_array, "template")
    for dic in dic_array:
        if not has_key(dic, "template"):
            for name in dic["names"]:
                specific_pod.append([name, dic["severity"]])

    for pod in my_dic:
        position = 0
        exists = False
        for i in range(0, len(specific_pod)):
            print(specific_pod[i])
            print(specific_pod[i][0], pod["Names"][0], i)
            if specific_pod[i][0] == pod["Names"][0]:
                print("OK")
                exists = True
                position = i

        severity = specific_pod[i][1] if exists else template["severity"]


        pods.append({"alert": template["alert"], "environment": template["environment"],
                    "type": template["type"] + ":" + pod["Names"][0], "description": template["description"],
                    "group": template["group"], "message": template["message"],
                    "severity": severity, "active": True})
    return pods



all_pods = get_pods(podman_config_dic_array)
for pod in all_pods:
    print(pod)
