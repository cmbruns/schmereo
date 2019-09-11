import inspect

from OpenGL import GL
from OpenGL.GL.shaders import compileShader, compileProgram
from PIL import Image
from PyQt5 import QtGui, QtWidgets


class ImageWidget(QtWidgets.QOpenGLWidget):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent=parent, *args, **kwargs)
        self.vao = None
        self.shader = None
        self.texture = None
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        md = event.mimeData()
        if md.hasImage() or md.hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent):
        md = event.mimeData()
        if md.hasUrls():
            for url in md.urls():
                img = Image.open(url.toLocalFile())
                print(img)

    def initializeGL(self) -> None:
        self.vao = GL.glGenVertexArrays(1)
        self.shader = compileProgram(
            compileShader(inspect.cleandoc('''
                #version 460
                
                const float s = 0.4;
                const vec4 SCREEN_QUAD[4] = vec4[4](
                    vec4( s, -s, 0.5, 1),
                    vec4( s,  s, 0.5, 1),
                    vec4(-s, -s, 0.5, 1),
                    vec4(-s,  s, 0.5, 1)
                );
                const vec2 TEX_COORD[4] = vec2[4](
                    vec2(1, 0),
                    vec2(1, 1),
                    vec2(0, 0),
                    vec2(0, 1)
                );
                
                out noperspective vec2 texCoord;
                
                void main() {
                    gl_Position = SCREEN_QUAD[gl_VertexID];
                    texCoord = TEX_COORD[gl_VertexID];
                }
            '''), GL.GL_VERTEX_SHADER),
            compileShader(inspect.cleandoc('''
                #version 460
                
                in noperspective vec2 texCoord;
                out vec4 frag_color;
                
                void main() {
                    frag_color = vec4(texCoord, 0.5, 1);
                }
            '''), GL.GL_FRAGMENT_SHADER),
        )
        self.texture = GL.glGenTextures(1)

    def paintGL(self) -> None:
        GL.glBindVertexArray(self.vao)
        GL.glUseProgram(self.shader)
        GL.glDrawArrays(GL.GL_TRIANGLE_STRIP, 0, 4)

    def resizeGL(self, width: int, height: int) -> None:
        pass
