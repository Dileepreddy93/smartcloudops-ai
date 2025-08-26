#!/bin/bash
# SmartCloudOps AI - Production Deployment Script
# ==============================================
#
# This script deploys the complete SmartCloudOps AI platform to production
# with comprehensive monitoring, metrics, and validation.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="smartcloudops-ai"
ENVIRONMENT="production"
AWS_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Logging
LOG_FILE="deployment_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo -e "${BLUE}🚀 SmartCloudOps AI - Production Deployment${NC}"
echo "=================================================="
echo "Timestamp: $(date)"
echo "Environment: $ENVIRONMENT"
echo "AWS Region: $AWS_REGION"
echo "AWS Account: $AWS_ACCOUNT_ID"
echo "Log File: $LOG_FILE"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed"
        exit 1
    fi
    
    # Check required environment variables
    required_vars=(
        "SECRET_KEY"
        "ADMIN_API_KEY"
        "ML_API_KEY"
        "READONLY_API_KEY"
        "DB_PASSWORD"
        "REDIS_PASSWORD"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("$var")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        print_error "Missing required environment variables: ${missing_vars[*]}"
        print_info "Please run: ./scripts/setup_secure_environment.sh"
        exit 1
    fi
    
    print_status "All prerequisites satisfied"
}

# Function to validate infrastructure
validate_infrastructure() {
    print_info "Validating infrastructure configuration..."
    
    cd terraform/production
    
    # Initialize Terraform
    print_info "Initializing Terraform..."
    terraform init
    
    # Validate configuration
    print_info "Validating Terraform configuration..."
    if ! terraform validate; then
        print_error "Terraform configuration validation failed"
        exit 1
    fi
    
    # Plan deployment
    print_info "Planning Terraform deployment..."
    terraform plan -out=tfplan
    
    print_status "Infrastructure validation completed"
    cd ../..
}

# Function to deploy infrastructure
deploy_infrastructure() {
    print_info "Deploying infrastructure..."
    
    cd terraform/production
    
    # Apply Terraform plan
    print_info "Applying Terraform configuration..."
    terraform apply tfplan
    
    # Get outputs
    print_info "Getting infrastructure outputs..."
    DB_HOST=$(terraform output -raw database_host)
    DB_PORT=$(terraform output -raw database_port)
    DB_NAME=$(terraform output -raw database_name)
    DB_USERNAME=$(terraform output -raw database_username)
    REDIS_HOST=$(terraform output -raw redis_host)
    REDIS_PORT=$(terraform output -raw redis_port)
    ALB_DNS=$(terraform output -raw alb_dns_name)
    ECR_REPO=$(terraform output -raw ecr_repository_url)
    
    print_status "Infrastructure deployed successfully"
    print_info "Database: $DB_HOST:$DB_PORT/$DB_NAME"
    print_info "Redis: $REDIS_HOST:$REDIS_PORT"
    print_info "Load Balancer: $ALB_DNS"
    print_info "ECR Repository: $ECR_REPO"
    
    cd ../..
}

# Function to build and push Docker images
build_and_push_images() {
    print_info "Building and pushing Docker images..."
    
    # Login to ECR
    print_info "Logging into ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
    
    # Build and push main application
    print_info "Building main application image..."
    docker build -f Dockerfile.production -t "$ECR_REPO:latest" .
    docker push "$ECR_REPO:latest"
    
    # Build and push auth service
    print_info "Building authentication service image..."
    docker build -f services/auth_service/Dockerfile -t "$ECR_REPO:auth-service" services/auth_service/
    docker push "$ECR_REPO:auth-service"
    
    # Build and push ML service
    print_info "Building ML service image..."
    docker build -f services/ml_service/Dockerfile -t "$ECR_REPO:ml-service" services/ml_service/
    docker push "$ECR_REPO:ml-service"
    
    print_status "All Docker images built and pushed successfully"
}

# Function to deploy application
deploy_application() {
    print_info "Deploying application..."
    
    # Update ECS services
    print_info "Updating ECS services..."
    
    # Update main application service
    aws ecs update-service \
        --cluster "$PROJECT_NAME-cluster" \
        --service "$PROJECT_NAME-app" \
        --force-new-deployment \
        --region "$AWS_REGION"
    
    # Update auth service
    aws ecs update-service \
        --cluster "$PROJECT_NAME-cluster" \
        --service "$PROJECT_NAME-auth" \
        --force-new-deployment \
        --region "$AWS_REGION"
    
    # Update ML service
    aws ecs update-service \
        --cluster "$PROJECT_NAME-cluster" \
        --service "$PROJECT_NAME-ml" \
        --force-new-deployment \
        --region "$AWS_REGION"
    
    print_status "Application deployment initiated"
}

