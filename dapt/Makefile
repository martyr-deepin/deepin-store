PREFIX = /usr

all:

install:
	mkdir -p ${DESTDIR}${PREFIX}/lib/deepin-store
	mkdir -p ${DESTDIR}${PREFIX}/share/dbus-1/system-services
	mkdir -p ${DESTDIR}/etc/dbus-1/system.d
	cp main.py ${DESTDIR}${PREFIX}/lib/deepin-store/deepin-store-backend
	cp conf/com.deepin.store.Api.service ${DESTDIR}${PREFIX}/share/dbus-1/system-services
	cp conf/com.deepin.store.Api.conf ${DESTDIR}/etc/dbus-1/system.d
