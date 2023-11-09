import os
import json
import re
import socket
from datetime import datetime


def dir_exists(path):
    return os.path.isdir(path)


def file_exists(file, my_path=os.getcwd()):
    file_path = my_path + file if my_path[-1] == "/" else my_path + "/" + file
    return os.path.isfile(file_path)


def load_file(file, my_path=os.getcwd()):
    if file_exists(file, my_path):
        file_path = my_path + file if my_path[-1] == "/" else my_path + "/" + file
        with open(file_path, "r") as f:
            f_content = f.read()
            return f_content
    else:
        return "FileNotFoundError"


def load_file_to_list(file, my_path=os.getcwd()):
    if file_exists(file, my_path):
        file_path = my_path + file if my_path[-1] == "/" else my_path + "/" + file
        with open(file_path) as fp:
            lines = fp.readlines()
        return lines
    else:
        return "FileNotFoundError"


def json_to_dic(full_path):
    my_file = load_file(file, my_path)
    if my_file != "FileNotFoundError":
        my_dic = json.loads(full_path)
        return my_dic
    else:
        return my_file


def load_json(full_path):
    return json.loads(full_path)


def has_key(dic, key):
    if key in dic.keys():
        return True
    else:
        return False


def get_dict_from_array(dic_array, dic_key):
    for dic in dic_array:
        if has_key(dic, dic_key):
            return dic
        else:
            pass


def ordered_dic(dic):
    # Creates a sorted dictionary (sorted by key)
    my_keys = list(dic.keys())
    my_keys.sort()
    sorted_dict = {i: dic[i] for i in my_keys}
    return sorted_dict


def find_position(string, pattern):
    positions = [patt.start() for patt in re.finditer(pattern, string)]
    return positions


def find_and_replace(string, pattern, new_val):
    # new_val must be array
    pos = find_position(string, pattern)
    pos_count = len(pos)
    if pos_count != len(new_val):
        return "Number of fields do not match"
    for count in range(0, pos_count):
        str_pos = string.lower().find(pattern.lower())
        string = string[0: str_pos] + str(new_val[count]) + string[(str_pos + len(pattern)):len(string)]
    return string


def find_and_replace_multi(string, patterns, vals):
    # patterns and new_val must be array
    for val in range(0, len(patterns)):
        string = string.replace(patterns[val], str(vals[val]), 1)
    return string


def epoch_to_human(time):
    datetime_uptime = datetime.fromtimestamp(time)
    date_human_read = datetime_uptime.strftime("%Y-%m-%d %H:%M:%S")
    return date_human_read


def get_hostname():
    return socket.gethostname().split(".")[0]


def get_site():
    site = get_hostname()[0:2]
    if site.lower() != "vs" and site.lower() != "lx":
        site = "na"
    return site


def get_environment():
    env_dic = {
        "d": "DES",
        "q": "QLY",
        "i": "TSI",
        "t": "TST",
        "c": "CER",
        "p": "PRD"

    }
    env = get_hostname().strip('1234567890')[-1]
    return env_dic[env] if has_key(env_dic, env) else "na"
