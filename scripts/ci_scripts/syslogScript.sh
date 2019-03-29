#!/bin/bash

if [ ! -f "/etc/rsyslog.d/10-${1}.conf" ]; then echo "Syslog rule not found, adding it.";
    sudo sh -c "echo \":syslogtag,startswith,\\\"${1}\\\" /var/log/scribe/${1}.log\n& stop\" > /etc/rsyslog.d/10-${1}.conf";
fi
