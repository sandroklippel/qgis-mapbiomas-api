# -*- coding: utf-8 -*-

# The content of this file is from
# plpygis package by Benjamin Trigona-Harany (GPLv3 license)

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


from binascii import hexlify, unhexlify
from struct import calcsize, pack, unpack_from


class PlpygisError(Exception):
    """
    Basic exception for ``plpygis``.
    """
    def __init__(self, msg):
        super(PlpygisError, self).__init__(msg)
      

class WkbError(PlpygisError):
    """
    Exception for problems in parsing WKBs.
    """
    def __init__(self, msg=None):
        if msg is None:
            msg = "Unreadable WKB."
        super(WkbError, self).__init__(msg)


class DimensionalityError(PlpygisError):
    """
    Exception for problems in dimensionality of geometries.
    """
    def __init__(self, msg=None):
        if msg is None:
            msg = "Geometry has invalid dimensionality."
        super(DimensionalityError, self).__init__(msg)


class SridError(PlpygisError):
    """
    Exception for problems in dimensionality of geometries.
    """
    def __init__(self, msg=None):
        if msg is None:
            msg = "Geometry has invalid SRID."
        super(SridError, self).__init__(msg)


class HexReader:
    """
    A reader for generic hex data. The current position in the stream of bytes
    will be retained as data is read.
    """

    def __init__(self, hexdata, order, offset=0):
        self._data = hexdata
        self._order = order
        self._ini_offset = offset
        self._cur_offset = offset

    def reset(self):
        """
        Start reading from the initial position again.

        :rtype: int
        """
        self._cur_offset = self._ini_offset

    def _get_value(self, fmt):
        value = unpack_from("{}{}".format(self._order, fmt), self._data, self._cur_offset)[0]
        self._cur_offset += calcsize(fmt)
        return value

    def get_char(self):
        return self._get_value("B")

    def get_int(self):
        """
        Get the next four-byte integer from the stream of bytes.

        :rtype: int
        """
        return self._get_value("I")

    def get_double(self):
        """
        Get the next double from the stream of bytes.

        :rtype: int
        """
        return self._get_value("d")


class HexWriter:
    def __init__(self, order):
        self._fmts = []
        self._values = []
        self._order = order

    def _add_value(self, fmt, value):
        self._fmts.append(fmt)
        self._values.append(value)

    def add_order(self):
        if self._order == "<":
            self.add_char(1)
        else:
            self.add_char(0)

    def add_char(self, value):
        self._add_value("B", value)

    def add_int(self, value):
        self._add_value("I", value)

    def add_double(self, value):
        self._add_value("d", value)

    @property
    def data(self):
        fmt = self._order + "".join(self._fmts)
        data = pack(fmt, *self._values)
        return HexBytes(data)


class HexBytes(bytes):
    """A subclass of bytearray that represents binary WKB data.
    It can be converted to a hexadecimal representation of the data using str()
    and compared to a hexadecimal representation with the normal equality operator."""

    def __new__(cls, data):
        if not isinstance(data, (bytes, bytearray)):
            data = unhexlify(str(data))
        elif data[:2] in (b'00', b'01'):  # hex-encoded string as bytes
            data = unhexlify(data.decode('ascii'))
        return bytes.__new__(cls, data)

    def __str__(self):
        return hexlify(self).decode('ascii')

    def __eq__(self, other):
        if isinstance(other, str) and other[:2] in ('00', '01'):
            other = unhexlify(other)
        return super(HexBytes, self).__eq__(other)


