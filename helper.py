import os
import json


def file_exists(file):
    file_path = os.getcwd() + "/" + file
    return os.path.isfile(file_path)


def load_file(file):
    if file_exists(file):
        file_path = os.getcwd() + "/" + file
        try:
            f = open(file_path, "r")
            f_content = f.read()
        except FileNotFoundError as e:
            print("Something went wrong when opening the file")
            print(e)
        finally:
            return f_content
    else:
        return "FileNotFoundError"


def json_to_dic(file):
    my_file = load_file(file)
    if my_file != "FileNotFoundError":
        my_dic = json.loads(my_file)
        return my_dic
    else:
        return my_file


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
