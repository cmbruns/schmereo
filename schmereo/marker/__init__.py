import inspect
import pkg_resources

import numpy
from OpenGL import GL
from OpenGL.GL.shaders import compileProgram, compileShader
from PIL import Image

from schmereo.coord_sys import ImagePixelCoordinate


class Marker(object):
    def __init__(self, pos: ImagePixelCoordinate):
        self.pos = pos
        self.is_manually_placed = False


class MarkerPair(object):
    def __init__(self, left: Marker, right: Marker):
        self.left = left
        self.right = right


class MarkerSet(object):
    def __init__(self, camera):
        self.camera = camera
        self.vao = None
        self.shader = None
        stream = pkg_resources.resource_stream(__name__, 'crosshair64.png')
        self.image = Image.open(stream)
        self.pixels = numpy.frombuffer(buffer=self.image.convert('RGBA').tobytes(), dtype=numpy.ubyte)
        self.texture = None

    def initializeGL(self):
        self.vao = GL.glGenVertexArrays(1)
        self.shader = compileProgram(
            compileShader(inspect.cleandoc('''
            #version 460 core
            
            void main()
            {
                gl_Position = vec4(0, 0, 0.5, 1);
                gl_PointSize = 48;
            }
            '''), GL.GL_VERTEX_SHADER),
            compileShader(inspect.cleandoc('''
            #version 460 core
            
            uniform sampler2D image;
            
            out vec4 fragColor;
            
            void main()
            {
                vec4 color = vec4(1.0, 1.0, 0.2, 0.3);
                fragColor = texture(image, gl_PointCoord) * color;
            }
            '''), GL.GL_FRAGMENT_SHADER),
        )
        GL.glBindVertexArray(self.vao)
        GL.glEnable(GL.GL_PROGRAM_POINT_SIZE)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        self.texture = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        # GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA,
            self.image.width,
            self.image.height,
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            self.pixels,
        )
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
        GL.glGenerateMipmap(GL.GL_TEXTURE_2D)

    def paintGL(self):
        GL.glBindVertexArray(self.vao)
        GL.glUseProgram(self.shader)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        GL.glDrawArrays(GL.GL_POINTS, 0, 1)