class Geometry(object):
    r"""A representation of a PostGIS geometry.

    PostGIS geometries are either an OpenGIS Consortium Simple Features for SQL
    specification type or a PostGIS extended type. The object's canonical form
    is stored in WKB or EWKB format along with an SRID and flags indicating
    whether the coordinates are 3DZ, 3DM or 4D.

    ``Geometry`` objects can be created in a number of ways. In all cases, a
    subclass for the particular geometry type will be instantiated.

    From an (E)WKB::

        >>> Geometry(b'\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        <Point: 'geometry(Point)'>

    From the hexadecimal string representation of an (E)WKB::

        >>> Geometry("0101000080000000000000000000000000000000000000000000000000")
        <Point: 'geometry(PointZ)'>

    The response above indicates an instance of the ``Point`` class has been
    created and that it represents a PostGIS ``geometry(PointZ)`` type.

    From a GeoJSON::

        >>> Geometry.from_geojson({'type': 'Point', 'coordinates': (0.0, 0.0)})
        <Point: 'geometry(Point,4326)'>

    From a Shapely object::

        >>> from shapely.geometry import Point
        >>> Geometry.from_shapely(Point((0, 0)), 3857)
        <Point: 'geometry(Point,3857)'>

    From any object supporting ``__geo_interface__``::

        >>> from shapefile import Reader
        >>> feature = Reader("test/multipoint.shp").shape(0)
        >>> Geometry.shape(feature)
        <MultiPoint: 'geometry(MultiPoint)'>

    A ``Geometry`` can be read as long as it is one of the following
    types: ``Point``, ``LineString``, ``Polygon``, ``MultiPoint``, ``MultiLineString``,
    ``MultiPolygon`` or ``GeometryCollection``. The M dimension will be preserved.
    """

    _WKBTYPE = 0x1fffffff
    _WKBZFLAG = 0x80000000
    _WKBMFLAG = 0x40000000
    _WKBSRIDFLAG = 0x20000000
    __slots__ = ["_wkb", "_reader", "_srid", "_dimz", "_dimm"]

    def __new__(cls, wkb, srid=None, dimz=False, dimm=False):
        if cls == Geometry:
            if not wkb:
                raise WkbError("No EWKB provided")
            wkb = HexBytes(wkb)
            newcls, dimz, dimm, srid, reader = Geometry._from_wkb(wkb)
            geom = super(Geometry, cls).__new__(newcls)
            geom._wkb = wkb
            geom._reader = reader
            geom._srid = srid
            geom._dimz = dimz
            geom._dimm = dimm
        else:
            geom = super(Geometry, cls).__new__(cls)
            geom._wkb = None
            geom._reader = None
        return geom

    @staticmethod
    def from_geojson(geojson, srid=4326):
        """
        Create a Geometry from a GeoJSON. The SRID can be overridden from the
        expected 4326.
        """
        type_ = geojson["type"].lower()
        if type_ == "geometrycollection":
            geometries = []
            for geometry in geojson["geometries"]:
                geometries.append(Geometry.from_geojson(geometry, srid=None))
            return GeometryCollection(geometries, srid)
        elif type_ == "point":
            return Point(geojson["coordinates"], srid=srid)
        elif type_ == "linestring":
            return LineString(geojson["coordinates"], srid=srid)
        elif type_ == "polygon":
            return Polygon(geojson["coordinates"], srid=srid)
        elif type_ == "multipoint":
            geometries = _MultiGeometry._multi_from_geojson(geojson, Point)
            return MultiPoint(geometries, srid=srid)
        elif type_ == "multilinestring":
            geometries = _MultiGeometry._multi_from_geojson(geojson, LineString)
            return MultiLineString(geometries, srid=srid)
        elif type_ == "multipolygon":
            geometries = _MultiGeometry._multi_from_geojson(geojson, Polygon)
            return MultiPolygon(geometries, srid=srid)

    @staticmethod
    def shape(shape, srid=None):
        """
        Create a Geometry using ``__geo_interface__`` and the specified SRID.
        """
        return Geometry.from_geojson(shape.__geo_interface__, srid)

    @property
    def type(self):
        """
        The geometry type.
        """
        return self.__class__.__name__

    @property
    def srid(self):
        """
        The geometry SRID.
        """
        return self._srid

    @srid.setter
    def srid(self, value):
        self._check_cache()
        self._srid = value

    @property
    def geojson(self):
        """
        Get the geometry as a GeoJSON dict. There is no check that the
        GeoJSON is using an SRID of 4326.
        """
        return self._to_geojson(dimz=self.dimz)

    @property
    def wkb(self):
        """
        Get the geometry as an (E)WKB.
        """
        return self._to_wkb(use_srid=True, dimz=self.dimz, dimm=self.dimm)

    @property
    def shapely(self):
        """
        Get the geometry as a Shapely geometry. If the geometry has an SRID,
        the Shapely object will be created with it set.
        """
        return self._to_shapely()

    @property
    def bounds(self):
        """
        Get the minimum and maximum extents of the geometry: (minx, miny, maxx,
        maxy).
        """
        return self._bounds()

    @property
    def postgis_type(self):
        """
        Get the type of the geometry in PostGIS format, including additional
        dimensions and SRID if they exist.
        """
        dimz = "Z" if self.dimz else ""
        dimm = "M" if self.dimm else ""
        if self.srid:
            return "geometry({}{}{},{})".format(self.type, dimz, dimm, self.srid)
        else:
            return "geometry({}{}{})".format(self.type, dimz, dimm)

    @staticmethod
    def _from_wkb(wkb):
        try:
            if wkb.startswith(b"\x00"):
                reader = HexReader(wkb, ">")  # big-endian reader
            elif wkb.startswith(b"\x01"):
                reader = HexReader(wkb, "<")  # little-endian reader
            else:
                raise WkbError("First byte in WKB must be 0 or 1.")
        except TypeError:
            raise WkbError()
        return Geometry._get_wkb_type(reader) + (reader,)

    def _check_cache(self):
        if self._reader is not None:
            self._load_geometry()
            self._wkb = None
            self._reader = None

    def _to_wkb(self, use_srid, dimz, dimm):
        if self._wkb is not None:
            return self._wkb
        writer = HexWriter("<")
        self._write_wkb_header(writer, use_srid, dimz, dimm)
        self._write_wkb(writer, dimz, dimm)
        return writer.data

    def _to_geojson(self, dimz):
        coordinates = self._to_geojson_coordinates(dimz)
        geojson = {
                "type": self.type,
                "coordinates": coordinates
        }
        return geojson

    def __repr__(self):
        return "<{}: '{}'>".format(self.type, self.postgis_type)

    def __str__(self):
        return self.wkb.__str__()

    @property
    def __geo_interface__(self):
        return self.geojson

    def _set_dimensionality(self, geometries):
        self._dimz = None
        self._dimm = None
        for geometry in geometries:
            if self._dimz is None:
                self._dimz = geometry.dimz
            elif self._dimz != geometry.dimz:
                raise DimensionalityError("Mixed dimensionality in MultiGeometry")
            if self._dimm is None:
                self._dimm = geometry.dimm
            elif self._dimm != geometry.dimm:
                raise DimensionalityError("Mixed dimensionality in MultiGeometry")

    @staticmethod
    def _get_wkb_type(reader):
        lwgeomtype, dimz, dimm, srid = Geometry._read_wkb_header(reader)
        if lwgeomtype == 1:
            cls = Point
        elif lwgeomtype == 2:
            cls = LineString
        elif lwgeomtype == 3:
            cls = Polygon
        elif lwgeomtype == 4:
            cls = MultiPoint
        elif lwgeomtype == 5:
            cls = MultiLineString
        elif lwgeomtype == 6:
            cls = MultiPolygon
        elif lwgeomtype == 7:
            cls = GeometryCollection
        else:
            raise WkbError("Unsupported WKB type: {}".format(lwgeomtype))
        return cls, dimz, dimm, srid

    @staticmethod
    def _read_wkb_header(reader):
        try:
            reader.get_char()
            header = reader.get_int()
            lwgeomtype = header & Geometry._WKBTYPE
            dimz = bool(header & Geometry._WKBZFLAG)
            dimm = bool(header & Geometry._WKBMFLAG)
            if header & Geometry._WKBSRIDFLAG:
                srid = reader.get_int()
            else:
                srid = None
        except TypeError:
            raise WkbError()
        return lwgeomtype, dimz, dimm, srid

    def _write_wkb_header(self, writer, use_srid, dimz, dimm):
        writer.add_order()
        header = (self._LWGEOMTYPE |
                  (Geometry._WKBZFLAG if dimz else 0) |
                  (Geometry._WKBMFLAG if dimm else 0) |
                  (Geometry._WKBSRIDFLAG if self.srid else 0))
        writer.add_int(header)
        if use_srid and self.srid:
            writer.add_int(self.srid)
        return writer


