#!/usr/bin/env sh

# start the server in the background
uv run main.py > server.log 2>&1 &
SERVER_PID=$!

sleep 1

# now only redis-cli output shows up here
redis-cli < COMMANDS

kill $SERVER_PID