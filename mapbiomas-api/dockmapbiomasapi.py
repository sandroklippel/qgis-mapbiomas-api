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


from qgis.PyQt import QtWidgets
from .dockmapbiomasapi_ui import Ui_DockMapBiomasApi


class DockMapBiomasApi(QtWidgets.QDockWidget, Ui_DockMapBiomasApi):

    def __init__(self, parent=None):

        super(DockMapBiomasApi, self).__init__(parent)
        self.setupUi(self)