class _MultiGeometry(Geometry):
    @property
    def dimz(self):
        """
        Whether the geometry has a Z dimension.

        :getter: ``True`` if the geometry has a Z dimension.
        :setter: Add or remove the Z dimension from this and all geometries in the collection.
        :rtype: bool
        """
        return self._dimz

    @dimz.setter
    def dimz(self, value):
        if self._dimz == value:
            return
        for geometry in self.geometries:
            geometry.dimz = value
        self._dimz = value

    @property
    def dimm(self):
        """
        Whether the geometry has an M dimension.

        :getter: ``True`` if the geometry has an M dimension.
        :setter: Add or remove the M dimension from this and all geometries in the collection.
        :rtype: bool
       """
        return self._dimm

    @dimm.setter
    def dimm(self, value):
        if self._dimm == value:
            return
        for geometry in self.geometries:
            geometry.dimm = value
        self._dimm = value

    def _bounds(self):
        bounds = [g.bounds for g in self.geometries]
        minx = min([b[0] for b in bounds])
        miny = min([b[1] for b in bounds])
        maxx = max([b[2] for b in bounds])
        maxy = max([b[3] for b in bounds])
        return (minx, miny, maxx, maxy)

    @staticmethod
    def _multi_from_geojson(geojson, cls):
        geometries = []
        for coordinates in geojson["coordinates"]:
            geometry = cls(coordinates, srid=None)
            geometries.append(geometry)
        return geometries

    def _load_geometry(self):
        self._geometries = self.__class__._read_wkb(self._reader, self._dimz, self._dimm)

    def _set_multi_metadata(self):
        self._dimz = None
        self._dimm = None
        for geometry in self.geometries:
            if self._dimz is None:
                self._dimz = geometry.dimz
            elif self._dimz != geometry.dimz:
                raise DimensionalityError("Mixed dimensionality in MultiGeometry")
            if self._dimm is None:
                self._dimm = geometry.dimm
            elif self._dimm != geometry.dimm:
                raise DimensionalityError("Mixed dimensionality in MultiGeometry")
            if self.srid is None:
                if geometry._srid is not None:
                    self._srid = geometry.srid
            elif self.srid != geometry.srid and geometry.srid is not None:
                raise SridError("Mixed SRIDs in MultiGeometry")

    def _to_geojson_coordinates(self, dimz):
        coordinates = [g._to_geojson_coordinates(dimz=dimz) for g in self.geometries]
        return coordinates

    @staticmethod
    def _read_wkb(reader, dimz, dimm):
        geometries = []
        try:
            for _ in range(reader.get_int()):
                cls, dimz, dimm, srid = Geometry._get_wkb_type(reader)
                coordinates = cls._read_wkb(reader, dimz, dimm)
                geometry = cls(coordinates, srid=srid, dimz=dimz, dimm=dimm)
                geometries.append(geometry)
        except TypeError:
            raise WkbError()
        return geometries

    def _write_wkb(self, writer, dimz, dimm):
        writer.add_int(len(self.geometries))
        for geometry in self.geometries:
            geometry._write_wkb_header(writer, False, dimz, dimm)
            geometry._write_wkb(writer, dimz, dimm)