# Function to wait for deployment
wait_for_deployment() {
    print_info "Waiting for deployment to complete..."
    
    # Wait for ECS services to be stable
    services=("$PROJECT_NAME-app" "$PROJECT_NAME-auth" "$PROJECT_NAME-ml")
    
    for service in "${services[@]}"; do
        print_info "Waiting for $service to be stable..."
        aws ecs wait services-stable \
            --cluster "$PROJECT_NAME-cluster" \
            --services "$service" \
            --region "$AWS_REGION"
        print_status "$service is stable"
    done
    
    print_status "All services are stable"
}

# Function to run health checks
run_health_checks() {
    print_info "Running health checks..."
    
    # Wait for load balancer to be ready
    print_info "Waiting for load balancer to be ready..."
    sleep 30
    
    # Health check endpoints
    endpoints=(
        "http://$ALB_DNS/health"
        "http://$ALB_DNS/metrics"
        "http://$ALB_DNS/status"
    )
    
    for endpoint in "${endpoints[@]}"; do
        print_info "Checking $endpoint..."
        
        for i in {1..10}; do
            if curl -f -s "$endpoint" > /dev/null; then
                print_status "$endpoint is healthy"
                break
            else
                if [[ $i -eq 10 ]]; then
                    print_error "$endpoint health check failed"
                    return 1
                fi
                print_warning "Attempt $i/10 failed, retrying in 10 seconds..."
                sleep 10
            fi
        done
    done
    
    print_status "All health checks passed"
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    print_info "Running comprehensive tests..."
    
    # Set test environment variables
    export BASE_URL="http://$ALB_DNS"
    export AUTH_SERVICE_URL="http://$ALB_DNS/auth"
    export ML_SERVICE_URL="http://$ALB_DNS/ml"
    
    # Run test suite
    print_info "Running test suite..."
    if python3 tests/comprehensive_test_suite.py; then
        print_status "All tests passed"
    else
        print_error "Some tests failed"
        return 1
    fi
}

# Function to setup monitoring
setup_monitoring() {
    print_info "Setting up monitoring..."
    
    # Create CloudWatch dashboards
    print_info "Creating CloudWatch dashboards..."
    
    # Application metrics dashboard
    cat > cloudwatch-dashboard.json << EOF
{
    "widgets": [
        {
            "type": "metric",
            "x": 0,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "$ALB_DNS"],
                    [".", "TargetResponseTime", ".", "."],
                    [".", "HTTPCode_Target_5XX_Count", ".", "."]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "$AWS_REGION",
                "title": "Application Load Balancer Metrics"
            }
        },
        {
            "type": "metric",
            "x": 12,
            "y": 0,
            "width": 12,
            "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/ECS", "CPUUtilization", "ServiceName", "$PROJECT_NAME-app", "ClusterName", "$PROJECT_NAME-cluster"],
                    [".", "MemoryUtilization", ".", ".", ".", "."]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "$AWS_REGION",
                "title": "ECS Service Metrics"
            }
        }
    ]
}
EOF
    
    # Create dashboard
    aws cloudwatch put-dashboard \
        --dashboard-name "$PROJECT_NAME-dashboard" \
        --dashboard-body file://cloudwatch-dashboard.json \
        --region "$AWS_REGION"
    
    # Setup CloudWatch alarms
    print_info "Setting up CloudWatch alarms..."
    
    # High CPU alarm
    aws cloudwatch put-metric-alarm \
        --alarm-name "$PROJECT_NAME-high-cpu" \
        --alarm-description "High CPU utilization" \
        --metric-name CPUUtilization \
        --namespace AWS/ECS \
        --statistic Average \
        --period 300 \
        --threshold 80 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 2 \
        --dimensions Name=ServiceName,Value=$PROJECT_NAME-app Name=ClusterName,Value=$PROJECT_NAME-cluster \
        --region "$AWS_REGION"
    
    # High memory alarm
    aws cloudwatch put-metric-alarm \
        --alarm-name "$PROJECT_NAME-high-memory" \
        --alarm-description "High memory utilization" \
        --metric-name MemoryUtilization \
        --namespace AWS/ECS \
        --statistic Average \
        --period 300 \
        --threshold 80 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 2 \
        --dimensions Name=ServiceName,Value=$PROJECT_NAME-app Name=ClusterName,Value=$PROJECT_NAME-cluster \
        --region "$AWS_REGION"
    
    # High error rate alarm
    aws cloudwatch put-metric-alarm \
        --alarm-name "$PROJECT_NAME-high-errors" \
        --alarm-description "High error rate" \
        --metric-name HTTPCode_Target_5XX_Count \
        --namespace AWS/ApplicationELB \
        --statistic Sum \
        --period 300 \
        --threshold 10 \
        --comparison-operator GreaterThanThreshold \
        --evaluation-periods 2 \
        --dimensions Name=LoadBalancer,Value=$ALB_DNS \
        --region "$AWS_REGION"
    
    print_status "Monitoring setup completed"
}

