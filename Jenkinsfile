pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        disableConcurrentBuilds(abortPrevious: true)
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Получение исходного кода'
                checkout scm

                echo "Текущая ветка: ${env.GIT_BRANCH}"
                echo "Коммит: ${env.GIT_COMMIT}"
            }
        }


        stage('Build Docker Images') {
            steps {
                echo 'Сборка Docker-образа backend'

                bat '''
                    docker build -t devops-lab-backend:ci-%BUILD_NUMBER% .
                    
                '''

                echo 'Сборка Docker-образа frontend'

                bat '''
                    docker build -t devops-lab-frontend:ci-%BUILD_NUMBER% ./client   
                '''
            }
        }


        stage('Tests') {
            steps {
                echo 'Запуск 20 CRUD-тестов внутри Docker'

                bat '''
                    docker run --rm devops-lab-backend:ci-%BUILD_NUMBER% python manage.py test

                '''
            }
        }


        stage('Artifact') {
            steps {
                echo 'Формирование артефакта сборки'

                bat '''
                    if exist release rmdir /S /Q release
                    mkdir release

                    copy compose.yaml release\\
                    copy Dockerfile release\\Dockerfile.backend
                    copy client\\Dockerfile release\\Dockerfile.frontend
                    copy client\\nginx.conf release\\nginx.conf

                    echo Jenkins build: %BUILD_NUMBER% > release\\build-info.txt
                    echo Branch: %GIT_BRANCH% >> release\\build-info.txt
                    echo Commit: %GIT_COMMIT% >> release\\build-info.txt
                    echo Backend image: devops-lab-backend:ci-%BUILD_NUMBER% >> release\\build-info.txt
                    echo Frontend image: devops-lab-frontend:ci-%BUILD_NUMBER% >> release\\build-info.txt
                '''

                archiveArtifacts(
                    artifacts: 'release/**/*',
                    fingerprint: true
                )
            }
        }


        stage('Docker Registry') {
            when {
                expression {
                    env.GIT_BRANCH == 'origin/main' ||
                    env.GIT_BRANCH == 'main'
                }
            }

            steps {
                echo 'Публикация Docker-образов в Docker Hub'

                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_TOKEN'
                    )
                ]) {

                    bat '''
                        @echo off
                	powershell -NoProfile -Command "[Console]::Out.Write($env:DOCKER_TOKEN)" | docker login -u "%DOCKER_USER%" --password-stdin
            	    '''

		    bat '''
                	docker tag devops-lab-backend:ci-%BUILD_NUMBER% elizavetakek/devops-lab-backend:%BUILD_NUMBER%
                	docker tag devops-lab-backend:ci-%BUILD_NUMBER% elizavetakek/devops-lab-backend:latest
            	    '''

            	    bat '''
                	docker tag devops-lab-frontend:ci-%BUILD_NUMBER% elizavetakek/devops-lab-frontend:%BUILD_NUMBER%
                	docker tag devops-lab-frontend:ci-%BUILD_NUMBER% elizavetakek/devops-lab-frontend:latest
            	    '''

            	    bat 'docker push elizavetakek/devops-lab-backend:%BUILD_NUMBER%'
            	    bat 'docker push elizavetakek/devops-lab-backend:latest'

            	    bat 'docker push elizavetakek/devops-lab-frontend:%BUILD_NUMBER%'
            	    bat 'docker push elizavetakek/devops-lab-frontend:latest'

            	    bat 'docker logout'

                }
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
                echo 'Получение проверенных образов из Docker Registry'

                bat '''
                    docker compose -p devops_lab -f "%WORKSPACE%\\compose.yaml" pull
                    
                '''

                echo 'Обновление работающего приложения'

                bat '''
                    docker compose -p devops_lab -f "%WORKSPACE%\\compose.yaml" up -d --no-build --force-recreate
                    
                '''

                echo 'Deployment completed'
            }
        }
    }


    post {

        success {
            echo "Pipeline для ${env.GIT_BRANCH} успешно завершен"
        }

        failure {
            echo "Pipeline для ${env.GIT_BRANCH} завершен с ошибкой"
        }

        aborted {
            echo 'Предыдущая сборка отменена новой сборкой'
        }
    }
}