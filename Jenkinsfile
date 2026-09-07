pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Получение исходного кода из GitHub'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Установка зависимостей Django'
                bat 'python -m pip install -r requirements.txt'

                echo 'Установка зависимостей Vue'
                dir('client') {
                    bat 'npm ci'
                }
            }
        }

        stage('Tests') {
            steps {
                echo 'Запуск 20 CRUD-тестов'
                bat 'python manage.py test'
            }
        }

        stage('Build') {
            steps {
                echo 'Сборка Vue-приложения'
                dir('client') {
                    bat 'npm run build'
                }
            }
        }

        stage('Delivery') {
            steps {
                echo 'Подготовка стабильной версии приложения'

                bat '''
                    if exist release rmdir /S /Q release
                    mkdir release

                    xcopy app release\\app /E /I /Y
                    xcopy gym release\\gym /E /I /Y
                    xcopy client\\dist release\\client\\dist /E /I /Y

                    copy manage.py release\\
                    copy requirements.txt release\\
                '''

                echo 'Сохранение готовой версии как артефакта Jenkins'

                archiveArtifacts(
                    artifacts: 'release/**/*',
                    fingerprint: true
                )
            }
        }
    }

    post {
        success {
            echo 'CI/CD pipeline успешно завершен'
        }

        failure {
            echo 'CI/CD pipeline завершен с ошибкой'
        }
    }
}