#!/bin/sh
cd `dirname $0`
rm -f /usr/bin/dsc-daemon
ln -s `pwd`/dsc-daemon.py /usr/bin/dsc-daemon
echo "Build symbol link for dsc-daemon"

cp ./deepin-software-center-autostart.desktop /etc/xdg/autostart/
echo "Copy auto start script to /etc/xdg/autostart/"
