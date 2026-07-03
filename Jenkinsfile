// Jenkinsfile — build, push, and deploy Mother Teresa Transport.
//
// Before this runs, set up in Jenkins:
//   1. Credentials (Manage Jenkins → Credentials):
//        - "dockerhub-creds"   : Username/Password — your registry login
//        - "deploy-ssh-key"    : SSH Username with private key — access to the
//                                 server that will run `docker compose`
//   2. A multibranch pipeline or a pipeline job pointed at this repo.
//   3. Replace REGISTRY_NAMESPACE, DEPLOY_HOST and DEPLOY_PATH below with real values.
//
// What it does:
//   - Builds the "api" image (backend/Dockerfile) and the "web" image (nginx/Dockerfile)
//   - Tags each with the build number and "latest"
//   - Pushes both to your registry
//   - SSHes into the deploy host, pulls the new images, and restarts the stack
//     with zero manual steps

pipeline {
    agent any

    environment {
        REGISTRY_NAMESPACE = 'YOUR_DOCKERHUB_USERNAME'   // e.g. "palaraj"
        API_IMAGE  = "${REGISTRY_NAMESPACE}/mtt-api"
        WEB_IMAGE  = "${REGISTRY_NAMESPACE}/mtt-web"
        IMAGE_TAG  = "${env.BUILD_NUMBER}"

        DEPLOY_HOST = 'YOUR_SERVER_IP_OR_HOSTNAME'        // e.g. "203.0.113.10"
        DEPLOY_USER = 'deploy'                             // user on that server
        DEPLOY_PATH = '/opt/mother-teresa-transport'       // repo checkout location on that server
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Backend sanity check') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet -r backend/requirements.txt
                    python -m py_compile backend/app/*.py backend/app/routers/*.py
                '''
            }
        }

        stage('Build images') {
            steps {
                sh """
                    docker build -t ${API_IMAGE}:${IMAGE_TAG} -t ${API_IMAGE}:latest backend/
                    docker build -t ${WEB_IMAGE}:${IMAGE_TAG} -t ${WEB_IMAGE}:latest -f nginx/Dockerfile .
                """
            }
        }

        stage('Push images') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'REGISTRY_USER',
                    passwordVariable: 'REGISTRY_PASS'
                )]) {
                    sh '''
                        echo "$REGISTRY_PASS" | docker login -u "$REGISTRY_USER" --password-stdin
                        docker push '''+"${API_IMAGE}"+''':'''+"${IMAGE_TAG}"+'''
                        docker push '''+"${API_IMAGE}"+''':latest
                        docker push '''+"${WEB_IMAGE}"+''':'''+"${IMAGE_TAG}"+'''
                        docker push '''+"${WEB_IMAGE}"+''':latest
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                sshagent(credentials: ['deploy-ssh-key']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no ${DEPLOY_USER}@${DEPLOY_HOST} '
                            cd ${DEPLOY_PATH} &&
                            git pull origin main &&
                            REGISTRY_NAMESPACE=${REGISTRY_NAMESPACE} docker compose -f docker-compose.prod.yml pull &&
                            REGISTRY_NAMESPACE=${REGISTRY_NAMESPACE} docker compose -f docker-compose.prod.yml up -d --remove-orphans &&
                            docker image prune -f
                        '
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Deployed build #${env.BUILD_NUMBER} successfully."
        }
        failure {
            echo "Build #${env.BUILD_NUMBER} failed — check the stage logs above."
        }
        always {
            sh 'docker logout || true'
        }
    }
}
