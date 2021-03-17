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

"""Mapbiomas alerts API
"""

import requests

from .geometry import Geometry


class MapbiomasApi(object):

    ENDPOINT = 'https://plataforma.alerta.mapbiomas.org/api/graphql'
    LIMIT = 500
    TIMEOUT = 120

    @staticmethod
    def token(credentials):
        """A function to get an Authorization Token""" 
        
        mutation = \
        """mutation($email: String!, $password: String!)
            { 
            createToken(email: $email, password: $password)
                {
                    token
                }
            }
        """

        request = requests.post(MapbiomasApi.ENDPOINT, json={'query': mutation, 'variables': credentials}, timeout=MapbiomasApi.TIMEOUT)

        if request.status_code == 200:
            result = request.json()
            if 'errors' in result:
                msg = '\n'.join([error['message'] for error in result['errors']])
                return None, msg
            else:
                return result["data"]["createToken"]["token"], None
        else:
            msg = "Failed to run by returning code of {}.".format(request.status_code)
            return None, msg

    @classmethod
    def get(cls, token, filters=dict()):

        headers = {'Authorization': 'Bearer ' + token}
        rows = []
        offset = 0
        once = not filters

        with requests.Session() as session:
        
            while True:
                filters.update({'limit': cls.LIMIT, 'offset': offset})
                request = session.post(cls.ENDPOINT, json={'query': cls.QUERY, 'variables': filters}, headers=headers, timeout=cls.TIMEOUT)
                if request.status_code == 200:
                    row = request.json()
                    if 'errors' in row:
                        msg = '\n'.join([error['message'] for error in row['errors']])
                        return None, msg
                else:
                    msg = "Query failed to run by returning code of {}.".format(request.status_code)
                    return None, msg
    
                rows.extend(row['data'][cls.__name__])
                if len(row['data'][cls.__name__]) < cls.LIMIT or once:
                    break
                else:
                    offset += cls.LIMIT


        return cls.parse(rows), None



class allTerritories(MapbiomasApi):

    QUERY = \
    """
    query
    (
        $category: TerritoryCategoryEnum
    )
    {
    allTerritories
    (
        category: $category
    )
        {
            id
            name
        }
    }
    """

    @staticmethod
    def parse(data):
        return {d['name']: d['id'] for d in data}



class allPublishedAlerts(MapbiomasApi):

    QUERY = \
    """
    query
    (
      $startDetectedAt: String
      $endDetectedAt: String
      $startPublishedAt: String
      $endPublishedAt: String
      $territoryIds: [Int!]
      $limit: Int
      $offset: Int
    )
    {
    allPublishedAlerts 
    (
        startDetectedAt: $startDetectedAt
        endDetectedAt: $endDetectedAt
        startPublishedAt: $startPublishedAt
        endPublishedAt: $endPublishedAt
        territoryIds: $territoryIds
        limit: $limit
        offset: $offset
    )
        {
            alertCode
            alertInsertedAt
            areaHa
            cars { carCode, id }
            detectedAt
            geometry { geom }
            id
            source
        }
    }
    """

    @staticmethod
    def parse(data):

        def feature(d):
            geometry = Geometry(d.pop("geometry")["geom"]).geojson
            return {"type": "Feature", "properties": d, "geometry": geometry}

        srid = Geometry(data[0]['geometry']['geom']).srid
        crs = { "type": "name", "properties": { "name": f"urn:ogc:def:crs:EPSG::{srid}" } }

        return {"type": "FeatureCollection",
                "name": "allPublishedAlerts",
                "crs": crs,
                "features": [feature(d) for d in data]}
