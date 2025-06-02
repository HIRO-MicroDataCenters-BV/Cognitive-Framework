#!/bin/bash

# Check required environment variables
if [[ -z "$JUJU_USERNAME" || -z "$JUJU_PASSWORD" || -z "$JUJU_API_ENDPOINTS" || -z "$JUJU_CON" ]]; then
  echo "Error: Required environment variables (JUJU_USERNAME, JUJU_PASSWORD, JUJU_API_ENDPOINTS, JUJU_CON) are not set."
  exit 1
fi

# Extract the first API endpoint for public-hostname
FIRST_API_ENDPOINT=$(echo "$JUJU_API_ENDPOINTS" | cut -d',' -f1 | cut -d':' -f1)

# Resolve DNS cache
if [[ -z "$JUJU_DNS_CACHE" ]]; then
  RESOLVED_IP=$(dig +short "$FIRST_API_ENDPOINT" | head -n1)
  JUJU_DNS_CACHE="{${FIRST_API_ENDPOINT}: [$RESOLVED_IP]}"
fi

# Create accounts.yaml
cat <<EOF > /root/.local/share/juju/accounts.yaml
controllers:
    $JUJU_CON:
        user: $JUJU_USERNAME
        password: $JUJU_PASSWORD
        last-known-access: superuser
current-controller: $JUJU_CON
EOF

echo "accounts.yaml created."

# Create controllers.yaml
cat <<EOF > /root/.local/share/juju/controllers.yaml
controllers:
    $JUJU_CON:
        uuid: f04abcd1-4c9a-4fb3-8468-77d0c053185c
        api-endpoints: ['${JUJU_API_ENDPOINTS//,/\', \'}']
        dns-cache: $JUJU_DNS_CACHE
        public-hostname: $FIRST_API_ENDPOINT
EOF

# Add CA certificate if provided
if [[ -n "$JUJU_CA_CERT" ]]; then
  echo "        ca-cert: |" >> /root/.local/share/juju/controllers.yaml
  while IFS= read -r line; do
    echo "            $line" >> /root/.local/share/juju/controllers.yaml
  done <<< "$JUJU_CA_CERT"
fi

# Append static fields
cat <<EOF >> /root/.local/share/juju/controllers.yaml
        cloud: ""
        agent-version: 3.6.1
        controller-machine-count: 0
        active-controller-machine-count: 0
current-controller: $JUJU_CON
EOF

echo "controllers.yaml created:"
#cat /root/.local/share/juju/controllers.yaml
