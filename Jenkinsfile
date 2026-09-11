// Jenkins pipeline for the Intelligent Test Planning Agent.
//
// Stages: checkout -> static checks -> import/unit smoke -> docker build ->
//         container smoke test -> push -> deploy.
//
// Credentials are pulled from the Jenkins credential store and never inlined.
// Configure these credential IDs in Jenkins before the first run:
//   - registry-credentials : username/password for the container registry
// The app needs no build-time secrets: Jira and LLM credentials are supplied
// by each user at runtime in the UI.

pipeline {
    agent any

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    environment {
        IMAGE_NAME   = 'test-planning-agent'
        REGISTRY     = "${env.DOCKER_REGISTRY ?: 'registry.gitlab.com/your-group/aiagentsqa'}"
        IMAGE_TAG    = "${env.BUILD_NUMBER}-${env.GIT_COMMIT?.take(7) ?: 'local'}"
        APP_PORT     = '8088'
        SMOKE_PORT   = '18088'   // separate port so a smoke test never collides with a running deployment
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                sh 'git --no-pager log -1 --oneline'
            }
        }

        stage('Static checks') {
            steps {
                // Compile every module: catches syntax errors before a build is
                // spent, and is the cheapest possible signal.
                sh '''
                    python3 -m compileall -q tools/
                    echo "All Python modules compile."
                '''
                // Fail the build if a credential pattern was committed.
                sh '''
                    if git grep -nIE "ATATT[A-Za-z0-9]{10,}|sk-ant-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}" -- . ; then
                        echo "ERROR: a credential-like string is committed."
                        exit 1
                    fi
                    echo "No committed credentials detected."
                '''
            }
        }

        stage('Import smoke test') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet --no-cache-dir -r requirements.txt
                    # Every tool module must import cleanly, and demo mode must
                    # return issues without any network access.
                    python - <<'PY'
import sys
sys.path.insert(0, "tools")
import server, jira_client, llm_generator, test_plan_exporter, test_connection
res = jira_client.fetch_jira_issues(host="demo")
assert res["status"] == "success", res
assert len(res["issues"]) == 3, res
assert all(i["key"].startswith("XSM") for i in res["issues"]), res
print(f"Demo fetch OK: {[i['key'] for i in res['issues']]}")
PY
                '''
            }
        }

        stage('Docker build') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Container smoke test') {
            steps {
                // Start the image and assert /health answers. Always tear the
                // container down, including on failure.
                sh """
                    docker rm -f ${IMAGE_NAME}-smoke || true
                    docker run -d --name ${IMAGE_NAME}-smoke -p ${SMOKE_PORT}:8088 ${IMAGE_NAME}:${IMAGE_TAG}
                    for i in \$(seq 1 30); do
                        if curl -fsS http://127.0.0.1:${SMOKE_PORT}/health > /dev/null 2>&1; then
                            echo "Health check passed after \${i}s"
                            curl -sS http://127.0.0.1:${SMOKE_PORT}/health
                            exit 0
                        fi
                        sleep 1
                    done
                    echo "Container failed to become healthy; logs follow:"
                    docker logs ${IMAGE_NAME}-smoke
                    exit 1
                """
            }
            post {
                always {
                    sh "docker rm -f ${IMAGE_NAME}-smoke || true"
                }
            }
        }

        stage('Push image') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'registry-credentials',
                    usernameVariable: 'REG_USER',
                    passwordVariable: 'REG_PASS'
                )]) {
                    // Single-quoted sh block so $REG_PASS is expanded by the
                    // shell, not interpolated by Groovy into the build log.
                    sh '''
                        set -e
                        REGISTRY_HOST="${REGISTRY%%/*}"
                        echo "$REG_PASS" | docker login "$REGISTRY_HOST" -u "$REG_USER" --password-stdin
                        docker tag "$IMAGE_NAME:$IMAGE_TAG" "$REGISTRY:$IMAGE_TAG"
                        docker tag "$IMAGE_NAME:$IMAGE_TAG" "$REGISTRY:latest"
                        docker push "$REGISTRY:$IMAGE_TAG"
                        docker push "$REGISTRY:latest"
                        docker logout "$REGISTRY_HOST"
                    '''
                }
            }
        }

        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                // Single-host deployment via compose. Swap this for your
                // orchestrator (kubectl / helm / ansible) if you move off a
                // single VM.
                sh """
                    APP_VERSION=${IMAGE_TAG} docker compose up -d --build
                    sleep 5
                    curl -fsS http://127.0.0.1:${APP_PORT}/health
                """
            }
        }
    }

    post {
        success {
            echo "Build ${IMAGE_TAG} succeeded."
        }
        failure {
            echo "Build ${IMAGE_TAG} FAILED - check the stage logs above."
        }
        always {
            // Reclaim disk on the agent; build images accumulate quickly.
            sh 'docker image prune -f || true'
            cleanWs()
        }
    }
}
