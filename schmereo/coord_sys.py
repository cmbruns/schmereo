"""
Use thin wrapper classes to keep different coordinate frames semantically distinct
"""

from typing import TypeVar

from PyQt5 import QtCore
import numpy

import schmereo

T = TypeVar('T')


def _vec2(x, y):
    return numpy.array((x, y), dtype=numpy.float32)


class PosBase(object):
    def __init__(self, x, y):
        self._pos = _vec2(x=x, y=y)

    def __add__(self: T, other: T) -> T:
        r = self._pos + other._pos
        return self.__class__(x=r[0], y=r[1])

    def __eq__(self, other) -> bool:
        result = numpy.array_equal(self._pos, other._pos)
        return result

    def __getitem__(self, key) -> float:
        return self._pos[key]

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.x}, {self.y})'

    def __sub__(self: T, other: T) -> T:
        r = self._pos - other._pos
        return self.__class__(x=r[0], y=r[1])

    @property
    def bytes(self) -> numpy.array:
        return self._pos

    @property
    def x(self) -> float:
        return self._pos[0]

    @property
    def y(self) -> float:
        return self._pos[1]


class WindowPos(PosBase):
    """
    Thin wrapper around QPoint.
    Units are pixels.
    Frame is QWidget relative.
    X increases to the right.
    Y increases down.
    Origin is at center of widget window.
    """
    @classmethod
    def from_QPoint(cls, qpoint: QtCore.QPoint) -> 'WindowPos':
        return WindowPos(x=qpoint.x(), y=qpoint.y())


class CanvasPos(PosBase):
    """
    Frame is virtual canvas underneath the image widget.
    One unit equals half of left image width.
    X increases to the right.
    Y increases down.
    Origin is at center of untransformed image.
    """
    @classmethod
    def from_WindowPos(cls, pos: WindowPos, camera: 'schmereo.Camera', size: QtCore.QSize) -> 'CanvasPos':
        """
        Note: no origin offset is applied. This is method scales relative positions only.
        """
        x = 2.0 * (1.0/camera.zoom) * pos.x / size.width()
        y = 2.0 * (1.0/camera.zoom) * pos.y / size.width()  # yes, width
        return CanvasPos(x=x, y=y)


class FractionalImagePos(PosBase):
    """
    Frame is relative to image bounds.
    One unit equals half the image width.
    X increases to the right.
    Y increases to the bottom.
    Origin is center of image.
    """
    @classmethod
    def from_CanvasPos(cls, pos: CanvasPos, transform: 'ImageTransform') -> 'FractionalImagePos':
        x = pos.x + transform.center.x
        y = pos.y + transform.center.y
        # TODO: rotation, scale
        return FractionalImagePos(x, y)


class TextureCoordinate(PosBase):
    pass


class PixelCoordinate(PosBase):
    """
    X increases to the right.
    Y increases to the bottom.
    Origin is a upper left corner.
    Units are pixels.
    """


class ImageTransform(object):
    """
    Image Transform: the 'real' output of schmereo
    """
    def __init__(self):
        self.center = FractionalImagePos(0, 0)