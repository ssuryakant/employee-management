pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-south-1'
        ECR_REPO = 'devops-python-app'
        EKS_CLUSTER = 'devops-eks'
    }

    stages {

        stage('Git Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Python Validation') {
            steps {
                sh '''
                python3 -m pip install -r app/requirements.txt
                python3 -m compileall -q app
                '''
            }
        }

        stage('Docker Build') {
            steps {
                sh '''
                docker build -t $ECR_REPO:$BUILD_NUMBER .
                '''
            }
        }

        stage('Login to ECR') {
            steps {
                sh '''
                ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
                REGISTRY=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

                aws ecr get-login-password --region $AWS_REGION |
                docker login --username AWS --password-stdin $REGISTRY
                '''
            }
        }

        stage('Push Docker Image') {
            steps {
                sh '''
                ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
                IMAGE=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$BUILD_NUMBER

                docker tag $ECR_REPO:$BUILD_NUMBER $IMAGE
                docker push $IMAGE
                '''
            }
        }

        stage('Deploy to EKS') {
            steps {
                sh '''
                ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
                IMAGE=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$BUILD_NUMBER

                aws eks update-kubeconfig \
                  --region $AWS_REGION \
                  --name $EKS_CLUSTER

                kubectl set image deployment/python-app \
                  python-app=$IMAGE

                kubectl rollout status deployment/python-app \
                  --timeout=180s
                '''
            }
        }
    }

    post {
        always {
            sh 'docker image prune -f || true'
        }
    }
}
