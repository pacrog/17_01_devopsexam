#!/bin/bash
# Deploy to Yandex Cloud Serverless Containers
# Prerequisites: yc CLI, docker, terraform

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Change to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploying to Yandex Cloud${NC}"
echo -e "${GREEN}========================================${NC}"

# Check prerequisites
check_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"

    if ! command -v yc &> /dev/null; then
        echo -e "${RED}Error: yc CLI not installed${NC}"
        echo "Install: curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: docker not installed${NC}"
        exit 1
    fi

    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}Error: terraform not installed${NC}"
        exit 1
    fi

    echo -e "${GREEN}All prerequisites installed${NC}"
}

# Get YC configuration
get_yc_config() {
    echo -e "\n${YELLOW}Getting Yandex Cloud configuration...${NC}"

    FOLDER_ID=$(yc config get folder-id 2>/dev/null || echo "")
    CLOUD_ID=$(yc config get cloud-id 2>/dev/null || echo "")

    if [ -z "$FOLDER_ID" ]; then
        echo -e "${RED}Error: Yandex Cloud not configured${NC}"
        echo "Run: yc init"
        exit 1
    fi

    echo "Cloud ID: $CLOUD_ID"
    echo "Folder ID: $FOLDER_ID"

    export YC_FOLDER_ID=$FOLDER_ID
    export YC_CLOUD_ID=$CLOUD_ID
}

# Create Container Registry if not exists
setup_registry() {
    echo -e "\n${YELLOW}Setting up Container Registry...${NC}"

    REGISTRY_NAME="mlservice-registry"
    REGISTRY_ID=$(yc container registry get --name "$REGISTRY_NAME" --format json 2>/dev/null | jq -r '.id' || echo "")

    if [ -z "$REGISTRY_ID" ] || [ "$REGISTRY_ID" == "null" ]; then
        echo "Creating registry..."
        REGISTRY_ID=$(yc container registry create --name "$REGISTRY_NAME" --format json | jq -r '.id')
    fi

    echo "Registry ID: $REGISTRY_ID"
    export REGISTRY_ID

    # Configure docker authentication
    echo -e "\n${YELLOW}Configuring Docker authentication...${NC}"
    yc container registry configure-docker
}

# Build and push Docker images
build_and_push() {
    echo -e "\n${YELLOW}Building Docker images...${NC}"

    REGISTRY_URL="cr.yandex/$REGISTRY_ID"

    # Build API image
    echo "Building API image..."
    docker build -t "$REGISTRY_URL/api:latest" -f api/Dockerfile api/

    # Build MLflow image
    echo "Building MLflow image..."
    docker build -t "$REGISTRY_URL/mlflow:latest" -f mlflow/Dockerfile mlflow/

    # Push images
    echo -e "\n${YELLOW}Pushing images to registry...${NC}"
    docker push "$REGISTRY_URL/api:latest"
    docker push "$REGISTRY_URL/mlflow:latest"

    echo -e "${GREEN}Images pushed successfully${NC}"
}

# Deploy infrastructure with Terraform
deploy_terraform() {
    echo -e "\n${YELLOW}Deploying infrastructure with Terraform...${NC}"

    cd infrastructure/yandex-cloud

    # Check if tfvars exists
    if [ ! -f "terraform.tfvars" ]; then
        echo -e "${YELLOW}Creating terraform.tfvars from example...${NC}"

        # Get YC token
        YC_TOKEN=$(yc iam create-token)

        # Generate password
        DB_PASSWORD=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)

        cat > terraform.tfvars <<EOF
yc_token     = "$YC_TOKEN"
yc_cloud_id  = "$YC_CLOUD_ID"
yc_folder_id = "$YC_FOLDER_ID"
yc_zone      = "ru-central1-a"

project_name = "mlservice"
environment  = "dev"

db_username = "mlflow"
db_password = "$DB_PASSWORD"
db_resource_preset = "s2.micro"
db_disk_size = 10

api_memory_mb    = 512
api_cores        = 1
mlflow_memory_mb = 1024
mlflow_cores     = 1

artifact_retention_days = 90
EOF
        echo -e "${GREEN}Created terraform.tfvars${NC}"
        echo -e "${YELLOW}DB Password: $DB_PASSWORD (save this!)${NC}"
    fi

    # Initialize and apply
    terraform init
    terraform plan -out=tfplan

    echo -e "\n${YELLOW}Apply Terraform changes? (yes/no)${NC}"
    read -r CONFIRM

    if [ "$CONFIRM" == "yes" ]; then
        terraform apply tfplan
        echo -e "${GREEN}Infrastructure deployed!${NC}"

        # Show outputs
        echo -e "\n${GREEN}========================================${NC}"
        echo -e "${GREEN}Deployment Complete!${NC}"
        echo -e "${GREEN}========================================${NC}"
        terraform output
    else
        echo "Deployment cancelled"
    fi

    cd "$PROJECT_DIR"
}

# Quick deploy - only build and push images
quick_deploy() {
    echo -e "\n${YELLOW}Quick deploy - updating containers...${NC}"

    REGISTRY_URL="cr.yandex/$REGISTRY_ID"

    # Build and push
    docker build -t "$REGISTRY_URL/api:latest" -f api/Dockerfile api/
    docker push "$REGISTRY_URL/api:latest"

    # Get container ID and redeploy
    API_CONTAINER_ID=$(yc serverless container list --format json | jq -r '.[] | select(.name | contains("api")) | .id')

    if [ -n "$API_CONTAINER_ID" ]; then
        echo "Redeploying container $API_CONTAINER_ID..."
        yc serverless container revision deploy \
            --container-id "$API_CONTAINER_ID" \
            --image "$REGISTRY_URL/api:latest" \
            --memory 512MB \
            --execution-timeout 30s
        echo -e "${GREEN}Container updated!${NC}"
    fi
}

# Main
main() {
    ACTION=${1:-"full"}

    check_prerequisites
    get_yc_config
    setup_registry

    case $ACTION in
        "full")
            build_and_push
            deploy_terraform
            ;;
        "quick")
            quick_deploy
            ;;
        "build")
            build_and_push
            ;;
        "infra")
            deploy_terraform
            ;;
        *)
            echo "Usage: $0 [full|quick|build|infra]"
            echo "  full  - Full deployment (default)"
            echo "  quick - Quick update (rebuild and redeploy API)"
            echo "  build - Build and push images only"
            echo "  infra - Deploy infrastructure only"
            exit 1
            ;;
    esac
}

main "$@"
