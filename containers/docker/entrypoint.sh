#!/bin/bash
echo "student:${USER_PASSWORD}" | chpasswd
exec /usr/sbin/sshd -D
