from schmereo.coord_sys import CanvasPos


class Camera(object):
    def __init__(self):
        self.zoom = 1.0
        self.center = CanvasPos(0, 0)
