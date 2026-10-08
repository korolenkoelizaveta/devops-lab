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

                echo 'Сборка Docker-образа statistics'

                bat '''
                    docker build -t devops-lab-statistics:ci-%BUILD_NUMBER% ./statistics-service
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
                echo 'Формирование артефакта для Kubernetes'

                bat '''
                    if exist release rmdir /S /Q release

                    mkdir release
                    mkdir release\\k8s

                    copy Dockerfile release\\Dockerfile.backend
                    copy client\\Dockerfile release\\Dockerfile.frontend
                    copy statistics-service\\Dockerfile release\\Dockerfile.statistics

                    copy k8s\\*.yaml release\\k8s\\

                    echo Jenkins build: %BUILD_NUMBER% > release\\build-info.txt
                    echo Branch: %GIT_BRANCH% >> release\\build-info.txt
                    echo Commit: %GIT_COMMIT% >> release\\build-info.txt

                    echo Backend image: devops-lab-backend:ci-%BUILD_NUMBER% >> release\\build-info.txt
                    echo Frontend image: devops-lab-frontend:ci-%BUILD_NUMBER% >> release\\build-info.txt
                    echo Statistics image: devops-lab-statistics:ci-%BUILD_NUMBER% >> release\\build-info.txt
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

                    bat '''
                        docker tag devops-lab-statistics:ci-%BUILD_NUMBER% elizavetakek/devops-lab-statistics:%BUILD_NUMBER%
                        docker tag devops-lab-statistics:ci-%BUILD_NUMBER% elizavetakek/devops-lab-statistics:latest
                    '''

                    bat 'docker push elizavetakek/devops-lab-backend:%BUILD_NUMBER%'
                    bat 'docker push elizavetakek/devops-lab-backend:latest'

                    bat 'docker push elizavetakek/devops-lab-frontend:%BUILD_NUMBER%'
                    bat 'docker push elizavetakek/devops-lab-frontend:latest'

                    bat 'docker push elizavetakek/devops-lab-statistics:%BUILD_NUMBER%'
                    bat 'docker push elizavetakek/devops-lab-statistics:latest'

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
                echo 'Развертывание приложения в Kubernetes'

                withCredentials([
                    file(
                        credentialsId: 'kubeconfig-docker-desktop',
                        variable: 'KUBECONFIG'
                    )
                ]) {

                    bat '''
                        @echo off
                        set "KUBECTL=C:\\Program Files\\Docker\\Docker\\resources\\bin\\kubectl.exe"

                        echo Проверка подключения к Kubernetes
                        "%KUBECTL%" get nodes || exit /b 1

                        echo Применение Kubernetes-манифестов
                        "%KUBECTL%" apply -n devops-lab -f k8s/ || exit /b 1

                        echo Обновление Docker-образов
                        "%KUBECTL%" rollout restart deployment/backend -n devops-lab || exit /b 1
                        "%KUBECTL%" rollout restart deployment/frontend -n devops-lab || exit /b 1
                        "%KUBECTL%" rollout restart deployment/statistics -n devops-lab || exit /b 1

                        echo Ожидание готовности сервисов
                        "%KUBECTL%" rollout status deployment/backend -n devops-lab --timeout=180s || exit /b 1
                        "%KUBECTL%" rollout status deployment/frontend -n devops-lab --timeout=180s || exit /b 1
                        "%KUBECTL%" rollout status deployment/statistics -n devops-lab --timeout=180s || exit /b 1

                        echo Проверка Pod
                        "%KUBECTL%" get pods -n devops-lab || exit /b 1
                    '''
                }

                echo 'Kubernetes deployment completed'
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