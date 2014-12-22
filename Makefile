PREFIX = /usr

all:
	cd tools; ./generate_mo.py; cd ..
	pycompile ui pkg_manager

install:
	mkdir -p ${DESTDIR}${PREFIX}/bin
	mkdir -p ${DESTDIR}${PREFIX}/share/applications
	mkdir -p ${DESTDIR}${PREFIX}/share/deepin-software-center
	mkdir -p ${DESTDIR}${PREFIX}/share/dbus-1/system-services
	mkdir -p ${DESTDIR}${PREFIX}/share/polkit-1/actions
	mkdir -p ${DESTDIR}${PREFIX}/share/dbus-1/services
	mkdir -p ${DESTDIR}${PREFIX}/share/icons/hicolor/scalable/apps
	mkdir -p ${DESTDIR}/etc/dbus-1/system.d
	cp -r app_theme pkg_manager ui image wizard skin mirrors \
	  ${DESTDIR}${PREFIX}/share/deepin-software-center
	cp -r locale/mo ${DESTDIR}${PREFIX}/share/locale
	cp pkg_manager/apt/dbus_script/com.linuxdeepin.softwarecenter.service ${DESTDIR}${PREFIX}/share/dbus-1/system-services
	cp pkg_manager/apt/dbus_script/com.linuxdeepin.softwarecenter.policy ${DESTDIR}${PREFIX}/share/polkit-1/actions
	cp pkg_manager/apt/dbus_script/com.linuxdeepin.softwarecenter.conf ${DESTDIR}/etc/dbus-1/system.d
	cp com.linuxdeepin.softwarecenter_frontend.service ${DESTDIR}${PREFIX}/share/dbus-1/services
	cp image/deepin-software-center.svg ${DESTDIR}${PREFIX}/share/icons/hicolor/scalable/apps
	cp deepin-software-center.desktop ${DESTDIR}${PREFIX}/share/applications
	ln -sf ${PREFIX}/share/deepin-software-center/pkg_manager/apt/main.py ${DESTDIR}${PREFIX}/bin/deepin-software-center-backend.py
	ln -sf ${PREFIX}/share/deepin-software-center/ui/main.py ${DESTDIR}${PREFIX}/bin/deepin-software-center
	ln -sf ${PREFIX}/share/deepin-software-center/ui/dsc-daemon.py ${DESTDIR}${PREFIX}/bin/dsc-daemon
	make -C dapt install
