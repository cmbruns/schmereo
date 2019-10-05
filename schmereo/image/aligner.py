import math
from typing import List

from schmereo import CanvasPos
from schmereo.coord_sys import ImagePixelCoordinate


class Aligner(object):
    def __init__(self, main_window: "SchmereoMainWindow"):
        self.widgets = list(main_window.eye_widgets())

    @staticmethod
    def _compute_centroid(points: List[ImagePixelCoordinate]):
        weight = 1.0
        total_weight = 0.0
        x = 0.0
        y = 0.0
        for p in points:
            x += p[0] * weight
            y += p[1] * weight
            total_weight += weight
        if total_weight != 0:
            x /= total_weight
            y /= total_weight
        return ImagePixelCoordinate(x, y)

    def _rotation_from_dv(self, point, dv):
        # polar coordinates
        x, y = point
        theta = math.atan2(y, x)
        r = (x * x + y * y) ** 0.5
        y2 = y + dv
        theta2 = math.asin(y2/r)  # range -pi/2 -> +pi/2
        if abs(theta) > math.pi / 2:  # TODO: might not be exactly the right test
            theta2 = math.pi - theta2
        dtheta = theta2 - theta
        while dtheta > math.pi:
            dtheta -= 2*math.pi
        while dtheta < -math.pi:
            dtheta += 2*math.pi
        weight = r * (math.cos(theta/2.0) + 1)
        return dtheta, weight

    def _compute_rotation(
        self, points1: List[ImagePixelCoordinate], points2: List[ImagePixelCoordinate]
    ) -> float:
        if len(points1) < 2:
            return 0.0
        # Move to local coordinate system
        c1 = self._compute_centroid(points1)
        c2 = self._compute_centroid(points2)
        points1 = [ImagePixelCoordinate(*x) - c1 for x in points1]
        points2 = [ImagePixelCoordinate(*x) - c2 for x in points2]
        # vertical offset per point -- right minus left
        dv = [x2[1] - x1[1] for x1, x2 in zip(points1, points2)]
        # best rotation per point
        for i in range(len(points1)):
            dtheta, weight = self._rotation_from_dv(points1[i], dv[i])
            print(f'point {i}: {dtheta * 180.0 / math.pi: 0.2f} degrees')
        for i in range(len(points2)):
            dtheta, weight = self._rotation_from_dv(points2[i], -dv[i])
            print(f'point {i}: {-dtheta * 180.0 / math.pi: 0.2f} degrees')
        return 0

    def _compute_translation(
        self, points1: List[ImagePixelCoordinate], points2: List[ImagePixelCoordinate]
    ) -> ImagePixelCoordinate:
        c1 = self._compute_centroid(points1)
        c2 = self._compute_centroid(points2)
        dx, dy = c2 - c1  # TODO: translate extreme dx, not mean
        return ImagePixelCoordinate(dx, dy)

    def align(self):
        lwidg = self.widgets[0]
        rwidg = self.widgets[1]
        lm = lwidg.markers
        rm = rwidg.markers
        cm = min(len(lm), len(rm))
        if cm < 1:
            return
        # TODO: rotation
        angle = self._compute_rotation(lm[:cm], rm[:cm])
        print(angle)
        # Translation
        c1 = self._compute_centroid(lm[:cm])
        c2 = self._compute_centroid(rm[:cm])
        dx, dy = c2 - c1  # TODO: translate extreme dx, not mean
        print(dx, dy)
        desired = self._compute_translation(lm[:cm], rm[:cm])
        # convert current center difference to image pixels
        c_c = CanvasPos(0, 0)  # center of image is canvas 0, 0
        lc_i = lwidg.image_from_canvas(c_c)
        rc_i = rwidg.image_from_canvas(c_c)
        current = rc_i - lc_i
        change = desired - current
        # Apply half to each eye image
        change2 = ImagePixelCoordinate(0.5 * change.x, 0.5 * change.y)
        lc_i -= change2
        lc_f = lwidg.fract_from_image(lc_i)
        lwidg.image.transform.center = lc_f
        rc_i += change2
        rc_f = rwidg.fract_from_image(rc_i)
        rwidg.image.transform.center = rc_f
        lwidg.update()
        rwidg.update()
