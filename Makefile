PLUGINNAME = mapbiomas-api
PLUGIN_FILES = $(PLUGINNAME)/*

plugin: clean
	zip $(PLUGINNAME).zip $(PLUGIN_FILES)

clean:
	rm -f $(PLUGINNAME).zip