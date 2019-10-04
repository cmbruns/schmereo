from OpenGL import GL
from PIL import Image

from schmereo.camera import Camera


class EyeSaver(object):
    def __init__(self, gl_widget):
        self.gl_widget = gl_widget
        self.framebuffer = None
        self.texture = None
        self.fb_size = None

    def _create_framebuffer(self):
        """
        Make sure opengl context is bound before calling this method
        """
        fb = GL.glGenFramebuffers(1)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, fb)
        self.texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,  # target
            0,
            GL.GL_RGBA,
            self.fb_size[0],
            self.fb_size[1],
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            None,
        )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glFramebufferTexture(
            GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, self.texture, 0
        )
        GL.glDrawBuffers(1, [GL.GL_COLOR_ATTACHMENT0])
        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE:
            raise Exception("Incomplete framebuffer")
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        return fb

    def get_image(self):
        self.gl_widget.makeCurrent()
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self.framebuffer)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        data = GL.glReadPixels(0, 0, *self.fb_size, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE)
        self.gl_widget.doneCurrent()
        image = Image.frombytes("RGBA", self.fb_size, data)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        return image

    def render_image(self, fb_size, camera):
        self.gl_widget.makeCurrent()
        # TODO: recreate if size changed
        if self.framebuffer is None:
            self.fb_size = fb_size
            self.framebuffer = self._create_framebuffer()
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.framebuffer)
        w, h = fb_size[0], fb_size[1]
        GL.glViewport(0, 0, w, h)
        aspect = h / w
        self.gl_widget.image.paintGL(aspect, camera)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        self.gl_widget.doneCurrent()
        self.fb_size = fb_size


class ImageSaver(object):
    def __init__(self, left_widget, right_widget):
        self.lw = left_widget
        self.rw = right_widget
        self.eye_size = (500, 500)  # TODO: intelligent sizing
        self.left_eye = EyeSaver(self.lw)
        self.right_eye = EyeSaver(self.rw)
        self.camera = Camera()  # store a permanently neutral camera
        self.camera.zoom = 2.0

    def can_save(self) -> bool:
        img1 = self.lw.image.image
        img2 = self.rw.image.image
        if img1 is None or img2 is None:
            return False
        return True

    def save_image(self, file_name, file_type) -> None:
        self.left_eye.render_image(self.eye_size, self.camera)
        self.right_eye.render_image(self.eye_size, self.camera)
        left_img = self.left_eye.get_image()
        right_img = self.right_eye.get_image()
        w, h = self.eye_size
        combined_img = Image.new("RGBA", (w * 2, h))
        combined_img.paste(left_img, (0, 0))
        combined_img.paste(right_img, (w, 0))
        combined_img.save(fp=file_name, format="png")  # TODO: output format logic
