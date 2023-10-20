from alert import *
from sqlite import Sqlite
from datetime import datetime
from helper import *
import psutil


class OsAlert(Alert):
    def __init__(self, config, db_name):
        super().__init__(config)
        self.db_name = db_name
        self.run()

    def system_uptime(self):
        host_db = Sqlite(self.db_name)

        query = "SELECT uptime FROM host"
        saved_uptime = host_db.run_query(query)[0][0]
        saved_uptime = int(float(saved_uptime))
        boot_time = int(psutil.boot_time())

        # datetime_saved_uptime = datetime.fromtimestamp(saved_uptime)
        datetime_uptime = datetime.fromtimestamp(boot_time)
        date_human_read = datetime_uptime.strftime("%Y-%m-%d %H:%M:%S")
        state = "OK" if boot_time <= saved_uptime else "NOK"
        # return get_values(dic, datetime_uptime, state)
        return [state, date_human_read]

    def memory_usage(self):
        # Gets free virtual memory being used
        virtual_memory = psutil.virtual_memory()
        total_memory = virtual_memory.total
        used_memory = virtual_memory.used

        if self.config["threshold_type"] == "%":
            return [float(100 - (used_memory * 100) / total_memory)]
        else:
            return [round((total_memory - used_memory) / (2 ** 20), 2)] \
                if self.config["threshold_type"].upper() == "MB" else [round((total_memory - used_memory) / (2 ** 30), 2)]

    def cpu_avg_load(self):
        # Return OK id avg_usage < cpu_count/3 (last 5 min)
        load1, load5, load15 = psutil.getloadavg()
        cpu_count = os.cpu_count()
        state = "OK" if load5 < (cpu_count / 3) else "NOK"
        return [state, load5]

    def run(self):
        name = self.name
        #method_list = [method for method in dir(self.__class__) if method.startswith('__') is False]
        if name == "system_uptime":
            values = self.system_uptime()
        elif name == "memory_usage":
            values = self.memory_usage()
        elif name == "cpu_avg_load":
            values = self.cpu_avg_load()
        else:
            "Not Set"

        self.severity = self.get_severity(values[0])
        self.state = self.get_state()
        self.message = self.set_message(values)
        self.run_timestamp = self.get_run_timestamp()



