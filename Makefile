PREFIX=$(CURDIR)/debian/

install: python-cyberfusion-borg-support

python-cyberfusion-borg-support: PKGNAME	:= python-cyberfusion-borg-support
python-cyberfusion-borg-support: PKGPREFIX	:= $(PREFIX)/$(PKGNAME)
python-cyberfusion-borg-support: SDIR		:= python

python-cyberfusion-borg-support:
	rm -rf $(CURDIR)/build
	python3 setup.py install --force --root=$(PKGPREFIX) --no-compile -O0 --install-layout=deb

clean:
	rm -rf $(PREFIX)/python-cyberfusion-borg-support/
	rm -rf $(PREFIX)/*debhelper*
	rm -rf $(PREFIX)/*substvars
	rm -rf $(PREFIX)/files
	rm -rf $(CURDIR)/build
	rm -rf $(CURDIR)/src/*.egg-info
