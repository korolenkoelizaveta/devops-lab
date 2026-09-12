pipeline {
    agent any

    environment {
        DEPLOY_DIR = 'C:\\ProgramData\\Jenkins\\deploy\\devops-lab'
    }

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
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Установка зависимостей backend'
                bat 'python -m pip install -r requirements.txt'

                echo 'Установка зависимостей frontend'
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
                echo 'Сборка frontend'

                dir('client') {
                    bat 'npm run build'
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
                echo 'Остановка старой версии приложения'

                bat '''
                    powershell -NoProfile -Command "$p = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue; if ($p) { $p | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }"
                    powershell -NoProfile -Command "$p = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue; if ($p) { $p | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }"
                '''

                echo 'Обновление рабочей версии приложения'

                bat '''
                    if not exist "%DEPLOY_DIR%" mkdir "%DEPLOY_DIR%"

                    robocopy "%WORKSPACE%" "%DEPLOY_DIR%" /MIR /R:1 /W:1 ^
                    /XD .git __pycache__ .pytest_cache ^
                    /XF db.sqlite3 *.pyc

                    if %ERRORLEVEL% GEQ 8 exit /b %ERRORLEVEL%
                    exit /b 0
                '''

                echo 'Применение миграций базы данных'

                bat '''
                    cd /d "%DEPLOY_DIR%"
                    python manage.py migrate
                '''

                echo 'Запуск backend'

                bat '''
                    set JENKINS_NODE_COOKIE=dontKillMe
                    powershell -NoProfile -Command "$env:JENKINS_NODE_COOKIE='dontKillMe'; Start-Process -FilePath 'python' -ArgumentList 'manage.py runserver 0.0.0.0:8000 --noreload' -WorkingDirectory '%DEPLOY_DIR%' -WindowStyle Hidden"
                '''

                echo 'Запуск frontend'

                bat '''
                    set JENKINS_NODE_COOKIE=dontKillMe
                    powershell -NoProfile -Command "$env:JENKINS_NODE_COOKIE='dontKillMe'; Start-Process -FilePath 'cmd.exe' -ArgumentList '/c npm run dev -- --host 0.0.0.0 --port 5173' -WorkingDirectory '%DEPLOY_DIR%\\client' -WindowStyle Hidden"
                '''
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