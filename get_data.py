import os
from os.path import join, isdir, isfile, abspath
import yaml
import subprocess
import shlex
import sys
import signal

def execute_command(command):
    """
    Executes and displays the real-time output to stdout
    """
    if sys.platform == "win32":
        args = command
    else:
        args = shlex.split(command)

    # create the subprocess
    process = subprocess.Popen(args)

    try:
        # wait till it's finished
        process.wait()
    except KeyboardInterrupt:
        try:
            # kill the process on keyboard interrupt
            process.kill()
        except OSError:
            pass    

# read the config file
with open("config.yml") as f:
    config = yaml.safe_load(f)

# check if `data` folder exists
dpath = join(config["pwd"], config["storage"])
if not isdir(dpath):
    os.mkdir(dpath)
    print(dpath, "created")

# create the project folders
# if they are not already there
for folder in config["proj-config"]:
    # current folder path
    path = join(dpath, folder)

    if not isdir(path):
       os.mkdir(path)
       print(path, "created")
    else:
        print(path, "already exists")
        print("Updating Datasets")

    # execute the aws comamnd
    execute_command(config["aws-commands"][folder].format(abspath(path)))
