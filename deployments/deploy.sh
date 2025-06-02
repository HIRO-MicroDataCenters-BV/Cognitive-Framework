#!/bin/bash

# Apply the Kubernetes Deployment
kubectl apply -f deployment.yaml

# Apply the Kubernetes Service
kubectl apply -f service.yaml

echo "Deployment and Service have been applied."