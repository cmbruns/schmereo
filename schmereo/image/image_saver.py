from OpenGL import GL
from PIL import Image

from schmereo.camera import Camera


class ImageSaver(object):
    def __init__(self, left_widget, right_widget):
        self.lw = left_widget
        self.rw = right_widget
        self.framebuffer = None
        self.texture = None
        self.fb_size = (1000, 500)  # TODO: something intelligent
        self.camera = Camera()  # store a permanently neutral camera
        self.camera.zoom = 2.0

    def can_save(self) -> bool:
        img1 = self.lw.image.image
        img2 = self.rw.image.image
        if img1 is None or img2 is None:
            return False
        return True

    def save_image(self, file_name, file_type) -> None:
        print(file_name)
        self._render_left_image()
        # self._render_right_image()
        img = self._get_image()
        img.save(fp=file_name, format='png')
        print(img)
        print("Hey! This isn't saving an image!")

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
            None
        )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glFramebufferTexture(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, self.texture, 0)
        GL.glDrawBuffers(1, [GL.GL_COLOR_ATTACHMENT0])
        if GL.glCheckFramebufferStatus(GL.GL_FRAMEBUFFER) != GL.GL_FRAMEBUFFER_COMPLETE:
            raise Exception('Incomplete framebuffer')
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        return fb

    def _get_image(self):
        self.lw.makeCurrent()
        GL.glBindFramebuffer(GL.GL_READ_FRAMEBUFFER, self.framebuffer)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        data = GL.glReadPixels(
            0, 0,
            *self.fb_size,
            GL.GL_RGBA, GL.GL_UNSIGNED_BYTE
        )
        self.lw.doneCurrent()
        image = Image.frombytes('RGBA', self.fb_size, data)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        return image

    def _render_eye_image(self, widget, left_edge):
        widget.makeCurrent()
        if self.framebuffer is None:
            self.framebuffer = self._create_framebuffer()
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, self.framebuffer)
        w, h = int(self.fb_size[0]/2), self.fb_size[1]
        GL.glViewport(left_edge, 0, w, h)
        aspect = h / w
        widget.image.paintGL(aspect, self.camera)
        GL.glBindFramebuffer(GL.GL_FRAMEBUFFER, 0)
        widget.doneCurrent()

    def _render_left_image(self):
        self._render_eye_image(self.lw, 0)

    def _render_right_image(self):
        self._render_eye_image(self.rw, int(self.fb_size[0]/2))
