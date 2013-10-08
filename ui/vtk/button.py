# call trayicon vtk api.
from utils import cairo_disable_antialias
from draw import draw_text
from utils import get_text_size, cairo_disable_antialias
from color import color_hex_to_cairo
import gtk

class SelectButton(gtk.Button):        
    def __init__(self, 
                 text="", 
                 ali_padding=0,
                 font_size=10,
                 bg_color="#ebf4fd",
                 line_color="#7da2ce"):
        gtk.Button.__init__(self)
        # init values.
        self.text = text
        self.font_size=font_size 
        self.ali_padding = ali_padding
        self.bg_color = bg_color
        self.line_color = line_color
        self.text_color = "#000000"
        self.draw_check = False
        width, height = get_text_size(self.text, font_size)
        self.set_size_request(width, height)
        # init events.
        self.add_events(gtk.gdk.ALL_EVENTS_MASK)
        self.connect("button-press-event", self.select_button_button_press_event)
        self.connect("button-release-event", self.select_button_button_release_event)
        self.connect("expose-event", self.select_button_expose_event)        

    def select_button_button_press_event(self, widget, event):
        widget.grab_add()

    def select_button_button_release_event(self, widget, event):
        widget.grab_remove()
        
    def select_button_expose_event(self, widget, event):
        cr = widget.window.cairo_create()
        rect = widget.allocation
        # 
        if widget.state == gtk.STATE_PRELIGHT:
            # draw rectangle.
            with cairo_disable_antialias(cr):
                cr.set_source_rgb(*color_hex_to_cairo(self.bg_color))
                cr.rectangle(rect.x, 
                            rect.y, 
                            rect.width, 
                            rect.height)
                cr.fill()
        
                cr.set_line_width(1)
                cr.set_source_rgb(*color_hex_to_cairo(self.line_color))
                cr.rectangle(rect.x + 1,
                             rect.y + 1, 
                             rect.width - 2,
                             rect.height - 2)
                cr.stroke()              
        if widget.state == gtk.STATE_INSENSITIVE:
            text_color = "#a6a6a6"
        else:
            text_color = self.text_color
        # get font width/height.
        font_w, font_h = get_text_size(self.text, text_size=self.font_size)
        # draw text.
        x_padding = rect.x + rect.width - font_w - self.ali_padding
        x_padding = max(20, x_padding)
        draw_text(cr, self.text,
                  x_padding,
                  rect.y + rect.height/2 - font_h/2,
                  text_size=self.font_size, 
                  text_color=text_color)
        # set size.
        if font_h > rect.height:
            widget.set_size_request(rect.width, font_h)
        return True
