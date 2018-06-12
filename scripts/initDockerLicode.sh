#!/usr/bin/env bash
SCRIPT=`pwd`/$0
ROOT=/opt/licode
SCRIPTS="$ROOT"/scripts
BUILD_DIR="$ROOT"/build
DB_DIR="$BUILD_DIR"/db
EXTRAS="$ROOT"/extras
NVM_CHECK="$ROOT"/scripts/checkNvm.sh

parse_arguments(){
  if [ -z "$1" ]; then
    echo "No parameters -- starting everything"
    MONGODB=true
    RABBITMQ=true
    NUVE=true
    ERIZOCONTROLLER=true
    ERIZOAGENT=true
    BASICEXAMPLE=true

  else
    while [ "$1" != "" ]; do
      case $1 in
        "--mongodb")
        MONGODB=true
        ;;
        "--rabbitmq")
        RABBITMQ=true
        ;;
        "--nuve")
        NUVE=true
        ;;
        "--erizoController")
        ERIZOCONTROLLER=true
        ;;
        "--erizoAgent")
        ERIZOAGENT=true
        ;;
        "--basicExample")
        BASICEXAMPLE=true
        ;;
      esac
      shift
    done
  fi
}

run_nvm() {
  echo "Running NVM"
  . $ROOT/build/libdeps/nvm/nvm.sh

}
check_result() {
  if [ "$1" -eq 1 ]
  then
    exit 1
  fi
}
run_rabbitmq() {
  echo "Starting Rabbitmq"
  rabbitmq-server -detached
  sleep 3
}

create_superservice() {
  dbURL=`grep "config.nuve.dataBaseURL" $SCRIPTS/licode_default.js`

  dbURL=`echo $dbURL| cut -d'"' -f 2`
  dbURL=`echo $dbURL| cut -d'"' -f 1`

  echo [licode] Creating superservice in $dbURL
  
  {
    NUVEDB=$(mongo $dbURL --quiet --eval "printjson(db.adminCommand( 'listDatabases' ))" | grep "nuvedb")
  } || {
    NUVEDB=""
  }

  if [ ! -z "$NUVE_ID" ] && [ ! -z "$NUVE_KEY" ]; then
    if [ ! -z "$NUVEDB" ]; then
     SERVID=`mongo $dbURL --quiet --eval "db.services.findOne()._id"`
     SERVKEY=`mongo $dbURL --quiet --eval "db.services.findOne().key"`
     SERVID=`echo $SERVID| cut -d'"' -f 2`
     SERVID=`echo $SERVID| cut -d'"' -f 1`

     if [ "$SERVID" = "$NUVE_ID" ] && [ "$SERVKEY" = "$NUVE_KEY" ] ; then
       echo [licode] Using SuperService ID: "$NUVE_ID" and key: "$NUVE_KEY" that matched existing ones.
       SERVID="$NUVE_ID"
       SERVKEY="$NUVE_KEY"
     else
       echo [licode] ERROR: Found existing ID of "$SERVID" and key "$SERVKEY", which do not match the passed ID: "$NUVE_ID" and key: "$NUVE_KEY"
       exit 1
    fi
    else
      echo [licode] No existing nuvedb detected. Will set the passed in values of SuperService ID: "$NUVE_ID" and key: "$NUVE_KEY"
      SERVID="$NUVE_ID"
      SERVKEY="$NUVE_KEY"
      {
      mongo $dbURL --eval "db.services.insert({_id: ObjectId('$NUVE_ID'), name: 'superService', key: '$NUVE_KEY', rooms: []})"
      } ||
      {
        echo [licode] ERROR: Unable to create nuve database in mongo. Check that mongo is running and accessible.
        exit 1
      }
    fi
  else
    mongo $dbURL --eval "db.services.insert({name: 'superService', key: '$RANDOM', rooms: []})"
    SERVID=`mongo $dbURL --quiet --eval "db.services.findOne()._id"`
    SERVKEY=`mongo $dbURL --quiet --eval "db.services.findOne().key"`
    SERVID=`echo $SERVID| cut -d'"' -f 2`
    SERVID=`echo $SERVID| cut -d'"' -f 1`
  fi

  echo [licode] SuperService ID "$SERVID"
  echo [licode] SuperService KEY "$SERVKEY"
  cd $BUILD_DIR
  replacement=s/_auto_generated_ID_/${SERVID}/
  sed $replacement $SCRIPTS/licode_default.js > $BUILD_DIR/licode_1.js
  replacement=s/_auto_generated_KEY_/${SERVKEY}/
  sed $replacement $BUILD_DIR/licode_1.js > $ROOT/licode_config.js
  rm $BUILD_DIR/licode_1.js

}
run_nuve() {
  create_superservice

  echo "Starting Nuve"
  cd $ROOT/nuve/nuveAPI
  node nuve.js &
  sleep 5
}
run_erizoController() {
  echo "Starting erizoController"
  cd $ROOT/erizo_controller/erizoController
  node erizoController.js &
}
run_erizoAgent() {
  echo "Starting erizoAgent"
  cd $ROOT/erizo_controller/erizoAgent
  node erizoAgent.js &
}
run_basicExample() {
  echo "Starting basicExample"
  sleep 5
  cp $ROOT/erizo_controller/erizoClient/dist/erizo.js $EXTRAS/basic_example/public/
  cp $ROOT/nuve/nuveClient/dist/nuve.js $EXTRAS/basic_example/
  cd $EXTRAS/basic_example
  node basicServer.js &
}

