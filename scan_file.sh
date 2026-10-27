#!/usr/bin/env bash
FILE=$1
echo "🚨 Scanning $FILE..."
cat $FILE | ollama run RedRabbit "Analyze this code for critical vulnerabilities and output the exploit paths:"
