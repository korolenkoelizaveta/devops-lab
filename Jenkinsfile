pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds(abortPrevious: true)
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm

                echo "Current branch: ${env.GIT_BRANCH}"
            }
        }

        stage('Build Docker Images') {
            steps {
                bat 'docker build -t devops-lab-backend:ci-%BUILD_NUMBER% .'

                bat 'docker build -t devops-lab-frontend:ci-%BUILD_NUMBER% ./client'
            }
        }

        stage('Tests') {
            steps {
                echo 'Running 20 Django CRUD tests'

                bat 'docker run --rm devops-lab-backend:ci-%BUILD_NUMBER% python manage.py test'
            }
        }

        stage('Deploy') {
            when {
                expression {
                    env.GIT_BRANCH == 'origin/main' ||
                    env.GIT_BRANCH == 'main'
                }
            }

            steps {
                echo 'Preparing Docker images for deployment'

                bat 'docker tag devops-lab-backend:ci-%BUILD_NUMBER% devops-lab-backend:local'

                bat 'docker tag devops-lab-frontend:ci-%BUILD_NUMBER% devops-lab-frontend:local'

                echo 'Updating running application'

                bat 'docker compose -p devops_lab -f "%WORKSPACE%\\compose.yaml" up -d --no-build --force-recreate'

                echo 'Deployment completed'
            }
        }
    }

    post {
        success {
            echo "Pipeline for ${env.GIT_BRANCH} completed successfully"
        }

        failure {
            echo "Pipeline for ${env.GIT_BRANCH} failed"
        }

        aborted {
            echo 'Previous pipeline was aborted'
        }
    }
}