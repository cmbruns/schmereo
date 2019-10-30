import math
import traceback
from typing import List

from schmereo.coord_sys import CanvasPos, ImagePixelCoordinate


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
        theta2 = math.asin(y2 / r)  # range -pi/2 -> +pi/2
        if abs(theta) > math.pi / 2:  # TODO: might not be exactly the right test
            theta2 = math.pi - theta2
        dtheta = theta2 - theta
        while dtheta > math.pi:
            dtheta -= 2 * math.pi
        while dtheta < -math.pi:
            dtheta += 2 * math.pi
        weight = r * (math.cos(theta / 2.0) + 1)
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
        total_weight = 0.0
        angle_sum = 0.0
        for i in range(len(points1)):
            try:
                dtheta, weight = self._rotation_from_dv(points1[i], dv[i])
                total_weight += weight
                angle_sum += dtheta * weight
                # print(f'point {i}: {dtheta * 180.0 / math.pi: 0.2f} degrees {weight}')
            except ValueError as ve:
                print(f"ERROR: rotation error for point1 {i} {points1[i]} dv: {dv[i]}")
                traceback.print_exc()  # TODO: debug this
                pass  # ???
        for i in range(len(points2)):
            try:
                dtheta, weight = self._rotation_from_dv(points2[i], -dv[i])
                total_weight += weight
                angle_sum += -dtheta * weight
                # print(f'point {i}: {-dtheta * 180.0 / math.pi: 0.2f} degrees {weight}')
            except ValueError as ve:
                print(f"ERROR: rotation error for point2 {i} {points2[i]} dv: {-dv[i]}")
                traceback.print_exc()  # TODO: debug this
                pass  # ???
        final_angle = angle_sum / total_weight
        return final_angle

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
        # Convert to current canvas coordinates
        lc = [lwidg.x_canvas_from_image(ImagePixelCoordinate(*x)) for x in lm]
        rc = [rwidg.x_canvas_from_image(ImagePixelCoordinate(*x)) for x in rm]
        # Compute rotation
        d_angle = self._compute_rotation(lc[:cm], rc[:cm])
        # print(f"total rotation = {math.degrees(d_angle) : 0.2f}\N{DEGREE SIGN}")
        lwidg.image.transform.rotation += d_angle/2.0
        rwidg.image.transform.rotation -= d_angle/2.0
        # Recompute positions using updated rotation
        lc = [lwidg.x_canvas_from_image(ImagePixelCoordinate(*x)) for x in lm]
        rc = [rwidg.x_canvas_from_image(ImagePixelCoordinate(*x)) for x in rm]
        d_angle = self._compute_rotation(lc[:cm], rc[:cm])
        assert abs(math.degrees(d_angle)) < 0.05
        # Translation
        # a) horizontal - use minimum separation
        min_dh = None
        for ix in range(cm):
            dh = rc[ix].x - lc[ix].x
            if min_dh is None or min_dh > dh:
                min_dh = dh
        if min_dh is None:
            min_dh = 0
        # b) vertical - use average separation
        sum_v = 0.0
        sum_weight = 0.0
        for ix in range(cm):
            dv = rc[ix].y - lc[ix].y
            sum_v += dv
            sum_weight += 1.0
        if sum_weight <= 0.0:
            avg_dv = 0.0
        else:
            avg_dv = sum_v / sum_weight
        dh = [a - b for a, b in zip(rc[:cm], lc[:cm])]

        new_center_c = CanvasPos(0.5 * min_dh, 0.5 * avg_dv)  # for left image (?)
        old_center_c = CanvasPos(0, 0)
        ldiff = [lwidg.x_fract_from_canvas(c) for c in (new_center_c, old_center_c)]
        ldiff1 = ldiff[1] - ldiff[0]
        lwidg.image.transform.center += ldiff1
        rdiff = [rwidg.x_fract_from_canvas(c) for c in (old_center_c, new_center_c)]
        rdiff1 = rdiff[1] - rdiff[0]
        rwidg.image.transform.center += rdiff1
