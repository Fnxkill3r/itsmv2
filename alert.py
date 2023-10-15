from helper import *

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
        return f"{self.name}({self.type})"

    def get_category(self):
        return "threshold" if has_key(self.config, "thresholds") else "ok_nok"

    def get_state(self):
        return "OK" if self.severity == "NORMAL" else "NOK"

    def get_severity(self):
        if self.get_category() == "ok_nok":
            return "NORMAL" if self.values[0].lower() == "OK".lower() else self.config["severity"]
        else:
            return self.get_threshold()

    def get_threshold(self, alert_value):
        dic = ordered_dic(self.config["thresholds"])
        if dic['WARNING'] > dic['CRITICAL']:
            if alert_value > dic['WARNING']:
                return "NORMAL"
            else:
                for threshold_key, threshold_value in dic.items():
                    if alert_value <= threshold_value:
                        return threshold_key
        else:
            if alert_value < dic['WARNING']:
                return "NORMAL"
            else:
                for threshold_key, threshold_value in dic.items():
                    if alert_value >= threshold_value:
                        return threshold_key