class Point(Geometry):
    """
    A representation of a PostGIS Point.

    ``Point`` objects can be created directly.

        >>> Point((0, -52, 5), dimm=True, srid=4326)
        <Point: 'geometry(PointM,4326)'>

    The ``dimz`` and ``dimm`` parameters will indicate how to interpret the
    coordinates that have been passed as the first argument. By default, the
    third coordinate will be interpreted as representing the Z dimension.
    """

    _LWGEOMTYPE = 1
    __slots__ = ["_x", "_y", "_z", "_m"]

    def __init__(self, coordinates=None, srid=None, dimz=False, dimm=False):
        if self._wkb:
            self._x = None
            self._y = None
            self._z = None
            self._m = None
        else:
            self._srid = srid
            coordinates = list(coordinates)
            self._x = coordinates[0]
            self._y = coordinates[1]
            num = len(coordinates)
            if num > 4:
                raise DimensionalityError("Maximum dimensionality supported for coordinates is 4: {}".format(coordinates))
            elif num == 2:  # fill in Z and M if we are supposed to have them, else None
                if dimz and dimm:
                    self._z = 0
                    self._m = 0
                elif dimz:
                    self._z = 0
                    self._m = None
                elif dimm:
                    self._z = None
                    self._m = 0
                else:
                    self._z = None
                    self._m = None
            elif num == 3:  # use the 3rd coordinate for Z or M as directed or as Z
                if dimz and dimm:
                    self._z = coordinates[2]
                    self._m = 0
                elif dimm:
                    self._z = None
                    self._m = coordinates[2]
                else:
                    self._z = coordinates[2]
                    self._m = None
            else:  # use both the 3rd and 4th coordinates, ensure not None
                    self._z = coordinates[2]
                    self._m = coordinates[3]

            self._dimz = self._z is not None
            self._dimm = self._m is not None

    @property
    def x(self):
        """
        X coordinate.
        """
        self._check_cache()
        return self._x

    @x.setter
    def x(self, value):
        self._check_cache()
        self._x = value

    @property
    def y(self):
        """
        M coordinate.
        """
        self._check_cache()
        return self._y

    @y.setter
    def y(self, value):
        self._check_cache()
        self._y = value

    @property
    def z(self):
        """
        Z coordinate.
        """
        if not self._dimz:
            return None
        self._check_cache()
        return self._z

    @z.setter
    def z(self, value):
        self._check_cache()
        self._z = value
        if value is None:
            self._dimz = False
        else:
            self._dimz = True

    @property
    def m(self):
        """
        M coordinate.
        """
        if not self._dimm:
            return None
        self._check_cache()
        return self._m

    @m.setter
    def m(self, value):
        self._check_cache()
        self._m = value
        if value is None:
            self._dimm = False
        else:
            self._dimm = True

    @property
    def dimz(self):
        """
        Whether the geometry has a Z dimension.

        :getter: ``True`` if the geometry has a Z dimension.
        :setter: Add or remove the Z dimension.
        :rtype: bool
        """
        return self._dimz

    @dimz.setter
    def dimz(self, value):
        if self._dimz == value:
            return None
        self._check_cache()
        if value and self._z is None:
            self._z = 0
        elif value is None:
            self._z = None
        self._dimz = value

    @property
    def dimm(self):
        """
        Whether the geometry has an M dimension.

        :getter: ``True`` if the geometry has an M dimension.
        :setter: Add or remove the M dimension.
        :rtype: bool
        """
        return self._dimm

    @dimm.setter
    def dimm(self, value):
        if self._dimm == value:
            return None
        self._check_cache()
        if value and self._m is None:
            self._m = 0
        elif value is None:
            self._m = None
        self._dimm = value

    def _to_geojson_coordinates(self, dimz):
        coordinates = [self.x, self.y]
        if dimz:
            coordinates.append(self.z)
        return coordinates

    def _bounds(self):
        return (self.x, self.y, self.x, self.y)

    def _load_geometry(self):
        self._x, self._y, self._z, self._m = Point._read_wkb(self._reader, self._dimz, self._dimm)

    @staticmethod
    def _read_wkb(reader, dimz, dimm):
        try:
            x = reader.get_double()
            y = reader.get_double()
            if dimz and dimm:
                z = reader.get_double()
                m = reader.get_double()
            elif dimz:
                z = reader.get_double()
                m = None
            elif dimm:
                z = None
                m = reader.get_double()
            else:
                z = None
                m = None
        except TypeError:
            raise WkbError()
        return x, y, z, m

    def _write_wkb(self, writer, dimz, dimm):
        writer.add_double(self.x)
        writer.add_double(self.y)
        if dimz and dimm:
            writer.add_double(self.z)
            writer.add_double(self.m)
        elif dimz:
            writer.add_double(self.z)
        elif dimm:
            writer.add_double(self.m)


