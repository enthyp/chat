import datetime


def get_time():
    return datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')

colors = {
    'RED': '\033[91m',
    'GREEN': '\033[92m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'WHITE': '\033[97m',
}
ENDC = '\033[0m'


def mark(msg, color):
    if color in colors:
        return colors[color] + msg + ENDC
    return colors['WHITE'] + msg + ENDC
