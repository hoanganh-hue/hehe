#!/bin/bash

###############################################################################
# Generate MongoDB Keyfile for Replica Set Authentication
###############################################################################

echo "Generating MongoDB keyfile for replica set authentication..."

# Generate random keyfile
openssl rand -base64 756 > mongodb-keyfile

# Set correct permissions (very important!)
chmod 400 mongodb-keyfile

echo "✓ MongoDB keyfile generated: mongodb-keyfile"
echo "✓ Permissions set to 400"
echo ""
echo "IMPORTANT: Keep this file secure and never commit to git!"
echo "This keyfile is used for inter-node authentication in MongoDB replica set."

