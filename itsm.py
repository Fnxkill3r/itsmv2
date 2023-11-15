from modules.alarmistic import *
from modules.helpers.helper import *


if __name__ == '__main__':
    args = len(sys.argv) - 1
    if args == 0:
        print("No port set")
    else:
        if sys.argv[1].isdigit():
            port = sys.argv[1]
            check_pgpass = load_conn_values(port)
            if not check_pgpass:
                print("No pgpass line for localhost and setted port")
            else:
                run = Alarmistic(port)
                run.run()
        else:
            print("First arg must be Port number")