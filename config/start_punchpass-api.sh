#!/bin/bash

#Return to root
cd ~

# Kill all running screen sessions
screen -ls | awk '{print $1}' | xargs -I{} screen -X -S {} quit

# Remove the punchpass-api directory
rm -rf punchpass-api/

# Clone the punchpass-api repository
git clone https://github.com/victor1778/punchpass-api.git

# Change to the punchpass-api directory
cd punchpass-api/

# Start the application in a detached screen session
screen -d -m python3 -m uvicorn main:app