class LineString(Geometry):
    """
    A representation of a PostGIS Line.

    ``LineString`` objects can be created directly.

        >>> LineString([(0, 0, 0, 0), (1, 1, 0, 0), (2, 2, 0, 0)])
        <LineString: 'geometry(LineStringZM)'>

    The ``dimz`` and ``dimm`` parameters will indicate how to interpret the
    coordinates that have been passed as the first argument. By default, the
    third coordinate will be interpreted as representing the Z dimension.
    """

    _LWGEOMTYPE = 2
    __slots__ = ["_vertices"]

    def __init__(self, vertices=None, srid=None, dimz=False, dimm=False):
        if self._wkb:
            self._vertices = None
        else:
            self._srid = srid
            self._dimz = dimz
            self._dimm = dimm
            self._vertices = LineString._from_coordinates(vertices, dimz=dimz, dimm=dimm)
            self._set_dimensionality(self._vertices)

    @property
    def vertices(self):
        """
        List of vertices that comprise the line.
        """
        self._check_cache()
        return self._vertices

    @property
    def dimz(self):
        """
        Whether the geometry has a Z dimension.

        :getter: ``True`` if the geometry has a Z dimension.
        :setter: Add or remove the Z dimension from this and all vertices in the line.
        :rtype: bool
        """
        return self._dimz

    @dimz.setter
    def dimz(self, value):
        if self.dimz == value:
            return
        for vertex in self.vertices:
            vertex.dimz = value
        self._dimz = value

    @property
    def dimm(self):
        """
        Whether the geometry has a M dimension.

        :getter: ``True`` if the geometry has a M dimension.
        :setter: Add or remove the M dimension from this and all vertices in the line.
        :rtype: bool
        """
        return self._dimm

    @dimm.setter
    def dimm(self, value):
        if self.dimm == value:
            return
        for vertex in self.vertices:
            vertex.dimm = value
        self._dimm = value

    def _to_geojson_coordinates(self, dimz):
        coordinates = [v._to_geojson_coordinates(dimz=dimz) for v in self.vertices]
        return coordinates

    def _bounds(self):
        x = [v.x for v in self.vertices]
        y = [v.y for v in self.vertices]
        return (min(x), min(y), max(x), max(y))

    @staticmethod
    def _from_coordinates(vertices, dimz, dimm):
        return [Point(vertex, dimz=dimz, dimm=dimm) for vertex in vertices]

    def _load_geometry(self):
        vertices = LineString._read_wkb(self._reader, self._dimz, self._dimm)
        self._vertices = LineString._from_coordinates(vertices, self._dimz, self._dimm)

    @staticmethod
    def _read_wkb(reader, dimz, dimm):
        vertices = []
        try:
            for _ in range(reader.get_int()):
                coordinates = Point._read_wkb(reader, dimz, dimm)
                vertices.append(coordinates)
        except TypeError:
            raise WkbError()
        return vertices

    def _write_wkb(self, writer, dimz, dimm):
        writer.add_int(len(self.vertices))
        for vertex in self.vertices:
            vertex._write_wkb(writer, dimz, dimm)


