#!/bin/bash

echo "🚀 Starting Telegram Whale Bot..."

# Loop forever
while true
do
    python3 app/main.py
    echo "⚠️ Bot crashed with exit code $?. Restarting in 5 seconds..."
    sleep 5
done
