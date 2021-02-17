# -*- coding: utf-8 -*-

# Copyright (c) 2021 Sandro Klippel

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import os
from tempfile import NamedTemporaryFile

from qgis.core import Qgis, QgsMessageLog, QgsProject, QgsVectorLayer
from qgis.PyQt.QtCore import QDate, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

from .dockmapbiomasapi import DockMapBiomasApi
from .mapbiomas_api import MapbiomasApi, allPublishedAlerts, allTerritories

__author__ = "Sandro Klippel"
__copyright__ = "Copyright 2021, Sandro Klippel"
__license__ = "GPLv3"
__version__ = "0.1.0"
__maintainer__ = "Sandro Klippel"
__email__ = "sandroklippel at gmail.com"
__status__ = "Prototype"
__revision__ = '$Format:%H$'


class QgisMapBiomasAPI:
    """Plugin implementation
    """    

    def __init__(self, iface):
        """
        Constructor

        Args:
            iface (qgis.gui.QgisInterface): a reference to the QGIS GUI interface
        """        
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.dockwidget = None
        self.action = None
        self.name = 'MapBiomas API'
        self.about = 'MapBiomas API for QGIS'
        self.token = None
        self.biome = None
        self.state = None

    def initGui(self):
        """
        This method is called by QGIS when the main GUI starts up or 
        when the plugin is enabled in the Plugin Manager.
        Only want to register the menu items and toolbar buttons here,
        and connects action with run method.
        """ 
        
        icon = QIcon(os.path.join(self.plugin_dir, 'icon.png'))
        self.action = QAction(icon, self.name, self.iface.mainWindow())
        self.action.setWhatsThis(self.about)
        self.action.setStatusTip(self.about)
        self.action.setCheckable(True)
        self.action.triggered.connect(self.run)

        # for plugin menu/toolbar
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.name, self.action)

    def unload(self):
        """
        Will be executed when the plugin is disabled. 
        Either in the Plugin Manager or when QGIS shuts down.
        It removes the previously defined QAction object from
        the menu and remove the plugin icon from the toolbar.
        """

        # for plugin menu/toolbar
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu(self.name, self.action)

        if self.dockwidget is not None:
            # disconnect triggers here
            self.dockwidget.pushButton.clicked.disconnect(self.do_something)
            self.dockwidget.checkBoxStartDetected.toggled[bool].disconnect(self.dockwidget.startDetectedAt.setEnabled)
            self.dockwidget.checkBoxEndDetected.toggled[bool].disconnect(self.dockwidget.endDetectedAt.setEnabled)
            self.dockwidget.checkBoxStartPublished.toggled[bool].disconnect(self.dockwidget.startPublishedAt.setEnabled)
            self.dockwidget.checkBoxEndPublished.toggled[bool].disconnect(self.dockwidget.endPublishedAt.setEnabled)
            self.dockwidget.close()
            self.dockwidget.visibilityChanged.disconnect(self.visibility_changed)
            self.iface.removeDockWidget(self.dockwidget)
            del self.dockwidget

    def run(self):
        """
        Executes the custom plugin functionality.
        This method is called by the previously defined QAction object (callback), 
        which went into the toolbar icon and the menu entry.
        """
        if self.dockwidget is None:
            self.dockwidget = DockMapBiomasApi()
            self.iface.addDockWidget(Qt.LeftDockWidgetArea , self.dockwidget)
            self.dockwidget.visibilityChanged.connect(self.visibility_changed)
            self.init()
            self.dockwidget.show()
        else:
            if self.dockwidget.isVisible():
                self.dockwidget.hide()
            else:
                self.dockwidget.show()

    def visibility_changed(self, change):
        """
        Change icon checked status with dockwidget visibility
        """
        self.action.setChecked(change)

    def info(self, msg, level=Qgis.Info, duration=5):
        """
        docstring
        """
        self.iface.messageBar().pushMessage(msg, level, duration)

    def log(self, msg, level=Qgis.Info):
        """
        docstring
        """
        QgsMessageLog.logMessage(msg, self.name, level)

    def sign_in(self):
        """
        Creation of an access token in the JWT standard 
        to be used in the Authorization header and
        populate BIOME and STATE if empty
        """

        err = None

        email = self.dockwidget.email.text()
        password = self.dockwidget.password.text()

        if password and email:
            try:
                self.token, err = MapbiomasApi.token({"email": email, "password": password})
            except Exception as e:
                err = str(e)
            if self.token is not None:
                if self.biome is None:
                    self.biome, err = allTerritories.get(self.token, {"category": "BIOME"})
                if self.state is None:
                    self.state, err = allTerritories.get(self.token, {"category": "STATE"})
        else:
            err = 'Email and password are required.'
        
        return err

    def get_alerts(self):

        filters = {}
        territories = []

        if self.dockwidget.BIOME.count:
            territories.extend([self.biome[k] for k in self.dockwidget.BIOME.checkedItems()])

        if self.dockwidget.STATE.count:
            territories.extend([self.state[k] for k in self.dockwidget.STATE.checkedItems()])

        if territories:
            filters["territoryIds"] = territories
        
        if self.dockwidget.checkBoxStartDetected.isChecked():
            filters["startDetectedAt"] = self.dockwidget.startDetectedAt.date().toString('yyyy-MM-dd')

        if self.dockwidget.checkBoxEndDetected.isChecked():
            filters["endDetectedAt"] = self.dockwidget.endDetectedAt.date().toString('yyyy-MM-dd')

        if self.dockwidget.checkBoxStartPublished.isChecked():
            filters["startPublishedAt"] = self.dockwidget.startPublishedAt.date().toString('yyyy-MM-dd')

        if self.dockwidget.checkBoxEndPublished.isChecked():
            filters["endPublishedAt"] = self.dockwidget.endPublishedAt.date().toString('yyyy-MM-dd')

        try:
            data, err = allPublishedAlerts.get(self.token, filters)
        except Exception as e:
            err = str(e)
        if err is None:
            with NamedTemporaryFile("w+t", prefix="alerts_", suffix=".geojson", delete=False) as outfile:
                json.dump(data, outfile)
                fn = outfile.name
            # add vector layer
            layer = QgsVectorLayer(fn, 'MapBiomasAPI', 'ogr')
            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
            else:
                self.log("Invalid layer file: {}".format(fn))
                self.info("Unknown error. Invalid layer. Try it again.", level=Qgis.Critical)
        elif err == 'Você não tem permissão para realizar esta ação':
            self.dockwidget.pushButton.setText('SIGN IN')
            self.dockwidget.options.setDisabled(True)
            self.dockwidget.mGroupBox.setCollapsed(False)
            self.info("The session has expired. Sign in again.", level=Qgis.Critical)
        else:
            self.info(err, level=Qgis.Critical)

    def do_something(self):
        """Sign in or get alerts
        """
        if self.dockwidget.pushButton.text() == 'SIGN IN':
            err = self.sign_in()
            if err is None:
                self.dockwidget.BIOME.addItems(self.biome.keys())
                self.dockwidget.STATE.addItems(self.state.keys())
                self.dockwidget.pushButton.setText('GET ALERTS')
                self.dockwidget.options.setEnabled(True)
                self.dockwidget.mGroupBox.setCollapsed(True)
            else:
                self.info(err, level=Qgis.Critical)
        else:
            self.get_alerts()

    def init(self):
        """
        Fill options, default values and connect triggers of the dockwidget
        """

        # connect triggers
        self.dockwidget.pushButton.clicked.connect(self.do_something)
        self.dockwidget.checkBoxStartDetected.toggled[bool].connect(self.dockwidget.startDetectedAt.setEnabled)
        self.dockwidget.checkBoxEndDetected.toggled[bool].connect(self.dockwidget.endDetectedAt.setEnabled)
        self.dockwidget.checkBoxStartPublished.toggled[bool].connect(self.dockwidget.startPublishedAt.setEnabled)
        self.dockwidget.checkBoxEndPublished.toggled[bool].connect(self.dockwidget.endPublishedAt.setEnabled)

        # set defaults
        self.dockwidget.endDetectedAt.setDate(QDate.currentDate())
        self.dockwidget.endPublishedAt.setDate(QDate.currentDate())