parse_arguments $*

cd $ROOT/scripts

run_nvm
nvm use

#if [ "$MONGODB" = "true" ]; then
#  run_mongo
#fi

#if [ "$RABBITMQ" = "true" ]; then
#  run_rabbitmq
#fi

if [ ! -f "$ROOT"/licode_config.js ]; then
    cp "$SCRIPTS"/licode_default.js "$ROOT"/licode_config.js
fi

if [ "$ERIZOAGENT" = "true" ] || [ "$ERIZOCONTROLLER" = "true" ] || [ "$NUVE" = "true" ] ; then
  if [ ! -z "$NUVE_ID" ] && [ ! -z "$NUVE_KEY" ]; then 
      echo "config.nuve.superserviceID = '$NUVE_ID';" >> /opt/licode/licode_config.js
      echo "config.nuve.superserviceKey= '$NUVE_KEY';" >> /opt/licode/licode_config.js
  fi
  if [ ! -z "$RABBIT_URL" ]; then 
      echo "config.rabbit.url = '$RABBIT_URL';" >> /opt/licode/licode_config.js
  fi
fi

if [ "$NUVE" = "true" ]; then
  run_nuve
fi

if [ "$ERIZOCONTROLLER" = "true" ]; then
  if [ ! -z "$ERIZO_CONTROLLER_IP" ]
  then 
    echo "config.erizoController.publicIP = '$ERIZO_CONTROLLER_IP';" >> /opt/licode/licode_config.js
  fi

  if [ ! -z "$ERIZO_PORT" ]
  then 
    echo "config.erizoController.port = '$ERIZO_PORT';" >> /opt/licode/licode_config.js
  fi
  if [ ! -z "$ERIZO_SSL" ]
  then 
    echo "config.erizoController.ssl = '$ERIZO_SSL';" >> /opt/licode/licode_config.js
  fi
  if [ ! -z "$ERIZO_LISTEN_SSL" ]
  then 
    echo "config.erizoController.listen_ssl = '$ERIZO_LISTEN_SSL';" >> /opt/licode/licode_config.js
  fi
  if [ ! -z "$ERIZO_LISTEN_PORT" ]
  then 
    echo "config.erizoController.listen_port = '$ERIZO_LISTEN_PORT';" >> /opt/licode/licode_config.js
  fi
  if [ ! -z "$TURN_USERNAME" ] && [ ! -z "$TURN_CRED" ] && [ ! -z "$PUBLIC_IP" ] ; then
    echo "config.erizoController.iceServers = [{\"url\":\"stun:'$PUBLIC_IP':3478\"}, {\"username\":\"'$TURN_USERNAME'\",\"url\":\"turn:'$PUBLIC_IP':3478\",\"credential\":\"'$TURN_CRED'\"}, {\"username\":\"'$TURN_USERNAME'\",\"url\":\"turn:'$PUBLIC_IP':5349\",\"credential\":\"'$TURN_CRED'\"}]" >> /opt/licode/licode_config.js
  fi
  run_erizoController
fi

if [ "$ERIZOAGENT" = "true" ]; then
  if [ ! -z "$ERIZO_AGENT_IP"  ]
  then
    echo "config.erizoAgent.publicIP = '$ERIZO_AGENT_IP';" >> /opt/licode/licode_config.js
  fi

  echo "config.erizo.minport = '$MIN_PORT';" >> /opt/licode/licode_config.js
  echo "config.erizo.maxport = '$MAX_PORT';" >> /opt/licode/licode_config.js
  run_erizoAgent
fi

wait
