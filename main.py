import configparser
import os

from app.interpreter import Interpreter

CONFIG_NAME = "streamql.cfg"
STREAM_QL_CONFIG_DICT = "StreamQL"
MAIN_SRC_ENV = "main_src"
RUN_CMD = "run"
HELP_CMD = "help"

config = configparser.ConfigParser()
config.read(CONFIG_NAME)

main_src = config[STREAM_QL_CONFIG_DICT][MAIN_SRC_ENV]
i = Interpreter(lambda s: print(s))


def show_help():
    print(f"'{RUN_CMD}' -- execute code from source file by default (set in config '{CONFIG_NAME}')")
    print(f"'{HELP_CMD}' -- show help")
    print("any other string is interpreted as the path to the source file")
    print()


def run(file_name: str):
    with open(file_name, "r") as f:
        i.run(f.read())
        print()


os.system("clear")

while True:
    try:
        print(f"Input (type '{HELP_CMD}' to show help): ", end="")
        cmd = input()
        if cmd == HELP_CMD:
            show_help()
        elif cmd == RUN_CMD:
            run(main_src)
        else:
            run(cmd)
    except Exception as e:
        print(e)
        print()