class Polygon(Geometry):
    """
    A representation of a PostGIS Polygon.

    ``Polygon`` objects can be created directly.

        >>> Polygon([[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 0)]])
        <Polygon: 'geometry(PolygonZ)'>

    The first polygon in the list of linear rings is the exterior ring, while
    any subsequent rings are interior boundaries.

    The ``dimz`` and ``dimm`` parameters will indicate how to interpret the
    coordinates that have been passed as the first argument. By default, the
    third coordinate will be interpreted as representing the Z dimension.
    """

    _LWGEOMTYPE = 3
    __slots__ = ["_rings"]

    def __init__(self, rings=None, srid=None, dimz=False, dimm=False):
        if self._wkb:
            self._rings = None
        else:
            self._srid = srid
            self._dimz = dimz
            self._dimm = dimm
            self._rings = Polygon._from_coordinates(rings, dimz, dimm)
            self._set_dimensionality(self._rings)

    @property
    def rings(self):
        """
        List of linearrings that comprise the polygon.
        """
        self._check_cache()
        return self._rings

    @property
    def exterior(self):
        """
        The exterior ring of the polygon.
        """
        return self.rings[0]

    @property
    def interior(self):
        """
        A list of interior rings of the polygon.
        """
        return self.rings[1:]

    @property
    def dimz(self):
        """
        Whether the geometry has a Z dimension.

        :getter: ``True`` if the geometry has a Z dimension.
        :setter: Add or remove the Z dimension from this and all linear rings in the polygon.
        :rtype: bool
        """
        return self._dimz

    @dimz.setter
    def dimz(self, value):
        if self._dimz == value:
            return
        for ring in self.rings:
            ring.dimz = value
        self._dimz = value

    @property
    def dimm(self):
        """
        Whether the geometry has a M dimension.

        :getter: ``True`` if the geometry has a M dimension.
        :setter: Add or remove the M dimension from this and all linear rings in the polygon.
        :rtype: bool
        """
        return self._dimm

    @dimm.setter
    def dimm(self, value):
        if self._dimm == value:
            return
        for ring in self.rings:
            ring.dimm = value
        self._dimm = value

    def _to_geojson_coordinates(self, dimz):
        coordinates = [r._to_geojson_coordinates(dimz=dimz) for r in self.rings]
        return coordinates

    def _bounds(self):
        return self.exterior.bounds

    @staticmethod
    def _from_coordinates(rings, dimz, dimm):
        return [LineString(vertices, dimz, dimm) for vertices in rings]

    def _load_geometry(self):
        rings = Polygon._read_wkb(self._reader, self._dimz, self._dimm)
        self._rings = Polygon._from_coordinates(rings, self._dimz, self._dimm)

    @staticmethod
    def _read_wkb(reader, dimz, dimm):
        rings = []
        try:
            for _ in range(reader.get_int()):
                vertices = LineString._read_wkb(reader, dimz, dimm)
                rings.append(vertices)
        except TypeError:
            raise WkbError()
        return rings

    def _write_wkb(self, writer, dimz, dimm):
        writer.add_int(len(self.rings))
        for ring in self.rings:
            ring._write_wkb(writer, dimz, dimm)


