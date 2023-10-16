from helper import *
from _datetime import datetime

'''{
    'alert': 'postgres_uptime',
    'type': 'psqlUptime',
    'description': 'Check if postgres uptime restarted'
    ,'query': 'SELECT pg_postmaster_start_time();',
    'group': 'psql',
    'message':
      {'OK': 'Psql uptime is greater than last check. Uptime varValue',
        'NOK': 'Psql has been restarted since last check. Uptime varValue'
      },
    'severity': 'WARNING',
    'active': True
    }
'''


class Alert:

    def __init__(self, config):
        # <config> is a dic with specific alert config
        self.config = config
        self.name = config["alert"]
        self.type = config["type"]
        self.description = config["description"]
        self.category = ""
        self.severity = ""
        self.state = ""
        self.message = ""
        self.run_timestamp = ""

    def __str__(self):
        return f"{self.name}({self.type}, {self.state}, {self.severity}, {self.message} )"

    def get_category(self):
        return "threshold" if has_key(self.config, "thresholds") else "ok_nok"

    def get_state(self):
        return "OK" if self.severity == "NORMAL" else "NOK"

    def get_severity(self, value):
        if self.get_category() == "ok_nok":
            return "NORMAL" if value.upper() == "OK" else self.config["severity"]
        else:
            return self.get_threshold(value)

    def get_threshold(self, value):
        dic = ordered_dic(self.config["thresholds"])
        if dic['WARNING'] > dic['CRITICAL']:
            if value > dic['WARNING']:
                return "NORMAL"
            else:
                for threshold_key, threshold_value in dic.items():
                    if value <= threshold_value:
                        return threshold_key
        else:
            if value < dic['WARNING']:
                return "NORMAL"
            else:
                for threshold_key, threshold_value in dic.items():
                    if value >= threshold_value:
                        return threshold_key

    def get_message(self):
        return self.config["message"][self.state] if self.get_category() == "ok_nok" else self.config["message"]

    def set_message(self, values):
        message = self.get_message()
        if self.get_category() == "ok_nok":
            return find_and_replace_multi(message, ["var_value"], [values[1]])
        else:
            return find_and_replace_multi(message, ["var_threshold_value", "var_threshold_type"],
                                          [values[0], self.config["threshold_type"]])

    def get_run_timestamp(self):
        dt = datetime.now()
        return datetime.timestamp(dt)
