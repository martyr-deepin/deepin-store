#!/bin/sh
cp ./dbus_script/com.linuxdeepin.softwarecenter.service /usr/share/dbus-1/system-services/ 
echo "Copy .service file to /usr/share/dbus-1/system-services/"

cp ./dbus_script/com.linuxdeepin.softwarecenter.policy /usr/share/polkit-1/actions/
echo "Copy .policy file to /usr/share/polkit-1/actions/"

cp ./dbus_script/com.linuxdeepin.softwarecenter.conf /etc/dbus-1/system.d/
echo "Copy .conf file to /etc/dbus-1/system.d/"

rm -f /usr/bin/deepin-software-center-backend.py
echo "Remove /usr/bin/deepin-software-center-backend.py"

chmod +x `pwd`/main.py
ln -s `pwd`/main.py /usr/bin/deepin-software-center-backend.py
echo "Build symbol link for service file"
