PLUGINNAME = mapbiomas-api
PLUGIN_FILES = $(PLUGINNAME)/* $(PLUGINNAME)/i18n/*

plugin: clean
	zip $(PLUGINNAME).zip $(PLUGIN_FILES)

clean:
	rm -f $(PLUGINNAME).zip

ts_macos: mapbiomas-api.pro
	/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3.8 -m PyQt5.pylupdate_main $(CURDIR)/mapbiomas-api.pro

ts_linux: mapbiomas-api.pro
	pylupdate5 mapbiomas-api.pro