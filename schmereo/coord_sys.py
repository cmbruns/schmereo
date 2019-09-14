"""
Use thin wrapper classes to keep different coordinate frames semantically distinct
"""

from typing import TypeVar

from PyQt5 import QtCore
import numpy


T = TypeVar('T')


def _vec2(x, y):
    return numpy.array((x, y), dtype=numpy.float32)


class PosBase(object):
    def __init__(self, x, y):
        self._pos = _vec2(x=x, y=y)

    def __getitem__(self, key) -> float:
        return self._pos[key]

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.x}, {self.y})'

    def __sub__(self: T, other: T) -> T:
        r = self._pos - other._pos
        return self.__class__(x=r[0], y=r[1])

    @property
    def x(self) -> float:
        return self._pos[0]

    @property
    def y(self) -> float:
        return self._pos[1]


class WindowPos(PosBase):
    @classmethod
    def from_QPoint(cls, qpoint: QtCore.QPoint):
        return cls(x=qpoint.x(), y=qpoint.y())


class CanvasPos(PosBase):
    pass


class FractionalImagePos(PosBase):
    pass


class TextureCoordinate(PosBase):
    pass
