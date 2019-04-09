// Templated from ConversationalAgentApi's Jenkinsfile
// Properties configure Jenkins plugins and other built in behavior
properties([
  // Throw away old builds that we don't need
  buildDiscarder([
    $class: 'EnhancedOldBuildDiscarder',
    numToKeepStr: '10',
    daysToKeepStr: '30',
    discardOnlyOnSuccess: true,
    artifactDaysToKeepStr: '',
    artifactNumToKeepStr: '',
  ]),
])

// All of our stages are designed to run in docker containers.
// This means that the only requirement for our build agent is
// a *nix box that can run bash scripts and has Docker installed.
// We use the 'docker' tag to express this requirment.
node('Scribe_Centos_01') {

    try{
        // Produces a docker image (using `docker build`) that contains the compiled
        // distribution files for the project, as well as acting as a production image
        stage('Build') {
            checkout scm
            //sh 'cd scripts; python -u service_detect.py --default_tag default-CI build'
            sh cd scripts; python -u service_detect.py --default_tag default-CI --dockerfile ./docker/agent/Dockerfile --servicename licode-agent --workingdir .. build'
            stash includes: '*.tar', name: 'dockerImage'
            stash includes: '*.id', name: 'dockerID'
        }
        
        stage('Publish'){
            checkout scm
            unstash 'dockerID'
            sh 'cd scripts; python -u service_detect.py --default_tag default-CI publish'
        }
  
        stage('Deploy'){
            //checkout scm
            //unstash 'dockerImage'
            //sh 'cd scripts; python -u service_detect.py --default_tag default-CI deploy'
        }    

    }    
    finally{
        stage('Cleanup'){
            unstash 'dockerID'
            sh 'cd scripts; python -u service_detect.py cleanup'
        }
    }
}