class MultiPoint(_MultiGeometry):
    """
    A representation of a PostGIS MultiPoint.

    ``MultiPoint`` objects can be created directly from a list of ``Point``
    objects.

        >>> p1 = Point((0, 0, 0))
        >>> p2 = Point((1, 1, 0))
        >>> MultiPoint([p1, p2])
        <MultiPoint: 'geometry(MultiPointZ)'>

    The dimensionality of all geometries in the collection must be identical.
    """

    _LWGEOMTYPE = 4
    __slots__ = ["_points"]

    def __init__(self, points=None, srid=None):
        if self._wkb:
            self._points = None
        else:
            self._points = points
            self._srid = srid
            self._set_multi_metadata()

    @property
    def points(self):
        """
        List of all component points.
        """
        self._check_cache()
        return self._points

    @property
    def geometries(self):
        """
        List of all component points.
        """
        return self.points

    def _load_geometry(self):
        self._points = MultiPoint._read_wkb(self._reader, self._dimz, self._dimm)


class MultiLineString(_MultiGeometry):
    """
    A representation of a PostGIS MultiLineString

    ``MultiLineString`` objects can be created directly from a list of
    ``LineString`` objects.

        >>> l1 = LineString([(1, 1, 0), (2, 2, 0)], dimm=True)
        >>> l2 = LineString([(0, 0, 0), (0, 1, 0)], dimm=True)
        >>> MultiLineString([l1, l2])
        <MultiLineString: 'geometry(MultiLineStringM)'>

    The dimensionality of all geometries in the collection must be identical.
    """

    _LWGEOMTYPE = 5
    __slots__ = ["_linestrings"]

    def __init__(self, linestrings=None, srid=None):
        if self._wkb:
            self._linestrings = None
        else:
            self._linestrings = linestrings
            self._srid = srid
            self._set_multi_metadata()

    @property
    def linestrings(self):
        """
        List of all component lines.
        """
        self._check_cache()
        return self._linestrings

    @property
    def geometries(self):
        """
        List of all component lines.
        """
        return self.linestrings

    def _load_geometry(self):
        self._linestrings = MultiLineString._read_wkb(self._reader, self._dimz, self._dimm)


