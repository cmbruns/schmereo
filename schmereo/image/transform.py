from schmereo.coord_sys import FractionalImagePos


class Transform(object):
    """
    Image Transform: the 'real' output of schmereo
    """
    def __init__(self):
        self.center = FractionalImagePos(0, 0)
