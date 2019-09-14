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

    def __getitem__(self, key) -> float:
        return self._pos[key]

    def __iadd__(self: T, other: T) -> T:
        self._pos += other._pos
        return self

    def __isub__(self: T, other: T) -> T:
        self._pos -= other._pos
        return self

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
    """
    @classmethod
    def from_QPoint(cls, qpoint: QtCore.QPoint) -> 'WindowPos':
        return WindowPos(x=qpoint.x(), y=qpoint.y())


class CanvasPos(PosBase):
    """
    Frame is virtual canvas underneath the image widget.
    Units are left image width / 2.
    X increases to the right.
    Y increases up.
    """
    @classmethod
    def from_WindowPos(cls, pos: WindowPos, camera: 'schmereo.Camera', size: QtCore.QSize) -> 'CanvasPos':
        x = 2.0 * camera.zoom * pos.x / size.width()
        y = 2.0 * camera.zoom * pos.y / size.width()  # yes, width
        return CanvasPos(x=x, y=y)


class FractionalImagePos(PosBase):
    pass


class TextureCoordinate(PosBase):
    pass
