<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.16.4-Hannover" styleCategories="Symbology|Actions">
  <renderer-v2 enableorderby="0" type="singleSymbol" symbollevels="0" forceraster="0">
    <symbols>
      <symbol alpha="0.2" name="0" type="fill" force_rhr="0" clip_to_extent="1">
        <layer class="SimpleFill" pass="0" enabled="1" locked="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="228,26,28,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="255,14,16,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="2"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <effect type="effectStack" enabled="0">
            <effect type="dropShadow">
              <prop k="blend_mode" v="13"/>
              <prop k="blur_level" v="2.645"/>
              <prop k="blur_unit" v="MM"/>
              <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="0,0,0,255"/>
              <prop k="draw_mode" v="2"/>
              <prop k="enabled" v="0"/>
              <prop k="offset_angle" v="135"/>
              <prop k="offset_distance" v="2"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="offset_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="opacity" v="1"/>
            </effect>
            <effect type="outerGlow">
              <prop k="blend_mode" v="0"/>
              <prop k="blur_level" v="0.7935"/>
              <prop k="blur_unit" v="MM"/>
              <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color1" v="0,0,255,255"/>
              <prop k="color2" v="0,255,0,255"/>
              <prop k="color_type" v="0"/>
              <prop k="discrete" v="0"/>
              <prop k="draw_mode" v="2"/>
              <prop k="enabled" v="0"/>
              <prop k="opacity" v="0.5"/>
              <prop k="rampType" v="gradient"/>
              <prop k="single_color" v="255,255,255,255"/>
              <prop k="spread" v="2"/>
              <prop k="spread_unit" v="MM"/>
              <prop k="spread_unit_scale" v="3x:0,0,0,0,0,0"/>
            </effect>
            <effect type="blur">
              <prop k="blend_mode" v="0"/>
              <prop k="blur_level" v="2.645"/>
              <prop k="blur_method" v="0"/>
              <prop k="blur_unit" v="MM"/>
              <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="draw_mode" v="2"/>
              <prop k="enabled" v="1"/>
              <prop k="opacity" v="1"/>
            </effect>
            <effect type="innerShadow">
              <prop k="blend_mode" v="13"/>
              <prop k="blur_level" v="2.645"/>
              <prop k="blur_unit" v="MM"/>
              <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color" v="0,0,0,255"/>
              <prop k="draw_mode" v="2"/>
              <prop k="enabled" v="0"/>
              <prop k="offset_angle" v="135"/>
              <prop k="offset_distance" v="2"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="offset_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="opacity" v="1"/>
            </effect>
            <effect type="innerGlow">
              <prop k="blend_mode" v="0"/>
              <prop k="blur_level" v="0.7935"/>
              <prop k="blur_unit" v="MM"/>
              <prop k="blur_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="color1" v="0,0,255,255"/>
              <prop k="color2" v="0,255,0,255"/>
              <prop k="color_type" v="0"/>
              <prop k="discrete" v="0"/>
              <prop k="draw_mode" v="2"/>
              <prop k="enabled" v="0"/>
              <prop k="opacity" v="0.5"/>
              <prop k="rampType" v="gradient"/>
              <prop k="single_color" v="255,255,255,255"/>
              <prop k="spread" v="2"/>
              <prop k="spread_unit" v="MM"/>
              <prop k="spread_unit_scale" v="3x:0,0,0,0,0,0"/>
            </effect>
          </effect>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" type="QString" value=""/>
              <Option name="properties"/>
              <Option name="type" type="QString" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
    <actionsetting name="Abrir laudo do alerta (web)" icon="" capture="0" type="1" id="{5e284694-42a2-4012-8551-26c963a406c5}" shortTitle="Abrir laudo do alerta (web)" action="import webbrowser&#xa;&#xa;try:&#xa;    web = webbrowser.get('google-chrome')&#xa;except webbrowser.Error:&#xa;    web = webbrowser.get()&#xa;&#xa;cars = '[%carId%]'&#xa;&#xa;web.open_new_tab('https://plataforma.alerta.mapbiomas.org/laudos/[%alertCode%]/')&#xa;if cars:&#xa;    for car in cars.split(', '):&#xa;        web.open_new_tab('https://plataforma.alerta.mapbiomas.org/laudos/[%alertCode%]/car/{}/'.format(car))" notificationMessage="" isEnabledOnlyWhenEditable="0">
      <actionScope id="Feature"/>
    </actionsetting>
    <actionsetting name="Puxar dados do laudo do alerta" icon="" capture="0" type="1" id="{a6a0b8e9-04c5-4abc-ba94-e4f69fea8fe8}" shortTitle="Puxar dados do laudo do alerta" action="from qgis import processing, utils&#xa;from qgis.core import Qgis, QgsApplication, QgsProject&#xa;&#xa;if QgsApplication.processingRegistry().algorithmById('mapbiomas-api:pullalertdata') is None:&#xa;    utils.iface.messageBar().pushMessage('Complemento MapBiomas API não está carregado', level=Qgis.Critical) # MapBiomas API plugin is not loaded&#xa;else:&#xa;    p = QgsProject.instance()&#xa;    layer = p.mapLayer('[% @layer_id %]')&#xa;    if layer.selectedFeatureCount() > 0:&#xa;        result = processing.run(&quot;mapbiomas-api:pullalertdata&quot;, {'INPUT_LAYER': '[% @layer_id %]', 'ONLY_SELECTED': True, 'FIELD_ALERTCODE': 'alertCode', 'FIELD_CARID': 'carId', 'OUTPUT': 'memory:'})&#xa;        QgsProject.instance().addMapLayer(result['OUTPUT'])&#xa;    else:&#xa;        result = processing.run(&quot;mapbiomas-api:pullalertdata&quot;, {'INPUT_LAYER': '[% @layer_id %]', 'ONLY_SELECTED': False, 'FIELD_ALERTCODE': 'alertCode', 'FIELD_CARID': 'carId', 'OUTPUT': 'memory:'})&#xa;        QgsProject.instance().addMapLayer(result['OUTPUT'])&#xa;" notificationMessage="" isEnabledOnlyWhenEditable="0">
      <actionScope id="Layer"/>
    </actionsetting>
  </attributeactions>
  <layerGeometryType>2</layerGeometryType>
</qgis>
