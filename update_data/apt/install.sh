#!/bin/sh
cp ./dbus_script/com.linuxdeepin.softwarecenter_updater.service /usr/share/dbus-1/system-services/ 
echo "Copy .service file to /usr/share/dbus-1/system-services/"

cp ./dbus_script/com.linuxdeepin.softwarecenter_updater.policy /usr/share/polkit-1/actions/
echo "Copy .policy file to /usr/share/polkit-1/actions/"

cp ./dbus_script/com.linuxdeepin.softwarecenter_updater.conf /etc/dbus-1/system.d/
echo "Copy .conf file to /etc/dbus-1/system.d/"

rm -f /usr/bin/deepin-software-center-updater.py
echo "Remove /usr/bin/deepin-software-center-updater.py"

chmod +x `pwd`/main.py
ln -s `pwd`/main.py /usr/bin/deepin-software-center-updater.py
echo "Build symbol link for service file"

cp ./deepin-software-center-autostart.desktop /etc/xdg/autostart/
echo "Copy auto start script to /etc/xdg/autostart/"