class MultiPolygon(_MultiGeometry):
    """
    A representation of a PostGIS MultiPolygon.

    ``MultiPolygon`` objects can be created directly from a list of ``Polygon``
    objects.

        >>> p1 = Polygon([[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]], srid=4326)
        >>> p2 = Polygon([[(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)]], srid=4326)
        >>> MultiPolygon([p1, p2])
        <MultiPolygon: 'geometry(MultiPolygon,4326)'>

    The dimensionality of all geometries in the collection must be identical.
    """

    _LWGEOMTYPE = 6
    __slots__ = ["__polygons__"]

    def __init__(self, polygons=None, srid=None, dimz=False, dimm=False):
        if self._wkb:
            self._polygons = None
        else:
            self._srid = srid
            self._dimz = dimz
            self._dimm = dimm
            self._polygons = polygons
            self._set_multi_metadata()

    @property
    def polygons(self):
        """
        List of all component polygons.
        """
        self._check_cache()
        return self._polygons

    @property
    def geometries(self):
        """
        List of all component polygons.
        """
        return self.polygons

    def _load_geometry(self):
        self._polygons = MultiPolygon._read_wkb(self._reader, self._dimz, self._dimm)


class GeometryCollection(_MultiGeometry):
    """
    A representation of a PostGIS GeometryCollection.

    ``GeometryCollection`` objects can be created directly from a list of
    geometries, including other collections.

        >>> p = Point((0, 0, 0))
        >>> l = LineString([(1, 1, 0), (2, 2, 0)])
        >>> GeometryCollection([p, l])
        <GeometryCollection: 'geometry(GeometryCollectionZ)'>

    The dimensionality of all geometries in the collection must be identical.
    """

    _LWGEOMTYPE = 7
    __slots__ = ["_geometries"]

    def __init__(self, geometries=None, srid=None, dimz=False, dimm=False):
        if self._wkb:
            self._geometries = None
        else:
            self._geometries = geometries
            self._srid = srid
            self._set_multi_metadata()

    @property
    def geometries(self):
        """
        List of all component geometries.
        """
        self._check_cache()
        return self._geometries

    def _to_geojson(self, dimz):
        geometries = [g._to_geojson(dimz=dimz) for g in self.geometries]
        geojson = {
                "type": self.__class__.__name__,
                "geometries": geometries
        }
        return geojson
