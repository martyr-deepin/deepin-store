#!/bin/sh
cd `dirname $0`
cp ./dbus_script/com.linuxdeepin.softwarecenterupdater.service /usr/share/dbus-1/system-services/
echo "Copy .service file to /usr/share/dbus-1/system-services/"

cp ./dbus_script/com.linuxdeepin.softwarecenterupdater.policy /usr/share/polkit-1/actions/
echo "Copy .policy file to /usr/share/polkit-1/actions/"

cp ./dbus_script/com.linuxdeepin.softwarecenterupdater.conf /etc/dbus-1/system.d/
echo "Copy .conf file to /etc/dbus-1/system.d/"

rm -f /usr/bin/deepin-software-center-updater.py
echo "Remove /usr/bin/deepin-software-center-updater.py"

chmod +x `pwd`/update-data.py
ln -s `pwd`/update-data.py /usr/bin/deepin-software-center-updater.py
echo "Build symbol link for update-data.py"

rm -f /usr/bin/deepin-software-center-start-updater.py
ln -s `pwd`/start_updater.py /usr/bin/deepin-software-center-start-updater.py
echo "Build symbol link for start_updater.py"

cp ./deepin-software-center-autostart.desktop /etc/xdg/autostart/
echo "Copy auto start script to /etc/xdg/autostart/"
