#!/bin/bash
set -euo pipefail

# Step 1: Initialize repository for notif-api-service
TARGET_DIR="$HOME/notif-api-service"
IMAGE="$DOCKER_USERNAME/notif-api-service"
mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

# Step 2: Sync repository (clone/pull latest code)
if [ -d ".git" ]; then
    echo "--- Syncing ---"
    git fetch origin
    git reset --hard origin/main
else
    echo "--- Cloning ---"
    git init
    git remote add origin https://github.com/Moin-A/notif-api-service.git
    git fetch origin
    git reset --hard origin/main
fi

# Step 3: Docker build
TAG=$(git rev-parse --short HEAD)
echo "--- Image tag: $TAG ---"

echo "--- Docker Login ---"
echo $DOCKER_PASSWORD | docker login -u $DOCKER_USERNAME --password-stdin

echo "--- Building & Pushing ---"
docker build --network=host -t "$IMAGE:$TAG" .
docker push "$IMAGE:$TAG"

# Step 4: Retag the same build as latest so the manifests' default ref stays current
docker tag "$IMAGE:$TAG" "$IMAGE:latest"
docker push "$IMAGE:latest"

# Step 5: Kubernetes config
DEPLOY_YAML="notif-kube-deployment.yaml"
WORKER_YAML="notif-kube-worker-deployment.yaml"
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Step 6: Kubernetes apply
echo "--- Applying Manifests ---"
kubectl apply -f "$DEPLOY_YAML"
kubectl apply -f "$WORKER_YAML"

# Force rollout with the immutable SHA tag
echo "--- Deploying $TAG ---"
kubectl set image deployment/notif-api notif-api="$IMAGE:$TAG" -n notif
kubectl set image deployment/notif-worker notif-worker="$IMAGE:$TAG" -n notif

kubectl rollout status deployment/notif-api -n notif --timeout=180s
kubectl rollout status deployment/notif-worker -n notif --timeout=180s

echo "--- Done ---"