# Function to generate deployment report
generate_deployment_report() {
    print_info "Generating deployment report..."
    
    report_file="deployment_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
    "deployment": {
        "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
        "environment": "$ENVIRONMENT",
        "project": "$PROJECT_NAME",
        "aws_region": "$AWS_REGION",
        "aws_account": "$AWS_ACCOUNT_ID"
    },
    "infrastructure": {
        "database": {
            "host": "$DB_HOST",
            "port": "$DB_PORT",
            "name": "$DB_NAME",
            "username": "$DB_USERNAME"
        },
        "redis": {
            "host": "$REDIS_HOST",
            "port": "$REDIS_PORT"
        },
        "load_balancer": "$ALB_DNS",
        "ecr_repository": "$ECR_REPO"
    },
    "services": {
        "main_app": {
            "status": "deployed",
            "url": "http://$ALB_DNS"
        },
        "auth_service": {
            "status": "deployed",
            "url": "http://$ALB_DNS/auth"
        },
        "ml_service": {
            "status": "deployed",
            "url": "http://$ALB_DNS/ml"
        }
    },
    "monitoring": {
        "cloudwatch_dashboard": "$PROJECT_NAME-dashboard",
        "alarms": [
            "$PROJECT_NAME-high-cpu",
            "$PROJECT_NAME-high-memory",
            "$PROJECT_NAME-high-errors"
        ]
    },
    "next_steps": [
        "Monitor application performance",
        "Set up additional alerting",
        "Configure backup and disaster recovery",
        "Implement CI/CD pipeline",
        "Set up user access and permissions"
    ]
}
EOF
    
    print_status "Deployment report generated: $report_file"
}

# Function to display final status
display_final_status() {
    echo ""
    echo -e "${GREEN}🎉 PRODUCTION DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
    echo "=================================================="
    echo ""
    echo -e "${BLUE}📊 Application URLs:${NC}"
    echo "  Main Application: http://$ALB_DNS"
    echo "  Authentication: http://$ALB_DNS/auth"
    echo "  ML Service: http://$ALB_DNS/ml"
    echo "  Health Check: http://$ALB_DNS/health"
    echo "  Metrics: http://$ALB_DNS/metrics"
    echo ""
    echo -e "${BLUE}📈 Monitoring:${NC}"
    echo "  CloudWatch Dashboard: $PROJECT_NAME-dashboard"
    echo "  CloudWatch Alarms: $PROJECT_NAME-high-cpu, $PROJECT_NAME-high-memory, $PROJECT_NAME-high-errors"
    echo ""
    echo -e "${BLUE}🔧 Management:${NC}"
    echo "  AWS Console: https://console.aws.amazon.com"
    echo "  ECS Cluster: $PROJECT_NAME-cluster"
    echo "  ECR Repository: $ECR_REPO"
    echo ""
    echo -e "${YELLOW}⚠️ Important Notes:${NC}"
    echo "  • Monitor application performance closely"
    echo "  • Set up additional alerting as needed"
    echo "  • Configure backup and disaster recovery"
    echo "  • Implement proper CI/CD pipeline"
    echo "  • Set up user access and permissions"
    echo ""
    echo -e "${GREEN}✅ Deployment completed at $(date)${NC}"
}

# Main deployment function
main() {
    echo "Starting production deployment..."
    
    # Check prerequisites
    check_prerequisites
    
    # Validate infrastructure
    validate_infrastructure
    
    # Deploy infrastructure
    deploy_infrastructure
    
    # Build and push images
    build_and_push_images
    
    # Deploy application
    deploy_application
    
    # Wait for deployment
    wait_for_deployment
    
    # Run health checks
    run_health_checks
    
    # Run comprehensive tests
    run_comprehensive_tests
    
    # Setup monitoring
    setup_monitoring
    
    # Generate deployment report
    generate_deployment_report
    
    # Display final status
    display_final_status
}

# Run main function
main "$@"
