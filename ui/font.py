#! /usr/bin/env python
import ctypes
import cairo
import gtk
from dtk.ui.utils import get_content_size, color_hex_to_cairo

class PycairoContext(ctypes.Structure):
    _fields_ = [("PyObject_HEAD", ctypes.c_byte * object.__basicsize__),
        ("ctx", ctypes.c_void_p),
        ("base", ctypes.c_void_p)]

_initialized = False
def create_cairo_font_face_for_file (filename, faceindex=0, loadoptions=0):
    global _initialized
    global _freetype_so
    global _cairo_so
    global _ft_lib
    global _surface

    CAIRO_STATUS_SUCCESS = 0
    FT_Err_Ok = 0

    if not _initialized:

        # find shared objects
        _freetype_so = ctypes.CDLL ("libfreetype.so.6")
        _cairo_so = ctypes.CDLL ("libcairo.so.2")

        _cairo_so.cairo_ft_font_face_create_for_ft_face.restype = ctypes.c_void_p
        _cairo_so.cairo_ft_font_face_create_for_ft_face.argtypes = [ ctypes.c_void_p, ctypes.c_int ]
        _cairo_so.cairo_set_font_face.argtypes = [ ctypes.c_void_p, ctypes.c_void_p ]
        _cairo_so.cairo_font_face_status.argtypes = [ ctypes.c_void_p ]
        _cairo_so.cairo_status.argtypes = [ ctypes.c_void_p ]

        # initialize freetype
        _ft_lib = ctypes.c_void_p ()
        if FT_Err_Ok != _freetype_so.FT_Init_FreeType (ctypes.byref (_ft_lib)):
          raise "Error initialising FreeType library."


        _surface = cairo.ImageSurface (cairo.FORMAT_A8, 0, 0)

        _initialized = True

    # create freetype face
    ft_face = ctypes.c_void_p()
    cairo_ctx = cairo.Context (_surface)
    cairo_t = PycairoContext.from_address(id(cairo_ctx)).ctx

    if FT_Err_Ok != _freetype_so.FT_New_Face (_ft_lib, filename, faceindex, ctypes.byref(ft_face)):
        raise Exception("Error creating FreeType font face for " + filename)

    # create cairo font face for freetype face
    cr_face = _cairo_so.cairo_ft_font_face_create_for_ft_face (ft_face, loadoptions)
    if CAIRO_STATUS_SUCCESS != _cairo_so.cairo_font_face_status (cr_face):
        raise Exception("Error creating cairo font face for " + filename)

    _cairo_so.cairo_set_font_face (cairo_t, cr_face)
    if CAIRO_STATUS_SUCCESS != _cairo_so.cairo_status (cairo_t):
        raise Exception("Error creating cairo font face for " + filename)

    face = cairo_ctx.get_font_face ()

    return face

def draw_font_img(text, cr, x, y, face, text_size, text_color="#000000"):
    cr.set_font_face(face)
    cr.set_source_rgb(*color_hex_to_cairo(text_color))
    cr.set_font_size(text_size)
    cr.move_to(x, y)
    cr.show_text(text)

class Example(gtk.Window):

    def __init__(self):
        super(Example, self).__init__()
        
        self.init_ui()
        gtk.main()

    def init_ui(self):    
        darea = gtk.DrawingArea()
        darea.connect("expose-event", self.on_draw)
        self.add(darea)

        self.set_title("GTK window")
        self.resize(420, 120)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("delete-event", gtk.main_quit)
        self.show_all()
    
    def on_draw(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        face = create_cairo_font_face_for_file ("/home/iceleaf/.fonts/category.ttf", 0)
        cr.set_font_face(face)
        cr.set_source_rgb(0, 0, 0)
        cr.set_font_size(24)
        
        cr.move_to(rect.x, rect.y+24)
        cr.show_text("ABCDEFGHIJKLM")
    
if __name__ == '__main__':
    print get_content_size("A", 24, "DeepinIcon")
    Example()
