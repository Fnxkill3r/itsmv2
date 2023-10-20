from alert import *
from helper import *
import psutil


class FilesystemAlert(Alert):
    def __init__(self, config):
        super().__init__(config)
        self.run()

    def filesystem_usage(self, my_fs):
        disk_usage = psutil.disk_usage(my_fs)
        if self.config["threshold_type"] == "%":
            return float(100 - disk_usage.percent)
        else:
            return round(disk_usage.free / (2 ** 20), 2) if self.config["threshold_type"] == "mb" else round(disk_usage.free / (2 ** 30), 2)

    def set_message(self, values):
        message = self.get_message()
        return find_and_replace_multi(message, ["var_filesystem_name", "var_threshold_value", "var_threshold_type"], values)

    def run(self):
        self.name = self.config["alert"]
        my_fs = self.config["type"].split(":")[1]
        if os.path.isdir(my_fs):
            value = self.filesystem_usage(my_fs)
            self.severity = self.get_severity(value)
            self.state = self.get_state()
            self.message = self.set_message([self.config["type"].split(":")[1], value, self.config["threshold_type"]])
        else:
            self.severity = "CRITICAL"
            self.state = "NOK"
            self.message = "Filesystem: {} does not exist. ".format(my_fs)


