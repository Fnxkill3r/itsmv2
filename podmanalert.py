import subprocess
import json
from alert import *
from helper import *


class PodmanAlert(Alert):
    def __init__(self, config):
        super().__init__(config)
        self.run()


    def set_message(self, values):
        message = self.get_message()
        return find_and_replace_multi(message, ["var_value", "var_value"],
                                      values)

    def run(self):
        self.name = self.config["alert"]
        self.state = "OK" if self.config["rstate"] == 'running' else "NOK"
        self.severity = self.get_severity(self.state)
        self.message = self.set_message([self.config["rstate"], self.config["rstatus"]])
