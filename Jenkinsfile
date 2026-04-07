pipeline {
    agent any

    environment {
        // 1. Docker Hub 정보 (성공한 계정 사용)
        DOCKER_USER = "sharkey1982" 
        IMAGE_NAME = "python-fullstack-app"
        
        // 2. Linux Mint(CasaOS) 서버 정보 업데이트
        MINT_IP = "100.117.139.81"  // <-- 이 부분을 수정하세요!
        MINT_USER = "david"
        APP_NAME = "my-running-app"
        APP_PORT = "8080" // 포트 변수를 하나 추가하거나 아래 docker run 부분을 수정합니다.
    }

    stages {
        stage('Step 1: Code Build & Docker Push') {
            steps {
                script {
                    echo "📦 이미지를 빌드합니다 (AMD64 호환)..."
                    // Dockerfile이 있는 위치에서 빌드 실행
                    sh "docker build --platform linux/amd64 -t ${DOCKER_USER}/${IMAGE_NAME}:latest ."
                    
                    echo "🚀 Docker Hub로 업로드합니다..."
                    // Jenkins Credentials에 등록한 'docker-hub-id' 사용
                    withDockerRegistry([credentialsId: 'sharkey', url: '']) {
                        sh "docker push ${DOCKER_USER}/${IMAGE_NAME}:latest"
                    }
                }
            }
        }

        stage('Step 2: Remote Deploy to Linux Mint') {
            steps {
                echo "🚚 Mint 서버(CasaOS)에 접속하여 배포를 시작합니다..."
                // Jenkins Credentials에 등록한 'mint-ssh-key' 사용
                sshagent(['mint-ssh-key']) {
                sh """
                ssh -o StrictHostKeyChecking=no ${MINT_USER}@${MINT_IP} "
                   docker pull ${DOCKER_USER}/${IMAGE_NAME}:latest
                   docker stop ${APP_NAME} || true
                   docker rm ${APP_NAME} || true
                   docker run -d --name ${APP_NAME} -p 8080:8501 --restart always ${DOCKER_USER}/${IMAGE_NAME}:latest
                   docker image prune -f
                "
                """
                }
            }
        }
    }
}
