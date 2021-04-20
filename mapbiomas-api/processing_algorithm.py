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


import requests
from qgis.core import (QgsCoordinateReferenceSystem, QgsFeature, QgsField,
                       QgsFields, QgsGeometry, QgsProcessingAlgorithm,
                       QgsProcessingException, QgsProcessingParameterBoolean,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterMapLayer, QgsWkbTypes)
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from .mapbiomas_api import alertReport


class PullAlertData(QgsProcessingAlgorithm):
    """
    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_LAYER = 'INPUT_LAYER'
    ONLY_SELECTED = 'ONLY_SELECTED'
    FIELD_ALERTCODE = 'FIELD_ALERTCODE'
    FIELD_CARID = 'FIELD_CARID'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('PullAlertData', string)

    def createInstance(self):
        return PullAlertData()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'pullalertdata'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Pull alert report data')

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Pull the data from the alert report")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # INPUTS
        self.addParameter(QgsProcessingParameterMapLayer(self.INPUT_LAYER, self.tr('Alerts layer')))
        self.addParameter(QgsProcessingParameterBoolean(self.ONLY_SELECTED, self.tr('Only selected features')))
        self.addParameter(QgsProcessingParameterField(self.FIELD_ALERTCODE, self.tr('Alert Code Field'), None, self.INPUT_LAYER, type=QgsProcessingParameterField.String))
        self.addParameter(QgsProcessingParameterField(self.FIELD_CARID, self.tr('CAR Id Field'), None, self.INPUT_LAYER, type=QgsProcessingParameterField.String, optional = True))

        # OUTPUT
        self.addParameter(QgsProcessingParameterFeatureSink(self.OUTPUT,self.tr('Output layer')))

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        def get_fields():
            f = QgsFields()
            f.append(QgsField('alertareaincar', QVariant.Double))
            f.append(QgsField('alertcode', QVariant.String))
            f.append(QgsField('areaha', QVariant.Double))
            f.append(QgsField('carcode', QVariant.String))
            f.append(QgsField('images_before_acquiredat', QVariant.DateTime))
            f.append(QgsField('images_before_satellite', QVariant.String))
            f.append(QgsField('images_before_url', QVariant.Url))
            f.append(QgsField('images_after_acquiredat', QVariant.DateTime))
            f.append(QgsField('images_after_satellite', QVariant.String))
            f.append(QgsField('images_after_url', QVariant.Url))
            f.append(QgsField('images_alertinproperty', QVariant.Url))
            f.append(QgsField('images_propertyinstate', QVariant.Url))
            f.append(QgsField('intersections_conservationunits_area', QVariant.Double))
            f.append(QgsField('intersections_deforestmentsauthorized_area', QVariant.Double))
            f.append(QgsField('intersections_forestmanagements_area', QVariant.Double))
            f.append(QgsField('intersections_indigenouslands_area', QVariant.Double))
            f.append(QgsField('intersections_settlements_area', QVariant.Double))
            f.append(QgsField('intersections_withruralproperty_embargoes_area', QVariant.Double))
            f.append(QgsField('intersections_withruralproperty_legalreserves_area', QVariant.Double))
            f.append(QgsField('intersections_withruralproperty_permanentprotected_area', QVariant.Double))
            f.append(QgsField('intersections_withruralproperty_riversources_count', QVariant.Int))
            f.append(QgsField('simplifiedpoints_imageurl', QVariant.Url))
            f.append(QgsField('simplifiedpoints_table', QVariant.String))
            f.append(QgsField('changes_labels', QVariant.String))
            for year in range(1985, 2019):
                f.append(QgsField('changes_' + str(year), QVariant.Url)) 
            f.append(QgsField('bioma', QVariant.String))
            f.append(QgsField('estado', QVariant.String))
            f.append(QgsField('municipio', QVariant.String))
            f.append(QgsField('source', QVariant.String))

            return f

        def get_feature(f, d):
            feat = QgsFeature(f)
            wkt = d.pop('alertgeomwkt')
            for k in d.keys():
                try:
                    feat.setAttribute(k, d[k])
                except KeyError:
                    pass
            
            feat.setGeometry(QgsGeometry.fromWkt(wkt))

            return feat

        # Retrieve the values of the input parameters

        input_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LAYER, context)
        only_selected = self.parameterAsBool(parameters, self.ONLY_SELECTED, context)
        field_alertcode = self.parameterAsString(parameters, self.FIELD_ALERTCODE, context)
        field_carid = self.parameterAsString(parameters, self.FIELD_CARID, context)

        # define output fields
        fields = get_fields()

        # open output sink
        (sink, output_file) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, QgsWkbTypes.MultiPolygon, QgsCoordinateReferenceSystem(4674))

        # test for error in sink
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # check if it is canceled before any processing
        if feedback.isCanceled():
            return {}

        #  get input features
        if only_selected:
            total = input_layer.selectedFeatureCount()
            features = input_layer.selectedFeatures()
        else:
            total = input_layer.featureCount()
            features = input_layer.getFeatures()

        # test input
        if not total:
            feedback.reportError(self.tr('No features'))
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_LAYER))

        # info user
        feedback.setProgressText(self.tr('Getting data for {} alert(s)').format(total))
        
        with requests.Session() as s:
            for i, feature in enumerate(features):
                # Stop if cancel button has been clicked
                if feedback.isCanceled():
                    break
    
                # Get Alert Code
                alertcode = int(feature[field_alertcode])
    
                # Read CAR IDs
                carids = feature[field_carid] if field_carid else ''
    
                if carids:
                    for carid in carids.split(', '):
                        # Read report data for each CAR
                        (data, err) = alertReport.get({'alertId': alertcode, 'carId': int(carid)}, session=s)
                        # Add a feature in the sink
                        if err is None:
                            outfeat = get_feature(fields, data)
                            sink.addFeature(outfeat)
                        else:
                            feedback.setProgressText('Error getting data for Alert Code {} / CAR Id {}'.format(alertcode, carid))
                            feedback.reportError(err)
                else:
                    # Read report data without CAR
                    (data, err) = alertReport.get({'alertId': alertcode}, session=s)
                    # Add a feature in the sink
                    if err is None:
                        outfeat = get_feature(fields, data)
                        sink.addFeature(outfeat)
                    else:
                        feedback.setProgressText('Error getting data for Alert Code {}'.format(alertcode))
                        feedback.reportError(err)
    
                # Update the progress bar
                percent = (i + 1) / total * 100
                feedback.setProgress(percent)

            sink.flushBuffer()

        return {self.OUTPUT: output_file}
