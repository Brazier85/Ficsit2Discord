#!/bin/bash

# Description: This script controls the execution of a Python script with a start and stop parameter.
# Usage: ./script.sh start|stop
# "start" will run the Python script in the background and save its process ID.
# "stop" will terminate the process using the saved process ID.

# Define the path to the Python script
SCRIPT="./main.py"
LOG_FILE="Ficit2Discord.log"
PID_FILE="current.pid"

source .venv/bin/activate

pip install -r requirements.txt

# Check the input parameter
case "$1" in
start)
    if [ -f "$PID_FILE" ]; then
        echo "Script is already running with PID: $(cat $PID_FILE)"
        exit 1
    fi
    echo "Check for a new version"
    git pull
    echo "Starting script..."
    nohup $SCRIPT >$LOG_FILE 2>&1 &
    echo $! >$PID_FILE
    echo "Script started with PID: $(cat $PID_FILE)"
    ;;

stop)
    if [ ! -f "$PID_FILE" ]; then
        echo "No script is running."
        exit 1
    fi
    PID=$(cat $PID_FILE)
    echo "Stopping script with PID: $PID"
    kill -9 $PID
    rm -f $PID_FILE
    echo "Script stopped."
    ;;

*)
    echo "Usage: $0 start|stop"
    exit 1
    ;;
esac
