"""
author: Hasan Alp Boz
date: 26/10/2020
"""
import os
from os.path import join, isdir, isfile, abspath
import yaml
import subprocess
import shlex
import sys

def execute_command(command):
    """
    Executes and displays the real-time output to stdout
    """
    if sys.platform == "win32":
        args = command
    else:
        args = shelx.split(command)

    process = subprocess.popen(args, stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        try:
            output = output.decode("utf-8")
        except:
            pass

        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
    rc = process.poll()
    return rc

# read the config file
with open("config.yml") as f:
    config = yaml.safe_load(f)

# create the project folders
# if they are not already there
for folder in config["proj-config"]:
    # current folder path
    path = join(config["pwd"], config["storage"], folder)

    if not isdir(path):
       os.mkdir(path)
       print(path, "created")
    else:
        print(path, "already exists")
        print("Updating Datasets")

    # execute the aws comamnd
    execute_command(config["aws-commands"][folder].format(abspath(path))) 

