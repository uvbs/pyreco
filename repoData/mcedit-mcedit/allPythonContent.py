__FILENAME__ = controls
#
#   Albow - Controls
#

from pygame import Rect, draw
from widget import Widget, overridable_property
from theme import ThemeProperty
from utils import blit_in_rect, frame_rect
import resource

#---------------------------------------------------------------------------


class Control(object):

    highlighted = overridable_property('highlighted')
    enabled = overridable_property('enabled')
    value = overridable_property('value')

    enable = None
    ref = None
    _highlighted = False
    _enabled = True
    _value = None

    def get_value(self):
        ref = self.ref
        if ref:
            return ref.get()
        else:
            return self._value

    def set_value(self, x):
        ref = self.ref
        if ref:
            ref.set(x)
        else:
            self._value = x

    def get_highlighted(self):
        return self._highlighted

    def get_enabled(self):
        enable = self.enable
        if enable:
            return enable()
        else:
            return self._enabled

    def set_enabled(self, x):
        self._enabled = x

#---------------------------------------------------------------------------


class AttrRef(object):

    def __init__(self, obj, attr):
        self.obj = obj
        self.attr = attr

    def get(self):
        return getattr(self.obj, self.attr)

    def set(self, x):
        setattr(self.obj, self.attr, x)

#---------------------------------------------------------------------------


class ItemRef(object):

    def __init__(self, obj, item):
        self.obj = obj
        self.item = item

    def get(self):
        return self.obj[self.item]

    def set(self, x):
        self.obj[self.item] = x

#---------------------------------------------------------------------------


class Label(Widget):

    text = overridable_property('text')
    align = overridable_property('align')

    hover_color = ThemeProperty('hover_color')
    highlight_color = ThemeProperty('highlight_color')
    disabled_color = ThemeProperty('disabled_color')
    highlight_bg_color = ThemeProperty('highlight_bg_color')
    hover_bg_color = ThemeProperty('hover_bg_color')
    enabled_bg_color = ThemeProperty('enabled_bg_color')
    disabled_bg_color = ThemeProperty('disabled_bg_color')

    enabled = True
    highlighted = False
    _align = 'l'

    def __init__(self, text, width=None, **kwds):
        Widget.__init__(self, **kwds)
        font = self.font
        lines = text.split("\n")
        tw, th = 0, 0
        for line in lines:
            w, h = font.size(line)
            tw = max(tw, w)
            th += h
        if width is not None:
            tw = width
        else:
            tw = max(1, tw)
        d = 2 * self.margin
        self.size = (tw + d, th + d)
        self._text = text

    def __repr__(self):
        return "Label {0}, child of {1}".format(self.text, self.parent)

    def get_text(self):
        return self._text

    def set_text(self, x):
        self._text = x

    def get_align(self):
        return self._align

    def set_align(self, x):
        self._align = x

    def draw(self, surface):
        if not self.enabled:
            fg = self.disabled_color
            bg = self.disabled_bg_color
        else:
            fg = self.fg_color
            bg = self.enabled_bg_color
            if self.is_default:
                fg = self.default_choice_color or fg
                bg = self.default_choice_bg_color or bg
            if self.is_hover:
                fg = self.hover_color or fg
                bg = self.hover_bg_color or bg
            if self.highlighted:
                fg = self.highlight_color or fg
                bg = self.highlight_bg_color or bg

        self.draw_with(surface, fg, bg)

    is_default = False

    def draw_with(self, surface, fg, bg=None):
        if bg:
            r = surface.get_rect()
            b = self.border_width
            if b:
                e = -2 * b
                r.inflate_ip(e, e)
            surface.fill(bg, r)
        m = self.margin
        align = self.align
        width = surface.get_width()
        y = m
        lines = self.text.split("\n")
        font = self.font
        dy = font.get_linesize()
        for line in lines:
            if len(line):
                size = font.size(line)
                if size[0] == 0:
                    continue

                image = font.render(line, True, fg)
                r = image.get_rect()
                r.top = y
                if align == 'l':
                    r.left = m
                elif align == 'r':
                    r.right = width - m
                else:
                    r.centerx = width // 2
                surface.blit(image, r)
            y += dy


class GLLabel(Label):
    pass


class SmallLabel(Label):
    """Small text size. See theme.py"""

#---------------------------------------------------------------------------


class ButtonBase(Control):

    align = 'c'
    action = None
    default_choice_color = ThemeProperty('default_choice_color')
    default_choice_bg_color = ThemeProperty('default_choice_bg_color')

    def mouse_down(self, event):
        if self.enabled:
            self._highlighted = True

    def mouse_drag(self, event):
        state = event in self
        if state != self._highlighted:
            self._highlighted = state
            self.invalidate()

    def mouse_up(self, event):
        if event in self:
            if self is event.clicked_widget or (event.clicked_widget and self in event.clicked_widget.all_parents()):
                self._highlighted = False
                if self.enabled:
                    self.call_handler('action')

#---------------------------------------------------------------------------


class Button(ButtonBase, Label):

    def __init__(self, text, action=None, enable=None, **kwds):
        if action:
            kwds['action'] = action
        if enable:
            kwds['enable'] = enable
        Label.__init__(self, text, **kwds)

#---------------------------------------------------------------------------


class Image(Widget):
    #  image   Image to display

    highlight_color = ThemeProperty('highlight_color')

    image = overridable_property('image')

    highlighted = False

    def __init__(self, image=None, rect=None, **kwds):
        Widget.__init__(self, rect, **kwds)
        if image:
            if isinstance(image, basestring):
                image = resource.get_image(image)
            w, h = image.get_size()
            d = 2 * self.margin
            self.size = w + d, h + d
            self._image = image

    def get_image(self):
        return self._image

    def set_image(self, x):
        self._image = x

    def draw(self, surf):
        frame = surf.get_rect()
        if self.highlighted:
            surf.fill(self.highlight_color)
        image = self.image
        r = image.get_rect()
        r.center = frame.center
        surf.blit(image, r)

#    def draw(self, surf):
#        frame = self.get_margin_rect()
#        surf.blit(self.image, frame)

#---------------------------------------------------------------------------


class ImageButton(ButtonBase, Image):
    pass

#---------------------------------------------------------------------------


class ValueDisplay(Control, Label):

    format = "%s"
    align = 'l'

    def __init__(self, width=100, **kwds):
        Label.__init__(self, "", **kwds)
        self.set_size_for_text(width)

#    def draw(self, surf):
#        value = self.value
#        text = self.format_value(value)
#        buf = self.font.render(text, True, self.fg_color)
#        frame = surf.get_rect()
#        blit_in_rect(surf, buf, frame, self.align, self.margin)

    def get_text(self):
        return self.format_value(self.value)

    def format_value(self, value):
        if value is not None:
            return self.format % value
        else:
            return ""


class SmallValueDisplay(ValueDisplay):
    pass


class ValueButton(ButtonBase, ValueDisplay):

    align = 'c'

    def get_text(self):
        return self.format_value(self.value)

#---------------------------------------------------------------------------


class CheckControl(Control):

    def mouse_down(self, e):
        self.value = not self.value

    def get_highlighted(self):
        return self.value

#---------------------------------------------------------------------------


class CheckWidget(Widget):

    default_size = (16, 16)
    margin = 4
    border_width = 1
    check_mark_tweak = 2

    smooth = ThemeProperty('smooth')

    def __init__(self, **kwds):
        Widget.__init__(self, Rect((0, 0), self.default_size), **kwds)

    def draw(self, surf):
        if self.highlighted:
            r = self.get_margin_rect()
            fg = self.fg_color
            d = self.check_mark_tweak
            p1 = (r.left, r.centery - d)
            p2 = (r.centerx - d, r.bottom)
            p3 = (r.right, r.top - d)
            if self.smooth:
                draw.aalines(surf, fg, False, [p1, p2, p3])
            else:
                draw.lines(surf, fg, False, [p1, p2, p3])

#---------------------------------------------------------------------------


class CheckBox(CheckControl, CheckWidget):
    pass

#---------------------------------------------------------------------------


class RadioControl(Control):

    setting = None

    def get_highlighted(self):
        return self.value == self.setting

    def mouse_down(self, e):
        self.value = self.setting

#---------------------------------------------------------------------------


class RadioButton(RadioControl, CheckWidget):
    pass

########NEW FILE########
__FILENAME__ = dialogs
import textwrap
from pygame import Rect, event
from pygame.locals import *
from widget import Widget
from controls import Label, Button
from layout import Row, Column
from fields import TextField


class Modal(object):

    enter_response = True
    cancel_response = False

    def ok(self):
        self.dismiss(True)

    def cancel(self):
        self.dismiss(False)


class Dialog(Modal, Widget):

    click_outside_response = None

    def __init__(self, client=None, responses=None,
            default=0, cancel=-1, **kwds):
        Widget.__init__(self, **kwds)
        if client or responses:
            rows = []
            w1 = 0
            w2 = 0
            if client:
                rows.append(client)
                w1 = client.width
            if responses:
                buttons = Row([
                    Button(text, action=lambda t=text: self.dismiss(t))
                        for text in responses])
                rows.append(buttons)
                w2 = buttons.width
            if w1 < w2:
                a = 'l'
            else:
                a = 'r'
            contents = Column(rows, align=a)
            m = self.margin
            contents.topleft = (m, m)
            self.add(contents)
            self.shrink_wrap()
        if responses and default is not None:
            self.enter_response = responses[default]
        if responses and cancel is not None:
            self.cancel_response = responses[cancel]

    def mouse_down(self, e):
        if not e in self:
            response = self.click_outside_response
            if response is not None:
                self.dismiss(response)


class QuickDialog(Dialog):
    """ Dialog that closes as soon as you click outside or press a key"""
    def mouse_down(self, evt):
        if evt not in self:
            self.dismiss(-1)
            if evt.button != 1:
                event.post(evt)

    def key_down(self, evt):
        self.dismiss()
        event.post(evt)


def wrapped_label(text, wrap_width, **kwds):
    paras = text.split("\n")
    text = "\n".join([textwrap.fill(para, wrap_width) for para in paras])
    return Label(text, **kwds)

#def alert(mess, wrap_width = 60, **kwds):
#    box = Dialog(**kwds)
#    d = box.margin
#    lb = wrapped_label(mess, wrap_width)
#    lb.topleft = (d, d)
#    box.add(lb)
#    box.shrink_wrap()
#    return box.present()


def alert(mess, **kwds):
    ask(mess, ["OK"], **kwds)


def ask(mess, responses=["OK", "Cancel"], default=0, cancel=-1,
        wrap_width=60, **kwds):
    box = Dialog(**kwds)
    d = box.margin
    lb = wrapped_label(mess, wrap_width)
    lb.topleft = (d, d)
    buts = []
    for caption in responses:
        but = Button(caption, action=lambda x=caption: box.dismiss(x))
        buts.append(but)
    brow = Row(buts, spacing=d)
    lb.width = max(lb.width, brow.width)
    col = Column([lb, brow], spacing=d, align='r')
    col.topleft = (d, d)
    if default is not None:
        box.enter_response = responses[default]
        buts[default].is_default = True
    else:
        box.enter_response = None
    if cancel is not None:
        box.cancel_response = responses[cancel]
    else:
        box.cancel_response = None
    box.add(col)
    box.shrink_wrap()
    return box.present()


def input_text(prompt, width, initial=None, **kwds):
    box = Dialog(**kwds)
    d = box.margin

    def ok():
        box.dismiss(True)

    def cancel():
        box.dismiss(False)

    lb = Label(prompt)
    lb.topleft = (d, d)
    tf = TextField(width)
    if initial:
        tf.set_text(initial)
    tf.enter_action = ok
    tf.escape_action = cancel
    tf.top = lb.top
    tf.left = lb.right + 5
    box.add(lb)
    box.add(tf)
    tf.focus()
    box.shrink_wrap()
    if box.present():
        return tf.get_text()
    else:
        return None

########NEW FILE########
__FILENAME__ = fields
#
#   Albow - Fields
#

from pygame import draw
import pygame
from pygame.locals import K_LEFT, K_RIGHT, K_TAB, K_c, K_v, SCRAP_TEXT, K_UP, K_DOWN
from widget import Widget, overridable_property
from controls import Control

#---------------------------------------------------------------------------


class TextEditor(Widget):

    upper = False
    tab_stop = True

    _text = u""

    def __init__(self, width, upper=None, **kwds):
        Widget.__init__(self, **kwds)
        self.set_size_for_text(width)
        if upper is not None:
            self.upper = upper
        self.insertion_point = None

    def get_text(self):
        return self._text

    def set_text(self, text):
        self._text = text

    text = overridable_property('text')

    def draw(self, surface):
        frame = self.get_margin_rect()
        fg = self.fg_color
        font = self.font
        focused = self.has_focus()
        text, i = self.get_text_and_insertion_point()
        if focused and i is None:
            surface.fill(self.sel_color, frame)
        image = font.render(text, True, fg)
        surface.blit(image, frame)
        if focused and i is not None:
            x, h = font.size(text[:i])
            x += frame.left
            y = frame.top
            draw.line(surface, fg, (x, y), (x, y + h - 1))

    def key_down(self, event):
        if not (event.cmd or event.alt):
            k = event.key
            if k == K_LEFT:
                self.move_insertion_point(-1)
                return
            if k == K_RIGHT:
                self.move_insertion_point(1)
                return
            if k == K_TAB:
                self.attention_lost()
                self.tab_to_next()
                return
            try:
                c = event.unicode
            except ValueError:
                c = ""
            if self.insert_char(c) != 'pass':
                return
        if event.cmd and event.unicode:
            if event.key == K_c:
                try:
                    pygame.scrap.put(SCRAP_TEXT, self.text)
                except:
                    print "scrap not available"

            elif event.key == K_v:
                try:
                    t = pygame.scrap.get(SCRAP_TEXT).replace('\0', '')
                    self.text = t
                except:
                    print "scrap not available"
                #print repr(t)
            else:
                self.attention_lost()

        self.call_parent_handler('key_down', event)

    def get_text_and_insertion_point(self):
        text = self.get_text()
        i = self.insertion_point
        if i is not None:
            i = max(0, min(i, len(text)))
        return text, i

    def move_insertion_point(self, d):
        text, i = self.get_text_and_insertion_point()
        if i is None:
            if d > 0:
                i = len(text)
            else:
                i = 0
        else:
            i = max(0, min(i + d, len(text)))
        self.insertion_point = i

    def insert_char(self, c):
        if self.upper:
            c = c.upper()
        if c <= "\x7f":
            if c == "\x08" or c == "\x7f":
                text, i = self.get_text_and_insertion_point()
                if i is None:
                    text = ""
                    i = 0
                else:
                    text = text[:i - 1] + text[i:]
                    i -= 1
                self.change_text(text)
                self.insertion_point = i
                return
            elif c == "\r" or c == "\x03":
                return self.call_handler('enter_action')
            elif c == "\x1b":
                return self.call_handler('escape_action')
            elif c >= "\x20":
                if self.allow_char(c):
                    text, i = self.get_text_and_insertion_point()
                    if i is None:
                        text = c
                        i = 1
                    else:
                        text = text[:i] + c + text[i:]
                        i += 1
                    self.change_text(text)
                    self.insertion_point = i
                    return
        return 'pass'

    def allow_char(self, c):
        return True

    def mouse_down(self, e):
        self.focus()
        if e.num_clicks == 2:
            self.insertion_point = None
            return

        x, y = e.local
        i = self.pos_to_index(x)
        self.insertion_point = i

    def pos_to_index(self, x):
        text = self.get_text()
        font = self.font

        def width(i):
            return font.size(text[:i])[0]

        i1 = 0
        i2 = len(text)
        x1 = 0
        x2 = width(i2)
        while i2 - i1 > 1:
            i3 = (i1 + i2) // 2
            x3 = width(i3)
            if x > x3:
                i1, x1 = i3, x3
            else:
                i2, x2 = i3, x3
        if x - x1 > (x2 - x1) // 2:
            i = i2
        else:
            i = i1

        return i

    def change_text(self, text):
        self.set_text(text)
        self.call_handler('change_action')

#---------------------------------------------------------------------------


class Field(Control, TextEditor):
    #  type      func(string) -> value
    #  editing   boolean

    empty = NotImplemented
    format = u"%s"
    min = None
    max = None
    enter_passes = False

    def __init__(self, width=None, **kwds):
        min = self.predict_attr(kwds, 'min')
        max = self.predict_attr(kwds, 'max')
        if 'format' in kwds:
            self.format = kwds.pop('format')
        if 'empty' in kwds:
            self.empty = kwds.pop('empty')
        self.editing = False
        if width is None:
            w1 = w2 = ""
            if min is not None:
                w1 = self.format_value(min)
            if max is not None:
                w2 = self.format_value(max)
            if w2:
                if len(w1) > len(w2):
                    width = w1
                else:
                    width = w2
        if width is None:
            width = 100
        TextEditor.__init__(self, width, **kwds)

    def format_value(self, x):
        if x == self.empty:
            return ""
        else:
            return self.format % x

    def get_text(self):
        if self.editing:
            return self._text
        else:
            return self.format_value(self.value)

    def set_text(self, text):
        self.editing = True
        self._text = text
        if self.should_commit_immediately(text):
            self.commit()

    def should_commit_immediately(self, text):
        return False

    def enter_action(self):
        if self.editing:
            self.commit()
        elif self.enter_passes:
            return 'pass'

    def escape_action(self):
        if self.editing:
            self.editing = False
            self.insertion_point = None
        else:
            return 'pass'

    def attention_lost(self):
        self.commit(notify=True)

    def clamp_value(self, value):
        if self.max is not None:
            value = min(value, self.max)
        if self.min is not None:
            value = max(value, self.min)
        return value

    def commit(self, notify=False):
        if self.editing:
            text = self._text
            if text:
                try:
                    value = self.type(text)
                except ValueError:
                    return
                value = self.clamp_value(value)
            else:
                value = self.empty
                if value is NotImplemented:
                    return
            self.value = value
            self.insertion_point = None
            if notify:
                self.change_text(unicode(value))
            else:
                self._text = unicode(value)
            self.editing = False

        else:
            self.insertion_point = None

#    def get_value(self):
#        self.commit()
#        return Control.get_value(self)
#
#    def set_value(self, x):
#        Control.set_value(self, x)
#        self.editing = False

#---------------------------------------------------------------------------


class TextField(Field):
    type = unicode
    _value = u""


class IntField(Field):
    tooltipText = "Point here and use mousewheel to adjust"

    def type(self, i):
        try:
            return eval(i)
        except:
            try:
                return int(i)
            except:
                return 0

    _shift_increment = 16
    _increment = 1

    @property
    def increment(self):
        if key.get_mods() & KMOD_SHIFT:
            return self._shift_increment
        else:
            return self._increment
        return self._increment

    @increment.setter
    def increment(self, val):
        self._increment = val

    def decrease_value(self):
        self.value = self.clamp_value(self.value - self.increment)

    def increase_value(self):
        self.value = self.clamp_value(self.value + self.increment)

    def mouse_down(self, evt):
        if evt.button == 5:
            self.decrease_value()

            self.change_text(str(self.value))

        elif evt.button == 4:
            self.increase_value()
            self.change_text(str(self.value))

        else:
            Field.mouse_down(self, evt)

    allowed_chars = '-+*/<>()0123456789'

    def allow_char(self, c):
        return c in self.allowed_chars

    def should_commit_immediately(self, text):
        try:
            return str(eval(text)) == text
        except:
            return False


class TimeField(Field):
    allowed_chars = ':0123456789 APMapm'

    def format_value(self, hm):
        format = "%d:%02d"
        h, m = hm
        if h >= 12:
            h -= 12
            return format % (h or 12, m) + " PM"
        else:
            return format % (h or 12, m) + " AM"

    def allow_char(self, c):
        return c in self.allowed_chars

    def type(self, i):
        h, m = 0, 0
        i = i.upper()

        pm = "PM" in i
        for a in "APM":
            i = i.replace(a, "")

        parts = i.split(":")

        if len(parts):
            h = int(parts[0])
        if len(parts) > 1:
            m = int(parts[1])

        if pm and h < 12:
            h += 12
        h %= 24
        m %= 60
        return h, m

    def mouse_down(self, evt):
        if evt.button == 5:
            delta = -1
        elif evt.button == 4:
            delta = 1
        else:
            return Field.mouse_down(self, evt)

        (h, m) = self.value
        pos = self.pos_to_index(evt.local[0])
        if pos < 2:
            h += delta
        elif pos < 5:
            m += delta
        else:
            h = (h + 12) % 24

        self.value = (h, m)

    def set_value(self, v):
        h, m = v
        super(TimeField, self).set_value((h % 24, m % 60))

from pygame import key
from pygame.locals import KMOD_SHIFT


class FloatField(Field):
    type = float
    _increment = 1.0
    _shift_increment = 16.0
    tooltipText = "Point here and use mousewheel to adjust"

    allowed_chars = '-+.0123456789f'

    def allow_char(self, c):
        return c in self.allowed_chars

    @property
    def increment(self):
        if key.get_mods() & KMOD_SHIFT:
            return self._shift_increment
        return self._increment

    @increment.setter
    def increment(self, val):
        self._increment = self.clamp_value(val)

    def decrease_value(self):
        self.value = self.clamp_value(self.value - self.increment)

    def increase_value(self):
        self.value = self.clamp_value(self.value + self.increment)

    def mouse_down(self, evt):
        if evt.button == 5:
            self.decrease_value()

            self.change_text(str(self.value))

        elif evt.button == 4:
            self.increase_value()
            self.change_text(str(self.value))

        else:
            Field.mouse_down(self, evt)

#---------------------------------------------------------------------------


class TextEditorWrapped(Widget):

    upper = False
    tab_stop = True

    _text = u""

    def __init__(self, width, lines, upper=None, **kwds):
        Widget.__init__(self, **kwds)
        self.set_size_for_text(width, lines)
        if upper is not None:
            self.upper = upper
        self.insertion_point = None
        self.insertion_step = None
        self.insertion_line = None
        self.selection_start = None
        self.selection_end = None
        self.topLine = 0
        self.dispLines = lines
        self.textChanged = True

    def get_text(self):
        return self._text

    def set_text(self, text):
        self._text = text
        self.textChanged = True

    text = overridable_property('text')
#Text line list and text line EoL index reference
    textL = []
    textRefList = []
        
    def draw(self, surface):
        frame = self.get_margin_rect()
        frameW, frameH = frame.size
        fg = self.fg_color
        font = self.font
        focused = self.has_focus()
        text, i, il = self.get_text_and_insertion_data()
        ip = self.insertion_point

        self.updateTextWrap()

#Scroll the text up or down if necessary
        if self.insertion_line > self.topLine + self.dispLines - 1:
            self.scroll_down()
        elif self.insertion_line < self.topLine:
            self.scroll_up()

#Draw Border
        draw.rect(surface, self.sel_color, pygame.Rect(frame.left,frame.top,frame.size[0],frame.size[1]), 1)

#Draw Selection Highlighting if Applicable
        if focused and ip is None:
            if self.selection_start is None or self.selection_end is None:
                surface.fill(self.sel_color, frame)
            else:
                startLine, startStep = self.get_char_position(self.selection_start)
                endLine, endStep = self.get_char_position(self.selection_end)
                rects = []

                if startLine == endLine:
                    if startStep > endStep:
                        x1, h = font.size(self.textL[startLine][0:endStep])
                        x2, h = font.size(self.textL[startLine][0:startStep])
                        x1 += frame.left
                        x2 += frame.left
                        lineOffset = startLine - self.topLine
                        y = frame.top + lineOffset*h
                        if lineOffset >= 0:
                            selRect = pygame.Rect(x1,y,(x2-x1),h)
                    else:
                        x1, h = font.size(self.textL[startLine][0:startStep])
                        x2, h = font.size(self.textL[startLine][0:endStep])
                        x1 += frame.left
                        x2 += frame.left
                        lineOffset = startLine - self.topLine
                        y = frame.top + lineOffset*h
                        if lineOffset >= 0:
                            selRect = pygame.Rect(x1,y,(x2-x1),h)
                    draw.rect(surface, self.sel_color, selRect)
                elif startLine < endLine:
                    x1, h = font.size(self.textL[startLine][0:startStep])
                    x2, h = font.size(self.textL[endLine][0:endStep])
                    x1 += frame.left
                    x2 += frame.left
                    lineOffsetS = startLine - self.topLine
                    lineOffsetE = endLine - self.topLine
                    lDiff = lineOffsetE - lineOffsetS
                    while lDiff > 1 and lineOffsetS+lDiff >= 0 and lineOffsetS+lDiff < self.dispLines:
                        y = frame.top + lineOffsetS*h + (lDiff-1)*h
                        rects.append(pygame.Rect(frame.left,y,frame.right-frame.left,h))
                        lDiff += -1
                    y = frame.top + lineOffsetS*h
                    if lineOffsetS >= 0:
                        rects.append(pygame.Rect(x1,y,frame.right-x1,h))
                    y = frame.top + lineOffsetE*h
                    if lineOffsetE < self.dispLines:
                        rects.append(pygame.Rect(frame.left,y,x2-frame.left,h))
                    for selRect in rects:
                        draw.rect(surface, self.sel_color, selRect)                            
                elif startLine > endLine:
                    x2, h = font.size(self.textL[startLine][0:startStep])
                    x1, h = font.size(self.textL[endLine][0:endStep])
                    x1 += frame.left
                    x2 += frame.left
                    lineOffsetE = startLine - self.topLine
                    lineOffsetS = endLine - self.topLine
                    lDiff = lineOffsetE - lineOffsetS
                    while lDiff > 1 and lineOffsetS+lDiff >= 0 and lineOffsetS+lDiff < self.dispLines:
                        y = frame.top + lineOffsetS*h + (lDiff-1)*h
                        rects.append(pygame.Rect(frame.left,y,frame.right-frame.left,h))
                        lDiff += -1
                    y = frame.top + lineOffsetS*h
                    if lineOffsetS >= 0:
                        rects.append(pygame.Rect(x1,y,frame.right-x1,h))
                    y = frame.top + lineOffsetE*h
                    if lineOffsetE < self.dispLines:
                        rects.append(pygame.Rect(frame.left,y,x2-frame.left,h))
                    for selRect in rects:
                        draw.rect(surface, self.sel_color, selRect)

# Draw Lines of Text
        h = 0
        for textLine in self.textL[self.topLine:self.topLine + self.dispLines]:
            image = font.render(textLine, True, fg)
            surface.blit(image, frame.move(0,h))
            h += font.size(textLine)[1]

# Draw Cursor if Applicable                
        if focused and ip is not None and i is not None and il is not None:
            if(self.textL):
                x, h = font.size(self.textL[il][:i])
            else:
                x, h = (0, font.size("X")[1])
            x += frame.left
            y = frame.top + h*(il-self.topLine)
            draw.line(surface, fg, (x, y), (x, y + h - 1))

    def key_down(self, event):
        if not (event.cmd or event.alt):
            k = event.key
            if k == K_LEFT:
                self.move_insertion_point(-1)
                return
            if k == K_RIGHT:
                self.move_insertion_point(1)
                return
            if k == K_TAB:
                self.attention_lost()
                self.tab_to_next()
                return
            if k == K_DOWN:
                self.move_insertion_line(1)
                return
            if k == K_UP:
                self.move_insertion_line(-1)
                return
            try:
                c = event.unicode
            except ValueError:
                c = ""
            if self.insert_char(c) != 'pass':
                return
        if event.cmd and event.unicode:
            if event.key == K_c:
                try:
                    pygame.scrap.put(SCRAP_TEXT, self.text)
                except:
                    print "scrap not available"

            elif event.key == K_v:
                try:
                    t = pygame.scrap.get(SCRAP_TEXT).replace('\0', '')
                    if t != None:
                        if self.insertion_point is not None:
                            self.text = self.text[:self.insertion_point] + t + self.text[self.insertion_point:]
                            self.insertion_point += len(t)
                            self.textChanged = True
                            self.sync_line_and_step()
                        elif self.insertion_point is None and (self.selection_start is None or self.selection_end is None):
                            self.text = t
                            self.insertion_point = len(t)
                            self.textChanged = True
                            self.sync_line_and_step()
                        elif self.insertion_point is None and self.selection_start is not None and self.selection_end is not None:
                            self.selection_point = min(self.selection_start,self.selection_end) + len(t)
                            self.text = self.text[:(min(self.selection_start,self.selection_end))] + t + self.text[(max(self.selection_start,self.selection_end)):]
                            self.selection_start = None
                            self.selection_end = None
                            self.textChanged = True
                            self.sync_line_and_step()
                except:
                    print "scrap not available"
                #print repr(t)
            else:
                self.attention_lost()

        self.call_parent_handler('key_down', event)

    def get_text_and_insertion_point(self):
        text = self.get_text()
        i = self.insertion_point
        if i is not None:
            i = max(0, min(i, len(text)))
        return text, i
                
    def get_text_and_insertion_data(self):
        text = self.get_text()
        i = self.insertion_step
        il = self.insertion_line
        if il is not None:
            il = max(0, min(il, (len(self.textL)-1)))
        if i is not None and il is not None and len(self.textL) > 0:
            i = max(0, min(i, len(self.textL[il])-1))
        return text, i, il

    def move_insertion_point(self, d):
        text, i = self.get_text_and_insertion_point()
        if i is None:
            if d > 0:
                i = len(text)
            else:
                i = 0
        else:
            i = max(0, min(i + d, len(text)))
        self.insertion_point = i
        self.sync_line_and_step()

    def sync_line_and_step(self):
        self.updateTextWrap()
        self.sync_insertion_line()
        self.sync_insertion_step()

    def sync_insertion_line(self):
        ip = self.insertion_point
        i = 0

        for refVal in self.textRefList:
            if ip > refVal:
                i += 1
            elif ip <= refVal:
                break
        self.insertion_line = i

    def sync_insertion_step(self):
        ip = self.insertion_point
        il = self.insertion_line

        if ip is None:
            self.move_insertion_point(0)
            ip = self.insertion_point
        if il is None:
            self.move_insertion_line(0)
            il = self.insertion_line

        if il > 0:
            refPoint = self.textRefList[il-1]
        else:
            refPoint = 0
        self.insertion_step = ip - refPoint

    def get_char_position(self, i):
        j = 0

        for refVal in self.textRefList:
            if i > refVal:
                j += 1
            elif i <= refVal:
                break
        line = j

        if line > 0:
            refPoint = self.textRefList[line-1]
        else:
            refPoint = 0
        step = i - refPoint

        return line, step

    def move_insertion_line(self, d):
        text, i, il = self.get_text_and_insertion_data()

        if self.selection_end is not None:
            endLine, endStep = self.get_char_position(self.selection_end)
            il = endLine
            i = endStep
            self.insertion_step = i
            self.selection_end = None
            self.selection_start = None
        if il is None:
            if d > 0:
                if len(self.textL) > 1:
                    self.insertion_line = d
                else:
                    self.insertion_line = 0
            else:
                self.insertion_line = 0
        if i is None:
            self.insertion_step = 0
        elif il+d >= 0 and il+d < len(self.textL):
            self.insertion_line = il+d
        if self.insertion_line > 0:
            self.insertion_point = self.textRefList[self.insertion_line-1] + self.insertion_step
            if self.insertion_point > len(self.text):
                self.insertion_point = len(self.text)
        else:
            if self.insertion_step is not None:
                self.insertion_point = self.insertion_step
            else:
                self.insertion_point = 0
                self.insertion_step = 0

    def insert_char(self, c):
        if self.upper:
            c = c.upper()
        if c <= u"\xff":
            if c == "\x08" or c == "\x7f":
                text, i = self.get_text_and_insertion_point()
                if i is None and (self.selection_start is None or self.selection_end is None):
                    text = ""
                    i = 0
                    self.insertion_line = i
                    self.insertion_step = i
                elif i is None and self.selection_start is not None and self.selection_end is not None:
                    i = min(self.selection_start,self.selection_end)
                    text = text[:(min(self.selection_start,self.selection_end))] + text[(max(self.selection_start,self.selection_end)):]
                    self.selection_start = None
                    self.selection_end = None
                elif i > 0:
                    text = text[:i - 1] + text[i:]
                    i -= 1
                self.change_text(text)
                self.insertion_point = i
                self.sync_line_and_step()
                return
            elif c == "\r" or c == "\x03":
                return self.call_handler('enter_action')
            elif c == "\x1b":
                return self.call_handler('escape_action')
            elif c >= "\x20":
                if self.allow_char(c):
                    text, i = self.get_text_and_insertion_point()
                    if i is None and (self.selection_start is None or self.selection_end is None):
                        text = c
                        i = 1
                    elif i is None and self.selection_start is not None and self.selection_end is not None:
                        i = min(self.selection_start,self.selection_end) + 1
                        text = text[:(min(self.selection_start,self.selection_end))] + c + text[(max(self.selection_start,self.selection_end)):]
                        self.selection_start = None
                        self.selection_end = None
                    else:
                        text = text[:i] + c + text[i:]
                        i += 1
                    self.change_text(text)
                    self.insertion_point = i
                    self.sync_line_and_step()
                    return
        return 'pass'

    def allow_char(self, c):
        return True

    def mouse_down(self, e):
        self.focus()
        if e.button == 1:
            if e.num_clicks == 2:
                self.insertion_point = None
                self.selection_start = None
                self.selection_end = None
                return

            x, y = e.local
            i = self.pos_to_index(x,y)
            self.insertion_point = i
            self.selection_start = None
            self.selection_end = None
            self.sync_line_and_step()

        if e.button == 5:
#            self.scroll_down()
            self.move_insertion_line(1)

        if e.button == 4:
#            self.scroll_up()
            self.move_insertion_line(-1)

    def mouse_drag(self, e):
        x, y = e.local
        i = self.pos_to_index(x,y)

        if self.insertion_point is not None:
            if i != self.insertion_point:
                if self.selection_start is None:
                    self.selection_start = self.insertion_point
                self.selection_end = i
                self.insertion_point = None
        else:
            if self.selection_start is None:
                self.selection_start = i
            else:
                if self.selection_start == i:
                    self.selection_start = None
                    self.selection_end = None
                    self.insertion_point = i
                else:
                    self.selection_end = i
                

    def pos_to_index(self, x, y):
        text = self.get_text()
        textL = self.textL
        textRef = self.textRefList
        topLine = self.topLine
        dispLines = self.dispLines
        font = self.font

        if textL:
            h = font.size("X")[1]
            line = y//h

            if line >= dispLines:
                line = dispLines - 1

            line = line + topLine

            if line >= len(textL):
                line = len(textL) - 1
                
            if line < 0:
                line = 0

            def width(i):
                return font.size(textL[line][:i])[0]

            i1 = 0
            i2 = len(textL[line])
            x1 = 0
            x2 = width(i2)
            while i2 - i1 > 1:
                i3 = (i1 + i2) // 2
                x3 = width(i3)
                if x > x3:
                    i1, x1 = i3, x3
                else:
                    i2, x2 = i3, x3
            if x - x1 > (x2 - x1) // 2:
                i = i2
            else:
                i = i1
            if line > 0:
                i = i + textRef[line-1]
        else:
            i = 0
        return i

    def change_text(self, text):
        self.set_text(text)
        self.textChanged = True
        self.updateTextWrap()
        self.call_handler('change_action')
                
    def scroll_up(self):
        if self.topLine-1 >= 0:
            self.topLine += -1
    
    def scroll_down(self):
        if self.topLine+1 < len(self.textL)-self.dispLines + 1:
            self.topLine += 1
            
    def updateTextWrap(self):
        # Update text wrapping for box
        font = self.font
        frame = self.get_margin_rect()
        frameW, frameH = frame.size
        if(self.textChanged):
            ix = 0
            iz = 0
            textLi = 0
            text = self.text
            textL = []
            textR = []
            while ix < len(text):
                ix += 1
                if ix == '\r' or ix == '\x03' or ix == '\n':
                    print("RETURN FOUND")
                    if len(textL) > textLi:
                        textL[textLi] = text[iz:ix]
                        textR[textLi] = ix
                    else:
                        textL.append(text[iz:ix])
                        textR.append(ix)
                    iz = ix + 1
                    textLi += 1
                segW = font.size(text[iz:ix])[0]
                if segW > frameW:
                    if len(textL) > textLi:
                        textL[textLi] = text[iz:ix-1]
                        textR[textLi] = ix-1
                    else:
                        textL.append(text[iz:ix-1])
                        textR.append(ix-1)
                    iz = ix-1
                    textLi += 1
            if iz < ix:
                if len(textL) > textLi:
                    textL[textLi] = text[iz:ix]
                    textR[textLi] = ix
                else:
                    textL.append(text[iz:ix])
                    textR.append(ix)
                iz = ix
                textLi += 1                             
            textL = textL[:textLi]
            textR = textR[:textLi]
            self.textL = textL
            self.textRefList = textR
            self.textChanged = False

            i = 0
            
#---------------------------------------------------------------------------

class FieldWrapped(Control, TextEditorWrapped):
    #  type      func(string) -> value
    #  editing   boolean

    empty = NotImplemented
    format = u"%s"
    min = None
    max = None
    enter_passes = False

    def __init__(self, width=None, lines=1, **kwds):
        min = self.predict_attr(kwds, 'min')
        max = self.predict_attr(kwds, 'max')
        if 'format' in kwds:
            self.format = kwds.pop('format')
        if 'empty' in kwds:
            self.empty = kwds.pop('empty')
        self.editing = False
        if width is None:
            w1 = w2 = ""
            if min is not None:
                w1 = self.format_value(min)
            if max is not None:
                w2 = self.format_value(max)
            if w2:
                if len(w1) > len(w2):
                    width = w1
                else:
                    width = w2
        if width is None:
            width = 100
        if lines is None:
            lines = 1
        TextEditorWrapped.__init__(self, width, lines, **kwds)

    def format_value(self, x):
        if x == self.empty:
            return ""
        else:
            return self.format % x

    def get_text(self):
        if self.editing:
            return self._text
        else:
            return self.format_value(self.value)

    def set_text(self, text):
        self.editing = True
        self._text = text
        if self.should_commit_immediately(text):
            self.commit()

    def should_commit_immediately(self, text):
        return False

    def enter_action(self):
        if self.editing:
            self.commit()
        elif self.enter_passes:
            return 'pass'

    def escape_action(self):
        if self.editing:
            self.editing = False
            self.insertion_point = None
        else:
            return 'pass'

    def attention_lost(self):
        self.commit(notify=True)

    def clamp_value(self, value):
        if self.max is not None:
            value = min(value, self.max)
        if self.min is not None:
            value = max(value, self.min)
        return value

    def commit(self, notify=False):
        if self.editing:
            text = self._text
            if text:
                try:
                    value = self.type(text)
                except ValueError:
                    return
                value = self.clamp_value(value)
            else:
                value = self.empty
                if value is NotImplemented:
                    return
            self.value = value
            self.insertion_point = None
            if notify:
                self.change_text(unicode(value))
            else:
                self._text = unicode(value)
            self.editing = False

        else:
            self.insertion_point = None

#    def get_value(self):
#        self.commit()
#        return Control.get_value(self)
#
#    def set_value(self, x):
#        Control.set_value(self, x)
#        self.editing = False

#---------------------------------------------------------------------------

class TextFieldWrapped(FieldWrapped):
    type = unicode
    _value = u""

########NEW FILE########
__FILENAME__ = file_dialogs
# -*- coding: utf-8 -*-
#
#   Albow - File Dialogs
#

import os
from pygame import draw, Rect
from pygame.locals import *
from albow.widget import Widget
from albow.dialogs import Dialog, ask, alert
from albow.controls import Label, Button
from albow.fields import TextField
from albow.layout import Row, Column
from albow.palette_view import PaletteView
from albow.theme import ThemeProperty


class DirPathView(Widget):

    def __init__(self, width, client, **kwds):
        Widget.__init__(self, **kwds)
        self.set_size_for_text(width)
        self.client = client

    def draw(self, surf):
        frame = self.get_margin_rect()
        image = self.font.render(self.client.directory, True, self.fg_color)
        tw = image.get_width()
        mw = frame.width
        if tw <= mw:
            x = 0
        else:
            x = mw - tw
        surf.blit(image, (frame.left + x, frame.top))


class FileListView(PaletteView):

    #scroll_button_color = (255, 255, 0)

    def __init__(self, width, client, **kwds):
        font = self.predict_font(kwds)
        h = font.get_linesize()
        d = 2 * self.predict(kwds, 'margin')
        PaletteView.__init__(self, (width - d, h), 10, 1, scrolling=True, **kwds)
        self.client = client
        self.selection = None
        self.names = []

    def update(self):
        client = self.client
        dir = client.directory
        suffixes = client.suffixes

        def filter(name):
            path = os.path.join(dir, name)
            return os.path.isdir(path) or self.client.filter(path)

        try:
            names = [name for name in os.listdir(dir) if filter(name)]
                #if not name.startswith(".") and filter(name)]
        except EnvironmentError, e:
            alert(u"%s: %s" % (dir, e))
            names = []
        self.names = sorted(names)
        self.selection = None
        self.scroll = 0

    def num_items(self):
        return len(self.names)

    #def draw_prehighlight(self, surf, item_no, rect):
    #    draw.rect(surf, self.sel_color, rect)

    def draw_item(self, surf, item_no, rect):
        font = self.font
        color = self.fg_color
        buf = self.font.render(self.names[item_no], True, color)
        surf.blit(buf, rect)

    def click_item(self, item_no, e):
        self.selection = item_no
        self.client.dir_box_click(e.num_clicks == 2)

    def item_is_selected(self, item_no):
        return item_no == self.selection

    def get_selected_name(self):
        sel = self.selection
        if sel is not None:
            return self.names[sel]
        else:
            return ""


class FileDialog(Dialog):

    box_width = 250
    default_prompt = None
    up_button_text = ThemeProperty("up_button_text")

    def __init__(self, prompt=None, suffixes=None, **kwds):
        Dialog.__init__(self, **kwds)
        label = None
        d = self.margin
        self.suffixes = suffixes or ("",)
        up_button = Button(self.up_button_text, action=self.go_up)
        dir_box = DirPathView(self.box_width - up_button.width - 10, self)
        self.dir_box = dir_box
        top_row = Row([dir_box, up_button])
        list_box = FileListView(self.box_width - 16, self)
        self.list_box = list_box
        ctrls = [top_row, list_box]
        prompt = prompt or self.default_prompt
        if prompt:
            label = Label(prompt)
        if self.saving:
            filename_box = TextField(self.box_width)
            filename_box.change_action = self.update
            filename_box._enter_action = filename_box.enter_action
            filename_box.enter_action = self.enter_action
            self.filename_box = filename_box
            ctrls.append(Column([label, filename_box], align='l', spacing=0))
        else:
            if label:
                ctrls.insert(0, label)
        ok_button = Button(self.ok_label, action=self.ok, enable=self.ok_enable)
        self.ok_button = ok_button
        cancel_button = Button("Cancel", action=self.cancel)
        vbox = Column(ctrls, align='l', spacing=d)
        vbox.topleft = (d, d)
        y = vbox.bottom + d
        ok_button.topleft = (vbox.left, y)
        cancel_button.topright = (vbox.right, y)
        self.add(vbox)
        self.add(ok_button)
        self.add(cancel_button)
        self.shrink_wrap()
        self._directory = None
        self.directory = os.getcwdu()
        #print "FileDialog: cwd =", repr(self.directory) ###
        if self.saving:
            filename_box.focus()

    def get_directory(self):
        return self._directory

    def set_directory(self, x):
        x = os.path.abspath(x)
        while not os.path.exists(x):
            y = os.path.dirname(x)
            if y == x:
                x = os.getcwdu()
                break
            x = y
        if self._directory != x:
            self._directory = x
            self.list_box.update()
            self.update()

    directory = property(get_directory, set_directory)

    def filter(self, path):
        suffixes = self.suffixes
        if not suffixes or os.path.isdir(path):
            #return os.path.isfile(path)
            return True
        for suffix in suffixes:
            if path.endswith(suffix.lower()):
                return True

    def update(self):
        pass

    def go_up(self):
        self.directory = os.path.dirname(self.directory)
        self.list_box.scroll_to_item(0)

    def dir_box_click(self, double):
        if double:
            name = self.list_box.get_selected_name()
            path = os.path.join(self.directory, name)
            suffix = os.path.splitext(name)[1]
            if suffix not in self.suffixes and os.path.isdir(path):
                self.directory = path
            else:
                self.double_click_file(name)
        self.update()

    def enter_action(self):
        self.filename_box._enter_action()
        self.ok()

    def ok(self):
        self.dir_box_click(True)
        #self.dismiss(True)

    def cancel(self):
        self.dismiss(False)

    def key_down(self, evt):
        k = evt.key
        if k == K_RETURN or k == K_KP_ENTER:
            self.dir_box_click(True)
        if k == K_ESCAPE:
            self.cancel()


class FileSaveDialog(FileDialog):

    saving = True
    default_prompt = "Save as:"
    ok_label = "Save"

    def get_filename(self):
        return self.filename_box.value

    def set_filename(self, x):
        dsuf = self.suffixes[0]
        if x.endswith(dsuf):
            x = x[:-len(dsuf)]
        self.filename_box.value = x

    filename = property(get_filename, set_filename)

    def get_pathname(self):
        path = os.path.join(self.directory, self.filename_box.value)
        suffixes = self.suffixes
        if suffixes and not path.endswith(suffixes[0]):
            path = path + suffixes[0]
        return path

    pathname = property(get_pathname)

    def double_click_file(self, name):
        self.filename_box.value = name

    def ok(self):
        path = self.pathname
        if os.path.exists(path):
            answer = ask("Replace existing '%s'?" % os.path.basename(path))
            if answer != "OK":
                return
        #FileDialog.ok(self)
        self.dismiss(True)

    def update(self):
        FileDialog.update(self)

    def ok_enable(self):
        return self.filename_box.text != ""


class FileOpenDialog(FileDialog):

    saving = False
    ok_label = "Open"

    def get_pathname(self):
        name = self.list_box.get_selected_name()
        if name:
            return os.path.join(self.directory, name)
        else:
            return None

    pathname = property(get_pathname)

    #def update(self):
    #    FileDialog.update(self)

    def ok_enable(self):
        path = self.pathname
        enabled = self.item_is_choosable(path)
        return enabled

    def item_is_choosable(self, path):
        return bool(path) and self.filter(path)

    def double_click_file(self, name):
        self.dismiss(True)


class LookForFileDialog(FileOpenDialog):

    target = None

    def __init__(self, target, **kwds):
        FileOpenDialog.__init__(self, **kwds)
        self.target = target

    def item_is_choosable(self, path):
        return path and os.path.basename(path) == self.target

    def filter(self, name):
        return name and os.path.basename(name) == self.target


def request_new_filename(prompt=None, suffix=None, extra_suffixes=None,
        directory=None, filename=None, pathname=None):
    if pathname:
        directory, filename = os.path.split(pathname)
    if extra_suffixes:
        suffixes = extra_suffixes
    else:
        suffixes = []
    if suffix:
        suffixes = [suffix] + suffixes
    dlog = FileSaveDialog(prompt=prompt, suffixes=suffixes)
    if directory:
        dlog.directory = directory
    if filename:
        dlog.filename = filename
    if dlog.present():
        return dlog.pathname
    else:
        return None


def request_old_filename(suffixes=None, directory=None):
    dlog = FileOpenDialog(suffixes=suffixes)
    if directory:
        dlog.directory = directory
    if dlog.present():
        return dlog.pathname
    else:
        return None


def look_for_file_or_directory(target, prompt=None, directory=None):
    dlog = LookForFileDialog(target=target, prompt=prompt)
    if directory:
        dlog.directory = directory
    if dlog.present():
        return dlog.pathname
    else:
        return None

########NEW FILE########
__FILENAME__ = grid_view
from pygame import Rect
from widget import Widget


class GridView(Widget):
    #  cell_size   (width, height)   size of each cell
    #
    #  Abstract methods:
    #
    #    num_rows()  -->  no. of rows
    #    num_cols()  -->  no. of columns
    #    draw_cell(surface, row, col, rect)
    #    click_cell(row, col, event)

    def __init__(self, cell_size, nrows, ncols, **kwds):
        """nrows, ncols are for calculating initial size of widget"""
        Widget.__init__(self, **kwds)
        self.cell_size = cell_size
        w, h = cell_size
        d = 2 * self.margin
        self.size = (w * ncols + d, h * nrows + d)
        self.cell_size = cell_size

    def draw(self, surface):
        for row in xrange(self.num_rows()):
            for col in xrange(self.num_cols()):
                r = self.cell_rect(row, col)
                self.draw_cell(surface, row, col, r)

    def cell_rect(self, row, col):
        w, h = self.cell_size
        d = self.margin
        x = col * w + d
        y = row * h + d
        return Rect(x, y, w, h)

    def draw_cell(self, surface, row, col, rect):
        pass

    def mouse_down(self, event):
        if event.button == 1:
            x, y = event.local
            w, h = self.cell_size
            W, H = self.size
            d = self.margin
            if d <= x < W - d and d <= y < H - d:
                row = (y - d) // h
                col = (x - d) // w
                self.click_cell(row, col, event)

    def click_cell(self, row, col, event):
        pass

########NEW FILE########
__FILENAME__ = image_array
from pygame import Rect
from albow.resource import get_image


class ImageArray(object):

    def __init__(self, image, shape):
        self.image = image
        self.shape = shape
        if isinstance(shape, tuple):
            self.nrows, self.ncols = shape
        else:
            self.nrows = 1
            self.ncols = shape
        iwidth, iheight = image.get_size()
        self.size = iwidth // self.ncols, iheight // self.nrows

    def __len__(self):
        return self.shape

    def __getitem__(self, index):
        image = self.image
        nrows = self.nrows
        ncols = self.ncols
        if nrows == 1:
            row = 0
            col = index
        else:
            row, col = index
        #left = iwidth * col // ncols
        #top = iheight * row // nrows
        #width = iwidth // ncols
        #height = iheight // nrows
        width, height = self.size
        left = width * col
        top = height * row
        return image.subsurface(left, top, width, height)

    def get_rect(self):
        return Rect((0, 0), self.size)


image_array_cache = {}


def get_image_array(name, shape, **kwds):
    result = image_array_cache.get(name)
    if not result:
        result = ImageArray(get_image(name, **kwds), shape)
        image_array_cache[name] = result
    return result

########NEW FILE########
__FILENAME__ = layout
#
#   Albow - Layout widgets
#

from pygame import Rect
from widget import Widget


class RowOrColumn(Widget):

    _is_gl_container = True

    def __init__(self, size, items, kwds):
        align = kwds.pop('align', 'c')
        spacing = kwds.pop('spacing', 10)
        expand = kwds.pop('expand', None)
        if isinstance(expand, int):
            expand = items[expand]
        #if kwds:
        #    raise TypeError("Unexpected keyword arguments to Row or Column: %s"
        #        % kwds.keys())
        Widget.__init__(self, **kwds)
        #print "albow.controls: RowOrColumn: size =", size, "expand =", expand ###
        d = self.d
        longways = self.longways
        crossways = self.crossways
        axis = self.axis
        k, attr2, attr3 = self.align_map[align]
        w = 0
        length = 0
        if isinstance(expand, int):
            expand = items[expand]
        elif not expand:
            expand = items[-1]
        move = ''
        for item in items:
            r = item.rect
            w = max(w, getattr(r, crossways))
            if item is expand:
                item.set_resizing(axis, 's')
                move = 'm'
            else:
                item.set_resizing(axis, move)
                length += getattr(r, longways)
        if size is not None:
            n = len(items)
            if n > 1:
                length += spacing * (n - 1)
            #print "albow.controls: expanding size from", length, "to", size ###
            setattr(expand.rect, longways, max(1, size - length))
        h = w * k // 2
        m = self.margin
        px = h * d[1] + m
        py = h * d[0] + m
        sx = spacing * d[0]
        sy = spacing * d[1]
        for item in items:
            setattr(item.rect, attr2, (px, py))
            self.add(item)
            p = getattr(item.rect, attr3)
            px = p[0] + sx
            py = p[1] + sy
        self.shrink_wrap()

#---------------------------------------------------------------------------


class Row(RowOrColumn):

    d = (1, 0)
    axis = 'h'
    longways = 'width'
    crossways = 'height'
    align_map = {
        't': (0, 'topleft', 'topright'),
        'c': (1, 'midleft', 'midright'),
        'b': (2, 'bottomleft', 'bottomright'),
    }

    def __init__(self, items, width=None, **kwds):
        """
        Row(items, align=alignment, spacing=10, width=None, expand=None)
        align = 't', 'c' or 'b'
        """
        RowOrColumn.__init__(self, width, items, kwds)

#---------------------------------------------------------------------------


class Column(RowOrColumn):

    d = (0, 1)
    axis = 'v'
    longways = 'height'
    crossways = 'width'
    align_map = {
        'l': (0, 'topleft', 'bottomleft'),
        'c': (1, 'midtop', 'midbottom'),
        'r': (2, 'topright', 'bottomright'),
    }

    def __init__(self, items, height=None, **kwds):
        """
        Column(items, align=alignment, spacing=10, height=None, expand=None)
        align = 'l', 'c' or 'r'
        """
        RowOrColumn.__init__(self, height, items, kwds)

#---------------------------------------------------------------------------


class Grid(Widget):

    _is_gl_container = True

    def __init__(self, rows, row_spacing=10, column_spacing=10, **kwds):
        col_widths = [0] * len(rows[0])
        row_heights = [0] * len(rows)
        for j, row in enumerate(rows):
            for i, widget in enumerate(row):
                if widget:
                    col_widths[i] = max(col_widths[i], widget.width)
                    row_heights[j] = max(row_heights[j], widget.height)
        row_top = 0
        for j, row in enumerate(rows):
            h = row_heights[j]
            y = row_top + h // 2
            col_left = 0
            for i, widget in enumerate(row):
                if widget:
                    w = col_widths[i]
                    x = col_left
                    widget.midleft = (x, y)
                col_left += w + column_spacing
            row_top += h + row_spacing
        width = max(1, col_left - column_spacing)
        height = max(1, row_top - row_spacing)
        r = Rect(0, 0, width, height)
        #print "albow.controls.Grid: r =", r ###
        #print "...col_widths =", col_widths ###
        #print "...row_heights =", row_heights ###
        Widget.__init__(self, r, **kwds)
        self.add(rows)

#---------------------------------------------------------------------------


class Frame(Widget):
    #  margin  int        spacing between border and widget

    border_width = 1
    margin = 2

    def __init__(self, client, border_spacing=None, **kwds):
        Widget.__init__(self, **kwds)
        self.client = client
        if border_spacing is not None:
            self.margin = self.border_width + border_spacing
        d = self.margin
        w, h = client.size
        self.size = (w + 2 * d, h + 2 * d)
        client.topleft = (d, d)
        self.add(client)

########NEW FILE########
__FILENAME__ = menu
#---------------------------------------------------------------------------
#
#    Albow - Pull-down or pop-up menu
#
#---------------------------------------------------------------------------

import sys
from root import get_root, get_focus
from dialogs import Dialog
from theme import ThemeProperty
from pygame import Rect, draw

#---------------------------------------------------------------------------


class MenuItem(object):

    keyname = ""
    keycode = None
    shift = False
    alt = False
    enabled = False

    if sys.platform.startswith('darwin') or sys.platform.startswith('mac'):
        cmd_name = "Cmd "
        option_name = "Opt "
    else:
        cmd_name = "Ctrl "
        option_name = "Alt "

    def __init__(self, text="", command=None):
        self.command = command
        if "/" in text:
            text, key = text.split("/", 1)
        else:
            key = ""
        self.text = text
        if key:
            keyname = key[-1]
            mods = key[:-1]
            self.keycode = ord(keyname.lower())
            if "^" in mods:
                self.shift = True
                keyname = "Shift " + keyname
            if "@" in mods:
                self.alt = True
                keyname = self.option_name + keyname
            self.keyname = self.cmd_name + keyname

#---------------------------------------------------------------------------


class Menu(Dialog):

    disabled_color = ThemeProperty('disabled_color')
    click_outside_response = -1
    scroll_button_size = ThemeProperty('scroll_button_size')
    scroll_button_color = ThemeProperty('scroll_button_color')
    scroll = 0

    def __init__(self, title, items, scrolling=False, scroll_items=30,
                 scroll_page=5, **kwds):
        self.title = title
        self.items = items
        self._items = [MenuItem(*item) for item in items]
        self.scrolling = scrolling and len(self._items) > scroll_items
        self.scroll_items = scroll_items
        self.scroll_page = scroll_page
        Dialog.__init__(self, **kwds)

        h = self.font.get_linesize()
        if self.scrolling:
            self.height = h * self.scroll_items + h
        else:
            self.height = h * len(self._items) + h

    def present(self, client, pos):
        client = client or get_root()
        self.topleft = client.local_to_global(pos)
        focus = get_focus()
        font = self.font
        h = font.get_linesize()
        items = self._items
        margin = self.margin
        if self.scrolling:
            height = h * self.scroll_items + h
        else:
            height = h * len(items) + h
        w1 = w2 = 0
        for item in items:
            item.enabled = self.command_is_enabled(item, focus)
            w1 = max(w1, font.size(item.text)[0])
            w2 = max(w2, font.size(item.keyname)[0])
        width = w1 + 2 * margin
        self._key_margin = width
        if w2 > 0:
            width += w2 + margin
        if self.scrolling:
            width += self.scroll_button_size            
        self.size = (width, height)
        self._hilited = None

        root = get_root()
        self.rect.clamp_ip(root.rect)

        return Dialog.present(self, centered=False)

    def command_is_enabled(self, item, focus):
        cmd = item.command
        if cmd:
            enabler_name = cmd + '_enabled'
            handler = focus
            while handler:
                enabler = getattr(handler, enabler_name, None)
                if enabler:
                    return enabler()
                handler = handler.next_handler()
        return True

    def scroll_up_rect(self):
        d = self.scroll_button_size
        r = Rect(0, 0, d, d)
        m = self.margin
        r.top = m
        r.right = self.width - m
        r.inflate_ip(-4, -4)
        return r

    def scroll_down_rect(self):
        d = self.scroll_button_size
        r = Rect(0, 0, d, d)
        m = self.margin
        r.bottom = self.height - m
        r.right = self.width - m
        r.inflate_ip(-4, -4)
        return r

    def draw(self, surf):
        font = self.font
        h = font.get_linesize()
        sep = surf.get_rect()
        sep.height = 1
        if self.scrolling:
            sep.width -= self.margin + self.scroll_button_size
        colors = [self.disabled_color, self.fg_color]
        bg = self.bg_color
        xt = self.margin
        xk = self._key_margin
        y = h // 2
        hilited = self._hilited
        if self.scrolling:
            items = self._items[self.scroll:self.scroll + self.scroll_items]
        else:
            items = self._items
        for item in items:
            text = item.text
            if not text:
                sep.top = y + h // 2
                surf.fill(colors[0], sep)
            else:
                if item is hilited:
                    rect = surf.get_rect()
                    rect.top = y
                    rect.height = h
                    if self.scrolling:
                        rect.width -= xt + self.scroll_button_size
                    surf.fill(colors[1], rect)
                    color = bg
                else:
                    color = colors[item.enabled]
                buf = font.render(item.text, True, color)
                surf.blit(buf, (xt, y))
                keyname = item.keyname
                if keyname:
                    buf = font.render(keyname, True, color)
                    surf.blit(buf, (xk, y))
            y += h
        if self.scrolling:
            if self.can_scroll_up():
                self.draw_scroll_up_button(surf)
            if self.can_scroll_down():
                self.draw_scroll_down_button(surf)

    def draw_scroll_up_button(self, surface):
        r = self.scroll_up_rect()
        c = self.scroll_button_color
        draw.polygon(surface, c, [r.bottomleft, r.midtop, r.bottomright])

    def draw_scroll_down_button(self, surface):
        r = self.scroll_down_rect()
        c = self.scroll_button_color
        draw.polygon(surface, c, [r.topleft, r.midbottom, r.topright])

    def mouse_move(self, e):
        self.mouse_drag(e)

    def mouse_drag(self, e):
        item = self.find_enabled_item(e)
        if item is not self._hilited:
            self._hilited = item
            self.invalidate()

    def mouse_up(self, e):
        if 1 <= e.button <= 3:
            item = self.find_enabled_item(e)
            if item:
                self.dismiss(self._items.index(item))

    def find_enabled_item(self, e):
        x, y = e.local
        if 0 <= x < (self.width - self.margin - self.scroll_button_size
                     if self.scrolling else self.width):
            h = self.font.get_linesize()
            i = (y - h // 2) // h + self.scroll
            items = self._items
            if 0 <= i < len(items):
                item = items[i]
                if item.enabled:
                    return item

    def mouse_down(self, event):
        if event.button == 1:
            if self.scrolling:
                p = event.local
                if self.scroll_up_rect().collidepoint(p):
                    self.scroll_up()
                    return
                elif self.scroll_down_rect().collidepoint(p):
                    self.scroll_down()
                    return
        if event.button == 4:
            self.scroll_up()
        if event.button == 5:
            self.scroll_down()

        Dialog.mouse_down(self, event)

    def scroll_up(self):
        if self.can_scroll_up():
            self.scroll = max(self.scroll - self.scroll_page, 0)

    def scroll_down(self):
        if self.can_scroll_down():
            self.scroll = min(self.scroll + self.scroll_page,
                              len(self._items) - self.scroll_items)

    def can_scroll_up(self):
        return self.scrolling and self.scroll > 0

    def can_scroll_down(self):
        return (self.scrolling and
                self.scroll + self.scroll_items < len(self._items))

    def find_item_for_key(self, e):
        for item in self._items:
            if item.keycode == e.key \
                and item.shift == e.shift and item.alt == e.alt:
                    focus = get_focus()
                    if self.command_is_enabled(item, focus):
                        return self._items.index(item)
                    else:
                        return -1
        return -1

    def get_command(self, i):
        if i >= 0:
            item = self._items[i]
            cmd = item.command
            if cmd:
                return cmd + '_cmd'

    def invoke_item(self, i):
        cmd = self.get_command(i)
        if cmd:
            get_focus().handle_command(cmd)

########NEW FILE########
__FILENAME__ = menu_bar
#
#    Albow - Menu bar
#

from pygame import Rect
from widget import Widget, overridable_property


class MenuBar(Widget):

    menus = overridable_property('menus', "List of Menu instances")

    def __init__(self, menus=None, width=0, **kwds):
        font = self.predict_font(kwds)
        height = font.get_linesize()
        Widget.__init__(self, Rect(0, 0, width, height), **kwds)
        self.menus = menus or []
        self._hilited_menu = None

    def get_menus(self):
        return self._menus

    def set_menus(self, x):
        self._menus = x

    def draw(self, surf):
        fg = self.fg_color
        bg = self.bg_color
        font = self.font
        hilited = self._hilited_menu
        x = 0
        for menu in self._menus:
            text = " %s " % menu.title
            if menu is hilited:
                buf = font.render(text, True, bg, fg)
            else:
                buf = font.render(text, True, fg, bg)
            surf.blit(buf, (x, 0))
            x += surf.get_width()

    def mouse_down(self, e):
        mx = e.local[0]
        font = self.font
        x = 0
        for menu in self._menus:
            text = " %s " % menu.title
            w = font.size(text)[0]
            if x <= mx < x + w:
                self.show_menu(menu, x)

    def show_menu(self, menu, x):
        self._hilited_menu = menu
        try:
            i = menu.present(self, (x, self.height))
        finally:
            self._hilited_menu = None
        menu.invoke_item(i)

    def handle_command_key(self, e):
        menus = self.menus
        for m in xrange(len(menus) - 1, -1, -1):
            menu = menus[m]
            i = menu.find_item_for_key(e)
            if i >= 0:
                menu.invoke_item(i)
                return True
        return False

########NEW FILE########
__FILENAME__ = music
#---------------------------------------------------------------------------
#
#   Albow - Music
#
#---------------------------------------------------------------------------

from __future__ import division
import os
from random import randrange

try:
    from pygame.mixer import music
except ImportError:
    music = None
    print "Music not available"

if music:
    import root
    music.set_endevent(root.MUSIC_END_EVENT)

from resource import resource_path
from root import schedule

#---------------------------------------------------------------------------

fadeout_time = 1  # Time over which to fade out music (sec)
change_delay = 2  # Delay between end of one item and starting the next (sec)

#---------------------------------------------------------------------------

music_enabled = True
current_music = None
current_playlist = None
next_change_delay = 0

#---------------------------------------------------------------------------


class PlayList(object):
    """A collection of music filenames to be played sequentially or
    randomly. If random is true, items will be played in a random order.
    If repeat is true, the list will be repeated indefinitely, otherwise
    each item will only be played once."""

    def __init__(self, items, random=False, repeat=False):
        self.items = list(items)
        self.random = random
        self.repeat = repeat

    def next(self):
        """Returns the next item to be played."""
        items = self.items
        if items:
            if self.random:
                n = len(items)
                if self.repeat:
                    n = (n + 1) // 2
                i = randrange(n)
            else:
                i = 0
            item = items.pop(i)
            if self.repeat:
                items.append(item)
            return item

#---------------------------------------------------------------------------


def get_music(*names, **kwds):
    """Return the full pathname of a music file from the "music" resource
    subdirectory."""
    prefix = kwds.pop('prefix', "music")
    return resource_path(prefix, *names)


def get_playlist(*names, **kwds):
    prefix = kwds.pop('prefix', "music")
    dirpath = get_music(*names, **{'prefix': prefix})
    items = [os.path.join(dirpath, filename)
        for filename in os.listdir(dirpath)
            if not filename.startswith(".")]
    items.sort()
    return PlayList(items, **kwds)


def change_playlist(new_playlist):
    """Fade out any currently playing music and start playing from the given
    playlist."""
    #print "albow.music: change_playlist" ###
    global current_music, current_playlist, next_change_delay
    if music and new_playlist is not current_playlist:
        current_playlist = new_playlist
        if music_enabled:
            music.fadeout(fadeout_time * 1000)
            next_change_delay = max(0, change_delay - fadeout_time)
            jog_music()
        else:
            current_music = None


def change_music(new_music, repeat=False):
    """Fade out any currently playing music and start playing the given
    music file."""
    #print "albow.music: change_music" ###
    if music and new_music is not current_music:
        if new_music:
            new_playlist = PlayList([new_music], repeat=repeat)
        else:
            new_playlist = None
        change_playlist(new_playlist)


def music_end():
    #print "albow.music: music_end" ###
    schedule(next_change_delay, jog_music)


def jog_music():
    """If no music is currently playing, start playing the next item
    from the current playlist."""
    if music_enabled and not music.get_busy():
        start_next_music()


def start_next_music():
    """Start playing the next item from the current playlist immediately."""
    #print "albow.music: start_next_music" ###
    global current_music, next_change_delay
    if music_enabled and current_playlist:
        next_music = current_playlist.next()
        if next_music:
            print "albow.music: loading", repr(next_music)  ###
            music.load(next_music)
            music.play()
            next_change_delay = change_delay
        current_music = next_music


def get_music_enabled():
    return music_enabled


def set_music_enabled(state):
    global music_enabled
    if music_enabled != state:
        music_enabled = state
        if state:
            # Music pausing doesn't always seem to work.
            #music.unpause()
            if current_music:
                # After stopping and restarting currently loaded music,
                # fadeout no longer works.
                #print "albow.music: reloading", repr(current_music) ###
                music.load(current_music)
                music.play()
            else:
                jog_music()
        else:
            #music.pause()
            music.stop()

#---------------------------------------------------------------------------

from pygame import Rect
from albow.widget import Widget
from albow.controls import Label, Button, CheckBox
from albow.layout import Row, Column, Grid
from albow.dialogs import Dialog


class EnableMusicControl(CheckBox):

    def get_value(self):
        return get_music_enabled()

    def set_value(self, x):
        set_music_enabled(x)


class MusicVolumeControl(Widget):

    def __init__(self, **kwds):
        Widget.__init__(self, Rect((0, 0), (100, 20)), **kwds)

    def draw(self, surf):
        r = self.get_margin_rect()
        r.width = int(round(music.get_volume() * r.width))
        surf.fill(self.fg_color, r)

    def mouse_down(self, e):
        self.mouse_drag(e)

    def mouse_drag(self, e):
        m = self.margin
        w = self.width - 2 * m
        x = max(0.0, min(1.0, (e.local[0] - m) / w))
        music.set_volume(x)
        self.invalidate()


class MusicOptionsDialog(Dialog):

    def __init__(self):
        Dialog.__init__(self)
        emc = EnableMusicControl()
        mvc = MusicVolumeControl()
        controls = Grid([
            [Label("Enable Music"), emc],
            [Label("Music Volume"), mvc],
        ])
        buttons = Button("OK", self.ok)
        contents = Column([controls, buttons], align='r', spacing=20)
        contents.topleft = (20, 20)
        self.add(contents)
        self.shrink_wrap()


def show_music_options_dialog():
    dlog = MusicOptionsDialog()
    dlog.present()

########NEW FILE########
__FILENAME__ = openglwidgets
#-------------------------------------------------------------------------
#
#   Albow - OpenGL widgets
#
#-------------------------------------------------------------------------

from __future__ import division
from OpenGL import GL, GLU
from widget import Widget


class GLViewport(Widget):

    is_gl_container = True

    def gl_draw_self(self, root, offset):
        rect = self.rect.move(offset)
        # GL_CLIENT_ALL_ATTRIB_BITS is borked: defined as -1 but
        # glPushClientAttrib insists on an unsigned long.
        #GL.glPushClientAttrib(0xffffffff)
        #GL.glPushAttrib(GL.GL_ALL_ATTRIB_BITS)
        GL.glViewport(rect.left, root.height - rect.bottom, rect.width, rect.height)
        self.gl_draw_viewport()
        #GL.glPopAttrib()
        #GL.glPopClientAttrib()

    def gl_draw_viewport(self):
        self.setup_matrices()
        self.gl_draw()

    def setup_matrices(self):
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        self.setup_projection()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()
        self.setup_modelview()

    def setup_projection(self):
        pass

    def setup_modelview(self):
        pass

    def gl_draw(self):
        pass

    def augment_mouse_event(self, event):
        Widget.augment_mouse_event(self, event)
        w, h = self.size
        viewport = numpy.array((0, 0, w, h), dtype='int32')
        self.setup_matrices()
        gf = GL.glGetDoublev
        pr_mat = gf(GL.GL_PROJECTION_MATRIX)
        mv_mat = gf(GL.GL_MODELVIEW_MATRIX)
        x, y = event.local
        y = h - y
        up = GLU.gluUnProject
        try:
            p0 = up(x, y, 0.0, mv_mat, pr_mat, viewport)
            p1 = up(x, y, 1.0, mv_mat, pr_mat, viewport)
            event.dict['ray'] = (p0, p1)
        except ValueError:  # projection failed!
            pass

import numpy

#-------------------------------------------------------------------------


class GLOrtho(GLViewport):

    def __init__(self, rect=None,
            xmin=-1, xmax=1, ymin=-1, ymax=1,
            near=-1, far=1, **kwds):
        GLViewport.__init__(self, rect, **kwds)
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.near = near
        self.far = far

    def setup_projection(self):
        GL.glOrtho(self.xmin, self.xmax, self.ymin, self.ymax,
            self.near, self.far)


class GLPixelOrtho(GLOrtho):
    def __init__(self, rect=None, near=-1, far=1, **kwds):
        GLOrtho.__init__(self, rect, near, far, **kwds)
        self.xmin = 0
        self.ymin = 0
        self.xmax = self.width
        self.ymax = self.height


#-------------------------------------------------------------------------


class GLPerspective(GLViewport):

    def __init__(self, rect=None, fovy=20,
            near=0.1, far=1000, **kwds):
        GLViewport.__init__(self, rect, **kwds)
        self.fovy = fovy
        self.near = near
        self.far = far

    def setup_projection(self):
        aspect = self.width / self.height
        GLU.gluPerspective(self.fovy, aspect, self.near, self.far)

########NEW FILE########
__FILENAME__ = palette_view
from pygame import Rect, draw
from grid_view import GridView
from utils import frame_rect
from theme import ThemeProperty


class PaletteView(GridView):
    #  nrows   int   No. of displayed rows
    #  ncols   int   No. of displayed columns
    #
    #  Abstract methods:
    #
    #    num_items()  -->  no. of items
    #    draw_item(surface, item_no, rect)
    #    click_item(item_no, event)
    #    item_is_selected(item_no)  -->  bool

    sel_width = ThemeProperty('sel_width')
    zebra_color = ThemeProperty('zebra_color')
    scroll_button_size = ThemeProperty('scroll_button_size')
    scroll_button_color = ThemeProperty('scroll_button_color')
    highlight_style = ThemeProperty('highlight_style')
        # 'frame' or 'fill' or 'reverse' or None

    def __init__(self, cell_size, nrows, ncols, scrolling=False, **kwds):
        GridView.__init__(self, cell_size, nrows, ncols, **kwds)
        self.scrolling = scrolling
        if scrolling:
            d = self.scroll_button_size
            #l = self.width
            #b = self.height
            self.width += d
            #self.scroll_up_rect = Rect(l, 0, d, d).inflate(-4, -4)
            #self.scroll_down_rect = Rect(l, b - d, d, d).inflate(-4, -4)
        self.scroll = 0

    def scroll_up_rect(self):
        d = self.scroll_button_size
        r = Rect(0, 0, d, d)
        m = self.margin
        r.top = m
        r.right = self.width - m
        r.inflate_ip(-4, -4)
        return r

    def scroll_down_rect(self):
        d = self.scroll_button_size
        r = Rect(0, 0, d, d)
        m = self.margin
        r.bottom = self.height - m
        r.right = self.width - m
        r.inflate_ip(-4, -4)
        return r

    def draw(self, surface):

        GridView.draw(self, surface)
        if self.can_scroll_up():
            self.draw_scroll_up_button(surface)
        if self.can_scroll_down():
            self.draw_scroll_down_button(surface)

    def draw_scroll_up_button(self, surface):
        r = self.scroll_up_rect()
        c = self.scroll_button_color
        draw.polygon(surface, c, [r.bottomleft, r.midtop, r.bottomright])

    def draw_scroll_down_button(self, surface):
        r = self.scroll_down_rect()
        c = self.scroll_button_color
        draw.polygon(surface, c, [r.topleft, r.midbottom, r.topright])

    def draw_cell(self, surface, row, col, rect):
        i = self.cell_to_item_no(row, col)
        if i is not None:
            highlight = self.item_is_selected(i)
            self.draw_item_and_highlight(surface, i, rect, highlight)

    def draw_item_and_highlight(self, surface, i, rect, highlight):
        if i % 2:
            surface.fill(self.zebra_color, rect)
        if highlight:
            self.draw_prehighlight(surface, i, rect)
        if highlight and self.highlight_style == 'reverse':
            fg = self.inherited('bg_color') or self.sel_color
        else:
            fg = self.fg_color
        self.draw_item_with(surface, i, rect, fg)
        if highlight:
            self.draw_posthighlight(surface, i, rect)

    def draw_item_with(self, surface, i, rect, fg):
        old_fg = self.fg_color
        self.fg_color = fg
        try:
            self.draw_item(surface, i, rect)
        finally:
            self.fg_color = old_fg

    def draw_prehighlight(self, surface, i, rect):
        if self.highlight_style == 'reverse':
            color = self.fg_color
        else:
            color = self.sel_color
        self.draw_prehighlight_with(surface, i, rect, color)

    def draw_prehighlight_with(self, surface, i, rect, color):
        style = self.highlight_style
        if style == 'frame':
            frame_rect(surface, color, rect, self.sel_width)
        elif style == 'fill' or style == 'reverse':
            surface.fill(color, rect)

    def draw_posthighlight(self, surface, i, rect):
        pass

    def mouse_down(self, event):
        if event.button == 1:
            if self.scrolling:
                p = event.local
                if self.scroll_up_rect().collidepoint(p):
                    self.scroll_up()
                    return
                elif self.scroll_down_rect().collidepoint(p):
                    self.scroll_down()
                    return
        if event.button == 4:
            self.scroll_up()
        if event.button == 5:
            self.scroll_down()

        GridView.mouse_down(self, event)

    def scroll_up(self):
        if self.can_scroll_up():
            self.scroll -= self.items_per_page() / 2

    def scroll_down(self):
        if self.can_scroll_down():
            self.scroll += self.items_per_page() / 2

    def scroll_to_item(self, n):
        i = max(0, min(n, self.num_items() - 1))
        p = self.items_per_page()
        self.scroll = p * (i // p)

    def can_scroll_up(self):
        return self.scrolling and self.scroll > 0

    def can_scroll_down(self):
        return self.scrolling and self.scroll + self.items_per_page() < self.num_items()

    def items_per_page(self):
        return self.num_rows() * self.num_cols()

    def click_cell(self, row, col, event):
        i = self.cell_to_item_no(row, col)
        if i is not None:
            self.click_item(i, event)

    def cell_to_item_no(self, row, col):
        i = self.scroll + row * self.num_cols() + col
        if 0 <= i < self.num_items():
            return i
        else:
            return None

    def num_rows(self):
        ch = self.cell_size[1]
        if ch:
            return self.height // ch
        else:
            return 0

    def num_cols(self):
        width = self.width
        if self.scrolling:
            width -= self.scroll_button_size
        cw = self.cell_size[0]
        if cw:
            return width // cw
        else:
            return 0

    def item_is_selected(self, n):
        return False

    def click_item(self, n, e):
        pass

########NEW FILE########
__FILENAME__ = resource
# -*- coding: utf-8 -*-
import os
import sys
import pygame
from pygame.locals import RLEACCEL

#default_font_name = "Vera.ttf"
optimize_images = True
run_length_encode = False


def find_resource_dir():
    try:
        from directories import dataDir
        return dataDir
    except:
        pass
    dir = sys.path[0]
    while 1:
        path = os.path.join(dir, "MCEditData")
        if os.path.exists(path):
            return path
        parent = os.path.dirname(dir)
        if parent == dir:
            raise SystemError("albow: Unable to find Resources directory")
        dir = parent

resource_dir = find_resource_dir()

image_cache = {}
font_cache = {}
sound_cache = {}
text_cache = {}
cursor_cache = {}


def _resource_path(default_prefix, names, prefix=""):
    return os.path.join(resource_dir, prefix or default_prefix, *names)


def resource_path(*names, **kwds):
    return _resource_path("", names, **kwds)


def resource_exists(*names, **kwds):
    return os.path.exists(_resource_path("", names, **kwds))


def _get_image(names, border=0, optimize=optimize_images, noalpha=False,
        rle=run_length_encode, prefix="images"):
    path = _resource_path(prefix, names)
    image = image_cache.get(path)
    if not image:
        image = pygame.image.load(path)
        if noalpha:
            image = image.convert(24)
        elif optimize:
            image = image.convert_alpha()
        if rle:
            image.set_alpha(255, RLEACCEL)
        if border:
            w, h = image.get_size()
            b = border
            d = 2 * border
            image = image.subsurface(b, b, w - d, h - d)
        image_cache[path] = image
    return image


def get_image(*names, **kwds):
    return _get_image(names, **kwds)


def get_font(size, *names, **kwds):
    path = _resource_path("fonts", names, **kwds)
    key = (path, size)
    font = font_cache.get(key)
    if not font:
        try:
            font = pygame.font.Font(path, size)
        except Exception, e:
            try:
                font = pygame.font.Font(path.encode(sys.getfilesystemencoding()), size)
            except Exception, e:
                print "Couldn't get font {0}, using sysfont".format((path, size))
                font = pygame.font.SysFont("Courier New", size)
        font_cache[key] = font
    return font


class DummySound(object):
    def fadeout(self, x):
        pass

    def get_length(self):
        return 0.0

    def get_num_channels(self):
        return 0

    def get_volume(self):
        return 0.0

    def play(self, *args):
        pass

    def set_volume(self, x):
        pass

    def stop(self):
        pass

dummy_sound = DummySound()


def get_sound(*names, **kwds):
    if sound_cache is None:
        return dummy_sound
    path = _resource_path("sounds", names, **kwds)
    sound = sound_cache.get(path)
    if not sound:
        try:
            from pygame.mixer import Sound
        except ImportError, e:
            no_sound(e)
            return dummy_sound
        try:
            sound = Sound(path)
        except pygame.error, e:
            missing_sound(e, path)
            return dummy_sound
        sound_cache[path] = sound
    return sound


def no_sound(e):
    global sound_cache
    print "albow.resource.get_sound: %s" % e
    print "albow.resource.get_sound: Sound not available, continuing without it"
    sound_cache = None


def missing_sound(e, name):
    print "albow.resource.get_sound: %s: %s" % (name, e)


def get_text(*names, **kwds):
    path = _resource_path("text", names, **kwds)
    text = text_cache.get(path)
    if text is None:
        text = open(path, "rU").read()
        text_cache[path] = text
    return text


def load_cursor(path):
    image = get_image(path)
    width, height = image.get_size()
    hot = (0, 0)
    data = []
    mask = []
    rowbytes = (width + 7) // 8
    xr = xrange(width)
    yr = xrange(height)
    for y in yr:
        bit = 0x80
        db = mb = 0
        for x in xr:
            r, g, b, a = image.get_at((x, y))
            if a >= 128:
                mb |= bit
                if r + g + b < 383:
                    db |= bit
            if r == 0 and b == 255:
                hot = (x, y)
            bit >>= 1
            if not bit:
                data.append(db)
                mask.append(mb)
                db = mb = 0
                bit = 0x80
        if bit != 0x80:
            data.append(db)
            mask.append(mb)
    return (8 * rowbytes, height), hot, data, mask


def get_cursor(*names, **kwds):
    path = _resource_path("cursors", names, **kwds)
    cursor = cursor_cache.get(path)
    if cursor is None:
        cursor = load_cursor(path)
        cursor_cache[path] = cursor
    return cursor

########NEW FILE########
__FILENAME__ = root
#---------------------------------------------------------------------------
#
#   Albow - Root widget
#
#---------------------------------------------------------------------------

import sys
import pygame
from pygame.locals import *
#from pygame.time import get_ticks
from pygame.event import Event

from glbackground import *
import widget
from widget import Widget
from controls import Label

from datetime import datetime, timedelta
from albow.dialogs import wrapped_label
start_time = datetime.now()

mod_cmd = KMOD_LCTRL | KMOD_RCTRL | KMOD_LMETA | KMOD_RMETA
double_click_time = timedelta(0, 0, 300000)  # days, seconds, microseconds

import logging
log = logging.getLogger(__name__)

modifiers = dict(
    shift=False,
    ctrl=False,
    alt=False,
    meta=False,
)

modkeys = {
    K_LSHIFT: 'shift', K_RSHIFT: 'shift',
    K_LCTRL:  'ctrl', K_RCTRL:  'ctrl',
    K_LALT:   'alt', K_RALT:   'alt',
    K_LMETA:  'meta', K_RMETA:  'meta',
}

MUSIC_END_EVENT = USEREVENT + 1

last_mouse_event = Event(0, pos=(0, 0), local=(0, 0))
last_mouse_event_handler = None
root_widget = None     # Root of the containment hierarchy
top_widget = None      # Initial dispatch target
clicked_widget = None  # Target of mouse_drag and mouse_up events

#---------------------------------------------------------------------------


class Cancel(Exception):
    pass

#---------------------------------------------------------------------------


def set_modifier(key, value):
    attr = modkeys.get(key)
    if attr:
        modifiers[attr] = value


def add_modifiers(event):
    d = event.dict
    d.update(modifiers)
    d['cmd'] = event.ctrl or event.meta


def get_root():
    return root_widget


def get_top_widget():
    return top_widget


def get_focus():
    return top_widget.get_focus()

#---------------------------------------------------------------------------


class RootWidget(Widget):
    #  surface   Pygame display surface
    #  is_gl     True if OpenGL surface

    redraw_every_frame = False
    do_draw = False
    _is_gl_container = True

    def __init__(self, surface):
        global root_widget
        Widget.__init__(self, surface.get_rect())
        self.surface = surface
        root_widget = self
        widget.root_widget = self
        self.is_gl = surface.get_flags() & OPENGL != 0
        self.idle_handlers = []

    def set_timer(self, ms):
        pygame.time.set_timer(USEREVENT, ms)

    def run(self):
        self.run_modal(None)

    captured_widget = None

    def capture_mouse(self, widget):
        #put the mouse in "virtual mode" and pass mouse moved events to the
        #specified widget
        if widget:
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
            get_root().captured_widget = widget
        else:
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            get_root().captured_widget = None

    frames = 0
    hover_widget = None

    def run_modal(self, modal_widget):
        old_captured_widget = None

        if self.captured_widget:
            old_captured_widget = self.captured_widget
            self.capture_mouse(None)

        global last_mouse_event, last_mouse_event_handler
        global top_widget, clicked_widget
        is_modal = modal_widget is not None
        modal_widget = modal_widget or self
        from OpenGL import GL
        try:
            old_top_widget = top_widget
            top_widget = modal_widget
            was_modal = modal_widget.is_modal
            modal_widget.is_modal = True
            modal_widget.modal_result = None
            if not modal_widget.focus_switch:
                modal_widget.tab_to_first()
            mouse_widget = None
            if clicked_widget:
                clicked_widget = modal_widget
            num_clicks = 0
            last_click_time = start_time
            last_click_button = 0
            self.do_draw = True

            while modal_widget.modal_result is None:
                try:
                    self.hover_widget = self.find_widget(mouse.get_pos())
                    if self.do_draw:
                        if self.is_gl:
                            self.gl_clear()
                            self.gl_draw_all(self, (0, 0))
                            GL.glFlush()
                        else:
                            self.draw_all(self.surface)
                        self.do_draw = False
                        pygame.display.flip()
                        self.frames += 1
                    #events = [pygame.event.wait()]
                    events = [pygame.event.poll()]
                    events.extend(pygame.event.get())
                    for event in events:
                        #if event.type:
                            #log.debug("%s", event)

                        type = event.type
                        if type == QUIT:
                            self.quit()
                        elif type == MOUSEBUTTONDOWN:
                            self.do_draw = True
                            t = datetime.now()
                            if t - last_click_time <= double_click_time and event.button == last_click_button:
                                num_clicks += 1
                            else:
                                num_clicks = 1
                            last_click_button = event.button
                            last_click_time = t
                            event.dict['num_clicks'] = num_clicks
                            add_modifiers(event)
                            mouse_widget = self.find_widget(event.pos)
                            if self.captured_widget:
                                mouse_widget = self.captured_widget

                            if not mouse_widget.is_inside(modal_widget):
                                mouse_widget = modal_widget
                            #if event.button == 1:
                            clicked_widget = mouse_widget
                            last_mouse_event_handler = mouse_widget
                            last_mouse_event = event
                            mouse_widget.notify_attention_loss()
                            mouse_widget.handle_mouse('mouse_down', event)
                        elif type == MOUSEMOTION:
                            self.do_draw = True
                            add_modifiers(event)
                            modal_widget.dispatch_key('mouse_delta', event)
                            last_mouse_event = event

                            mouse_widget = self.update_tooltip(event.pos)

                            if clicked_widget:
                                last_mouse_event_handler = clicked_widget
                                clicked_widget.handle_mouse('mouse_drag', event)
                            else:
                                if not mouse_widget.is_inside(modal_widget):
                                    mouse_widget = modal_widget
                                last_mouse_event_handler = mouse_widget
                                mouse_widget.handle_mouse('mouse_move', event)
                        elif type == MOUSEBUTTONUP:
                            add_modifiers(event)
                            self.do_draw = True
                            mouse_widget = self.find_widget(event.pos)
                            if self.captured_widget:
                                mouse_widget = self.captured_widget
                            if clicked_widget:
                                last_mouse_event_handler = clicked_widget
                                event.dict['clicked_widget'] = clicked_widget
                            else:
                                last_mouse_event_handler = mouse_widget
                                event.dict['clicked_widget'] = None

                            last_mouse_event = event
                            clicked_widget = None
                            last_mouse_event_handler.handle_mouse('mouse_up', event)
                        elif type == KEYDOWN:
                            key = event.key
                            set_modifier(key, True)
                            self.do_draw = True
                            self.send_key(modal_widget, 'key_down', event)
                            if last_mouse_event_handler:
                                event.dict['pos'] = last_mouse_event.pos
                                event.dict['local'] = last_mouse_event.local
                                last_mouse_event_handler.setup_cursor(event)
                        elif type == KEYUP:
                            key = event.key
                            set_modifier(key, False)
                            self.do_draw = True
                            self.send_key(modal_widget, 'key_up', event)
                            if last_mouse_event_handler:
                                event.dict['pos'] = last_mouse_event.pos
                                event.dict['local'] = last_mouse_event.local
                                last_mouse_event_handler.setup_cursor(event)
                        elif type == MUSIC_END_EVENT:
                            self.music_end()
                        elif type == USEREVENT:
                            make_scheduled_calls()
                            if not is_modal:
                                self.do_draw = self.redraw_every_frame
                                if last_mouse_event_handler:
                                    event.dict['pos'] = last_mouse_event.pos
                                    event.dict['local'] = last_mouse_event.local
                                    add_modifiers(event)
                                    last_mouse_event_handler.setup_cursor(event)
                                self.begin_frame()
                        elif type == VIDEORESIZE:
                            #add_modifiers(event)
                            self.do_draw = True
                            self.size = (event.w, event.h)
                            #self.dispatch_key('reshape', event)
                        elif type == ACTIVEEVENT:
                            add_modifiers(event)
                            self.dispatch_key('activeevent', event)
                        elif type == NOEVENT:
                            add_modifiers(event)
                            self.call_idle_handlers(event)

                except Cancel:
                    pass
        finally:
            modal_widget.is_modal = was_modal
            top_widget = old_top_widget
            if old_captured_widget:
                self.capture_mouse(old_captured_widget)

        clicked_widget = None

    def call_idle_handlers(self, event):
        def call(ref):
            widget = ref()
            if widget:
                widget.idleevent(event)
            else:
                print "Idle ref died!"
            return bool(widget)

        self.idle_handlers = filter(call, self.idle_handlers)

    def add_idle_handler(self, widget):
        from weakref import ref
        self.idle_handlers.append(ref(widget))

    def remove_idle_handler(self, widget):
        from weakref import ref
        self.idle_handlers.remove(ref(widget))

    def send_key(self, widget, name, event):
        add_modifiers(event)
        widget.dispatch_key(name, event)

    def begin_frame(self):
        pass

    def get_root(self):
        return self

    labelClass = lambda s, t: wrapped_label(t, 45)

    def show_tooltip(self, widget, pos):

        if hasattr(self, 'currentTooltip'):
            if self.currentTooltip != None:
                self.remove(self.currentTooltip)

            self.currentTooltip = None

        def TextTooltip(text):
            tooltipBacking = Panel()
            tooltipBacking.bg_color = (0.0, 0.0, 0.0, 0.6)
            tooltipBacking.add(self.labelClass(text))
            tooltipBacking.shrink_wrap()
            return tooltipBacking

        def showTip(tip):
            tip.topleft = pos
            tip.top += 20
            if (tip.bottom > self.bottom) or hasattr(widget, 'tooltipsUp'):
                tip.bottomleft = pos
                tip.top -= 4
            if tip.right > self.right:
                tip.right = pos[0]

            self.add(tip)
            self.currentTooltip = tip

        if widget.tooltip is not None:
            tip = widget.tooltip
            showTip(tip)

        else:
            ttext = widget.tooltipText
            if ttext is not None:
                tip = TextTooltip(ttext)
                showTip(tip)

    def update_tooltip(self, pos=None):
        if pos is None:
            pos = mouse.get_pos()
        if self.captured_widget:
            mouse_widget = self.captured_widget
            pos = mouse_widget.center
        else:
            mouse_widget = self.find_widget(pos)

        self.show_tooltip(mouse_widget, pos)
        return mouse_widget

    def has_focus(self):
        return True

    def quit(self):
        if self.confirm_quit():
            self.capture_mouse(None)
            sys.exit(0)

    def confirm_quit(self):
        return True

    def get_mouse_for(self, widget):
        last = last_mouse_event
        event = Event(0, last.dict)
        event.dict['local'] = widget.global_to_local(event.pos)
        add_modifiers(event)
        return event

    def gl_clear(self):
        from OpenGL import GL
        bg = self.bg_color
        if bg:
            r = bg[0] / 255.0
            g = bg[1] / 255.0
            b = bg[2] / 255.0
            GL.glClearColor(r, g, b, 0.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    def music_end(self):
        import music
        music.music_end()

#---------------------------------------------------------------------------

from time import time
from bisect import insort

scheduled_calls = []


def make_scheduled_calls():
    sched = scheduled_calls
    t = time()
    while sched and sched[0][0] <= t:
        sched[0][1]()
        sched.pop(0)


def schedule(delay, func):
    """Arrange for the given function to be called after the specified
    delay in seconds. Scheduled functions are called synchronously from
    the event loop, and only when the frame timer is running."""
    t = time() + delay
    insort(scheduled_calls, (t, func))

########NEW FILE########
__FILENAME__ = screen
#
#   Albow - Screen
#

from widget import Widget

#------------------------------------------------------------------------------


class Screen(Widget):

    def __init__(self, shell, **kwds):
        Widget.__init__(self, shell.rect, **kwds)
        self.shell = shell
        self.center = shell.center

    def begin_frame(self):
        pass

    def enter_screen(self):
        pass

    def leave_screen(self):
        pass

########NEW FILE########
__FILENAME__ = shell
#
#   Albow - Shell
#

from root import RootWidget

#------------------------------------------------------------------------------


class Shell(RootWidget):

    def __init__(self, surface, **kwds):
        RootWidget.__init__(self, surface, **kwds)
        self.current_screen = None

    def show_screen(self, new_screen):
        old_screen = self.current_screen
        if old_screen is not new_screen:
            if old_screen:
                old_screen.leave_screen()
            self.remove(old_screen)
            self.add(new_screen)
            self.current_screen = new_screen
            if new_screen:
                new_screen.focus()
                new_screen.enter_screen()

    def begin_frame(self):
        screen = self.current_screen
        if screen:
            screen.begin_frame()

########NEW FILE########
__FILENAME__ = sound
#
#   Albow - Sound utilities
#

import pygame
from pygame import mixer


def pause_sound():
    try:
        mixer.pause()
    except pygame.error:
        pass


def resume_sound():
    try:
        mixer.unpause()
    except pygame.error:
        pass


def stop_sound():
    try:
        mixer.stop()
    except pygame.error:
        pass

########NEW FILE########
__FILENAME__ = table_view
#
#   Albow - Table View
#

from itertools import izip
from pygame import Rect
from layout import Column
from palette_view import PaletteView
from utils import blit_in_rect


class TableView(Column):

    columns = []
    header_font = None
    header_fg_color = None
    header_bg_color = None
    header_spacing = 5
    column_margin = 2

    def __init__(self, nrows=15, height=None,
            header_height=None, row_height=None,
            scrolling=True, **kwds):
        columns = self.predict_attr(kwds, 'columns')
        if row_height is None:
            font = self.predict_font(kwds)
            row_height = font.get_linesize()
        if header_height is None:
            header_height = row_height
        row_width = 0
        if columns:
            for column in columns:
                row_width += column.width
            row_width += 2 * self.column_margin * len(columns)
        contents = []
        header = None
        if header_height:
            header = TableHeaderView(row_width, header_height)
            contents.append(header)
        row_size = (row_width, row_height)
        if not nrows and height:
            nrows = height // row_height
        self.rows = rows = TableRowView(row_size, nrows or 10, scrolling=scrolling)
        contents.append(rows)
        s = self.header_spacing
        Column.__init__(self, contents, align='l', spacing=s, **kwds)
        if header:
            header.font = self.header_font or self.font
            header.fg_color = fg_color = self.header_fg_color or self.fg_color
            header.bg_color = bg_color = self.header_bg_color or self.bg_color
        rows.font = self.font
        rows.fg_color = self.fg_color
        rows.bg_color = self.bg_color
        rows.sel_color = self.sel_color

    def column_info(self, row_data):
        columns = self.columns
        m = self.column_margin
        d = 2 * m
        x = 0
        for i, column in enumerate(columns):
            width = column.width
            if row_data:
                data = row_data[i]
            else:
                data = None
            yield i, x + m, width - d, column, data
            x += width

    def draw_header_cell(self, surf, i, cell_rect, column):
        self.draw_text_cell(surf, i, column.title, cell_rect,
            column.alignment, self.font)

    def draw_table_cell(self, surf, i, data, cell_rect, column):
        text = column.format(data)
        self.draw_text_cell(surf, i, text, cell_rect, column.alignment, self.font)

    def draw_text_cell(self, surf, i, data, cell_rect, align, font):
        buf = font.render(unicode(data), True, self.fg_color)
        blit_in_rect(surf, buf, cell_rect, align)

    def row_is_selected(self, n):
        return False

    def click_row(self, n, e):
        pass

    def click_column_header(self, col):
        print "click_column_header: ", col

    def click_header(self, n, e):
        x, y = self.global_to_local(e.pos)
        width = 0
        for col in self.columns:
            width += col.width
            if x < width:
                return self.click_column_header(col)


class TableColumn(object):
    #  title           string
    #  width           int
    #  alignment       'l' or 'c' or 'r'
    #  formatter       func(data) -> string
    #  format_string   string                Used by default formatter

    format_string = "%s"

    def __init__(self, title, width, align='l', fmt=None):
        self.title = title
        self.width = width
        self.alignment = align
        if fmt:
            if isinstance(fmt, (str, unicode)):
                self.format_string = fmt
            else:
                self.formatter = fmt

    def format(self, data):
        if data is not None:
            return self.formatter(data)
        else:
            return ""

    def formatter(self, data):
            return self.format_string % data


class TableRowBase(PaletteView):

    def __init__(self, cell_size, nrows, scrolling):
        PaletteView.__init__(self, cell_size, nrows, 1, scrolling=scrolling)

    def num_items(self):
        return self.parent.num_rows()

    def draw_item(self, surf, row, row_rect):
        table = self.parent
        height = row_rect.height
        row_data = self.row_data(row)

        for i, x, width, column, cell_data in table.column_info(row_data):
            cell_rect = Rect(x + self.margin, row_rect.top, width, height)
            self.draw_table_cell(surf, row, cell_data, cell_rect, column)

    def row_data(self, row):
        return self.parent.row_data(row)

    def draw_table_cell(self, surf, i, data, cell_rect, column):
        self.parent.draw_table_cell(surf, i, data, cell_rect, column)


class TableRowView(TableRowBase):

    highlight_style = 'fill'
    vstretch = True

    def item_is_selected(self, n):
        return self.parent.row_is_selected(n)

    def click_item(self, n, e):
        self.parent.click_row(n, e)


class TableHeaderView(TableRowBase):

    def __init__(self, width, height):
        TableRowBase.__init__(self, (width, height), 1, False)

#    def row_data(self, row):
#        return [c.title for c in self.parent.columns]

#    def draw_table_cell(self, surf, i, text, cell_rect, column):
#        self.parent.draw_header_cell(surf, i, text, cell_rect, column)

    def row_data(self, row):
        None

    def draw_table_cell(self, surf, i, data, cell_rect, column):
        self.parent.draw_header_cell(surf, i, cell_rect, column)

    def click_item(self, n, e):
        self.parent.click_header(n, e)

########NEW FILE########
__FILENAME__ = tab_panel
################################################################
#
#   Albow - Tab Panel
#
################################################################

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from albow import *
from pygame import Rect, Surface, draw, image
from pygame.locals import SRCALPHA
from widget import Widget
from theme import ThemeProperty, FontProperty
from utils import brighten
from numpy import fromstring


class TabPanel(Widget):
    #  pages         [Widget]
    #  current_page  Widget

    tab_font = FontProperty('tab_font')
    tab_height = ThemeProperty('tab_height')
    tab_border_width = ThemeProperty('tab_border_width')
    tab_spacing = ThemeProperty('tab_spacing')
    tab_margin = ThemeProperty('tab_margin')
    tab_fg_color = ThemeProperty('tab_fg_color')
    default_tab_bg_color = ThemeProperty('default_tab_bg_color')
    tab_area_bg_color = ThemeProperty('tab_area_bg_color')
    tab_dimming = ThemeProperty('tab_dimming')
    tab_titles = None
    #use_page_bg_color_for_tabs = ThemeProperty('use_page_bg_color_for_tabs')

    def __init__(self, pages=None, **kwds):
        Widget.__init__(self, **kwds)
        self.pages = []
        self.current_page = None
        if pages:
            w = h = 0
            for title, page in pages:
                w = max(w, page.width)
                h = max(h, page.height)
                self._add_page(title, page)
            self.size = (w, h)
            self.show_page(pages[0][1])

    def content_size(self):
        return self.width, self.height - self.tab_height

    def content_rect(self):
        return Rect((0, self.tab_height), self.content_size())

    def page_height(self):
        return self.height - self.tab_height

    def add_page(self, title, page):
        self._add_page(title, page)
        if not self.current_page:
            self.show_page(page)

    def _add_page(self, title, page):
        page.tab_title = title
        page.anchor = 'ltrb'
        self.pages.append(page)

    def remove_page(self, page):
        try:
            i = self.pages.index(page)
            del self.pages[i]
        except IndexError:
            pass
        if page is self.current_page:
            self.show_page(None)

    def show_page(self, page):
        if self.current_page:
            self.remove(self.current_page)
        self.current_page = page
        if page:
            th = self.tab_height
            page.rect = Rect(0, th, self.width, self.height - th)
            self.add(page)
            page.focus()

    def draw(self, surf):
        self.draw_tab_area_bg(surf)
        self.draw_tabs(surf)

    def draw_tab_area_bg(self, surf):
        bg = self.tab_area_bg_color
        if bg:
            surf.fill(bg, (0, 0, self.width, self.tab_height))

    def draw_tabs(self, surf):
        font = self.tab_font
        fg = self.tab_fg_color
        b = self.tab_border_width
        if b:
            surf.fill(fg, (0, self.tab_height - b, self.width, b))
        for i, title, page, selected, rect in self.iter_tabs():
            x0 = rect.left
            w = rect.width
            h = rect.height
            r = rect
            if not selected:
                r = Rect(r)
                r.bottom -= b
            self.draw_tab_bg(surf, page, selected, r)
            if b:
                surf.fill(fg, (x0, 0, b, h))
                surf.fill(fg, (x0 + b, 0, w - 2 * b, b))
                surf.fill(fg, (x0 + w - b, 0, b, h))
            buf = font.render(title, True, page.fg_color or fg)
            r = buf.get_rect()
            r.center = (x0 + w // 2, h // 2)
            surf.blit(buf, r)

    def iter_tabs(self):
        pages = self.pages
        current_page = self.current_page
        n = len(pages)
        b = self.tab_border_width
        s = self.tab_spacing
        h = self.tab_height
        m = self.tab_margin
        width = self.width - 2 * m + s - b
        x0 = m
        for i, page in enumerate(pages):
            x1 = m + (i + 1) * width // n  # self.tab_boundary(i + 1)
            selected = page is current_page
            yield i, page.tab_title, page, selected, Rect(x0, 0, x1 - x0 - s + b, h)
            x0 = x1

    def draw_tab_bg(self, surf, page, selected, rect):
        bg = self.tab_bg_color_for_page(page)
        if not selected:
            bg = brighten(bg, self.tab_dimming)
        surf.fill(bg, rect)

    def tab_bg_color_for_page(self, page):
        return getattr(page, 'tab_bg_color', None) \
            or page.bg_color \
            or self.default_tab_bg_color

    def mouse_down(self, e):
        x, y = e.local
        if y < self.tab_height:
            i = self.tab_number_containing_x(x)
            if i is not None:
                self.show_page(self.pages[i])

    def tab_number_containing_x(self, x):
        n = len(self.pages)
        m = self.tab_margin
        width = self.width - 2 * m + self.tab_spacing - self.tab_border_width
        i = (x - m) * n // width
        if 0 <= i < n:
            return i
        
    def gl_draw_self(self, root, offset):
        self.gl_draw(root, offset)

    def gl_draw(self, root, offset):
        pages = self.pages

        if len(pages) > 1:
            tlcorner = (offset[0] + self.bottomleft[0], offset[1] + self.bottomleft[1])
            pageTabContents = []        
            current_page = self.current_page
            n = len(pages)
            b = self.tab_border_width
            s = self.tab_spacing
            h = self.tab_height
            m = self.tab_margin
            tabWidth = (self.size[0]-(s*n)-(2*m))/n
            width = self.width - 2 * m + s - b
            x0 = m + tlcorner[0]

            font = self.tab_font
            fg = self.tab_fg_color
            surface = Surface(self.size, SRCALPHA)

            glEnable(GL_BLEND)
            
            for i, page in enumerate(pages):
                x1 = x0+tabWidth
                selected = page is current_page
                if selected:
                    glColor(1.0, 1.0, 1.0, 0.5)
                else:
                    glColor(0.5, 0.5, 0.5, 0.5)
                glRectf(x0, tlcorner[1]-(m+b), x1, tlcorner[1]-(h))
                buf = font.render(self.pages[i].tab_title, True, self.fg_color or fg)
                r = buf.get_rect()

                offs = ((tabWidth - r.size[0])/2) + m +((s+tabWidth)*i)

                surface.blit(buf, (offs, m))
                x0 = x1 + s    
            
            data = image.tostring(surface, 'RGBA', 1)
            rect = self.rect.move(offset)
            w, h = root.size
            glViewport(0, 0, w, h)
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluOrtho2D(0, w, 0, h)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            glRasterPos2i(rect.left, h - rect.bottom)
            glPushAttrib(GL_COLOR_BUFFER_BIT)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDrawPixels(self.width, self.height,
                GL_RGBA, GL_UNSIGNED_BYTE, fromstring(data, dtype='uint8'))
            glPopAttrib()
            glFlush()

            glDisable(GL_BLEND)

########NEW FILE########
__FILENAME__ = text_screen
#
#   Albow - Text Screen
#

from pygame import Rect
from pygame.locals import *
from screen import Screen
from theme import FontProperty
from resource import get_image, get_font, get_text
from vectors import add, maximum
from controls import Button

#------------------------------------------------------------------------------


class Page(object):

    def __init__(self, text_screen, heading, lines):
        self.text_screen = text_screen
        self.heading = heading
        self.lines = lines
        width, height = text_screen.heading_font.size(heading)
        for line in lines:
            w, h = text_screen.font.size(line)
            width = max(width, w)
            height += h
        self.size = (width, height)

    def draw(self, surface, color, pos):
        heading_font = self.text_screen.heading_font
        text_font = self.text_screen.font
        x, y = pos
        buf = heading_font.render(self.heading, True, color)
        surface.blit(buf, (x, y))
        y += buf.get_rect().height
        for line in self.lines:
            buf = text_font.render(line, True, color)
            surface.blit(buf, (x, y))
            y += buf.get_rect().height

#------------------------------------------------------------------------------


class TextScreen(Screen):

#    bg_color = (0, 0, 0)
#    fg_color = (255, 255, 255)
#    border = 20

    heading_font = FontProperty('heading_font')
    button_font = FontProperty('button_font')

    def __init__(self, shell, filename, **kwds):
        text = get_text(filename)
        text_pages = text.split("\nPAGE\n")
        pages = []
        page_size = (0, 0)
        for text_page in text_pages:
            lines = text_page.strip().split("\n")
            page = Page(self, lines[0], lines[1:])
            pages.append(page)
            page_size = maximum(page_size, page.size)
        self.pages = pages
        bf = self.button_font
        b1 = Button("Prev Page", font=bf, action=self.prev_page)
        b2 = Button("Menu", font=bf, action=self.go_back)
        b3 = Button("Next Page", font=bf, action=self.next_page)
        b = self.margin
        page_rect = Rect((b, b), page_size)
        gap = (0, 18)
        b1.topleft = add(page_rect.bottomleft, gap)
        b2.midtop = add(page_rect.midbottom, gap)
        b3.topright = add(page_rect.bottomright, gap)
        Screen.__init__(self, shell, **kwds)
        self.size = add(b3.bottomright, (b, b))
        self.add(b1)
        self.add(b2)
        self.add(b3)
        self.prev_button = b1
        self.next_button = b3
        self.set_current_page(0)

    def draw(self, surface):
        b = self.margin
        self.pages[self.current_page].draw(surface, self.fg_color, (b, b))

    def at_first_page(self):
        return self.current_page == 0

    def at_last_page(self):
        return self.current_page == len(self.pages) - 1

    def set_current_page(self, n):
        self.current_page = n
        self.prev_button.enabled = not self.at_first_page()
        self.next_button.enabled = not self.at_last_page()

    def prev_page(self):
        if not self.at_first_page():
            self.set_current_page(self.current_page - 1)

    def next_page(self):
        if not self.at_last_page():
            self.set_current_page(self.current_page + 1)

    def go_back(self):
        self.parent.show_menu()

########NEW FILE########
__FILENAME__ = theme
#
#    Albow - Themes
#

import resource

debug_theme = False


class ThemeProperty(object):

    def __init__(self, name):
        self.name = name
        self.cache_name = intern("_" + name)

    def __get__(self, obj, owner):
        if debug_theme:
            print "%s(%r).__get__(%r)" % (self.__class__.__name__, self.name, obj)
        try:  ###
            cache_name = self.cache_name
            try:
                return getattr(obj, cache_name)
            except AttributeError, e:
                if debug_theme:
                    print e
                value = self.get_from_theme(obj.__class__, self.name)
                obj.__dict__[cache_name] = value
                return value
        except:  ###
            if debug_theme:
                import traceback
                traceback.print_exc()
                print "-------------------------------------------------------"
            raise  ###

    def __set__(self, obj, value):
        if debug_theme:
            print "Setting %r.%s = %r" % (obj, self.cache_name, value)  ###
        obj.__dict__[self.cache_name] = value

    def get_from_theme(self, cls, name):
        return root.get(cls, name)


class FontProperty(ThemeProperty):

    def get_from_theme(self, cls, name):
        return root.get_font(cls, name)


class ThemeError(Exception):
    pass


class Theme(object):
    #  name   string          Name of theme, for debugging
    #  base   Theme or None   Theme on which this theme is based

    def __init__(self, name, base=None):
        self.name = name
        self.base = base

    def get(self, cls, name):
        try:
            return self.lookup(cls, name)
        except ThemeError:
            raise AttributeError("No value found in theme %s for '%s' of %s.%s" %
                (self.name, name, cls.__module__, cls.__name__))

    def lookup(self, cls, name):
        if debug_theme:
            print "Theme(%r).lookup(%r, %r)" % (self.name, cls, name)
        for base_class in cls.__mro__:
            class_theme = getattr(self, base_class.__name__, None)
            if class_theme:
                try:
                    return class_theme.lookup(cls, name)
                except ThemeError:
                    pass
        else:
            try:
                return getattr(self, name)
            except AttributeError:
                base_theme = self.base
                if base_theme:
                    return base_theme.lookup(cls, name)
                else:
                    raise ThemeError

    def get_font(self, cls, name):
        if debug_theme:
            print "Theme.get_font(%r, %r)" % (cls, name)
        spec = self.get(cls, name)
        if spec:
            if debug_theme:
                print "font spec =", spec
            return resource.get_font(*spec)


root = Theme('root')
root.margin = 3
root.font = (15, "Vera.ttf")
root.fg_color = (255, 255, 255)
root.bg_color = None
root.bg_image = None
root.scale_bg = False
root.border_width = 0
root.border_color = (0, 0, 0)
root.tab_bg_color = None
root.sel_color = (112, 112, 112)
root.highlight_color = None
root.hover_color = None
root.disabled_color = None
root.highlight_bg_color = None
root.hover_bg_color = None
root.enabled_bg_color = None
root.disabled_bg_color = None

root.RootWidget = Theme('RootWidget')
root.RootWidget.bg_color = (0, 0, 0)

root.Button = Theme('Button')
root.Button.font = (17, "VeraBd.ttf")
root.Button.fg_color = (255, 255, 0)
root.Button.highlight_color = (16, 255, 16)
root.Button.disabled_color = (64, 64, 64)
root.Button.hover_color = (255, 255, 225)
root.Button.default_choice_color = (144, 133, 255)
root.Button.default_choice_bg_color = None
root.Button.highlight_bg_color = None
root.Button.enabled_bg_color = (48, 48, 48)
root.Button.disabled_bg_color = None
root.Button.margin = 7
root.Button.border_width = 1
root.Button.border_color = (64, 64, 64)

root.ValueButton = Theme('ValueButton', base=root.Button)

root.Label = Theme('Label')
root.Label.margin = 4

root.SmallLabel = Theme('SmallLabel')
root.SmallLabel.font = (10, 'Vera.ttf')

root.ValueDisplay = Theme('ValueDisplay')
root.ValueDisplay.margin = 4

root.SmallValueDisplay = Theme('SmallValueDisplay')
root.SmallValueDisplay.font = (10, 'Vera.ttf')
root.ValueDisplay.margin = 2

root.ImageButton = Theme('ImageButton')
root.ImageButton.highlight_color = (0, 128, 255)

framed = Theme('framed')
framed.border_width = 1
framed.margin = 3

root.Field = Theme('Field', base=framed)
root.Field.border_color = (128, 128, 128)

root.CheckWidget = Theme('CheckWidget')
root.CheckWidget.smooth = False
root.CheckWidget.border_color = root.Field.border_color

root.Dialog = Theme('Dialog')
root.Dialog.bg_color = (40, 40, 40)
root.Dialog.border_width = 1
root.Dialog.margin = 15

root.DirPathView = Theme('DirPathView', base=framed)

root.FileListView = Theme('FileListView', base=framed)
root.FileListView.scroll_button_color = (255, 255, 0)

root.FileDialog = Theme("FileDialog")
root.FileDialog.up_button_text = "<-"

root.PaletteView = Theme('PaletteView')
root.PaletteView.sel_width = 2
root.PaletteView.scroll_button_size = 16
root.PaletteView.scroll_button_color = (0, 128, 255)
root.PaletteView.highlight_style = 'frame'
root.PaletteView.zebra_color = (48, 48, 48)

root.TextScreen = Theme('TextScreen')
root.TextScreen.heading_font = (24, "VeraBd.ttf")
root.TextScreen.button_font = (18, "VeraBd.ttf")
root.TextScreen.margin = 20

root.TabPanel = Theme('TabPanel')
root.TabPanel.tab_font = (18, "Vera.ttf")
root.TabPanel.tab_height = 24
root.TabPanel.tab_border_width = 0
root.TabPanel.tab_spacing = 4
root.TabPanel.tab_margin = 0
root.TabPanel.tab_fg_color = root.fg_color
root.TabPanel.default_tab_bg_color = (128, 128, 128)
root.TabPanel.tab_area_bg_color = None
root.TabPanel.tab_dimming = 0.75
#root.TabPanel.use_page_bg_color_for_tabs = True

menu = Theme('menu')
menu.bg_color = (64, 64, 64)
menu.fg_color = (255, 255, 255)
menu.disabled_color = (0, 0, 0)
menu.margin = 8
menu.border_color = (192, 192, 192)
menu.scroll_button_size = 16
menu.scroll_button_color = (255, 255, 0)

root.MenuBar = Theme('MenuBar', base=menu)
root.MenuBar.border_width = 0

root.Menu = Theme('Menu', base=menu)
root.Menu.border_width = 1

root.MusicVolumeControl = Theme('MusicVolumeControl', base=framed)
root.MusicVolumeControl.fg_color = (0x40, 0x40, 0x40)

########NEW FILE########
__FILENAME__ = utils
from pygame import draw, Surface
from pygame.locals import SRCALPHA


def frame_rect(surface, color, rect, thick=1):
    o = 1
    surface.fill(color, (rect.left + o, rect.top, rect.width - o - o, thick))
    surface.fill(color, (rect.left + o, rect.bottom - thick, rect.width - o - o, thick))
    surface.fill(color, (rect.left, rect.top + o, thick, rect.height - o - o))
    surface.fill(color, (rect.right - thick, rect.top + o, thick, rect.height - o - o))


def blit_tinted(surface, image, pos, tint, src_rect=None):
    from Numeric import array, add, minimum
    from pygame.surfarray import array3d, pixels3d
    if src_rect:
        image = image.subsurface(src_rect)
    buf = Surface(image.get_size(), SRCALPHA, 32)
    buf.blit(image, (0, 0))
    src_rgb = array3d(image)
    buf_rgb = pixels3d(buf)
    buf_rgb[...] = minimum(255, add(tint, src_rgb)).astype('b')
    buf_rgb = None
    surface.blit(buf, pos)


def blit_in_rect(dst, src, frame, align='tl', margin=0):
    r = src.get_rect()
    align_rect(r, frame, align, margin)
    dst.blit(src, r)


def align_rect(r, frame, align='tl', margin=0):
    if 'l' in align:
        r.left = frame.left + margin
    elif 'r' in align:
        r.right = frame.right - margin
    else:
        r.centerx = frame.centerx
    if 't' in align:
        r.top = frame.top + margin
    elif 'b' in align:
        r.bottom = frame.bottom - margin
    else:
        r.centery = frame.centery


def brighten(rgb, factor):
    return [min(255, int(round(factor * c))) for c in rgb]

########NEW FILE########
__FILENAME__ = vectors
try:

    from Numeric import add, subtract, maximum

except ImportError:

    import operator

    def add(x, y):
        return map(operator.add, x, y)

    def subtract(x, y):
        return map(operator.sub, x, y)

    def maximum(*args):
        result = args[0]
        for x in args[1:]:
            result = map(max, result, x)
        return result

########NEW FILE########
__FILENAME__ = version
version = (2, 1, 0)

########NEW FILE########
__FILENAME__ = widget
from __future__ import division
import sys
from pygame import Rect, Surface, draw, image
from pygame.locals import K_RETURN, K_KP_ENTER, K_ESCAPE, K_TAB, \
    KEYDOWN, SRCALPHA
from pygame.mouse import set_cursor
from pygame.cursors import arrow as arrow_cursor
from pygame.transform import rotozoom
from vectors import add, subtract
from utils import frame_rect
import theme
from theme import ThemeProperty, FontProperty

from numpy import fromstring

debug_rect = False
debug_tab = True

root_widget = None
current_cursor = None


def overridable_property(name, doc=None):
    """Creates a property which calls methods get_xxx and set_xxx of
    the underlying object to get and set the property value, so that
    the property's behaviour may be easily overridden by subclasses."""

    getter_name = intern('get_' + name)
    setter_name = intern('set_' + name)
    return property(
        lambda self: getattr(self, getter_name)(),
        lambda self, value: getattr(self, setter_name)(value),
        None,
        doc)


def rect_property(name):
    def get(self):
        return getattr(self._rect, name)

    def set(self, value):
        r = self._rect
        old_size = r.size
        setattr(r, name, value)
        new_size = r.size
        if old_size != new_size:
            self._resized(old_size)
    return property(get, set)

#noinspection PyPropertyAccess


class Widget(object):
    #  rect            Rect       bounds in parent's coordinates
    #  parent          Widget     containing widget
    #  subwidgets      [Widget]   contained widgets
    #  focus_switch    Widget     subwidget to receive key events
    #  fg_color        color      or None to inherit from parent
    #  bg_color        color      to fill background, or None
    #  visible         boolean
    #  border_width    int        width of border to draw around widget, or None
    #  border_color    color      or None to use widget foreground color
    #  tab_stop        boolean    stop on this widget when tabbing
    #  anchor          string     of 'ltrb'

    font = FontProperty('font')
    fg_color = ThemeProperty('fg_color')
    bg_color = ThemeProperty('bg_color')
    bg_image = ThemeProperty('bg_image')
    scale_bg = ThemeProperty('scale_bg')
    border_width = ThemeProperty('border_width')
    border_color = ThemeProperty('border_color')
    sel_color = ThemeProperty('sel_color')
    margin = ThemeProperty('margin')
    menu_bar = overridable_property('menu_bar')
    is_gl_container = overridable_property('is_gl_container')

    tab_stop = False
    enter_response = None
    cancel_response = None
    anchor = 'ltwh'
    debug_resize = False
    _menubar = None
    _visible = True
    _is_gl_container = False

    tooltip = None
    tooltipText = None

    def __init__(self, rect=None, **kwds):
        if rect and not isinstance(rect, Rect):
            raise TypeError("Widget rect not a pygame.Rect")
        self._rect = Rect(rect or (0, 0, 100, 100))
        self.parent = None
        self.subwidgets = []
        self.focus_switch = None
        self.is_modal = False
        self.set(**kwds)

    def set(self, **kwds):
        for name, value in kwds.iteritems():
            if not hasattr(self, name):
                raise TypeError("Unexpected keyword argument '%s'" % name)
            setattr(self, name, value)

    def get_rect(self):
        return self._rect

    def set_rect(self, x):
        old_size = self._rect.size
        self._rect = Rect(x)
        self._resized(old_size)

#    def get_anchor(self):
#        if self.hstretch:
#            chars ='lr'
#        elif self.hmove:
#            chars = 'r'
#        else:
#            chars = 'l'
#        if self.vstretch:
#            chars += 'tb'
#        elif self.vmove:
#            chars += 'b'
#        else:
#            chars += 't'
#        return chars
#
#    def set_anchor(self, chars):
#        self.hmove = 'r' in chars and not 'l' in chars
#        self.vmove = 'b' in chars and not 't' in chars
#        self.hstretch = 'r' in chars and 'l' in chars
#        self.vstretch = 'b' in chars and 't' in chars
#
#    anchor = property(get_anchor, set_anchor)

    resizing_axes = {'h': 'lr', 'v': 'tb'}
    resizing_values = {'': [0], 'm': [1], 's': [0, 1]}

    def set_resizing(self, axis, value):
        chars = self.resizing_axes[axis]
        anchor = self.anchor
        for c in chars:
            anchor = anchor.replace(c, '')
        for i in self.resizing_values[value]:
            anchor += chars[i]
        self.anchor = anchor + value

    def _resized(self, (old_width, old_height)):
        new_width, new_height = self._rect.size
        dw = new_width - old_width
        dh = new_height - old_height
        if dw or dh:
            self.resized(dw, dh)

    def resized(self, dw, dh):
        if self.debug_resize:
            print "Widget.resized:", self, "by", (dw, dh), "to", self.size
        for widget in self.subwidgets:
            widget.parent_resized(dw, dh)

    def parent_resized(self, dw, dh):
        debug_resize = self.debug_resize or self.parent.debug_resize
        if debug_resize:
            print "Widget.parent_resized:", self, "by", (dw, dh)
        left, top, width, height = self._rect
        move = False
        resize = False
        anchor = self.anchor
        if dw:
            factors = [1, 1, 1]  # left, width, right
            if 'r' in anchor:
                factors[2] = 0
            if 'w' in anchor:
                factors[1] = 0
            if 'l' in anchor:
                factors[0] = 0
            if any(factors):
                resize = factors[1]
                move = factors[0] or factors[2]
                #print "lwr", factors
                left += factors[0] * dw / sum(factors)
                width += factors[1] * dw / sum(factors)
                #left = (left + width) + factors[2] * dw / sum(factors) - width

        if dh:
            factors = [1, 1, 1]  # bottom, height, top
            if 't' in anchor:
                factors[2] = 0
            if 'h' in anchor:
                factors[1] = 0
            if 'b' in anchor:
                factors[0] = 0
            if any(factors):
                resize = factors[1]
                move = factors[0] or factors[2]
                #print "bht", factors
                top += factors[2] * dh / sum(factors)
                height += factors[1] * dh / sum(factors)
                #top = (top + height) + factors[0] * dh / sum(factors) - height

        if resize:
            if debug_resize:
                print "Widget.parent_resized: changing rect to", (left, top, width, height)
            self.rect = (left, top, width, height)
        elif move:
            if debug_resize:
                print "Widget.parent_resized: moving to", (left, top)
            self._rect.topleft = (left, top)

    rect = property(get_rect, set_rect)

    left = rect_property('left')
    right = rect_property('right')
    top = rect_property('top')
    bottom = rect_property('bottom')
    width = rect_property('width')
    height = rect_property('height')
    size = rect_property('size')
    topleft = rect_property('topleft')
    topright = rect_property('topright')
    bottomleft = rect_property('bottomleft')
    bottomright = rect_property('bottomright')
    midleft = rect_property('midleft')
    midright = rect_property('midright')
    midtop = rect_property('midtop')
    midbottom = rect_property('midbottom')
    center = rect_property('center')
    centerx = rect_property('centerx')
    centery = rect_property('centery')

    def get_visible(self):
        return self._visible

    def set_visible(self, x):
        self._visible = x

    visible = overridable_property('visible')

    def add(self, arg):
        if arg:
            if isinstance(arg, Widget):
                arg.set_parent(self)
            else:
                for item in arg:
                    self.add(item)

    def add_centered(self, widget):
        w, h = self.size
        widget.center = w // 2, h // 2
        self.add(widget)

    def remove(self, widget):
        if widget in self.subwidgets:
            widget.set_parent(None)

    def set_parent(self, parent):
        if parent is not self.parent:
            if self.parent:
                self.parent._remove(self)
            self.parent = parent
            if parent:
                parent._add(self)

    def all_parents(self):
        widget = self
        parents = []
        while widget.parent:
            parents.append(widget.parent)
            widget = widget.parent
        return parents

    def _add(self, widget):
        self.subwidgets.append(widget)
        if hasattr(widget, "idleevent"):
            #print "Adding idle handler for ", widget
            self.get_root().add_idle_handler(widget)

    def _remove(self, widget):
        if hasattr(widget, "idleevent"):
            #print "Removing idle handler for ", widget
            self.get_root().remove_idle_handler(widget)
        self.subwidgets.remove(widget)

        if self.focus_switch is widget:
            self.focus_switch = None

    def draw_all(self, surface):
        if self.visible:
            surf_rect = surface.get_rect()
            bg_image = self.bg_image
            if bg_image:
                assert isinstance(bg_image, Surface)
                if self.scale_bg:
                    bg_width, bg_height = bg_image.get_size()
                    width, height = self.size
                    if width > bg_width or height > bg_height:
                        hscale = width / bg_width
                        vscale = height / bg_height
                        bg_image = rotozoom(bg_image, 0.0, max(hscale, vscale))
                r = bg_image.get_rect()
                r.center = surf_rect.center
                surface.blit(bg_image, r)
            else:
                bg = self.bg_color
                if bg:
                    surface.fill(bg)
            self.draw(surface)
            bw = self.border_width
            if bw:
                bc = self.border_color or self.fg_color
                frame_rect(surface, bc, surf_rect, bw)
            for widget in self.subwidgets:
                sub_rect = widget.rect
                if debug_rect:
                    print "Widget: Drawing subwidget %s of %s with rect %s" % (
                        widget, self, sub_rect)
                sub_rect = surf_rect.clip(sub_rect)
                if sub_rect.width > 0 and sub_rect.height > 0:
                    try:
                        sub = surface.subsurface(sub_rect)
                    except ValueError, e:
                        if str(e) == "subsurface rectangle outside surface area":
                            self.diagnose_subsurface_problem(surface, widget)
                        else:
                            raise
                    else:
                        widget.draw_all(sub)
            self.draw_over(surface)

    def diagnose_subsurface_problem(self, surface, widget):
        mess = "Widget %s %s outside parent surface %s %s" % (
            widget, widget.rect, self, surface.get_rect())
        sys.stderr.write("%s\n" % mess)
        surface.fill((255, 0, 0), widget.rect)

    def draw(self, surface):
        pass

    def draw_over(self, surface):
        pass

    def find_widget(self, pos):
        for widget in self.subwidgets[::-1]:
            if widget.visible:
                r = widget.rect
                if r.collidepoint(pos):
                    return widget.find_widget(subtract(pos, r.topleft))
        return self

    def handle_mouse(self, name, event):
        self.augment_mouse_event(event)
        self.call_handler(name, event)
        self.setup_cursor(event)

    def mouse_down(self, event):
        self.call_parent_handler("mouse_down", event)

    def mouse_up(self, event):
        self.call_parent_handler("mouse_up", event)

    def augment_mouse_event(self, event):
        event.dict['local'] = self.global_to_local(event.pos)

    def setup_cursor(self, event):
        global current_cursor
        cursor = self.get_cursor(event) or arrow_cursor
        if cursor is not current_cursor:
            set_cursor(*cursor)
            current_cursor = cursor

    def dispatch_key(self, name, event):
        if self.visible:

            if event.cmd and event.type == KEYDOWN:
                menubar = self._menubar
                if menubar and menubar.handle_command_key(event):
                    return
            widget = self.focus_switch
            if widget:
                widget.dispatch_key(name, event)
            else:
                self.call_handler(name, event)
        else:
            self.call_parent_handler(name, event)

    def get_focus(self):
        widget = self
        while 1:
            focus = widget.focus_switch
            if not focus:
                break
            widget = focus
        return widget

    def notify_attention_loss(self):
        widget = self
        while 1:
            if widget.is_modal:
                break
            parent = widget.parent
            if not parent:
                break
            focus = parent.focus_switch
            if focus and focus is not widget:
                focus.dispatch_attention_loss()
            widget = parent

    def dispatch_attention_loss(self):
        widget = self
        while widget:
            widget.attention_lost()
            widget = widget.focus_switch

    def attention_lost(self):
        pass

    def handle_command(self, name, *args):
        method = getattr(self, name, None)
        if method:
            return method(*args)
        else:
            parent = self.next_handler()
            if parent:
                return parent.handle_command(name, *args)

    def next_handler(self):
        if not self.is_modal:
            return self.parent

    def call_handler(self, name, *args):
        method = getattr(self, name, None)
        if method:
            return method(*args)
        else:
            return 'pass'

    def call_parent_handler(self, name, *args):
        parent = self.next_handler()
        if parent:
            parent.call_handler(name, *args)

    def global_to_local(self, p):
        return subtract(p, self.local_to_global_offset())

    def local_to_global(self, p):
        return add(p, self.local_to_global_offset())

    def local_to_global_offset(self):
        d = self.topleft
        parent = self.parent
        if parent:
            d = add(d, parent.local_to_global_offset())
        return d

    def key_down(self, event):
        k = event.key
        #print "Widget.key_down:", k ###
        if k == K_RETURN or k == K_KP_ENTER:
            if self.enter_response is not None:
                self.dismiss(self.enter_response)
                return
        elif k == K_ESCAPE:
            if self.cancel_response is not None:
                self.dismiss(self.cancel_response)
                return
        elif k == K_TAB:
            self.tab_to_next()
            return
        self.call_parent_handler('key_down', event)

    def key_up(self, event):
        self.call_parent_handler('key_up', event)

    def is_inside(self, container):
        widget = self
        while widget:
            if widget is container:
                return True
            widget = widget.parent
        return False

    @property
    def is_hover(self):
        return self.get_root().hover_widget is self

    def present(self, centered=True):
        #print "Widget: presenting with rect", self.rect
        root = self.get_root()
        if centered:
            self.center = root.center
        root.add(self)
        try:
            root.run_modal(self)
            self.dispatch_attention_loss()
        finally:
            root.remove(self)
        #print "Widget.present: returning", self.modal_result
        return self.modal_result

    def dismiss(self, value=True):
        self.modal_result = value

    def get_root(self):
        # Deprecated, use root.get_root()
        return root_widget

    def get_top_widget(self):
        top = self
        while top.parent and not top.is_modal:
            top = top.parent
        return top

    def focus(self):
        parent = self.next_handler()
        if parent:
            parent.focus_on(self)

    def focus_on(self, subwidget):
        old_focus = self.focus_switch
        if old_focus is not subwidget:
            if old_focus:
                old_focus.dispatch_attention_loss()
            self.focus_switch = subwidget
        self.focus()

    def has_focus(self):
        return self.is_modal or (self.parent and self.parent.focused_on(self))

    def focused_on(self, widget):
        return self.focus_switch is widget and self.has_focus()

    def focus_chain(self):
        result = []
        widget = self
        while widget:
            result.append(widget)
            widget = widget.focus_switch
        return result

    def shrink_wrap(self):
        contents = self.subwidgets
        if contents:
            rects = [widget.rect for widget in contents]
            #rmax = Rect.unionall(rects) # broken in PyGame 1.7.1
            rmax = rects.pop()
            for r in rects:
                rmax = rmax.union(r)
            self._rect.size = add(rmax.topleft, rmax.bottomright)

    def invalidate(self):
        root = self.get_root()
        if root:
            root.do_draw = True

    def get_cursor(self, event):
        return arrow_cursor

    def predict(self, kwds, name):
        try:
            return kwds[name]
        except KeyError:
            return theme.root.get(self.__class__, name)

    def predict_attr(self, kwds, name):
        try:
            return kwds[name]
        except KeyError:
            return getattr(self, name)

    def init_attr(self, kwds, name):
        try:
            return kwds.pop(name)
        except KeyError:
            return getattr(self, name)

    def predict_font(self, kwds, name='font'):
        return kwds.get(name) or theme.root.get_font(self.__class__, name)

    def get_margin_rect(self):
        r = Rect((0, 0), self.size)
        d = -2 * self.margin
        r.inflate_ip(d, d)
        return r

    def set_size_for_text(self, width, nlines=1):
        if width is not None:
            font = self.font
            d = 2 * self.margin
            if isinstance(width, basestring):
                width, height = font.size(width)
                width += d + 2
            else:
                height = font.size("X")[1]
            self.size = (width, height * nlines + d)

    def tab_to_first(self):
        chain = self.get_tab_order()
        if chain:
            chain[0].focus()

    def tab_to_next(self):
        top = self.get_top_widget()
        chain = top.get_tab_order()
        try:
            i = chain.index(self)
        except ValueError:
            return
        target = chain[(i + 1) % len(chain)]
        target.focus()

    def get_tab_order(self):
        result = []
        self.collect_tab_order(result)
        return result

    def collect_tab_order(self, result):
        if self.visible:
            if self.tab_stop:
                result.append(self)
            for child in self.subwidgets:
                child.collect_tab_order(result)

#    def tab_to_first(self, start = None):
#        if debug_tab:
#            print "Enter Widget.tab_to_first:", self ###
#            print "...start =", start ###
#        if not self.visible:
#            if debug_tab: print "...invisible" ###
#            self.tab_to_next_in_parent(start)
#        elif self.tab_stop:
#            if debug_tab: print "...stopping here" ###
#            self.focus()
#        else:
#            if debug_tab: print "...tabbing to next" ###
#            self.tab_to_next(start or self)
#        if debug_tab: print "Exit Widget.tab_to_first:", self ###
#
#    def tab_to_next(self, start = None):
#        if debug_tab:
#            print "Enter Widget.tab_to_next:", self ###
#            print "...start =", start ###
#        sub = self.subwidgets
#        if sub:
#            if debug_tab: print "...tabbing to first subwidget" ###
#            sub[0].tab_to_first(start or self)
#        else:
#            if debug_tab: print "...tabbing to next in parent" ###
#            self.tab_to_next_in_parent(start)
#        if debug_tab: print "Exit Widget.tab_to_next:", self ###
#
#    def tab_to_next_in_parent(self, start):
#        if debug_tab:
#            print "Enter Widget.tab_to_next_in_parent:", self ###
#            print "...start =", start ###
#        parent = self.parent
#        if parent and not self.is_modal:
#            if debug_tab: print "...telling parent to tab to next" ###
#            parent.tab_to_next_after(self, start)
#        else:
#            if self is not start:
#                if debug_tab: print "...wrapping back to first" ###
#                self.tab_to_first(start)
#        if debug_tab: print "Exit Widget.tab_to_next_in_parent:", self ###
#
#    def tab_to_next_after(self, last, start):
#        if debug_tab:
#            print "Enter Widget.tab_to_next_after:", self, last ###
#            print "...start =", start ###
#        sub = self.subwidgets
#        i = sub.index(last) + 1
#        if debug_tab: print "...next index =", i, "of", len(sub) ###
#        if i < len(sub):
#            if debug_tab: print "...tabbing there" ###
#            sub[i].tab_to_first(start)
#        else:
#            if debug_tab: print "...tabbing to next in parent" ###
#            self.tab_to_next_in_parent(start)
#        if debug_tab: print "Exit Widget.tab_to_next_after:", self, last ###

    def inherited(self, attribute):
        value = getattr(self, attribute)
        if value is not None:
            return value
        else:
            parent = self.next_handler()
            if parent:
                return parent.inherited(attribute)

    def __contains__(self, event):
        r = Rect(self._rect)
        r.left = 0
        r.top = 0
        p = self.global_to_local(event.pos)
        return r.collidepoint(p)

    def get_mouse(self):
        root = self.get_root()
        return root.get_mouse_for(self)

    def get_menu_bar(self):
        return self._menubar

    def set_menu_bar(self, menubar):
        if menubar is not self._menubar:
            if self._menubar:
                self.remove(self._menubar)
            self._menubar = menubar
            if menubar:
                if menubar.width == 0:
                    menubar.width = self.width
                    menubar.anchor = 'lr'
                self.add(menubar)

    def get_is_gl_container(self):
        return self._is_gl_container

    def set_is_gl_container(self, x):
        self._is_gl_container = x

    def gl_draw_all(self, root, offset):
        if not self.visible:
            return
        from OpenGL import GL, GLU
        rect = self.rect.move(offset)
        if self.is_gl_container:
            self.gl_draw_self(root, offset)
            suboffset = rect.topleft
            for subwidget in self.subwidgets:
                subwidget.gl_draw_all(root, suboffset)
        else:
            try:
                surface = Surface(self.size, SRCALPHA)
            except Exception, e:
                #size error?
                return
            self.draw_all(surface)
            data = image.tostring(surface, 'RGBA', 1)
            w, h = root.size
            GL.glViewport(0, 0, w, h)
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GLU.gluOrtho2D(0, w, 0, h)
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            GL.glRasterPos2i(max(rect.left, 0), max(h - rect.bottom, 0))
            GL.glPushAttrib(GL.GL_COLOR_BUFFER_BIT)
            GL.glEnable(GL.GL_BLEND)
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            GL.glDrawPixels(self.width, self.height,
                GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, fromstring(data, dtype='uint8'))
            GL.glPopAttrib()
            GL.glFlush()

    def gl_draw_self(self, root, offset):
        pass

########NEW FILE########
__FILENAME__ = bresenham
def bresenham(p1, p2):
    """Bresenham line algorithm
    adapted for 3d.  slooooow."""
    steep = 0
    coords = []
    x, y, z = p1
    x2, y2, z2 = p2

    dx = abs(x2 - x)
    if (x2 - x) > 0:
        sx = 1
    else:
        sx = -1
    dy = abs(y2 - y)
    if (y2 - y) > 0:
        sy = 1
    else:
        sy = -1
    dz = abs(z2 - z)
    if (z2 - z) > 0:
        sz = 1
    else:
        sz = -1

    dl = [dx, dy, dz]
    longestAxis = dl.index(max(dl))
    d = [2 * a - dl[longestAxis] for a in dl]

    #if dy > dx:
    #     steep = 1

    #d = (2 * dy) + (2 * dz) - dx
    otherAxes = [0, 1, 2]
    otherAxes.remove(longestAxis)
    p = [x, y, z]
    sp = [sx, sy, sz]
    for i in range(0, int(dl[longestAxis])):
        coords.append(tuple(p))
        for j in otherAxes:

            while d[j] >= 0:
                p[j] = p[j] + sp[j]
                d[j] = d[j] - (2 * dl[longestAxis])

        p[longestAxis] = p[longestAxis] + sp[longestAxis]
        d = map(lambda a, b: a + 2 * b, d, dl)

    return coords  # added by me

########NEW FILE########
__FILENAME__ = compass
"""
    compass
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import logging
from OpenGL import GL
from drawable import Drawable
from glutils import gl
from mceutils import loadPNGTexture

log = logging.getLogger(__name__)


def makeQuad(minx, miny, width, height):
    return [minx, miny, minx+width, miny, minx+width, miny+height, minx, miny + height]

class CompassOverlay(Drawable):
    _tex = None
    _yawPitch = (0., 0.)

    def __init__(self, small=False):
        super(CompassOverlay, self).__init__()
        self.small = small

    @property
    def yawPitch(self):
        return self._yawPitch

    @yawPitch.setter
    def yawPitch(self, value):
        self._yawPitch = value
        self.invalidate()

    def drawSelf(self):
        if self._tex is None:
            if self.small:
                filename = "compass_small.png"
            else:
                filename = "compass.png"

            self._tex = loadPNGTexture("toolicons/" + filename)#, minFilter=GL.GL_LINEAR, magFilter=GL.GL_LINEAR)

        self._tex.bind()
        size = 0.075

        with gl.glPushMatrix(GL.GL_MODELVIEW):
            GL.glLoadIdentity()

            yaw, pitch = self.yawPitch
            GL.glTranslatef(1.-size, size, 0.0)  # position on upper right corner
            GL.glRotatef(180-yaw, 0., 0., 1.)  # adjust to north
            GL.glColor3f(1., 1., 1.)

            with gl.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY):
                GL.glVertexPointer(2, GL.GL_FLOAT, 0, makeQuad(-size, -size, 2*size, 2*size))
                GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, makeQuad(0, 0, 256, 256))

                with gl.glEnable(GL.GL_BLEND, GL.GL_TEXTURE_2D):
                    GL.glDrawArrays(GL.GL_QUADS, 0, 4)



########NEW FILE########
__FILENAME__ = config
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""

"""
config.py
Configuration settings and storage.
"""
import os
import logging
import collections
import ConfigParser
from cStringIO import StringIO

import mcplatform

from albow import alert

log = logging.getLogger(__name__)


def configFilePath():
    return mcplatform.configFilePath


def loadConfig():

    class keyDict (collections.MutableMapping):
        def __init__(self, *args, **kwargs):
            self.dict = dict(*args, **kwargs)
            self.keyorder = []

        def keys(self):
            return list(self.keyorder)

        def items(self):
            return list(self.__iteritems__())

        def __iteritems__(self):
            return ((k, self.dict[k]) for k in self.keys())

        def __iter__(self):
            return self.keys().__iter__()

        def __getitem__(self, k):
            return self.dict[k]

        def __setitem__(self, k, v):
            self.dict[k] = v
            if not k in self.keyorder:
                self.keyorder.append(k)

        def __delitem__(self, k):
            del self.dict[k]
            if k in self.keyorder:
                self.keyorder.remove(k)

        def __contains__(self, k):
            return self.dict.__contains__(k)

        def __len__(self):
            return self.dict.__len__()

        def copy(self):
            k = keyDict()
            k.dict = self.dict.copy()
            k.keyorder = list(self.keyorder)
            return k

    config = ConfigParser.RawConfigParser([], keyDict)
    config.readfp(StringIO(configDefaults))
    try:
        config.read(configFilePath())

    except Exception, e:
        log.warn(u"Error while reading configuration file mcedit.ini: {0}".format(e))

    return config


def updateConfig():
    pass


def saveConfig():
    try:
        cf = file(configFilePath(), 'w')
        config.write(cf)
        cf.close()
    except Exception, e:
        try:
            alert(u"Error saving configuration settings to mcedit.ini: {0}".format(e))
        except:
            pass

configDefaults = """
[Keys]
forward = w
back = s
left = a
right = d
up = q
down = z
brake = space

rotate = e
roll = r
flip = f
mirror = g
swap = x

pan left = j
pan right = l
pan up = i
pan down = k

reset reach = mouse3
increase reach = mouse4
decrease reach = mouse5

confirm construction = return

open level = o
new level = n
delete blocks = delete

toggle fps counter = 0
toggle renderer = m

"""

log.info("Loading config...")
config = loadConfig()
config.observers = {}


def _propertyRef(section, name, dtype=str, default=None):
    class PropRef(object):
        def get(self):
            return _getProperty(section, name, dtype, default)

        def set(self, val):
            _setProperty(section, name, val)
    return PropRef()


def _configProperty(section, name, dtype=str, setter=None, default=None):
    assert default is not None

    def _getter(self):
        return _getProperty(section, name, dtype, default)

    def _setter(self, val):
        _setProperty(section, name, val)
        if setter:
            setter(self, val)

    return property(_getter, _setter, None)


def _getProperty(section, name, dtype=str, default=None):
    try:
        if dtype is bool:
            return config.getboolean(section, name)
        else:
            return dtype(config.get(section, name))
    except:
        if default is None:
            raise
        _setProperty(section, name, default)
        return default


def _setProperty(section, name, value):
    log.debug("Property Change: %15s %30s = %s", section, name, value)
    config.set(section, name, str(value))
    _notifyObservers(section, name, value)


def _notifyObservers(section, name, value):
    observers = config.observers.get((section.lower(), name.lower()), {})
    newObservers = {}
    for targetref, attr in observers:
        target = targetref()
        if target:
            log.debug("Notifying %s", target)
            setattr(target, attr, value)
            callback = observers[targetref, attr]
            if callback:
                callback(value)

            newObservers[targetref, attr] = callback

    config.observers[(section, name)] = newObservers

import weakref


def addObserver(section, name, target, attr=None, dtype=str, callback=None, default=None):
    """ Register 'target' for changes in the config var named by section and name.
    When the config is changed, calls setattr with target and attr.
    attr may be None; it will be created from the name by lowercasing the first
    word, uppercasing the rest, and removing spaces.
    e.g. "block buffer" becomes "blockBuffer"
    """
    observers = config.observers.setdefault((section.lower(), name.lower()), {})
    if not attr:
        tokens = name.lower().split()
        attr = tokens[0] + "".join(t.title() for t in tokens[1:])
    log.debug("Subscribing %s.%s", target, attr)

    attr = intern(attr)
    targetref = weakref.ref(target)
    observers.setdefault((targetref, attr), callback)

    val = _getProperty(section, name, dtype, default)

    setattr(target, attr, val)
    if callback:
        callback(val)


class Setting(object):
    def __init__(self, section, name, dtype, default):
        self.section = section
        self.name = name
        self.dtype = dtype
        self.default = default

    def __repr__(self):
        return "Setting(" + ", ".join(str(s) for s in (self.section, self.name, self.dtype, self.default))

    def addObserver(self, target, attr=None, callback=None):
        addObserver(self.section, self.name, target, attr, self.dtype, callback, self.default)

    def get(self):
        return _getProperty(self.section, self.name, self.dtype, self.default)

    def set(self, val):
        return _setProperty(self.section, self.name, self.dtype(val))

    def propertyRef(self):
        return _propertyRef(self.section, self.name, self.dtype, self.default)

    def configProperty(self, setter=None):
        return _configProperty(self.section, self.name, self.dtype, setter, self.default)

    def __int__(self):
        return int(self.get())

    def __float__(self):
        return float(self.get())

    def __bool__(self):
        return bool(self.get())


class Settings(object):
    Setting = Setting

    def __init__(self, section):
        self.section = section

    def __call__(self, name, default):
        assert default is not None

        dtype = type(default)
        section = self.section

        s = self.Setting(section, name, dtype, default)
        if not config.has_section(section):
            config.add_section(section)
        if not config.has_option(section, name):
            s.set(default)

        return s

    def __setattr__(self, attr, val):
        if hasattr(self, attr):
            old = getattr(self, attr)
            if isinstance(old, Setting):
                if isinstance(val, Setting):
                    raise ValueError("Attempting to reassign setting %s with %s" % (old, val))

                log.warn("Setting attr %s via __setattr__ instead of set()!", attr)
                return old.set(val)

        log.debug("Setting {%s => %s}" % (attr, val))
        return object.__setattr__(self, attr, val)

########NEW FILE########
__FILENAME__ = depths
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""


class DepthOffset(object):
    ChunkMarkers = 2
    Renderer = 1
    PreviewRenderer = 0
    TerrainWire = -1
    ClonePreview = -2
    Selection = -1
    SelectionCorners = -2
    PotentialSelection = -3
    SelectionReticle = -4
    FillMarkers = -3
    CloneMarkers = -3
    CloneReticle = -3

########NEW FILE########
__FILENAME__ = directories
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""


import sys
import os


def win32_utf8_argv():
    """Uses shell32.GetCommandLineArgvW to get sys.argv as a list of UTF-8
    strings.

    Versions 2.5 and older of Python don't support Unicode in sys.argv on
    Windows, with the underlying Windows API instead replacing multi-byte
    characters with '?'.

    Returns None on failure.

    Example usage:

    >>> def main(argv=None):
    ...    if argv is None:
    ...        argv = win32_utf8_argv() or sys.argv
    ...
    """

    try:
        from ctypes import POINTER, byref, cdll, c_int, windll
        from ctypes.wintypes import LPCWSTR, LPWSTR

        GetCommandLineW = cdll.kernel32.GetCommandLineW
        GetCommandLineW.argtypes = []
        GetCommandLineW.restype = LPCWSTR

        CommandLineToArgvW = windll.shell32.CommandLineToArgvW
        CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
        CommandLineToArgvW.restype = POINTER(LPWSTR)

        cmd = GetCommandLineW()
        argc = c_int(0)
        argv = CommandLineToArgvW(cmd, byref(argc))
        if argc.value > 0:
#            # Remove Python executable if present
#            if argc.value - len(sys.argv) == 1:
#                start = 1
#            else:
#                start = 0
            return [argv[i] for i in
                    xrange(0, argc.value)]
    except Exception:
        pass


def findDataDir():
    def fsdecode(x):
        return x.decode(sys.getfilesystemencoding())

    argzero = fsdecode(os.path.abspath(sys.argv[0]))

    if sys.platform == "win32":
        if hasattr(sys, 'frozen'):
            dataDir = os.path.dirname(fsdecode(sys.executable))
        else:
            dataDir = os.path.dirname(argzero)

    elif sys.platform == "darwin":
        dataDir = os.getcwdu()
    else:
        dataDir = os.getcwdu()

    return dataDir

dataDir = findDataDir()

########NEW FILE########
__FILENAME__ = drawable
"""
    ${NAME}
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import logging
log = logging.getLogger(__name__)

from OpenGL import GL

class Drawable(object):

    def __init__(self):
        super(Drawable, self).__init__()
        self._displayList = None
        self.invalidList = True
        self.children = []

    def setUp(self):
        """
        Set up rendering settings and view matrices
        :return:
        :rtype:
        """

    def tearDown(self):
        """
        Return any settings changed in setUp to their previous states
        :return:
        :rtype:
        """

    def drawSelf(self):
        """
        Draw this drawable, if it has its own graphics.
        :return:
        :rtype:
        """

    def _draw(self):
        self.setUp()
        self.drawSelf()
        for child in self.children:
            child.draw()
        self.tearDown()

    def draw(self):
        if self._displayList is None:
           self._displayList = GL.glGenLists(1)

        if self.invalidList:
            self.compileList()

        GL.glCallList(self._displayList)

    def compileList(self):
        GL.glNewList(self._displayList, GL.GL_COMPILE)
        self._draw()
        GL.glEndList()
        self.invalidList = False

    def invalidate(self):
        self.invalidList = True

########NEW FILE########
__FILENAME__ = blockpicker
from albow import Label, TextField, Row, TableView, TableColumn, Column, Widget, Button, AttrRef
from albow.dialogs import Dialog
from editortools import thumbview
from editortools import blockview
from glbackground import GLBackground
from mceutils import CheckBoxLabel
from pymclevel import materials

from pymclevel.materials import Block

def anySubtype(self):
    bl = Block(self.materials, self.ID, self.blockData)
    bl.wildcard = True
    return bl

Block.anySubtype = anySubtype
Block.wildcard = False  # True if


class BlockPicker(Dialog):
    is_gl_container = True

    def __init__(self, blockInfo, materials, *a, **kw):
        self.allowWildcards = False
        Dialog.__init__(self, *a, **kw)
        panelWidth = 350

        self.materials = materials
        self.anySubtype = blockInfo.wildcard

        self.matchingBlocks = materials.allBlocks

        try:
            self.selectedBlockIndex = self.matchingBlocks.index(blockInfo)
        except ValueError:
            self.selectedBlockIndex = 0
            for i, b in enumerate(self.matchingBlocks):
                if blockInfo.ID == b.ID and blockInfo.blockData == b.blockData:
                    self.selectedBlockIndex = i
                    break

        lbl = Label("Search")
        # lbl.rect.topleft = (0,0)

        fld = TextField(300)
        # fld.rect.topleft = (100, 10)
        # fld.centery = lbl.centery
        # fld.left = lbl.right

        fld.change_action = self.textEntered
        fld.enter_action = self.ok
        fld.escape_action = self.cancel

        self.awesomeField = fld

        searchRow = Row((lbl, fld))

        def formatBlockName(x):
            block = self.matchingBlocks[x]
            r = "({id}:{data}) {name}".format(name=block.name, id=block.ID, data=block.blockData)
            if block.aka:
                r += " [{0}]".format(block.aka)

            return r

        tableview = TableView(columns=[TableColumn(" ", 24, "l", lambda x: ""), TableColumn("(ID) Name [Aliases]", 276, "l", formatBlockName)])
        tableicons = [blockview.BlockView(materials) for i in range(tableview.rows.num_rows())]
        for t in tableicons:
            t.size = (16, 16)
            t.margin = 0
        icons = Column(tableicons, spacing=2)

        # tableview.margin = 5
        tableview.num_rows = lambda: len(self.matchingBlocks)
        tableview.row_data = lambda x: (self.matchingBlocks[x], x, x)
        tableview.row_is_selected = lambda x: x == self.selectedBlockIndex
        tableview.click_row = self.selectTableRow
        draw_table_cell = tableview.draw_table_cell

        def draw_block_table_cell(surf, i, data, cell_rect, column):
            if isinstance(data, Block):

                tableicons[i - tableview.rows.scroll].blockInfo = data
            else:
                draw_table_cell(surf, i, data, cell_rect, column)

        tableview.draw_table_cell = draw_block_table_cell
        tableview.width = panelWidth
        tableview.anchor = "lrbt"
        # self.add(tableview)
        self.tableview = tableview
        tableWidget = Widget()
        tableWidget.add(tableview)
        tableWidget.shrink_wrap()

        def wdraw(*args):
            for t in tableicons:
                t.blockInfo = materials.Air

        tableWidget.draw = wdraw
        self.blockButton = blockView = thumbview.BlockThumbView(materials, self.blockInfo)

        blockView.centerx = self.centerx
        blockView.top = tableview.bottom

        # self.add(blockview)

        but = Button("OK")
        but.action = self.ok
        but.top = blockView.bottom
        but.centerx = self.centerx
        but.align = "c"
        but.height = 30

        if self.allowWildcards:
        # self.add(but)
            anyRow = CheckBoxLabel("Any Subtype", ref=AttrRef(self, 'anySubtype'), tooltipText="Replace blocks with any data value. Only useful for Replace operations.")
            col = Column((searchRow, tableWidget, anyRow, blockView, but))
        else:
            col = Column((searchRow, tableWidget, blockView, but))
        col.anchor = "wh"
        self.anchor = "wh"

        panel = GLBackground()
        panel.bg_color = [i / 255. for i in self.bg_color]
        panel.anchor = "tlbr"
        self.add(panel)

        self.add(col)
        self.add(icons)
        icons.topleft = tableWidget.topleft
        icons.top += tableWidget.margin + 30
        icons.left += tableWidget.margin + 4

        self.shrink_wrap()
        panel.size = self.size

        try:
            self.tableview.rows.scroll_to_item(self.selectedBlockIndex)
        except:
            pass

    @property
    def blockInfo(self):
        if len(self.matchingBlocks):
            bl = self.matchingBlocks[self.selectedBlockIndex]
            if self.anySubtype:
                return bl.anySubtype()
            else:
                return bl

        else:
            return self.materials.Air

    def selectTableRow(self, i, e):
        oldIndex = self.selectedBlockIndex

        self.selectedBlockIndex = i
        self.blockButton.blockInfo = self.blockInfo
        if e.num_clicks > 1 and oldIndex == i:
            self.ok()

    def textEntered(self):
        text = self.awesomeField.text
        blockData = 0
        try:
            if ":" in text:
                text, num = text.split(":", 1)
                blockData = int(num) & 0xf
                blockID = int(text) % materials.id_limit
            else:
                blockID = int(text) % materials.id_limit

            block = self.materials.blockWithID(blockID, blockData)

            self.matchingBlocks = [block]
            self.selectedBlockIndex = 0
            self.tableview.rows.scroll_to_item(self.selectedBlockIndex)
            self.blockButton.blockInfo = self.blockInfo

            return
        except ValueError:
            pass
        except Exception, e:
            print repr(e)

        blocks = self.materials.allBlocks

        matches = blocks
        oldBlock = self.materials.Air
        if len(self.matchingBlocks):
            oldBlock = self.matchingBlocks[self.selectedBlockIndex]

        if len(text):
            matches = self.materials.blocksMatching(text)
            if blockData:
                ids = set(b.ID for b in matches)
                matches = sorted([self.materials.blockWithID(id, blockData) for id in ids])

            self.matchingBlocks = matches
        else:
            self.matchingBlocks = blocks

        if oldBlock in self.matchingBlocks:
            self.selectedBlockIndex = self.matchingBlocks.index(oldBlock)
        else:
            self.selectedBlockIndex = 0

        self.tableview.rows.scroll_to_item(self.selectedBlockIndex)
        self.blockButton.blockInfo = self.blockInfo

########NEW FILE########
__FILENAME__ = blockview
from OpenGL import GL

from numpy import array
from albow import ButtonBase, ValueDisplay, AttrRef, Row
from albow.openglwidgets import GLOrtho
import thumbview
import blockpicker
from glbackground import Panel, GLBackground
from glutils import DisplayList

class BlockView(GLOrtho):
    def __init__(self, materials, blockInfo=None):
        GLOrtho.__init__(self)
        self.list = DisplayList(self._gl_draw)
        self.blockInfo = blockInfo or materials.Air
        self.materials = materials

    listBlockInfo = None

    def gl_draw(self):
        if self.listBlockInfo != self.blockInfo:
            self.list.invalidate()
            self.listBlockInfo = self.blockInfo

        self.list.call()

    def _gl_draw(self):
        blockInfo = self.blockInfo
        if blockInfo.ID is 0:
            return

        GL.glColor(1.0, 1.0, 1.0, 1.0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_ALPHA_TEST)
        self.materials.terrainTexture.bind()
        pixelScale = 0.5 if self.materials.name in ("Pocket", "Alpha") else 1.0
        texSize = 16 * pixelScale

        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glVertexPointer(2, GL.GL_FLOAT, 0, array([-1, -1,
                                 - 1, 1,
                                 1, 1,
                                 1, -1, ], dtype='float32'))
        texOrigin = array(self.materials.blockTextures[blockInfo.ID, blockInfo.blockData, 0])
        texOrigin *= pixelScale

        GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, array([texOrigin[0], texOrigin[1] + texSize,
                                  texOrigin[0], texOrigin[1],
                                  texOrigin[0] + texSize, texOrigin[1],
                                  texOrigin[0] + texSize, texOrigin[1] + texSize], dtype='float32'))

        GL.glDrawArrays(GL.GL_QUADS, 0, 4)

        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisable(GL.GL_ALPHA_TEST)
        GL.glDisable(GL.GL_TEXTURE_2D)

    @property
    def tooltipText(self):
        return "{0}".format(self.blockInfo.name)


class BlockButton(ButtonBase, Panel):
    _ref = None

    def __init__(self, materials, blockInfo=None, ref=None, recentBlocks=None, *a, **kw):
        self.allowWildcards = False
        Panel.__init__(self, *a, **kw)

        self.bg_color = (1, 1, 1, 0.25)
        self._ref = ref
        if blockInfo is None and ref is not None:
            blockInfo = ref.get()
        blockInfo = blockInfo or materials.Air

        if recentBlocks is not None:
            self.recentBlocks = recentBlocks
        else:
            self.recentBlocks = []

        self.blockView = thumbview.BlockThumbView(materials, blockInfo, size=(48, 48))
        self.blockLabel = ValueDisplay(ref=AttrRef(self, 'labelText'), width=180, align="l")
        row = Row((self.blockView, self.blockLabel), align="b")

        # col = Column( (self.blockButton, self.blockNameLabel) )
        self.add(row)
        self.shrink_wrap()

        # self.blockLabel.bottom = self.blockButton.bottom
        # self.blockLabel.centerx = self.blockButton.centerx

        # self.add(self.blockLabel)

        self.materials = materials
        self.blockInfo = blockInfo
        # self._ref = ref
        self.updateRecentBlockView()

    recentBlockLimit = 7

    @property
    def blockInfo(self):
        if self._ref:
            return self._ref.get()
        else:
            return self._blockInfo

    @blockInfo.setter
    def blockInfo(self, bi):
        if self._ref:
            self._ref.set(bi)
        else:
            self._blockInfo = bi
        self.blockView.blockInfo = bi
        if bi not in self.recentBlocks:
            self.recentBlocks.append(bi)
            if len(self.recentBlocks) > self.recentBlockLimit:
                self.recentBlocks.pop(0)
            self.updateRecentBlockView()

    @property
    def labelText(self):
        labelText = self.blockInfo.name
        if len(labelText) > 24:
            labelText = labelText[:23] + "..."
        return labelText

        # self.blockNameLabel.text =

    def createRecentBlockView(self):
        def makeBlockView(bi):
            bv = BlockView(self.materials, bi)
            bv.size = (16, 16)

            def action(evt):
                self.blockInfo = bi
            bv.mouse_up = action
            return bv

        row = [makeBlockView(bi) for bi in self.recentBlocks]
        row = Row(row)

        widget = GLBackground()
        widget.bg_color = (0.8, 0.8, 0.8, 0.8)
        widget.add(row)
        widget.shrink_wrap()
        widget.anchor = "whtr"
        return widget

    def updateRecentBlockView(self):
        if self.recentBlockView:
            self.recentBlockView.set_parent(None)
        self.recentBlockView = self.createRecentBlockView()

        self.recentBlockView.right = self.width
        self.add(self.recentBlockView)
        #print self.rect, self.recentBlockView.rect

    recentBlockView = None

    @property
    def tooltipText(self):
        return "{0}".format(self.blockInfo.name)

    def action(self):
        blockPicker = blockpicker.BlockPicker(self.blockInfo, self.materials, allowWildcards=self.allowWildcards)
        if blockPicker.present():
            self.blockInfo = blockPicker.blockInfo

########NEW FILE########
__FILENAME__ = brush
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""
import collections
from datetime import datetime
import numpy
from numpy import newaxis
import pygame
from albow import AttrRef, Button, ValueDisplay, Row, Label, ValueButton, Column, IntField, CheckBox, FloatField, alert
import bresenham
from editortools.blockpicker import BlockPicker
from editortools.blockview import BlockButton
from editortools.editortool import EditorTool
from editortools.tooloptions import ToolOptions
from glbackground import Panel
from glutils import gl
import mcplatform
from pymclevel import block_fill, BoundingBox
import pymclevel
from pymclevel.level import extractHeights
from mceutils import ChoiceButton, CheckBoxLabel, showProgress, IntInputRow, alertException, drawTerrainCuttingWire
from os.path import basename
import tempfile
import itertools
import logging
from operation import Operation, mkundotemp
from pymclevel.mclevelbase import exhaust

from OpenGL import GL

log = logging.getLogger(__name__)

import config

BrushSettings = config.Settings("Brush")
BrushSettings.brushSizeL = BrushSettings("Brush Shape L", 3)
BrushSettings.brushSizeH = BrushSettings("Brush Shape H", 3)
BrushSettings.brushSizeW = BrushSettings("Brush Shape W", 3)
BrushSettings.updateBrushOffset = BrushSettings("Update Brush Offset", False)
BrushSettings.chooseBlockImmediately = BrushSettings("Choose Block Immediately", False)
BrushSettings.alpha = BrushSettings("Alpha", 0.66)

class BrushMode(object):
    options = []

    def brushBoxForPointAndOptions(self, point, options={}):
        # Return a box of size options['brushSize'] centered around point.
        # also used to position the preview reticle
        size = options['brushSize']
        origin = map(lambda x, s: x - (s >> 1), point, size)
        return BoundingBox(origin, size)

    def apply(self, op, point):
        """
        Called by BrushOperation for brush modes that can't be implemented using applyToChunk
        """
        pass
    apply = NotImplemented

    def applyToChunk(self, op, chunk, point):
        """
        Called by BrushOperation to apply this brush mode to the given chunk with a brush centered on point.
        Default implementation will compute:
          brushBox: a BoundingBox for the world area affected by this brush,
          brushBoxThisChunk: a box for the portion of this chunk affected by this brush,
          slices: a tuple of slices that can index the chunk's Blocks array to select the affected area.

        These three parameters are passed to applyToChunkSlices along with the chunk and the brush operation.
        Brush modes must implement either applyToChunk or applyToChunkSlices
        """
        brushBox = self.brushBoxForPointAndOptions(point, op.options)

        brushBoxThisChunk, slices = chunk.getChunkSlicesForBox(brushBox)
        if brushBoxThisChunk.volume == 0: return

        return self.applyToChunkSlices(op, chunk, slices, brushBox, brushBoxThisChunk)

    def applyToChunkSlices(self, op, chunk, slices, brushBox, brushBoxThisChunk):
        raise NotImplementedError

    def createOptions(self, panel, tool):
        pass


class Modes:
    class Fill(BrushMode):
        name = "Fill"

        def createOptions(self, panel, tool):
            col = [
                panel.modeStyleGrid,
                panel.hollowRow,
                panel.noiseInput,
                panel.brushSizeRows,
                panel.blockButton,
            ]
            return col

        def applyToChunkSlices(self, op, chunk, slices, brushBox, brushBoxThisChunk):
            brushMask = createBrushMask(op.brushSize, op.brushStyle, brushBox.origin, brushBoxThisChunk, op.noise, op.hollow)

            chunk.Blocks[slices][brushMask] = op.blockInfo.ID
            chunk.Data[slices][brushMask] = op.blockInfo.blockData

    class FloodFill(BrushMode):
        name = "Flood Fill"
        options = ['indiscriminate']

        def createOptions(self, panel, tool):
            col = [
                panel.brushModeRow,
                panel.blockButton
            ]
            indiscriminateButton = CheckBoxLabel("Indiscriminate", ref=AttrRef(tool, 'indiscriminate'))

            col.append(indiscriminateButton)
            return col

        def apply(self, op, point):

            undoLevel = pymclevel.MCInfdevOldLevel(mkundotemp(), create=True)
            dirtyChunks = set()

            def saveUndoChunk(cx, cz):
                if (cx, cz) in dirtyChunks:
                    return
                dirtyChunks.add((cx, cz))
                undoLevel.copyChunkFrom(op.level, cx, cz)

            doomedBlock = op.level.blockAt(*point)
            doomedBlockData = op.level.blockDataAt(*point)
            checkData = (doomedBlock not in (8, 9, 10, 11))
            indiscriminate = op.options['indiscriminate']

            if doomedBlock == op.blockInfo.ID:
                return
            if indiscriminate:
                checkData = False
                if doomedBlock == 2:  # grass
                    doomedBlock = 3  # dirt

            x, y, z = point
            saveUndoChunk(x // 16, z // 16)
            op.level.setBlockAt(x, y, z, op.blockInfo.ID)
            op.level.setBlockDataAt(x, y, z, op.blockInfo.blockData)

            def processCoords(coords):
                newcoords = collections.deque()

                for (x, y, z) in coords:
                    for _dir, offsets in pymclevel.faceDirections:
                        dx, dy, dz = offsets
                        p = (x + dx, y + dy, z + dz)

                        nx, ny, nz = p
                        b = op.level.blockAt(nx, ny, nz)
                        if indiscriminate:
                            if b == 2:
                                b = 3
                        if b == doomedBlock:
                            if checkData:
                                if op.level.blockDataAt(nx, ny, nz) != doomedBlockData:
                                    continue

                            saveUndoChunk(nx // 16, nz // 16)
                            op.level.setBlockAt(nx, ny, nz, op.blockInfo.ID)
                            op.level.setBlockDataAt(nx, ny, nz, op.blockInfo.blockData)
                            newcoords.append(p)

                return newcoords

            def spread(coords):
                while len(coords):
                    start = datetime.now()

                    num = len(coords)
                    coords = processCoords(coords)
                    d = datetime.now() - start
                    progress = "Did {0} coords in {1}".format(num, d)
                    log.info(progress)
                    yield progress

            showProgress("Flood fill...", spread([point]), cancel=True)
            op.editor.invalidateChunks(dirtyChunks)
            op.undoLevel = undoLevel

    class Replace(Fill):
        name = "Replace"

        def createOptions(self, panel, tool):
            return Modes.Fill.createOptions(self, panel, tool) + [panel.replaceBlockButton]

        def applyToChunkSlices(self, op, chunk, slices, brushBox, brushBoxThisChunk):

            blocks = chunk.Blocks[slices]
            data = chunk.Data[slices]

            brushMask = createBrushMask(op.brushSize, op.brushStyle, brushBox.origin, brushBoxThisChunk, op.noise, op.hollow)

            replaceWith = op.options['replaceBlockInfo']
            # xxx pasted from fill.py
            if op.blockInfo.wildcard:
                print "Wildcard replace"
                blocksToReplace = []
                for i in range(16):
                    blocksToReplace.append(op.editor.level.materials.blockWithID(op.blockInfo.ID, i))
            else:
                blocksToReplace = [op.blockInfo]

            replaceTable = block_fill.blockReplaceTable(blocksToReplace)
            replaceMask = replaceTable[blocks, data]
            brushMask &= replaceMask

            blocks[brushMask] = replaceWith.ID
            data[brushMask] = replaceWith.blockData

    class Erode(BrushMode):
        name = "Erode"
        options = ['erosionStrength']

        def createOptions(self, panel, tool):
            col = [
                panel.modeStyleGrid,
                panel.brushSizeRows,
            ]
            col.append(IntInputRow("Strength: ", ref=AttrRef(tool, 'erosionStrength'), min=1, max=20, tooltipText="Number of times to apply erosion. Larger numbers are slower."))
            return col

        def apply(self, op, point):
            brushBox = self.brushBoxForPointAndOptions(point, op.options).expand(1)

            if brushBox.volume > 1048576:
                raise ValueError("Affected area is too big for this brush mode")

            strength = op.options["erosionStrength"]

            erosionArea = op.level.extractSchematic(brushBox, entities=False)
            if erosionArea is None:
                return

            blocks = erosionArea.Blocks
            bins = numpy.bincount(blocks.ravel())
            fillBlockID = bins.argmax()

            def getNeighbors(solidBlocks):
                neighbors = numpy.zeros(solidBlocks.shape, dtype='uint8')
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[:-2, 1:-1, 1:-1]
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[2:, 1:-1, 1:-1]
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[1:-1, :-2, 1:-1]
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[1:-1, 2:, 1:-1]
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[1:-1, 1:-1, :-2]
                neighbors[1:-1, 1:-1, 1:-1] += solidBlocks[1:-1, 1:-1, 2:]
                return neighbors

            for i in range(strength):
                solidBlocks = blocks != 0
                neighbors = getNeighbors(solidBlocks)

                brushMask = createBrushMask(op.brushSize, op.brushStyle)
                erodeBlocks = neighbors < 5
                erodeBlocks &= (numpy.random.random(erodeBlocks.shape) > 0.3)
                erodeBlocks[1:-1, 1:-1, 1:-1] &= brushMask
                blocks[erodeBlocks] = 0

                solidBlocks = blocks != 0
                neighbors = getNeighbors(solidBlocks)

                fillBlocks = neighbors > 2
                fillBlocks &= ~solidBlocks
                fillBlocks[1:-1, 1:-1, 1:-1] &= brushMask
                blocks[fillBlocks] = fillBlockID

            op.level.copyBlocksFrom(erosionArea, erosionArea.bounds.expand(-1), brushBox.origin + (1, 1, 1))

    class Topsoil(BrushMode):
        name = "Topsoil"
        options = ['naturalEarth', 'topsoilDepth']

        def createOptions(self, panel, tool):
            depthRow = IntInputRow("Depth: ", ref=AttrRef(tool, 'topsoilDepth'))
            naturalRow = CheckBoxLabel("Only Change Natural Earth", ref=AttrRef(tool, 'naturalEarth'))
            col = [
                panel.modeStyleGrid,
                panel.hollowRow,
                panel.noiseInput,
                panel.brushSizeRows,
                panel.blockButton,
                depthRow,
                naturalRow
            ]
            return col

        def applyToChunkSlices(self, op, chunk, slices, brushBox, brushBoxThisChunk):

            depth = op.options['topsoilDepth']
            blocktype = op.blockInfo

            blocks = chunk.Blocks[slices]
            data = chunk.Data[slices]

            brushMask = createBrushMask(op.brushSize, op.brushStyle, brushBox.origin, brushBoxThisChunk, op.noise, op.hollow)


            if op.options['naturalEarth']:
                try:
                    # try to get the block mask from the topsoil filter
                    import topsoil  # @UnresolvedImport
                    blockmask = topsoil.naturalBlockmask()
                    blockmask[blocktype.ID] = True
                    blocktypeMask = blockmask[blocks]

                except Exception, e:
                    print repr(e), " while using blockmask from filters.topsoil"
                    blocktypeMask = blocks != 0

            else:
                # topsoil any block
                blocktypeMask = blocks != 0

            if depth < 0:
                blocktypeMask &= (blocks != blocktype.ID)

            heightmap = extractHeights(blocktypeMask)

            for x, z in itertools.product(*map(xrange, heightmap.shape)):
                h = heightmap[x, z]
                if h >= brushBoxThisChunk.height:
                    continue
                if depth > 0:
                    idx = x, z, slice(max(0, h - depth), h)
                else:
                    # negative depth values mean to put a layer above the surface
                    idx = x, z, slice(h, min(blocks.shape[2], h - depth))
                mask = brushMask[idx]
                blocks[idx][mask] = blocktype.ID
                data[idx][mask] = blocktype.blockData

    class Paste(BrushMode):

        name = "Paste"
        options = ['level'] + ['center' + c for c in 'xyz']

        def brushBoxForPointAndOptions(self, point, options={}):
            point = [p + options.get('center' + c, 0) for p, c in zip(point, 'xyz')]
            return BoundingBox(point, options['level'].size)

        def createOptions(self, panel, tool):
            col = [panel.brushModeRow]

            importButton = Button("Import", action=tool.importPaste)
            importLabel = ValueDisplay(width=150, ref=AttrRef(tool, "importFilename"))
            importRow = Row((importButton, importLabel))

            stack = tool.editor.copyStack
            if len(stack) == 0:
                tool.importPaste()
            else:
                tool.loadLevel(stack[0])
            tool.centery = 0
            tool.centerx = -(tool.level.Width / 2)
            tool.centerz = -(tool.level.Length / 2)

            cx, cy, cz = [IntInputRow(c, ref=AttrRef(tool, "center" + c), max=a, min=-a)
                          for a, c in zip(tool.level.size, "xyz")]
            centerRow = Row((cx, cy, cz))

            col.extend([importRow, centerRow])

            return col

        def apply(self, op, point):
            level = op.options['level']
            point = [p + op.options['center' + c] for p, c in zip(point, 'xyz')]

            return op.level.copyBlocksFromIter(level, level.bounds, point, create=True)


class BrushOperation(Operation):

    def __init__(self, editor, level, points, options):
        super(BrushOperation, self).__init__(editor, level)

        # if options is None: options = {}

        self.options = options
        self.editor = editor
        if isinstance(points[0], (int, float)):
            points = [points]

        self.points = points

        self.brushSize = options['brushSize']
        self.blockInfo = options['blockInfo']
        self.brushStyle = options['brushStyle']
        self.brushMode = options['brushMode']

        if max(self.brushSize) > BrushTool.maxBrushSize:
            self.brushSize = (BrushTool.maxBrushSize,) * 3
        if max(self.brushSize) < 1:
            self.brushSize = (1, 1, 1)

        boxes = [self.brushMode.brushBoxForPointAndOptions(p, options) for p in points]
        self._dirtyBox = reduce(lambda a, b: a.union(b), boxes)

    brushStyles = ["Round", "Square", "Diamond"]
    # brushModeNames = ["Fill", "Flood Fill", "Replace", "Erode", "Topsoil", "Paste"]  # "Smooth", "Flatten", "Raise", "Lower", "Build", "Erode", "Evert"]
    brushModeClasses = [
        Modes.Fill,
        Modes.FloodFill,
        Modes.Replace,
        Modes.Erode,
        Modes.Topsoil,
        Modes.Paste
    ]

    @property
    def noise(self):
        return self.options.get('brushNoise', 100)

    @property
    def hollow(self):
        return self.options.get('brushHollow', False)



    def dirtyBox(self):
        return self._dirtyBox

    def perform(self, recordUndo=True):
        if recordUndo:
            self.undoLevel = self.extractUndo(self.level, self._dirtyBox)

        def _perform():
            yield 0, len(self.points), "Applying {0} brush...".format(self.brushMode.name)
            if self.brushMode.apply is not NotImplemented: #xxx double negative
                for i, point in enumerate(self.points):
                    f = self.brushMode.apply(self, point)
                    if hasattr(f, "__iter__"):
                        for progress in f:
                            yield progress
                    else:
                        yield i, len(self.points), "Applying {0} brush...".format(self.brushMode.name)
            else:

                for j, cPos in enumerate(self._dirtyBox.chunkPositions):
                    if not self.level.containsChunk(*cPos):
                        continue
                    chunk = self.level.getChunk(*cPos)
                    for i, point in enumerate(self.points):

                        f = self.brushMode.applyToChunk(self, chunk, point)

                        if hasattr(f, "__iter__"):
                            for progress in f:
                                yield progress
                        else:
                            yield j * len(self.points) + i, len(self.points) * self._dirtyBox.chunkCount, "Applying {0} brush...".format(self.brushMode.name)

                    chunk.chunkChanged()

        if len(self.points) > 10:
            showProgress("Performing brush...", _perform(), cancel=True)
        else:
            exhaust(_perform())



class BrushPanel(Panel):
    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool

        self.brushModeButton = ChoiceButton([m.name for m in tool.brushModes],
                                            width=150,
                                            choose=self.brushModeChanged)

        self.brushModeButton.selectedChoice = tool.brushMode.name
        self.brushModeRow = Row((Label("Mode:"), self.brushModeButton))

        self.brushStyleButton = ValueButton(width=self.brushModeButton.width,
                                        ref=AttrRef(tool, "brushStyle"),
                                        action=tool.swapBrushStyles)

        self.brushStyleButton.tooltipText = "Shortcut: ALT-1"

        self.brushStyleRow = Row((Label("Brush:"), self.brushStyleButton))

        self.modeStyleGrid = Column([
            self.brushModeRow,
            self.brushStyleRow,
        ])

        shapeRows = []

        for d in ["L", "W", "H"]:
            l = Label(d)
            f = IntField(ref=getattr(BrushSettings, "brushSize" + d).propertyRef(), min=1, max=tool.maxBrushSize)
            row = Row((l, f))
            shapeRows.append(row)

        self.brushSizeRows = Column(shapeRows)

        self.noiseInput = IntInputRow("Chance: ", ref=AttrRef(tool, "brushNoise"), min=0, max=100)

        hollowCheckBox = CheckBox(ref=AttrRef(tool, "brushHollow"))
        hollowLabel = Label("Hollow")
        hollowLabel.mouse_down = hollowCheckBox.mouse_down
        hollowLabel.tooltipText = hollowCheckBox.tooltipText = "Shortcut: ALT-3"

        self.hollowRow = Row((hollowCheckBox, hollowLabel))

        self.blockButton = blockButton = BlockButton(
            tool.editor.level.materials,
            ref=AttrRef(tool, 'blockInfo'),
            recentBlocks=tool.recentFillBlocks,
            allowWildcards=(tool.brushMode.name == "Replace"))

        # col = [modeStyleGrid, hollowRow, noiseInput, shapeRows, blockButton]

        self.replaceBlockButton = replaceBlockButton = BlockButton(
            tool.editor.level.materials,
            ref=AttrRef(tool, 'replaceBlockInfo'),
            recentBlocks=tool.recentReplaceBlocks)

        col = tool.brushMode.createOptions(self, tool)

        if self.tool.brushMode.name != "Flood Fill":
            spaceRow = IntInputRow("Line Spacing", ref=AttrRef(tool, "minimumSpacing"), min=1, tooltipText="Hold SHIFT to draw lines")
            col.append(spaceRow)
        col = Column(col)

        self.add(col)
        self.shrink_wrap()

    def brushModeChanged(self):
        self.tool.brushMode = self.brushModeButton.selectedChoice

    def pickFillBlock(self):
        self.blockButton.action()
        self.tool.blockInfo = self.blockButton.blockInfo
        self.tool.setupPreview()

    def pickReplaceBlock(self):
        self.replaceBlockButton.action()
        self.tool.replaceBlockInfo = self.replaceBlockButton.blockInfo
        self.tool.setupPreview()

    def swap(self):
        t = self.blockButton.recentBlocks
        self.blockButton.recentBlocks = self.replaceBlockButton.recentBlocks
        self.replaceBlockButton.recentBlocks = t

        self.blockButton.updateRecentBlockView()
        self.replaceBlockButton.updateRecentBlockView()
        b = self.blockButton.blockInfo
        self.blockButton.blockInfo = self.replaceBlockButton.blockInfo
        self.replaceBlockButton.blockInfo = b


class BrushToolOptions(ToolOptions):
    def __init__(self, tool):
        Panel.__init__(self)
        alphaField = FloatField(ref=AttrRef(tool, 'brushAlpha'), min=0.0, max=1.0, width=60)
        alphaField.increment = 0.1
        alphaRow = Row((Label("Alpha: "), alphaField))
        autoChooseCheckBox = CheckBoxLabel("Choose Block Immediately",
                                            ref=AttrRef(tool, "chooseBlockImmediately"),
                                            tooltipText="When the brush tool is chosen, prompt for a block type.")

        updateOffsetCheckBox = CheckBoxLabel("Reset Distance When Brush Size Changes",
                                            ref=AttrRef(tool, "updateBrushOffset"),
                                            tooltipText="Whenever the brush size changes, reset the distance to the brush blocks.")

        col = Column((Label("Brush Options"), alphaRow, autoChooseCheckBox, updateOffsetCheckBox, Button("OK", action=self.dismiss)))
        self.add(col)
        self.shrink_wrap()
        return

from clone import CloneTool


class BrushTool(CloneTool):
    tooltipText = "Brush\nRight-click for options"
    toolIconName = "brush"
    minimumSpacing = 1

    def __init__(self, *args):
        CloneTool.__init__(self, *args)
        self.optionsPanel = BrushToolOptions(self)
        self.recentFillBlocks = []
        self.recentReplaceBlocks = []
        self.draggedPositions = []

        self.brushModes = [c() for c in BrushOperation.brushModeClasses]
        for m in self.brushModes:
            self.options.extend(m.options)

        self._brushMode = self.brushModes[0]
        BrushSettings.updateBrushOffset.addObserver(self)
        BrushSettings.brushSizeW.addObserver(self, 'brushSizeW', callback=self._setBrushSize)
        BrushSettings.brushSizeH.addObserver(self, 'brushSizeH', callback=self._setBrushSize)
        BrushSettings.brushSizeL.addObserver(self, 'brushSizeL', callback=self._setBrushSize)

    panel = None

    def _setBrushSize(self, _):
        if self.updateBrushOffset:
            self.reticleOffset = self.offsetMax()
            self.resetToolDistance()
        self.previewDirty = True

    previewDirty = False
    updateBrushOffset = True

    _reticleOffset = 1
    naturalEarth = True
    erosionStrength = 1
    indiscriminate = False

    @property
    def reticleOffset(self):
        if self.brushMode.name == "Flood Fill":
            return 0
        return self._reticleOffset

    @reticleOffset.setter
    def reticleOffset(self, val):
        self._reticleOffset = val

    brushSizeW, brushSizeH, brushSizeL = 1, 1, 1

    @property
    def brushSize(self):
        if self.brushMode.name == "Flood Fill":
            return 1, 1, 1
        return [self.brushSizeW, self.brushSizeH, self.brushSizeL]

    @brushSize.setter
    def brushSize(self, val):
        (w, h, l) = [max(1, min(i, self.maxBrushSize)) for i in val]
        BrushSettings.brushSizeH.set(h)
        BrushSettings.brushSizeL.set(l)
        BrushSettings.brushSizeW.set(w)

    maxBrushSize = 4096

    brushStyles = BrushOperation.brushStyles
    brushStyle = brushStyles[0]
    brushModes = None

    @property
    def brushMode(self):
        return self._brushMode

    @brushMode.setter
    def brushMode(self, val):
        if isinstance(val, str):
            val = [b for b in self.brushModes if b.name == val][0]

        self._brushMode = val

        self.hidePanel()
        self.showPanel()

    brushNoise = 100
    brushHollow = False
    topsoilDepth = 1

    chooseBlockImmediately = BrushSettings.chooseBlockImmediately.configProperty()

    _blockInfo = pymclevel.alphaMaterials.Stone

    @property
    def blockInfo(self):
        return self._blockInfo

    @blockInfo.setter
    def blockInfo(self, bi):
        self._blockInfo = bi
        self.setupPreview()

    _replaceBlockInfo = pymclevel.alphaMaterials.Stone

    @property
    def replaceBlockInfo(self):
        return self._replaceBlockInfo

    @replaceBlockInfo.setter
    def replaceBlockInfo(self, bi):
        self._replaceBlockInfo = bi
        self.setupPreview()

    @property
    def brushAlpha(self):
        return BrushSettings.alpha.get()

    @brushAlpha.setter
    def brushAlpha(self, f):
        f = min(1.0, max(0.0, f))
        BrushSettings.alpha.set(f)
        self.setupPreview()

    def importPaste(self):
        clipFilename = mcplatform.askOpenFile(title='Choose a schematic or level...', schematics=True)
        # xxx mouthful
        if clipFilename:
            try:
                self.loadLevel(pymclevel.fromFile(clipFilename, readonly=True))
            except Exception, e:
                alert("Failed to load file %s" % clipFilename)
                self.brushMode = "Fill"
                return

    def loadLevel(self, level):
        self.level = level
        self.minimumSpacing = min([s / 4 for s in level.size])
        self.centerx, self.centery, self.centerz = -level.Width / 2, 0, -level.Length / 2
        CloneTool.setupPreview(self)

    @property
    def importFilename(self):
        if self.level:
            return basename(self.level.filename or "No name")
        return "Nothing selected"

    @property
    def statusText(self):
        return "Click and drag to place blocks. ALT-Click to use the block under the cursor. {R} to increase and {F} to decrease size. {E} to rotate, {G} to roll. Mousewheel to adjust distance.".format(
            R=config.config.get("Keys", "Roll").upper(),
            F=config.config.get("Keys", "Flip").upper(),
            E=config.config.get("Keys", "Rotate").upper(),
            G=config.config.get("Keys", "Mirror").upper(),
            )

    @property
    def worldTooltipText(self):
        if pygame.key.get_mods() & pygame.KMOD_ALT:
            try:
                if self.editor.blockFaceUnderCursor is None:
                    return
                pos = self.editor.blockFaceUnderCursor[0]
                blockID = self.editor.level.blockAt(*pos)
                blockdata = self.editor.level.blockDataAt(*pos)
                return "Click to use {0} ({1}:{2})".format(self.editor.level.materials.names[blockID][blockdata], blockID, blockdata)

            except Exception, e:
                return repr(e)

        if self.brushMode.name == "Flood Fill":
            try:
                if self.editor.blockFaceUnderCursor is None:
                    return
                pos = self.editor.blockFaceUnderCursor[0]
                blockID = self.editor.level.blockAt(*pos)
                blockdata = self.editor.level.blockDataAt(*pos)
                return "Click to replace {0} ({1}:{2})".format(self.editor.level.materials.names[blockID][blockdata], blockID, blockdata)

            except Exception, e:
                return repr(e)

    def swapBrushStyles(self):
        brushStyleIndex = self.brushStyles.index(self.brushStyle) + 1
        brushStyleIndex %= len(self.brushStyles)
        self.brushStyle = self.brushStyles[brushStyleIndex]
        self.setupPreview()

    def swapBrushModes(self):
        brushModeIndex = self.brushModes.index(self.brushMode) + 1
        brushModeIndex %= len(self.brushModes)
        self.brushMode = self.brushModes[brushModeIndex]

    options = [
        'blockInfo',
        'brushStyle',
        'brushMode',
        'brushSize',
        'brushNoise',
        'brushHollow',
        'replaceBlockInfo',
    ]

    def getBrushOptions(self):
        return dict(((key, getattr(self, key))
                       for key
                       in self.options))

    draggedDirection = (0, 0, 0)
    centerx = centery = centerz = 0

    @alertException
    def mouseDown(self, evt, pos, direction):
        if pygame.key.get_mods() & pygame.KMOD_ALT:
            id = self.editor.level.blockAt(*pos)
            data = self.editor.level.blockDataAt(*pos)
            if self.brushMode.name == "Replace":
                self.panel.replaceBlockButton.blockInfo = self.editor.level.materials.blockWithID(id, data)
            else:
                self.panel.blockButton.blockInfo = self.editor.level.materials.blockWithID(id, data)

            return

        self.draggedDirection = direction
        point = [p + d * self.reticleOffset for p, d in zip(pos, direction)]
        self.dragLineToPoint(point)

    @alertException
    def mouseDrag(self, evt, pos, _dir):
        direction = self.draggedDirection
        if self.brushMode.name != "Flood Fill":
            if len(self.draggedPositions):  # if self.isDragging
                self.lastPosition = lastPoint = self.draggedPositions[-1]
                point = [p + d * self.reticleOffset for p, d in zip(pos, direction)]
                if any([abs(a - b) >= self.minimumSpacing
                        for a, b in zip(point, lastPoint)]):
                    self.dragLineToPoint(point)

    def dragLineToPoint(self, point):
        if self.brushMode.name == "Flood Fill":
            self.draggedPositions = [point]
            return

        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
            if len(self.draggedPositions):
                points = bresenham.bresenham(self.draggedPositions[-1], point)
                self.draggedPositions.extend(points[::self.minimumSpacing][1:])
            elif self.lastPosition is not None:
                points = bresenham.bresenham(self.lastPosition, point)
                self.draggedPositions.extend(points[::self.minimumSpacing][1:])
        else:
            self.draggedPositions.append(point)

    @alertException
    def mouseUp(self, evt, pos, direction):
        if 0 == len(self.draggedPositions):
            return

        size = self.brushSize
        # point = self.getReticlePoint(pos, direction)
        if self.brushMode.name == "Flood Fill":
            self.draggedPositions = self.draggedPositions[-1:]

        op = BrushOperation(self.editor,
                            self.editor.level,
                            self.draggedPositions,
                            self.getBrushOptions())

        box = op.dirtyBox()
        self.editor.addOperation(op)
        self.editor.addUnsavedEdit()

        self.editor.invalidateBox(box)
        self.lastPosition = self.draggedPositions[-1]

        self.draggedPositions = []

    def toolEnabled(self):
        return True

    def rotate(self):
        offs = self.reticleOffset
        dist = self.editor.cameraToolDistance
        W, H, L = self.brushSize
        self.brushSize = L, H, W
        self.reticleOffset = offs
        self.editor.cameraToolDistance = dist

    def mirror(self):
        offs = self.reticleOffset
        dist = self.editor.cameraToolDistance
        W, H, L = self.brushSize
        self.brushSize = W, L, H
        self.reticleOffset = offs
        self.editor.cameraToolDistance = dist

    def toolReselected(self):
        if self.brushMode.name == "Replace":
            self.panel.pickReplaceBlock()
        else:
            self.panel.pickFillBlock()

    def flip(self):
        self.decreaseBrushSize()

    def roll(self):
        self.increaseBrushSize()

    def swap(self):
        self.panel.swap()

    def decreaseBrushSize(self):
        self.brushSize = [i - 1 for i in self.brushSize]
        # self.setupPreview()

    def increaseBrushSize(self):
        self.brushSize = [i + 1 for i in self.brushSize]

    @alertException
    def setupPreview(self):
        self.previewDirty = False
        brushSize = self.brushSize
        brushStyle = self.brushStyle
        if self.brushMode.name == "Replace":
            blockInfo = self.replaceBlockInfo
        else:
            blockInfo = self.blockInfo

        class FakeLevel(pymclevel.MCLevel):
            filename = "Fake Level"
            materials = self.editor.level.materials

            def __init__(self):
                self.chunkCache = {}

            Width, Height, Length = brushSize

            zerolight = numpy.zeros((16, 16, Height), dtype='uint8')
            zerolight[:] = 15

            def getChunk(self, cx, cz):
                if (cx, cz) in self.chunkCache:
                    return self.chunkCache[cx, cz]

                class FakeBrushChunk(pymclevel.level.FakeChunk):
                    Entities = []
                    TileEntities = []

                f = FakeBrushChunk()
                f.world = self
                f.chunkPosition = (cx, cz)

                mask = createBrushMask(brushSize, brushStyle, (0, 0, 0), BoundingBox((cx << 4, 0, cz << 4), (16, self.Height, 16)))
                f.Blocks = numpy.zeros(mask.shape, dtype='uint8')
                f.Data = numpy.zeros(mask.shape, dtype='uint8')
                f.BlockLight = self.zerolight
                f.SkyLight = self.zerolight

                if blockInfo.ID:
                    f.Blocks[mask] = blockInfo.ID
                    f.Data[mask] = blockInfo.blockData

                else:
                    f.Blocks[mask] = 255
                self.chunkCache[cx, cz] = f
                return f

        self.level = FakeLevel()

        CloneTool.setupPreview(self, alpha=self.brushAlpha)

    def resetToolDistance(self):
        distance = max(self.editor.cameraToolDistance, 6 + max(self.brushSize) * 1.25)
        # print "Adjusted distance", distance, max(self.brushSize) * 1.25
        self.editor.cameraToolDistance = distance

    def toolSelected(self):

        if self.chooseBlockImmediately:
            blockPicker = BlockPicker(
                self.blockInfo,
                self.editor.level.materials,
                allowWildcards=self.brushMode.name == "Replace")

            if blockPicker.present():
                self.blockInfo = blockPicker.blockInfo

        if self.updateBrushOffset:
            self.reticleOffset = self.offsetMax()
        self.resetToolDistance()
        self.setupPreview()
        self.showPanel()

#    def cancel(self):
#        self.hidePanel()
#        super(BrushTool, self).cancel()

    def showPanel(self):
        if self.panel:
            self.panel.parent.remove(self.panel)

        panel = BrushPanel(self)
        panel.centery = self.editor.centery
        panel.left = self.editor.left
        panel.anchor = "lwh"

        self.panel = panel
        self.editor.add(panel)

    def increaseToolReach(self):
        # self.reticleOffset = max(self.reticleOffset-1, 0)
        if self.editor.mainViewport.mouseMovesCamera and not self.editor.longDistanceMode:
            return False
        self.reticleOffset = self.reticleOffset + 1
        return True

    def decreaseToolReach(self):
        if self.editor.mainViewport.mouseMovesCamera and not self.editor.longDistanceMode:
            return False
        self.reticleOffset = max(self.reticleOffset - 1, 0)
        return True

    def resetToolReach(self):
        if self.editor.mainViewport.mouseMovesCamera and not self.editor.longDistanceMode:
            self.resetToolDistance()
        else:
            self.reticleOffset = self.offsetMax()
        return True

    cameraDistance = EditorTool.cameraDistance

    def offsetMax(self):
        return max(1, ((0.5 * max(self.brushSize)) + 1))

    def getReticleOffset(self):
        return self.reticleOffset

    def getReticlePoint(self, pos, direction):
        if len(self.draggedPositions):
            direction = self.draggedDirection
        return map(lambda a, b: a + (b * self.getReticleOffset()), pos, direction)

    def drawToolReticle(self):
        for pos in self.draggedPositions:
            drawTerrainCuttingWire(BoundingBox(pos, (1, 1, 1)),
                                   (0.75, 0.75, 0.1, 0.4),
                                   (1.0, 1.0, 0.5, 1.0))

    lastPosition = None

    def drawTerrainReticle(self):
        if pygame.key.get_mods() & pygame.KMOD_ALT:
            # eyedropper mode
            self.editor.drawWireCubeReticle(color=(0.2, 0.6, 0.9, 1.0))
        else:
            pos, direction = self.editor.blockFaceUnderCursor
            reticlePoint = self.getReticlePoint(pos, direction)

            self.editor.drawWireCubeReticle(position=reticlePoint)
            if reticlePoint != pos:
                GL.glColor4f(1.0, 1.0, 0.0, 0.7)
                with gl.glBegin(GL.GL_LINES):
                    GL.glVertex3f(*map(lambda a: a + 0.5, reticlePoint))  # center of reticle block
                    GL.glVertex3f(*map(lambda a, b: a + 0.5 + b * 0.5, pos, direction))  # top side of surface block

            if self.previewDirty:
                self.setupPreview()

            dirtyBox = self.brushMode.brushBoxForPointAndOptions(reticlePoint, self.getBrushOptions())
            self.drawTerrainPreview(dirtyBox.origin)
            if pygame.key.get_mods() & pygame.KMOD_SHIFT and self.lastPosition and self.brushMode.name != "Flood Fill":
                GL.glColor4f(1.0, 1.0, 1.0, 0.7)
                with gl.glBegin(GL.GL_LINES):
                    GL.glVertex3f(*map(lambda a: a + 0.5, self.lastPosition))
                    GL.glVertex3f(*map(lambda a: a + 0.5, reticlePoint))

    def updateOffsets(self):
        pass

    def selectionChanged(self):
        pass

    def option1(self):
        self.swapBrushStyles()

    def option2(self):
        self.swapBrushModes()

    def option3(self):
        self.brushHollow = not self.brushHollow

def createBrushMask(shape, style="Round", offset=(0, 0, 0), box=None, chance=100, hollow=False):
    """
    Return a boolean array for a brush with the given shape and style.
    If 'offset' and 'box' are given, then the brush is offset into the world
    and only the part of the world contained in box is returned as an array
    """

    # we are returning indices for a Blocks array, so swap axes
    if box is None:
        box = BoundingBox(offset, shape)
    if chance < 100 or hollow:
        box = box.expand(1)

    outputShape = box.size
    outputShape = (outputShape[0], outputShape[2], outputShape[1])

    shape = shape[0], shape[2], shape[1]
    offset = numpy.array(offset) - numpy.array(box.origin)
    offset = offset[[0, 2, 1]]

    inds = numpy.indices(outputShape, dtype=float)
    halfshape = numpy.array([(i >> 1) - ((i & 1 == 0) and 0.5 or 0) for i in shape])

    blockCenters = inds - halfshape[:, newaxis, newaxis, newaxis]
    blockCenters -= offset[:, newaxis, newaxis, newaxis]

    # odd diameter means measure from the center of the block at 0,0,0 to each block center
    # even diameter means measure from the 0,0,0 grid point to each block center

    # if diameter & 1 == 0: blockCenters += 0.5
    shape = numpy.array(shape, dtype='float32')

    # if not isSphere(shape):
    if style == "Round":
        blockCenters *= blockCenters
        shape /= 2
        shape *= shape

        blockCenters /= shape[:, newaxis, newaxis, newaxis]
        distances = sum(blockCenters, 0)
        mask = distances < 1
    elif style == "Square":
        # mask = ones(outputShape, dtype=bool)
        # mask = blockCenters[:, newaxis, newaxis, newaxis] < shape
        blockCenters /= shape[:, newaxis, newaxis, newaxis]

        distances = numpy.absolute(blockCenters).max(0)
        mask = distances < .5

    elif style == "Diamond":
        blockCenters = numpy.abs(blockCenters)
        shape /= 2
        blockCenters /= shape[:, newaxis, newaxis, newaxis]
        distances = sum(blockCenters, 0)
        mask = distances < 1
    else:
        raise ValueError, "Unknown style: " + style

    if (chance < 100 or hollow) and max(shape) > 1:
        threshold = chance / 100.0
        exposedBlockMask = numpy.ones(shape=outputShape, dtype='bool')
        exposedBlockMask[:] = mask
        submask = mask[1:-1, 1:-1, 1:-1]
        exposedBlockSubMask = exposedBlockMask[1:-1, 1:-1, 1:-1]
        exposedBlockSubMask[:] = False

        for dim in (0, 1, 2):
            slices = [slice(1, -1), slice(1, -1), slice(1, -1)]
            slices[dim] = slice(None, -2)
            exposedBlockSubMask |= (submask & (mask[slices] != submask))
            slices[dim] = slice(2, None)
            exposedBlockSubMask |= (submask & (mask[slices] != submask))

        if hollow:
            mask[~exposedBlockMask] = False
        if chance < 100:
            rmask = numpy.random.random(mask.shape) < threshold

            mask[exposedBlockMask] = rmask[exposedBlockMask]

    if chance < 100 or hollow:
        return mask[1:-1, 1:-1, 1:-1]
    else:
        return mask

########NEW FILE########
__FILENAME__ = chunk
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""
import traceback
from OpenGL import GL
import numpy
from numpy import newaxis

from albow import Label, ValueDisplay, AttrRef, Button, Column, ask, Row, alert, Widget, Menu
from editortools.editortool import EditorTool
from glbackground import Panel
from glutils import DisplayList, gl
from mceutils import alertException, setWindowCaption, showProgress, ChoiceButton, IntInputRow, CheckBoxLabel
import mcplatform
import pymclevel
from pymclevel.minecraft_server import MCServerChunkGenerator

from albow.dialogs import Dialog


class ChunkToolPanel(Panel):

    def __init__(self, tool, *a, **kw):
        Panel.__init__(self, *a, **kw)

        self.tool = tool

        self.anchor = "whl"

        chunkToolLabel = Label("Selected Chunks:")

        self.chunksLabel = ValueDisplay(ref=AttrRef(self, 'chunkSizeText'), width=100)
        self.chunksLabel.align = "c"
        self.chunksLabel.tooltipText = "..."

        extractButton = Button("Extract")
        extractButton.tooltipText = "Extract these chunks to individual chunk files"
        extractButton.action = tool.extractChunks
        extractButton.highlight_color = (255, 255, 255)

        deselectButton = Button("Deselect",
            tooltipText=None,
            action=tool.editor.deselect,
        )

        createButton = Button("Create")
        createButton.tooltipText = "Create new, empty chunks within the selection."
        createButton.action = tool.createChunks
        createButton.highlight_color = (0, 255, 0)

        destroyButton = Button("Delete")
        destroyButton.tooltipText = "Delete the selected chunks from disk. Minecraft will recreate them the next time you are near."
        destroyButton.action = tool.destroyChunks

        pruneButton = Button("Prune")
        pruneButton.tooltipText = "Prune the world, leaving only the selected chunks. Any chunks outside of the selection will be removed, and empty region files will be deleted from disk"
        pruneButton.action = tool.pruneChunks

        relightButton = Button("Relight")
        relightButton.tooltipText = "Recalculate light values across the selected chunks"
        relightButton.action = tool.relightChunks
        relightButton.highlight_color = (255, 255, 255)

        repopButton = Button("Repop")
        repopButton.tooltipText = "Mark the selected chunks for repopulation. The next time you play Minecraft, the chunks will have trees, ores, and other features regenerated."
        repopButton.action = tool.repopChunks
        repopButton.highlight_color = (255, 200, 155)

        dontRepopButton = Button("Don't Repop")
        dontRepopButton.tooltipText = "Unmark the selected chunks. They will not repopulate the next time you play the game."
        dontRepopButton.action = tool.dontRepopChunks
        dontRepopButton.highlight_color = (255, 255, 255)

        col = Column((chunkToolLabel, self.chunksLabel, deselectButton, createButton, destroyButton, pruneButton, relightButton, extractButton, repopButton, dontRepopButton))
#        col.right = self.width - 10;
        self.width = col.width
        self.height = col.height
        #self.width = 120
        self.add(col)

    @property
    def chunkSizeText(self):
        return "{0} chunks".format(len(self.tool.selectedChunks()))

    def updateText(self):
        pass
        #self.chunksLabel.text = self.chunksLabelText()


class ChunkTool(EditorTool):
    toolIconName = "chunk"
    tooltipText = "Chunk Control"

    @property
    def statusText(self):
        return "Click and drag to select chunks. Hold ALT to deselect chunks. Hold SHIFT to select chunks."

    def toolEnabled(self):
        return isinstance(self.editor.level, pymclevel.ChunkedLevelMixin)

    _selectedChunks = None
    _displayList = None

    def drawToolMarkers(self):
        if self._displayList is None:
            self._displayList = DisplayList(self._drawToolMarkers)

        #print len(self._selectedChunks) if self._selectedChunks else None, "!=", len(self.editor.selectedChunks)

        if self._selectedChunks != self.editor.selectedChunks or True:  # xxx
            self._selectedChunks = set(self.editor.selectedChunks)
            self._displayList.invalidate()

        self._displayList.call()

    def _drawToolMarkers(self):

        lines = (
            ((-1, 0), (0, 0, 0, 1), []),
            ((1, 0),  (1, 0, 1, 1), []),
            ((0, -1), (0, 0, 1, 0), []),
            ((0, 1),  (0, 1, 1, 1), []),
        )
        for ch in self._selectedChunks:
            cx, cz = ch
            for (dx, dz), points, positions in lines:
                n = (cx + dx, cz + dz)
                if n not in self._selectedChunks:
                    positions.append([ch])

        color = self.editor.selectionTool.selectionColor + (0.3, )
        GL.glColor(*color)
        with gl.glEnable(GL.GL_BLEND):

            import renderer
            sizedChunks = renderer.chunkMarkers(self._selectedChunks)
            for size, chunks in sizedChunks.iteritems():
                if not len(chunks):
                    continue
                chunks = numpy.array(chunks, dtype='float32')

                chunkPosition = numpy.zeros(shape=(chunks.shape[0], 4, 3), dtype='float32')
                chunkPosition[..., (0, 2)] = numpy.array(((0, 0), (0, 1), (1, 1), (1, 0)), dtype='float32')
                chunkPosition[..., (0, 2)] *= size
                chunkPosition[..., (0, 2)] += chunks[:, newaxis, :]
                chunkPosition *= 16
                chunkPosition[..., 1] = self.editor.level.Height
                GL.glVertexPointer(3, GL.GL_FLOAT, 0, chunkPosition.ravel())
                #chunkPosition *= 8
                GL.glDrawArrays(GL.GL_QUADS, 0, len(chunkPosition) * 4)

        for d, points, positions in lines:
            if 0 == len(positions):
                continue
            vertexArray = numpy.zeros((len(positions), 4, 3), dtype='float32')
            vertexArray[..., [0, 2]] = positions
            vertexArray.shape = len(positions), 2, 2, 3

            vertexArray[..., 0, 0, 0] += points[0]
            vertexArray[..., 0, 0, 2] += points[1]
            vertexArray[..., 0, 1, 0] += points[2]
            vertexArray[..., 0, 1, 2] += points[3]
            vertexArray[..., 1, 0, 0] += points[2]
            vertexArray[..., 1, 0, 2] += points[3]
            vertexArray[..., 1, 1, 0] += points[0]
            vertexArray[..., 1, 1, 2] += points[1]

            vertexArray *= 16

            vertexArray[..., 1, :, 1] = self.editor.level.Height

            GL.glVertexPointer(3, GL.GL_FLOAT, 0, vertexArray)
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
            GL.glDrawArrays(GL.GL_QUADS, 0, len(positions) * 4)
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
            with gl.glEnable(GL.GL_BLEND, GL.GL_DEPTH_TEST):
                GL.glDepthMask(False)
                GL.glDrawArrays(GL.GL_QUADS, 0, len(positions) * 4)
                GL.glDepthMask(True)

    @property
    def worldTooltipText(self):
        box = self.editor.selectionTool.selectionBoxInProgress()
        if box:
            box = box.chunkBox(self.editor.level)
            l, w = box.length // 16, box.width // 16
            return "%s x %s chunks" % (l, w)

    def toolSelected(self):

        self.editor.selectionToChunks()

        self.panel = ChunkToolPanel(self)

        self.panel.centery = self.editor.centery
        self.panel.left = 10

        self.editor.add(self.panel)

    def cancel(self):
        self.editor.remove(self.panel)

    def selectedChunks(self):
        return self.editor.selectedChunks

    @alertException
    def extractChunks(self):
        folder = mcplatform.askSaveFile(mcplatform.docsFolder,
                title='Export chunks to...',
                defaultName=self.editor.level.displayName + "_chunks",
                filetype='Folder\0*.*\0\0',
                suffix="",
                )
        if not folder:
            return

        # TODO: We need a third dimension, Scotty!
        for cx, cz in self.selectedChunks():
            if self.editor.level.containsChunk(cx, cz):
                self.editor.level.extractChunk(cx, cz, folder)

    @alertException
    def destroyChunks(self, chunks=None):
        if "No" == ask("Really delete these chunks? This cannot be undone.", ("Yes", "No")):
            return
        if chunks is None:
            chunks = self.selectedChunks()
        chunks = list(chunks)

        def _destroyChunks():
            i = 0
            chunkCount = len(chunks)

            for cx, cz in chunks:
                i += 1
                yield (i, chunkCount)
                if self.editor.level.containsChunk(cx, cz):
                    try:
                        self.editor.level.deleteChunk(cx, cz)
                    except Exception, e:
                        print "Error during chunk delete: ", e

        with setWindowCaption("DELETING - "):
            showProgress("Deleting chunks...", _destroyChunks())

        self.editor.renderer.invalidateChunkMarkers()
        self.editor.renderer.discardChunks(chunks)
        #self.editor.addUnsavedEdit()

    @alertException
    def pruneChunks(self):
        if "No" == ask("Save these chunks and remove the rest? This cannot be undone.", ("Yes", "No")):
            return
        self.editor.saveFile()

        def _pruneChunks():
            selectedChunks = self.selectedChunks()
            for i, cPos in enumerate(list(self.editor.level.allChunks)):
                if cPos not in selectedChunks:
                    try:
                        self.editor.level.deleteChunk(*cPos)

                    except Exception, e:
                        print "Error during chunk delete: ", e

                yield i, self.editor.level.chunkCount

        with setWindowCaption("PRUNING - "):
            showProgress("Pruning chunks...", _pruneChunks())

        self.editor.renderer.invalidateChunkMarkers()
        self.editor.discardAllChunks()

        #self.editor.addUnsavedEdit()

    @alertException
    def relightChunks(self):

        def _relightChunks():
            for i in self.editor.level.generateLightsIter(self.selectedChunks()):
                yield i

        with setWindowCaption("RELIGHTING - "):

            showProgress("Lighting {0} chunks...".format(len(self.selectedChunks())),
                                     _relightChunks(), cancel=True)

            self.editor.invalidateChunks(self.selectedChunks())
            self.editor.addUnsavedEdit()

    @alertException
    def createChunks(self):
        panel = GeneratorPanel()
        col = [panel]
        label = Label("Create chunks using the settings above? This cannot be undone.")
        col.append(Row([Label("")]))
        col.append(label)
        col = Column(col)
        if Dialog(client=col, responses=["OK", "Cancel"]).present() == "Cancel":
            return
        chunks = self.selectedChunks()

        createChunks = panel.generate(self.editor.level, chunks)

        try:
            with setWindowCaption("CREATING - "):
                showProgress("Creating {0} chunks...".format(len(chunks)), createChunks, cancel=True)
        except Exception, e:
            traceback.print_exc()
            alert("Failed to start the chunk generator. {0!r}".format(e))
        finally:
            self.editor.renderer.invalidateChunkMarkers()
            self.editor.renderer.loadNearbyChunks()

    @alertException
    def repopChunks(self):
        for cpos in self.selectedChunks():
            try:
                chunk = self.editor.level.getChunk(*cpos)
                chunk.TerrainPopulated = False
            except pymclevel.ChunkNotPresent:
                continue
        self.editor.renderer.invalidateChunks(self.selectedChunks(), layers=["TerrainPopulated"])

    @alertException
    def dontRepopChunks(self):
        for cpos in self.selectedChunks():
            try:
                chunk = self.editor.level.getChunk(*cpos)
                chunk.TerrainPopulated = True
            except pymclevel.ChunkNotPresent:
                continue
        self.editor.renderer.invalidateChunks(self.selectedChunks(), layers=["TerrainPopulated"])

    def mouseDown(self, *args):
        return self.editor.selectionTool.mouseDown(*args)

    def mouseUp(self, evt, *args):
        self.editor.selectionTool.mouseUp(evt, *args)


def GeneratorPanel():
    panel = Widget()
    panel.chunkHeight = 64
    panel.grass = True
    panel.simulate = False

    jarStorage = MCServerChunkGenerator.getDefaultJarStorage()
    if jarStorage:
        jarStorage.reloadVersions()

    generatorChoice = ChoiceButton(["Minecraft Server", "Flatland"])
    panel.generatorChoice = generatorChoice
    col = [Row((Label("Generator:"), generatorChoice))]
    noVersionsRow = Label("Will automatically download and use the latest version")
    versionContainer = Widget()

    heightinput = IntInputRow("Height: ", ref=AttrRef(panel, "chunkHeight"), min=0, max=128)
    grassinput = CheckBoxLabel("Grass", ref=AttrRef(panel, "grass"))

    flatPanel = Column([heightinput, grassinput], align="l")

    def generatorChoiceChanged():
        serverPanel.visible = generatorChoice.selectedChoice == "Minecraft Server"
        flatPanel.visible = not serverPanel.visible

    generatorChoice.choose = generatorChoiceChanged

    versionChoice = None

    if len(jarStorage.versions):
        def checkForUpdates():
            def _check():
                yield
                jarStorage.downloadCurrentServer()
                yield

            showProgress("Checking for server updates...", _check())
            versionChoice.choices = sorted(jarStorage.versions, reverse=True)
            versionChoice.choiceIndex = 0

        versionChoice = ChoiceButton(sorted(jarStorage.versions, reverse=True))
        versionChoiceRow = (Row((
            Label("Server version:"),
            versionChoice,
            Label("or"),
            Button("Check for Updates", action=checkForUpdates))))
        panel.versionChoice = versionChoice
        versionContainer.add(versionChoiceRow)
    else:
        versionContainer.add(noVersionsRow)

    versionContainer.shrink_wrap()

    menu = Menu("Advanced", [
        ("Open Server Storage", "revealStorage"),
        ("Reveal World Cache", "revealCache"),
        ("Delete World Cache", "clearCache")
        ])

    def presentMenu():
        i = menu.present(advancedButton.parent, advancedButton.topleft)
        if i != -1:
            (revealStorage, revealCache, clearCache)[i]()

    advancedButton = Button("Advanced...", presentMenu)

    @alertException
    def revealStorage():
        mcplatform.platform_open(jarStorage.cacheDir)

    @alertException
    def revealCache():
        mcplatform.platform_open(MCServerChunkGenerator.worldCacheDir)

    #revealCacheRow = Row((Label("Minecraft Server Storage: "), Button("Open Folder", action=revealCache, tooltipText="Click me to install your own minecraft_server.jar if you have any.")))

    @alertException
    def clearCache():
        MCServerChunkGenerator.clearWorldCache()

    simRow = CheckBoxLabel("Simulate world", ref=AttrRef(panel, "simulate"), tooltipText="Simulate the world for a few seconds after generating it. Reduces the save file size by processing all of the TileTicks.")

    simRow = Row((simRow, advancedButton), anchor="lrh")
    #deleteCacheRow = Row((Label("Delete Temporary World File Cache?"), Button("Delete Cache!", action=clearCache, tooltipText="Click me if you think your chunks are stale.")))

    serverPanel = Column([versionContainer, simRow, ], align="l")

    col.append(serverPanel)
    col = Column(col, align="l")
    col.add(flatPanel)
    flatPanel.topleft = serverPanel.topleft
    flatPanel.visible = False
    panel.add(col)

    panel.shrink_wrap()

    def generate(level, arg):
        useServer = generatorChoice.selectedChoice == "Minecraft Server"

        if useServer:
            def _createChunks():
                if versionChoice:
                    version = versionChoice.selectedChoice
                else:
                    version = None
                gen = MCServerChunkGenerator(version=version)


                if isinstance(arg, pymclevel.BoundingBox):
                    for i in gen.createLevelIter(level, arg, simulate=panel.simulate):
                        yield i
                else:
                    for i in gen.generateChunksInLevelIter(level, arg, simulate=panel.simulate):
                        yield i

        else:
            def _createChunks():
                height = panel.chunkHeight
                grass = panel.grass and pymclevel.alphaMaterials.Grass.ID or pymclevel.alphaMaterials.Dirt.ID
                if isinstance(arg, pymclevel.BoundingBox):
                    chunks = list(arg.chunkPositions)
                else:
                    chunks = arg

                if level.dimNo in (-1, 1):
                    maxskylight = 0
                else:
                    maxskylight = 15

                for i, (cx, cz) in enumerate(chunks):

                    yield i, len(chunks)
                    #surface = blockInput.blockInfo

                    #for cx, cz in :
                    try:
                        level.createChunk(cx, cz)
                    except ValueError, e:  # chunk already present
                        print e
                        continue
                    else:
                        ch = level.getChunk(cx, cz)
                        if height > 0:
                            stoneHeight = max(0, height - 5)
                            grassHeight = max(0, height - 1)

                            ch.Blocks[:, :, grassHeight] = grass
                            ch.Blocks[:, :, stoneHeight:grassHeight] = pymclevel.alphaMaterials.Dirt.ID
                            ch.Blocks[:, :, :stoneHeight] = pymclevel.alphaMaterials.Stone.ID

                            ch.Blocks[:, :, 0] = pymclevel.alphaMaterials.Bedrock.ID
                            ch.SkyLight[:, :, height:] = maxskylight
                            if maxskylight:
                                ch.HeightMap[:] = height

                        else:
                            ch.SkyLight[:] = maxskylight

                        ch.needsLighting = False
                        ch.dirty = True

        return _createChunks()

    panel.generate = generate
    return panel

########NEW FILE########
__FILENAME__ = clone
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""
import os
import traceback
from OpenGL import GL
import numpy
import pygame
from albow import Widget, IntField, Column, Row, Label, Button, CheckBox, AttrRef, FloatField, alert
from depths import DepthOffset
from editortools.editortool import EditorTool
from editortools.nudgebutton import NudgeButton
from editortools.tooloptions import ToolOptions
from glbackground import Panel
from glutils import gl
from mceutils import setWindowCaption, showProgress, alertException, drawFace
import mcplatform
from operation import Operation
import pymclevel
from pymclevel.box import Vector
from renderer import PreviewRenderer

from select import SelectionOperation
from pymclevel.pocket import PocketWorld
from pymclevel import block_copy, BoundingBox

import logging
log = logging.getLogger(__name__)

import config


CloneSettings = config.Settings("Clone")
CloneSettings.copyAir = CloneSettings("Copy Air", True)
CloneSettings.copyWater = CloneSettings("Copy Water", True)
CloneSettings.copyBiomes = CloneSettings("Copy Biomes", True)
CloneSettings.placeImmediately = CloneSettings("Place Immediately", True)


class CoordsInput(Widget):
    is_gl_container = True

    def __init__(self):
        Widget.__init__(self)

        self.nudgeButton = NudgeButton()
        self.nudgeButton.nudge = self._nudge

        self.xField = IntField(value=0)
        self.yField = IntField(value=0)
        self.zField = IntField(value=0)

        for field in (self.xField, self.yField, self.zField):
            field.change_action = self._coordsChanged
            field.enter_passes = False

        offsetCol = Column((self.xField, self.yField, self.zField))

        nudgeOffsetRow = Row((offsetCol, self.nudgeButton))

        self.add(nudgeOffsetRow)
        self.shrink_wrap()

    def getCoords(self):
        return self.xField.value, self.yField.value, self.zField.value

    def setCoords(self, coords):
        x, y, z = coords
        self.xField.text = str(x)
        self.yField.text = str(y)
        self.zField.text = str(z)

    coords = property(getCoords, setCoords, None)

    def _coordsChanged(self):
        self.coordsChanged()

    def coordsChanged(self):
        # called when the inputs change.  override or replace
        pass

    def _nudge(self, nudge):
        self.nudge(nudge)

    def nudge(self, nudge):
        # nudge is a 3-tuple where one of the elements is -1 or 1, and the others are 0.
        pass


class BlockCopyOperation(Operation):
    def __init__(self, editor, sourceLevel, sourceBox, destLevel, destPoint, copyAir, copyWater, copyBiomes):
        super(BlockCopyOperation, self).__init__(editor, destLevel)
        self.sourceLevel = sourceLevel
        self.sourceBox = sourceBox
        self.destPoint = Vector(*destPoint)
        self.copyAir = copyAir
        self.copyWater = copyWater
        self.copyBiomes = copyBiomes
        self.sourceBox, self.destPoint = block_copy.adjustCopyParameters(self.level, self.sourceLevel, self.sourceBox,
                                                                         self.destPoint)

    def dirtyBox(self):
        return BoundingBox(self.destPoint, self.sourceBox.size)

    def name(self):
        return "Copy {0} blocks".format(self.sourceBox.volume)

    def perform(self, recordUndo=True):
        sourceBox = self.sourceBox

        if recordUndo:
            self.undoLevel = self.extractUndo(self.level, BoundingBox(self.destPoint, self.sourceBox.size))


        blocksToCopy = None
        if not (self.copyAir and self.copyWater):
            blocksToCopy = range(pymclevel.materials.id_limit)
            if not self.copyAir:
                blocksToCopy.remove(0)
            if not self.copyWater:
                blocksToCopy.remove(8)
            if not self.copyWater:
                blocksToCopy.remove(9)

        with setWindowCaption("Copying - "):
            i = self.level.copyBlocksFromIter(self.sourceLevel, self.sourceBox, self.destPoint, blocksToCopy, create=True, biomes=self.copyBiomes)
            showProgress("Copying {0:n} blocks...".format(self.sourceBox.volume), i)

    def bufferSize(self):
        return 123456


class CloneOperation(Operation):
    def __init__(self, editor, sourceLevel, sourceBox, originSourceBox, destLevel, destPoint, copyAir, copyWater, copyBiomes, repeatCount):
        super(CloneOperation, self).__init__(editor, destLevel)

        self.blockCopyOps = []
        dirtyBoxes = []
        if repeatCount > 1:  # clone tool only
            delta = destPoint - editor.toolbar.tools[0].selectionBox().origin
        else:
            delta = (0, 0, 0)

        for i in range(repeatCount):
            op = BlockCopyOperation(editor, sourceLevel, sourceBox, destLevel, destPoint, copyAir, copyWater, copyBiomes)
            dirty = op.dirtyBox()

            # bounds check - xxx move to BoundingBox
            if dirty.miny >= destLevel.Height or dirty.maxy < 0:
                continue
            if destLevel.Width != 0:
                if dirty.minx >= destLevel.Width or dirty.maxx < 0:
                    continue
                if dirty.minz >= destLevel.Length or dirty.maxz < 0:
                    continue

            dirtyBoxes.append(dirty)
            self.blockCopyOps.append(op)

            destPoint += delta

        if len(dirtyBoxes):
            def enclosingBox(dirtyBoxes):
                return reduce(lambda a, b: a.union(b), dirtyBoxes)

            self._dirtyBox = enclosingBox(dirtyBoxes)

            if repeatCount > 1 and self.selectOriginalAfterRepeat:
                dirtyBoxes.append(originSourceBox)

            dirty = enclosingBox(dirtyBoxes)
            points = (dirty.origin, dirty.maximum - (1, 1, 1))

            self.selectionOps = [SelectionOperation(editor.selectionTool, points)]

        else:
            self._dirtyBox = None
            self.selectionOps = []

    selectOriginalAfterRepeat = True

    def dirtyBox(self):
        return self._dirtyBox

    def perform(self, recordUndo=True):
        with setWindowCaption("COPYING - "):
            self.editor.freezeStatus("Copying %0.1f million blocks" % (float(self._dirtyBox.volume) / 1048576.,))
            if recordUndo:
                chunks = set()
                for op in self.blockCopyOps:
                    chunks.update(op.dirtyBox().chunkPositions)
                self.undoLevel = self.extractUndoChunks(self.level, chunks)

            [i.perform(False) for i in self.blockCopyOps]
            [i.perform(recordUndo) for i in self.selectionOps]

    def undo(self):
        super(CloneOperation, self).undo()
        [i.undo() for i in self.selectionOps]


class CloneToolPanel(Panel):
    useOffsetInput = True

    def transformEnable(self):
        return not isinstance(self.tool.level, pymclevel.MCInfdevOldLevel)

    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool

        rotateRow = Row((
            Label(config.config.get("Keys", "Rotate").upper()), Button("Rotate", width=80, action=tool.rotate, enable=self.transformEnable),
        ))

        rollRow = Row((
            Label(config.config.get("Keys", "Roll").upper()), Button("Roll", width=80, action=tool.roll, enable=self.transformEnable),
        ))

        flipRow = Row((
            Label(config.config.get("Keys", "Flip").upper()), Button("Flip", width=80, action=tool.flip, enable=self.transformEnable),
        ))

        mirrorRow = Row((
            Label(config.config.get("Keys", "Mirror").upper()), Button("Mirror", width=80, action=tool.mirror, enable=self.transformEnable),
        ))

        alignRow = Row((
            CheckBox(ref=AttrRef(self.tool, 'chunkAlign')), Label("Chunk Align")
        ))

        # headerLabel = Label("Clone Offset")
        if self.useOffsetInput:
            self.offsetInput = CoordsInput()
            self.offsetInput.coordsChanged = tool.offsetChanged
            self.offsetInput.nudgeButton.bg_color = tool.color
            self.offsetInput.nudge = tool.nudge
        else:
            self.nudgeButton = NudgeButton()
            self.nudgeButton.bg_color = tool.color
            self.nudgeButton.nudge = tool.nudge

        repeatField = IntField(ref=AttrRef(tool, 'repeatCount'))
        repeatField.min = 1
        repeatField.max = 50

        repeatRow = Row((
            Label("Repeat"), repeatField
        ))
        self.repeatField = repeatField

        scaleField = FloatField(ref=AttrRef(tool, 'scaleFactor'))
        scaleField.min = 0.125
        scaleField.max = 8
        dv = scaleField.decrease_value
        iv = scaleField.increase_value

        def scaleFieldDecrease():
            if scaleField.value > 1 / 8.0 and scaleField.value <= 1.0:
                scaleField.value *= 0.5
            else:
                dv()

        def scaleFieldIncrease():
            if scaleField.value < 1.0:
                scaleField.value *= 2.0
            else:
                iv()

        scaleField.decrease_value = scaleFieldDecrease
        scaleField.increase_value = scaleFieldIncrease

        scaleRow = Row((
            Label("Scale Factor"), scaleField
        ))

        self.scaleField = scaleField

        self.copyAirCheckBox = CheckBox(ref=AttrRef(self.tool, "copyAir"))
        self.copyAirLabel = Label("Copy Air")
        self.copyAirLabel.mouse_down = self.copyAirCheckBox.mouse_down
        self.copyAirLabel.tooltipText = "Shortcut: ALT-1"
        self.copyAirCheckBox.tooltipText = self.copyAirLabel.tooltipText

        copyAirRow = Row((self.copyAirCheckBox, self.copyAirLabel))

        self.copyWaterCheckBox = CheckBox(ref=AttrRef(self.tool, "copyWater"))
        self.copyWaterLabel = Label("Copy Water")
        self.copyWaterLabel.mouse_down = self.copyWaterCheckBox.mouse_down
        self.copyWaterLabel.tooltipText = "Shortcut: ALT-2"
        self.copyWaterCheckBox.tooltipText = self.copyWaterLabel.tooltipText

        copyWaterRow = Row((self.copyWaterCheckBox, self.copyWaterLabel))

        self.copyBiomesCheckBox = CheckBox(ref=AttrRef(self.tool, "copyBiomes"))
        self.copyBiomesLabel = Label("Copy Biomes")
        self.copyBiomesLabel.mouse_down = self.copyBiomesCheckBox.mouse_down
        self.copyBiomesLabel.tooltipText = "Shortcut: ALT-3"
        self.copyBiomesCheckBox.tooltipText = self.copyBiomesLabel.tooltipText

        copyBiomesRow = Row((self.copyBiomesCheckBox, self.copyBiomesLabel))

        self.performButton = Button("Clone", width=100, align="c")
        self.performButton.tooltipText = "Shortcut: ENTER"
        self.performButton.action = tool.confirm
        self.performButton.enable = lambda: (tool.destPoint is not None)
        if self.useOffsetInput:
            col = Column((rotateRow, rollRow, flipRow, mirrorRow, alignRow, self.offsetInput, repeatRow, scaleRow, copyAirRow, copyWaterRow, copyBiomesRow, self.performButton))
        else:
            col = Column((rotateRow, rollRow, flipRow, mirrorRow, alignRow, self.nudgeButton, copyAirRow, copyWaterRow, copyBiomesRow, self.performButton))

        self.add(col)
        self.anchor = "lwh"

        self.shrink_wrap()


class CloneToolOptions(ToolOptions):
    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool
        self.autoPlaceCheckBox = CheckBox(ref=AttrRef(tool, "placeImmediately"))
        self.autoPlaceLabel = Label("Place Immediately")
        self.autoPlaceLabel.mouse_down = self.autoPlaceCheckBox.mouse_down

        tooltipText = "When the clone tool is chosen, place the clone at the selection right away."
        self.autoPlaceLabel.tooltipText = self.autoPlaceCheckBox.tooltipText = tooltipText

        row = Row((self.autoPlaceCheckBox, self.autoPlaceLabel))
        col = Column((Label("Clone Options"), row, Button("OK", action=self.dismiss)))

        self.add(col)
        self.shrink_wrap()


class CloneTool(EditorTool):
    surfaceBuild = True
    toolIconName = "clone"
    tooltipText = "Clone\nRight-click for options"
    level = None
    repeatCount = 1
    _scaleFactor = 1.0
    _chunkAlign = False

    @property
    def scaleFactor(self):
        return self._scaleFactor

    @scaleFactor.setter
    def scaleFactor(self, val):
        self.rescaleLevel(val)
        self._scaleFactor = val

    @property
    def chunkAlign(self):
        return self._chunkAlign

    @chunkAlign.setter
    def chunkAlign(self, value):
        self._chunkAlign = value
        self.alignDestPoint()

    def alignDestPoint(self):
        if self.destPoint is not None:
            x, y, z = self.destPoint
            self.destPoint = Vector((x >> 4) << 4, y, (z >> 4) << 4)

    placeImmediately = CloneSettings.placeImmediately.configProperty()

    panelClass = CloneToolPanel
    # color = (0.89, 0.65, 0.35, 0.33)
    color = (0.3, 1.0, 0.3, 0.19)

    def __init__(self, *args):
        self.rotation = 0

        EditorTool.__init__(self, *args)
        self.previewRenderer = None
        self.panel = None

        self.optionsPanel = CloneToolOptions(self)

        self.destPoint = None

    @property
    def statusText(self):
        if self.destPoint == None:
            return "Click to set this item down."
        if self.draggingFace is not None:
            return "Mousewheel to move along the third axis. Hold SHIFT to only move along one axis."

        return "Click and drag to reposition the item. Double-click to pick it up. Click Clone or press ENTER to confirm."

    def quickNudge(self, nudge):
        return map(int.__mul__, nudge, self.selectionBox().size)

    copyAir = CloneSettings.copyAir.configProperty()
    copyWater = CloneSettings.copyWater.configProperty()
    copyBiomes = CloneSettings.copyBiomes.configProperty()

    def nudge(self, nudge):
        if self.destPoint is None:
            if self.selectionBox() is None:
                return
            self.destPoint = self.selectionBox().origin

        if self.chunkAlign:
            x, y, z = nudge
            nudge = x << 4, y, z << 4

        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
            nudge = self.quickNudge(nudge)

        # self.panel.performButton.enabled = True
        self.destPoint = self.destPoint + nudge
        self.updateOffsets()

    def selectionChanged(self):
        if self.selectionBox() is not None:
            self.updateSchematic()
            self.updateOffsets()

    def updateOffsets(self):
        if self.panel and self.panel.useOffsetInput and self.destPoint is not None:
            self.panel.offsetInput.setCoords(self.destPoint - self.selectionBox().origin)

    def offsetChanged(self):

        if self.panel:
            if not self.panel.useOffsetInput:
                return
            box = self.selectionBox()
            if box is None:
                return

            delta = self.panel.offsetInput.coords
            self.destPoint = box.origin + delta

    def toolEnabled(self):
        return not (self.selectionBox() is None)

    def cancel(self):

        self.discardPreviewer()
        if self.panel:
            self.panel.parent.remove(self.panel)
            self.panel = None

        self.destPoint = None
        self.level = None
        self.originalLevel = None

    def toolReselected(self):
        self.pickUp()

    def safeToolDistance(self):
        return numpy.sqrt(sum([self.level.Width ** 2, self.level.Height ** 2, self.level.Length ** 2]))

    def toolSelected(self):
        box = self.selectionBox()
        if box is None:
            self.editor.toolbar.selectTool(-1)
            return

        if box.volume > self.maxBlocks:
            self.editor.mouseLookOff()
            alert("Selection exceeds {0:n} blocks. Increase the block buffer setting and try again.".format(self.maxBlocks))
            self.editor.toolbar.selectTool(-1)
            return

        self.rotation = 0
        self.repeatCount = 1
        self._scaleFactor = 1.0

        if self.placeImmediately:
            self.destPoint = box.origin
        else:
            self.destPoint = None

        self.updateSchematic()
        self.cloneCameraDistance = max(self.cloneCameraDistance, self.safeToolDistance())
        self.showPanel()

    cloneCameraDistance = 0

    @property
    def cameraDistance(self):
        return self.cloneCameraDistance

    @alertException
    def rescaleLevel(self, factor):
        # if self.level.cloneToolScaleFactor == newFactor:
        #    return
        # oldfactor = self.level.cloneToolScaleFactor
        # factor = newFactor / oldfactor
        if factor == 1:
            self.level = self.originalLevel
            self.setupPreview()
            return

        oldshape = self.originalLevel.Blocks.shape
        blocks = self.originalLevel.Blocks
        data = self.originalLevel.Data

        if factor < 1.0:
            roundedShape = map(lambda x: int(int(x * factor) / factor), oldshape)
            roundedSlices = map(lambda x: slice(0, x), roundedShape)
            blocks = blocks[roundedSlices]
            data = data[roundedSlices]
        else:
            roundedShape = oldshape

        newshape = map(lambda x: int(x * factor), oldshape)
        xyzshape = newshape[0], newshape[2], newshape[1]
        newlevel = pymclevel.MCSchematic(xyzshape, mats=self.editor.level.materials)

        srcgrid = numpy.mgrid[0:roundedShape[0]:1.0 / factor, 0:roundedShape[1]:1.0 / factor, 0:roundedShape[2]:1.0 / factor].astype('uint')
        dstgrid = numpy.mgrid[0:newshape[0], 0:newshape[1], 0:newshape[2]].astype('uint')
        srcgrid = srcgrid[map(slice, dstgrid.shape)]
        dstgrid = dstgrid[map(slice, srcgrid.shape)]

        def copyArray(dest, src):
            dest[dstgrid[0], dstgrid[1], dstgrid[2]] = src[srcgrid[0], srcgrid[1], srcgrid[2]]

        copyArray(newlevel.Blocks, blocks)
        copyArray(newlevel.Data, data)

        self.level = newlevel
        self.setupPreview()
#
#        """
#        use array broadcasting to fill in the extra dimensions with copies of the
#        existing ones, then later change the shape to "fold" the extras back
#        into the original three
#        """
#        # if factor > 1.0:
#        sourceSlice = slice(0, 1)
#        destSlice = slice(None)
#
#        # if factor < 1.0:
#
#        destfactor = factor
#        srcfactor = 1
#        if factor < 1.0:
#            destfactor = 1.0
#            srcfactor = 1.0 / factor
#
#        intershape = newshape[0]/destfactor, destfactor, newshape[1]/destfactor, destfactor, newshape[2]/destfactor, destfactor
#        srcshape = roundedShape[0]/srcfactor, srcfactor, roundedShape[1]/srcfactor, srcfactor, roundedShape[2]/srcfactor, srcfactor
#
#        newlevel = MCSchematic(xyzshape)
#
#        def copyArray(dest, src):
#            dest.shape = intershape
#            src.shape = srcshape
#
#            dest[:, destSlice, :, destSlice, :, destSlice] = src[:, sourceSlice, :, sourceSlice, :, sourceSlice]
#            dest.shape = newshape
#            src.shape = roundedShape
#
#        copyArray(newlevel.Blocks, blocks)
#        copyArray(newlevel.Data, data)
#
#        newlevel.cloneToolScaleFactor = newFactor
#

    @alertException
    def updateSchematic(self):
        # extract blocks
        with setWindowCaption("COPYING - "):
            self.editor.freezeStatus("Copying to clone buffer...")
            box = self.selectionBox()
            self.level = self.editor.level.extractSchematic(box)
            self.originalLevel = self.level
            # self.level.cloneToolScaleFactor = 1.0
            self.rescaleLevel(self.scaleFactor)
            self.setupPreview()

    def showPanel(self):
        if self.panel:
            self.panel.set_parent(None)

        self.panel = self.panelClass(self)
        # self.panel.performButton.enabled = False

        self.panel.centery = self.editor.centery
        self.panel.left = self.editor.left
        self.editor.add(self.panel)

    def setupPreview(self, alpha=1.0):
        self.discardPreviewer()
        if self.level:
            self.previewRenderer = PreviewRenderer(self.level, alpha)
            self.previewRenderer.position = self.editor.renderer.position
            self.editor.addWorker(self.previewRenderer)
        else:
            self.editor.toolbar.selectTool(-1)

    @property
    def canRotateLevel(self):
        return not isinstance(self.level, (pymclevel.MCInfdevOldLevel, PocketWorld))

    def rotatedSelectionSize(self):
        if self.canRotateLevel:
            sizes = self.level.Blocks.shape
            return sizes[0], sizes[2], sizes[1]
        else:
            return self.level.size

    # ===========================================================================
    # def getSelectionRanges(self):
    #    return self.editor.selectionTool.selectionBox()
    #
    # ===========================================================================
    def getBlockAt(self):
        return None  # use level's blockAt

    def getReticleOrigin(self):
        # returns a new origin for the current selection, where the old origin is at the new selection's center.
        pos, direction = self.editor.blockFaceUnderCursor

        lev = self.editor.level
        size = self.rotatedSelectionSize()
        if not size:
            return
        if size[1] >= self.editor.level.Height:
            direction = (0, 1, 0)  # always use the upward face whenever we're splicing full-height pieces, to avoid "jitter"

        # print size; raise SystemExit
        if any(direction) and pos[1] >= 0:
            x, y, z = map(lambda p, s, d: p - s / 2 + s * d / 2 + (d > 0), pos, size, direction)
        else:
            x, y, z = map(lambda p, s: p - s / 2, pos, size)

        if self.chunkAlign:
            x = x & ~0xf
            z = z & ~0xf

        sy = size[1]
        if sy > lev.Height:  # don't snap really tall stuff to the height
            return Vector(x, y, z)

        if y + sy > lev.Height:
            y = lev.Height - sy
        if y < 0:
            y = 0

        if not isinstance(lev, pymclevel.MCInfdevOldLevel):
            sx = size[0]
            if x + sx > lev.Width:
                x = lev.Width - sx
            if x < 0:
                x = 0

            sz = size[2]
            if z + sz > lev.Length:
                z = lev.Length - sz
            if z < 0:
                z = 0

        return Vector(x, y, z)

    def getReticleBox(self):

        pos = self.getReticleOrigin()
        sizes = self.rotatedSelectionSize()

        if None is sizes:
            return

        return BoundingBox(pos, sizes)

    def getDestBox(self):
        selectionSize = self.rotatedSelectionSize()
        return BoundingBox(self.destPoint, selectionSize)

    def drawTerrainReticle(self):
        if self.level is None:
            return

        if self.destPoint != None:
            destPoint = self.destPoint
            if self.draggingFace is not None:
                # debugDrawPoint()
                destPoint = self.draggingOrigin()

            self.drawTerrainPreview(destPoint)
        else:
            self.drawTerrainPreview(self.getReticleBox().origin)

    draggingColor = (0.77, 1.0, 0.55, 0.05)

    def drawToolReticle(self):

        if self.level is None:
            return

        GL.glPolygonOffset(DepthOffset.CloneMarkers, DepthOffset.CloneMarkers)

        color = self.color
        if self.destPoint is not None:
            color = (self.color[0], self.color[1], self.color[2], 0.06)
            box = self.getDestBox()
            if self.draggingFace is not None:
                o = list(self.draggingOrigin())
                s = list(box.size)
                for i in range(3):
                    if i == self.draggingFace >> 1:
                        continue
                    o[i] -= 1000
                    s[i] += 2000
                guideBox = BoundingBox(o, s)

                color = self.draggingColor
                GL.glColor(1.0, 1.0, 1.0, 0.33)
                with gl.glEnable(GL.GL_BLEND, GL.GL_TEXTURE_2D, GL.GL_DEPTH_TEST):
                    self.editor.sixteenBlockTex.bind()
                    drawFace(guideBox, self.draggingFace ^ 1)
        else:
            box = self.getReticleBox()
            if box is None:
                return
        self.drawRepeatedCube(box, color)

        GL.glPolygonOffset(DepthOffset.CloneReticle, DepthOffset.CloneReticle)
        if self.destPoint:
            box = self.getDestBox()
            if self.draggingFace is not None:
                face = self.draggingFace
                box = BoundingBox(self.draggingOrigin(), box.size)
            face, point = self.boxFaceUnderCursor(box)
            if face is not None:
                GL.glEnable(GL.GL_BLEND)
                GL.glDisable(GL.GL_DEPTH_TEST)

                GL.glColor(*self.color)
                drawFace(box, face)
                GL.glDisable(GL.GL_BLEND)
                GL.glEnable(GL.GL_DEPTH_TEST)

    def drawRepeatedCube(self, box, color):
        # draw several cubes according to the repeat count
        # it's not really sensible to repeat a crane because the origin point is literally out of this world.
        delta = box.origin - self.selectionBox().origin

        for i in range(self.repeatCount):
            self.editor.drawConstructionCube(box, color)
            box = BoundingBox(box.origin + delta, box.size)

    def sourceLevel(self):
        return self.level

    @alertException
    def rotate(self, amount=1):
        if self.canRotateLevel:
            self.rotation += amount
            self.rotation &= 0x3
            for i in range(amount & 0x3):
                self.level.rotateLeft()

            self.previewRenderer.level = self.level

    @alertException
    def roll(self, amount=1):
        if self.canRotateLevel:
            for i in range(amount & 0x3):
                self.level.roll()

            self.previewRenderer.level = self.level

    @alertException
    def flip(self, amount=1):
        if self.canRotateLevel:
            for i in range(amount & 0x1):
                self.level.flipVertical()

            self.previewRenderer.level = self.level

    @alertException
    def mirror(self):
        if self.canRotateLevel:
            yaw = int(self.editor.mainViewport.yaw) % 360
            if (yaw >= 45 and yaw < 135) or (yaw > 225 and yaw <= 315):
                self.level.flipEastWest()
            else:
                self.level.flipNorthSouth()

            self.previewRenderer.level = self.level

    def option1(self):
        self.copyAir = not self.copyAir

    def option2(self):
        self.copyWater = not self.copyWater

    draggingFace = None
    draggingStartPoint = None

    def draggingOrigin(self):
        p = self._draggingOrigin()
        return p

    def _draggingOrigin(self):
        dragPos = map(int, map(numpy.floor, self.positionOnDraggingPlane()))
        delta = map(lambda s, e: e - int(numpy.floor(s)), self.draggingStartPoint, dragPos)

        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
            ad = map(abs, delta)
            midx = ad.index(max(ad))
            d = [0, 0, 0]
            d[midx] = delta[midx]
            dragY = self.draggingFace >> 1
            d[dragY] = delta[dragY]
            delta = d

        p = self.destPoint + delta
        if self.chunkAlign:
            p = [i // 16 * 16 for i in p]
        return Vector(*p)

    def positionOnDraggingPlane(self):
        pos = self.editor.mainViewport.cameraPosition
        dim = self.draggingFace >> 1
#        if key.get_mods() & KMOD_SHIFT:
#            dim = self.findBestTrackingPlane(self.draggingFace)
#
        distance = self.draggingStartPoint[dim] - pos[dim]
        distance += self.draggingY

        mouseVector = self.editor.mainViewport.mouseVector
        scale = distance / (mouseVector[dim] or 1)
        point = map(lambda a, b: a * scale + b, mouseVector, pos)
        return point

    draggingY = 0

    @alertException
    def mouseDown(self, evt, pos, direction):
        box = self.selectionBox()
        if not box:
            return
        self.draggingY = 0

        if self.destPoint is not None:
            if evt.num_clicks == 2:
                self.pickUp()
                return

            face, point = self.boxFaceUnderCursor(self.getDestBox())
            if face is not None:
                self.draggingFace = face
                self.draggingStartPoint = point

        else:
            self.destPoint = self.getReticleOrigin()

            if self.panel and self.panel.useOffsetInput:
                self.panel.offsetInput.setCoords(self.destPoint - box.origin)
            print "Destination: ", self.destPoint

    @alertException
    def mouseUp(self, evt, pos, direction):
        if self.draggingFace is not None:
            self.destPoint = self.draggingOrigin()

        self.draggingFace = None
        self.draggingStartPoint = None

    def increaseToolReach(self):
        if self.draggingFace is not None:
            d = (1, -1)[self.draggingFace & 1]
            if self.draggingFace >> 1 != 1:  # xxxxx y
                d = -d
            self.draggingY += d
            x, y, z = self.editor.mainViewport.cameraPosition
            pos = [x, y, z]
            pos[self.draggingFace >> 1] += d
            self.editor.mainViewport.cameraPosition = tuple(pos)

        else:
            self.cloneCameraDistance = self.editor._incrementReach(self.cloneCameraDistance)
        return True

    def decreaseToolReach(self):
        if self.draggingFace is not None:
            d = (1, -1)[self.draggingFace & 1]
            if self.draggingFace >> 1 != 1:  # xxxxx y
                d = -d

            self.draggingY -= d
            x, y, z = self.editor.mainViewport.cameraPosition
            pos = [x, y, z]
            pos[self.draggingFace >> 1] -= d
            self.editor.mainViewport.cameraPosition = tuple(pos)

        else:
            self.cloneCameraDistance = self.editor._decrementReach(self.cloneCameraDistance)
        return True

    def resetToolReach(self):
        if self.draggingFace is not None:
            x, y, z = self.editor.mainViewport.cameraPosition
            pos = [x, y, z]
            pos[self.draggingFace >> 1] += (1, -1)[self.draggingFace & 1] * -self.draggingY
            self.editor.mainViewport.cameraPosition = tuple(pos)
            self.draggingY = 0

        else:
            self.cloneCameraDistance = max(self.editor.defaultCameraToolDistance, self.safeToolDistance())

        return True

    def pickUp(self):
        if self.destPoint == None:
            return

        box = self.selectionBox()

        # pick up the object. reset the tool distance to the object's distance from the camera
        d = map(lambda a, b, c: abs(a - b - c / 2), self.editor.mainViewport.cameraPosition, self.destPoint, box.size)
        self.cloneCameraDistance = numpy.sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2])
        self.destPoint = None
        # self.panel.performButton.enabled = False
        print "Picked up"

    @alertException
    def confirm(self):
        destPoint = self.destPoint
        if destPoint is None:
            return

        sourceLevel = self.sourceLevel()
        sourceBox = sourceLevel.bounds

        destLevel = self.editor.level
        destVolume = BoundingBox(destPoint, sourceBox.size).volume

        op = CloneOperation(editor=self.editor,
                            sourceLevel=sourceLevel,
                            sourceBox=sourceBox,
                            originSourceBox=self.selectionBox(),
                            destLevel=destLevel,
                            destPoint=self.destPoint,
                            copyAir=self.copyAir,
                            copyWater=self.copyWater,
                            copyBiomes=self.copyBiomes,
                            repeatCount=self.repeatCount)

        self.editor.toolbar.selectTool(-1)  # deselect tool so that the clone tool's selection change doesn't update its schematic

        self.editor.addUnsavedEdit()

        self.editor.addOperation(op)

        dirtyBox = op.dirtyBox()
        if dirtyBox:
            self.editor.invalidateBox(dirtyBox)
        self.editor.renderer.invalidateChunkMarkers()

        self.editor.currentOperation = None

        self.destPoint = None
        self.level = None

    def discardPreviewer(self):
        if self.previewRenderer is None:
            return
        self.previewRenderer.stopWork()
        self.previewRenderer.discardAllChunks()
        self.editor.removeWorker(self.previewRenderer)
        self.previewRenderer = None


class ConstructionToolPanel (CloneToolPanel):
    useOffsetInput = False


class ConstructionTool(CloneTool):
    surfaceBuild = True
    toolIconName = "crane"
    tooltipText = "Import"

    panelClass = ConstructionToolPanel

    def toolEnabled(self):
        return True

    def selectionChanged(self):
        pass

    def updateSchematic(self):
        pass

    def quickNudge(self, nudge):
        return map(lambda x: x * 8, nudge)

    def __init__(self, *args):
        CloneTool.__init__(self, *args)
        self.level = None
        self.optionsPanel = None

    @property
    def statusText(self):
        if self.destPoint == None:
            return "Click to set this item down."

        return "Click and drag to reposition the item. Double-click to pick it up. Click Import or press ENTER to confirm."

    def showPanel(self):
        CloneTool.showPanel(self)
        self.panel.performButton.text = "Import"

    def toolReselected(self):
        self.toolSelected()

    #    def cancel(self):
#        print "Cancelled Clone"
#        self.level = None
#        super(ConstructionTool, self).cancel(self)
#

    def createTestBoard(self, anyBlock=True):
        if anyBlock:
            allBlocks = [self.editor.level.materials[a, b] for a in range(256) for b in range(16)]
            blockWidth = 64
        else:
            allBlocks = self.editor.level.materials.allBlocks
            blockWidth = 16
        blockCount = len(allBlocks)

        width = blockWidth * 3 + 1
        rows = blockCount // blockWidth + 1
        length = rows * 3 + 1
        height = 3

        schematic = pymclevel.MCSchematic((width, height, length), mats=self.editor.level.materials)
        schematic.Blocks[:, :, 0] = 1

        for i, block in enumerate(allBlocks):
            col = (i % blockWidth) * 3 + 1
            row = (i // blockWidth) * 3
            schematic.Blocks[col:col + 2, row:row + 2, 2] = block.ID
            schematic.Data[col:col + 2, row:row + 2, 2] = block.blockData

        return schematic

    def toolSelected(self):
        self.editor.mouseLookOff()

        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_ALT and mods & pygame.KMOD_SHIFT:
            self.loadLevel(self.createTestBoard())
            return

        self.editor.mouseLookOff()

        clipFilename = mcplatform.askOpenFile(title='Import a schematic or level...', schematics=True)
        # xxx mouthful
        if clipFilename:

            self.loadSchematic(clipFilename)

        print "Canceled"
        if self.level is None:
            print "No level selected."

            self.editor.toolbar.selectTool(-1)

        # CloneTool.toolSelected(self)

    originalLevelSize = (0, 0, 0)

    def loadSchematic(self, filename):
        """ actually loads a schematic or a level """

        try:
            level = pymclevel.fromFile(filename, readonly=True)
            self.loadLevel(level)
        except Exception, e:
            logging.warn(u"Unable to import file %s : %s", filename, e)

            traceback.print_exc()
            if filename:
                # self.editor.toolbar.selectTool(-1)
                alert(u"I don't know how to import this file: {0}.\n\nError: {1!r}".format(os.path.basename(filename), e))

            return

    @alertException
    def loadLevel(self, level):
        if level:
            self.level = level
            self.repeatCount = 1
            self.destPoint = None

            self.editor.currentTool = self  # because save window triggers loseFocus, which triggers tool.cancel... hmmmmmm

            self.cloneCameraDistance = self.safeToolDistance()

            self.chunkAlign = isinstance(self.level, pymclevel.MCInfdevOldLevel) and all(b % 16 == 0 for b in self.level.bounds.size)

            self.setupPreview()
            self.originalLevelSize = (self.level.Width, self.level.Height, self.level.Length)
            self.showPanel()
            return

    def selectionSize(self):
        if not self.level:
            return None
        return  self.originalLevelSize

    def selectionBox(self):
        if not self.level:
            return None
        return BoundingBox((0, 0, 0), self.selectionSize())

    def sourceLevel(self):
        return self.level

    def mouseDown(self, evt, pos, direction):
        # x,y,z = pos
        box = self.selectionBox()
        if not box:
            return

        CloneTool.mouseDown(self, evt, pos, direction)

########NEW FILE########
__FILENAME__ = editortool
from OpenGL import GL
import numpy
from depths import DepthOffset
from pymclevel import BoundingBox

class EditorTool(object):
    surfaceBuild = False
    panel = None
    optionsPanel = None
    toolIconName = None
    worldTooltipText = None
    previewRenderer = None

    tooltipText = "???"

    def levelChanged(self):
        """ called after a level change """
        pass

    @property
    def statusText(self):
        return ""

    @property
    def cameraDistance(self):
        return self.editor.cameraToolDistance

    def toolEnabled(self):
        return True

    def __init__(self, editor):
        self.editor = editor

    def toolReselected(self):
        pass

    def toolSelected(self):
        pass

    def drawTerrainReticle(self):
        pass

    def drawTerrainMarkers(self):
        pass

    def drawTerrainPreview(self, origin):
        if self.previewRenderer is None:
            return
        self.previewRenderer.origin = map(lambda a, b: a - b, origin, self.level.bounds.origin)

        GL.glPolygonOffset(DepthOffset.ClonePreview, DepthOffset.ClonePreview)
        GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
        self.previewRenderer.draw()
        GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)

    def rotate(self, amount=1):
        pass

    def roll(self, amount=1):
        pass

    def flip(self, amount=1):
        pass

    def mirror(self, amount=1):
        pass

    def swap(self, amount=1):
        pass

    def mouseDown(self, evt, pos, direction):
        '''pos is the coordinates of the block under the cursor,
        direction indicates which face is under it.  the tool performs
        its action on the specified block'''

        pass

    def mouseUp(self, evt, pos, direction):
        pass

    def mouseDrag(self, evt, pos, direction):
        pass

    def increaseToolReach(self):
        "Return True if the tool handles its own reach"
        return False

    def decreaseToolReach(self):
        "Return True if the tool handles its own reach"
        return False

    def resetToolReach(self):
        "Return True if the tool handles its own reach"
        return False

    def confirm(self):
        ''' called when user presses enter '''
        pass

    def cancel(self):
        '''cancel the current operation.  called when a different tool
        is picked, escape is pressed, or etc etc'''
        self.hidePanel()

    #        pass

    def findBestTrackingPlane(self, face):
        cv = list(self.editor.mainViewport.cameraVector)
        cv[face >> 1] = 0
        cv = map(abs, cv)

        return cv.index(max(cv))

    def drawToolReticle(self):

        '''get self.editor.blockFaceUnderCursor for pos and direction.
        pos is the coordinates of the block under the cursor,
        direction indicates which face is under it. draw something to
        let the user know where the tool is going to act.  e.g. a
        transparent block for the block placing tool.'''

        pass

    def drawToolMarkers(self):
        ''' draw any markers the tool wants to leave in the field
        while another tool is out.  e.g. the current selection for
        SelectionTool'''

        pass

    def selectionChanged(self):
        """ called when the selection changes due to nudge. other tools can be active. """
        pass

    edge_factor = 0.1

    def boxFaceUnderCursor(self, box):
        if self.editor.mainViewport.mouseMovesCamera:
            return None, None

        p0 = self.editor.mainViewport.cameraPosition
        normal = self.editor.mainViewport.mouseVector
        if normal is None:
            return None, None

        points = {}

#        glPointSize(5.0)
#        glColor(1.0, 1.0, 0.0, 1.0)
#        glBegin(GL_POINTS)

        for dim in range(3):
            dim1 = dim + 1
            dim2 = dim + 2
            dim1 %= 3
            dim2 %= 3

            def pointInBounds(point, x):
                return box.origin[x] <= point[x] <= box.maximum[x]

            neg = normal[dim] < 0

            for side in 0, 1:

                d = (box.maximum, box.origin)[side][dim] - p0[dim]

                if d >= 0 or (neg and d <= 0):
                    if normal[dim]:
                        scale = d / normal[dim]

                        point = map(lambda a, p: (a * scale + p), normal, p0)
    #                    glVertex3f(*point)

                        if pointInBounds(point, dim1) and pointInBounds(point, dim2):
                            points[dim * 2 + side] = point

#        glEnd()

        if not len(points):
            return None, None

        cp = self.editor.mainViewport.cameraPosition
        distances = dict((numpy.sum(map(lambda a, b: (b - a) ** 2, cp, point)), (face, point)) for face, point in points.iteritems())
        if not len(distances):
            return None, None

        # When holding alt, pick the face opposite the camera
        # if key.get_mods() & KMOD_ALT:
        #    minmax = max
        # else:

        face, point = distances[min(distances.iterkeys())]

        # if the point is near the edge of the face, and the edge is facing away,
        # return the away-facing face

        dim = face // 2
        side = face & 1

        dim1, dim2 = dim + 1, dim + 2
        dim1, dim2 = dim1 % 3, dim2 % 3
        cv = self.editor.mainViewport.cameraVector

        # determine if a click was within self.edge_factor of the edge of a selection box side. if so, click through
        # to the opposite side
        for d in dim1, dim2:
            edge_width = box.size[d] * self.edge_factor
            facenormal = [0, 0, 0]
            cameraBehind = False

            if point[d] - box.origin[d] < edge_width:
                facenormal[d] = -1
                cameraBehind = cp[d] - box.origin[d] > 0
            if point[d] - box.maximum[d] > -edge_width:
                facenormal[d] = 1
                cameraBehind = cp[d] - box.maximum[d] < 0

            if numpy.dot(facenormal, cv) > 0 or cameraBehind:
                # the face adjacent to the clicked edge faces away from the cam
                return distances[max(distances.iterkeys())]

        return face, point

    def selectionCorners(self):
        """ returns the positions of the two selection corners as a pair of 3-tuples, each ordered x,y,z """

        if(None != self.editor.selectionTool.bottomLeftPoint and
           None != self.editor.selectionTool.topRightPoint):

            return (self.editor.selectionTool.bottomLeftPoint,
                    self.editor.selectionTool.topRightPoint)

        return None

    def selectionBoxForCorners(self, p1, p2):
        ''' considers p1,p2 as the marked corners of a selection.
        returns a BoundingBox containing all the blocks within.'''

        if self.editor.level is None:
            return None

        p1, p2 = list(p1), list(p2)
        # d = [(a-b) for a,b in zip(p1,p2)]
        for i in range(3):
            if p1[i] > p2[i]:
                t = p2[i]
                p2[i] = p1[i]
                p1[i] = t

            p2[i] += 1

        size = map(lambda a, b: a - b, p2, p1)

        if p1[1] < 0:
            size[1] += p1[1]
            p1[1] = 0

        h = self.editor.level.Height
        if p1[1] >= h:
            p1[1] = h - 1
            size[1] = 1

        if p1[1] + size[1] >= h:
            size[1] = h - p1[1]

        return BoundingBox(p1, size)

    def selectionBox(self):
        ''' selection corners, ordered, with the greater point moved up one block for use as the ending value of an array slice '''
        c = self.selectionCorners()
        if c:
            return self.selectionBoxForCorners(*c)

        return None

    def selectionSize(self):
        ''' returns a tuple containing the size of the selection (x,y,z)'''
        c = self.selectionBox()
        if c is None:
            return None
        return c.size

    @property
    def maxBlocks(self):
        from leveleditor import Settings
        return Settings.blockBuffer.get() / 2  # assume block buffer in bytes

    def showPanel(self):
        pass

    def hidePanel(self):
        if self.panel and self.panel.parent:
            self.panel.parent.remove(self.panel)
            self.panel = None


########NEW FILE########
__FILENAME__ = fill
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""
from OpenGL import GL
import numpy
import pygame
from albow import Label, Button, Column
from depths import DepthOffset
from editortools.blockpicker import BlockPicker
from editortools.blockview import BlockButton
from editortools.editortool import EditorTool
from editortools.tooloptions import ToolOptions
from glbackground import Panel
from glutils import Texture
from mceutils import showProgress, CheckBoxLabel, alertException, setWindowCaption
from operation import Operation

import config
import pymclevel

FillSettings = config.Settings("Fill")
FillSettings.chooseBlockImmediately = FillSettings("Choose Block Immediately", True)


class BlockFillOperation(Operation):
    def __init__(self, editor, destLevel, destBox, blockInfo, blocksToReplace):
        super(BlockFillOperation, self).__init__(editor, destLevel)
        self.destBox = destBox
        self.blockInfo = blockInfo
        self.blocksToReplace = blocksToReplace

    def name(self):
        return "Fill with " + self.blockInfo.name

    def perform(self, recordUndo=True):
        if recordUndo:
            self.undoLevel = self.extractUndo(self.level, self.destBox)

        destBox = self.destBox
        if self.level.bounds == self.destBox:
            destBox = None

        fill = self.level.fillBlocksIter(destBox, self.blockInfo, blocksToReplace=self.blocksToReplace)
        showProgress("Replacing blocks...", fill, cancel=True)

    def bufferSize(self):
        return self.destBox.volume * 2

    def dirtyBox(self):
        return self.destBox


class FillToolPanel(Panel):

    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool
        replacing = tool.replacing

        self.blockButton = BlockButton(tool.editor.level.materials)
        self.blockButton.blockInfo = tool.blockInfo
        self.blockButton.action = self.pickFillBlock

        self.fillWithLabel = Label("Fill with:", width=self.blockButton.width, align="c")
        self.fillButton = Button("Fill", action=tool.confirm, width=self.blockButton.width)
        self.fillButton.tooltipText = "Shortcut: ENTER"

        rollkey = config.config.get("Keys", "Roll").upper()

        self.replaceLabel = replaceLabel = Label("Replace", width=self.blockButton.width)
        replaceLabel.mouse_down = lambda a: self.tool.toggleReplacing()
        replaceLabel.fg_color = (177, 177, 255, 255)
        # replaceLabelRow = Row( (Label(rollkey), replaceLabel) )
        replaceLabel.tooltipText = "Shortcut: {0}".format(rollkey)
        replaceLabel.align = "c"

        col = (self.fillWithLabel,
                self.blockButton,
                # swapRow,
                replaceLabel,
                # self.replaceBlockButton,
                self.fillButton)

        if replacing:
            self.fillWithLabel = Label("Find:", width=self.blockButton.width, align="c")

            self.replaceBlockButton = BlockButton(tool.editor.level.materials)
            self.replaceBlockButton.blockInfo = tool.replaceBlockInfo
            self.replaceBlockButton.action = self.pickReplaceBlock
            self.replaceLabel.text = "Replace with:"

            self.swapButton = Button("Swap", action=self.swapBlockTypes, width=self.blockButton.width)
            self.swapButton.fg_color = (255, 255, 255, 255)
            self.swapButton.highlight_color = (60, 255, 60, 255)
            swapkey = config.config.get("Keys", "Swap").upper()

            self.swapButton.tooltipText = "Shortcut: {0}".format(swapkey)

            self.fillButton = Button("Replace", action=tool.confirm, width=self.blockButton.width)
            self.fillButton.tooltipText = "Shortcut: ENTER"

            col = (self.fillWithLabel,
                    self.blockButton,
                    replaceLabel,
                    self.replaceBlockButton,
                    self.swapButton,
                    self.fillButton)

        col = Column(col)

        self.add(col)
        self.shrink_wrap()

    def swapBlockTypes(self):
        t = self.tool.replaceBlockInfo
        self.tool.replaceBlockInfo = self.tool.blockInfo
        self.tool.blockInfo = t

        self.replaceBlockButton.blockInfo = self.tool.replaceBlockInfo
        self.blockButton.blockInfo = self.tool.blockInfo  # xxx put this in a property

    def pickReplaceBlock(self):
        blockPicker = BlockPicker(self.tool.replaceBlockInfo, self.tool.editor.level.materials)
        if blockPicker.present():
            self.replaceBlockButton.blockInfo = self.tool.replaceBlockInfo = blockPicker.blockInfo

    def pickFillBlock(self):
        blockPicker = BlockPicker(self.tool.blockInfo, self.tool.editor.level.materials, allowWildcards=True)
        if blockPicker.present():
            self.tool.blockInfo = blockPicker.blockInfo


class FillToolOptions(ToolOptions):
    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool
        self.autoChooseCheckBox = CheckBoxLabel("Choose Block Immediately",
                                                ref=FillSettings.chooseBlockImmediately.propertyRef(),
                                                tooltipText="When the fill tool is chosen, prompt for a block type.")

        col = Column((Label("Fill Options"), self.autoChooseCheckBox, Button("OK", action=self.dismiss)))

        self.add(col)
        self.shrink_wrap()


class FillTool(EditorTool):
    toolIconName = "fill"
    _blockInfo = pymclevel.alphaMaterials.Stone
    replaceBlockInfo = pymclevel.alphaMaterials.Air
    tooltipText = "Fill and Replace\nRight-click for options"
    replacing = False

    def __init__(self, *args, **kw):
        EditorTool.__init__(self, *args, **kw)
        self.optionsPanel = FillToolOptions(self)

    @property
    def blockInfo(self):
        return self._blockInfo

    @blockInfo.setter
    def blockInfo(self, bt):
        self._blockInfo = bt
        if self.panel:
            self.panel.blockButton.blockInfo = bt

    def levelChanged(self):
        self.initTextures()

    def showPanel(self):
        if self.panel:
            self.panel.parent.remove(self.panel)

        panel = FillToolPanel(self)
        panel.centery = self.editor.centery
        panel.left = self.editor.left
        panel.anchor = "lwh"

        self.panel = panel
        self.editor.add(panel)

    def toolEnabled(self):
        return not (self.selectionBox() is None)

    def toolSelected(self):
        box = self.selectionBox()
        if None is box:
            return

        self.replacing = False
        self.showPanel()

        if self.chooseBlockImmediately:
            blockPicker = BlockPicker(self.blockInfo, self.editor.level.materials, allowWildcards=True)

            if blockPicker.present():
                self.blockInfo = blockPicker.blockInfo
                self.showPanel()

            else:
                self.editor.toolbar.selectTool(-1)

    chooseBlockImmediately = FillSettings.chooseBlockImmediately.configProperty()

    def toolReselected(self):
        self.showPanel()
        self.panel.pickFillBlock()

    def cancel(self):
        self.hidePanel()

    @alertException
    def confirm(self):
        box = self.selectionBox()
        if None is box:
            return

        with setWindowCaption("REPLACING - "):
            self.editor.freezeStatus("Replacing %0.1f million blocks" % (float(box.volume) / 1048576.,))

            if self.replacing:
                if self.blockInfo.wildcard:
                    print "Wildcard replace"
                    blocksToReplace = []
                    for i in range(16):
                        blocksToReplace.append(self.editor.level.materials.blockWithID(self.blockInfo.ID, i))
                else:
                    blocksToReplace = [self.blockInfo]

                op = BlockFillOperation(self.editor, self.editor.level, self.selectionBox(), self.replaceBlockInfo, blocksToReplace)

            else:
                blocksToReplace = []
                op = BlockFillOperation(self.editor, self.editor.level, self.selectionBox(), self.blockInfo, blocksToReplace)


        self.editor.addOperation(op)

        self.editor.addUnsavedEdit()
        self.editor.invalidateBox(box)
        self.editor.toolbar.selectTool(-1)

    def roll(self):
        self.toggleReplacing()

    def toggleReplacing(self):
        self.replacing = not self.replacing

        self.hidePanel()
        self.showPanel()
        if self.replacing:
            self.panel.pickReplaceBlock()

    @alertException
    def swap(self):
        if self.panel and self.replacing:
            self.panel.swapBlockTypes()

    def initTextures(self):

        terrainTexture = self.editor.level.materials.terrainTexture

        blockTextures = self.editor.level.materials.blockTextures[:, 0]

        if hasattr(self, 'blockTextures'):
            for tex in self.blockTextures.itervalues():
                tex.delete()

        self.blockTextures = {}

        pixelWidth = 512 if self.editor.level.materials.name in ("Pocket", "Alpha") else 256

        def blockTexFunc(type):
            def _func():
                s, t = blockTextures[type][0]
                if not hasattr(terrainTexture, "data"):
                    return
                w, h = terrainTexture.data.shape[:2]
                s = s * w / pixelWidth
                t = t * h / pixelWidth
                texData = numpy.array(terrainTexture.data[t:t + h / 16, s:s + w / 16])
                GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, w / 16, h / 16, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, texData)
            return _func

        for type in range(256):
            self.blockTextures[type] = Texture(blockTexFunc(type))

    def drawToolReticle(self):
        if pygame.key.get_mods() & pygame.KMOD_ALT:
            # eyedropper mode
            self.editor.drawWireCubeReticle(color=(0.2, 0.6, 0.9, 1.0))

    def drawToolMarkers(self):
        if self.editor.currentTool != self:
            return

        if self.panel and self.replacing:
            blockInfo = self.replaceBlockInfo
        else:
            blockInfo = self.blockInfo

        color = 1.0, 1.0, 1.0, 0.35
        if blockInfo:
            tex = self.blockTextures.get(blockInfo.ID, self.blockTextures[255]) # xxx

            # color = (1.5 - alpha, 1.0, 1.5 - alpha, alpha - 0.35)
            GL.glMatrixMode(GL.GL_TEXTURE)
            GL.glPushMatrix()
            GL.glScale(16., 16., 16.)

        else:
            tex = None
            # color = (1.0, 0.3, 0.3, alpha - 0.35)

        GL.glPolygonOffset(DepthOffset.FillMarkers, DepthOffset.FillMarkers)
        self.editor.drawConstructionCube(self.selectionBox(),
                                         color,
                                         texture=tex)

        if blockInfo:
            GL.glMatrixMode(GL.GL_TEXTURE)
            GL.glPopMatrix()

    @property
    def statusText(self):
        return "Press {hotkey} to choose a block. Press {R} to enter replace mode. Click Fill or press ENTER to confirm.".format(hotkey=self.hotkey, R=config.config.get("Keys", "Roll").upper())

    @property
    def worldTooltipText(self):
        if pygame.key.get_mods() & pygame.KMOD_ALT:
            try:
                if self.editor.blockFaceUnderCursor is None:
                    return
                pos = self.editor.blockFaceUnderCursor[0]
                blockID = self.editor.level.blockAt(*pos)
                blockdata = self.editor.level.blockDataAt(*pos)
                return "Click to use {0} ({1}:{2})".format(self.editor.level.materials.blockWithID(blockID, blockdata).name, blockID, blockdata)

            except Exception, e:
                return repr(e)

    def mouseUp(self, *args):
        return self.editor.selectionTool.mouseUp(*args)

    @alertException
    def mouseDown(self, evt, pos, dir):
        if pygame.key.get_mods() & pygame.KMOD_ALT:
            id = self.editor.level.blockAt(*pos)
            data = self.editor.level.blockDataAt(*pos)

            self.blockInfo = self.editor.level.materials.blockWithID(id, data)
        else:
            return self.editor.selectionTool.mouseDown(evt, pos, dir)

########NEW FILE########
__FILENAME__ = filter
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""
import collections
import os
import traceback
from albow import FloatField, IntField, AttrRef, Row, Label, Widget, TabPanel, CheckBox, Column, Button, TextFieldWrapped
from editortools.blockview import BlockButton
from editortools.editortool import EditorTool
from glbackground import Panel
from mceutils import ChoiceButton, alertException, setWindowCaption, showProgress
import mcplatform
from operation import Operation
from albow.dialogs import wrapped_label, alert
import pymclevel
from pymclevel import BoundingBox


def alertFilterException(func):
    def _func(*args, **kw):
        try:
            func(*args, **kw)
        except Exception, e:
            print traceback.format_exc()
            alert(u"Exception during filter operation. See console for details.\n\n{0}".format(e))

    return _func

def addNumField(page, optionName, val, min=None, max=None):
        if isinstance(val, float):
            ftype = FloatField
        else:
            ftype = IntField

        if min == max:
            min = None
            max = None

        field = ftype(value=val, width=100, min=min, max=max)
        page.optionDict[optionName] = AttrRef(field, 'value')

        row = Row([Label(optionName), field])
        return row

class FilterModuleOptions(Widget):
    is_gl_container = True

    def __init__(self, tool, module, *args, **kw):
        Widget.__init__(self, *args, **kw)
        self.tool = tool
        pages = TabPanel()
        pages.is_gl_container = True
        self.pages = pages
        self.optionDict = {}
        pageTabContents = []

        print "Creating options for ", module
        if hasattr(module, "inputs"):
            if isinstance(module.inputs, list):
                for tabData in module.inputs:
                    title, page, pageRect = self.makeTabPage(self.tool, tabData)
                    pages.add_page(title, page)
                    pages.set_rect(pageRect.union(pages._rect))
            elif isinstance(module.inputs, tuple):
                title, page, pageRect = self.makeTabPage(self.tool, module.inputs)
                pages.add_page(title, page)
                pages.set_rect(pageRect)
        else:
            self.size = (0, 0)

        pages.shrink_wrap()
        self.add(pages)
        self.shrink_wrap()
        if len(pages.pages):
            if(pages.current_page != None):
                pages.show_page(pages.current_page)
            else:
                pages.show_page(pages.pages[0])

        for eachPage in pages.pages:
            self.optionDict = dict(self.optionDict.items() + eachPage.optionDict.items())

    def makeTabPage(self, tool, inputs):
        page = Widget()
        page.is_gl_container = True
        rows = []
        cols = []
        height = 0
        max_height = 550
        page.optionDict = {}
        page.tool = tool
        title = "Tab"

        for optionName, optionType in inputs:
            if isinstance(optionType, tuple):
                if isinstance(optionType[0], (int, long, float)):
                    if len(optionType) > 2:
                        val, min, max = optionType
                    elif len(optionType) == 2:
                        min, max = optionType
                        val = min

                    rows.append(addNumField(page, optionName, val, min, max))

                if isinstance(optionType[0], (str, unicode)):
                    isChoiceButton = False

                    if optionType[0] == "string":
                        kwds = []
                        wid = None
                        lin = None
                        val = None
                        for keyword in optionType:
                            if isinstance(keyword, (str, unicode)) and keyword != "string":
                                kwds.append(keyword)
                        for keyword in kwds:
                            splitWord = keyword.split('=')
                            if len(splitWord) > 1:
                                v = None
                                key = None

                                try:
                                    v = int(splitWord[1])
                                except:
                                    pass

                                key = splitWord[0]
                                if v is not None:
                                    if key == "lines":
                                        lin = v
                                    elif key == "width":
                                        wid = v
                                else:
                                    if key == "value":
                                        val = splitWord[1]

                        if lin is None:
                            lin = 1
                        if val is None:
                            val = "Input String Here"
                        if wid is None:
                            wid = 200

                        field = TextFieldWrapped(value=val, width=wid,lines=lin)
                        page.optionDict[optionName] = AttrRef(field, 'value')

                        row = Row((Label(optionName), field))
                        rows.append(row)
                    else:
                        isChoiceButton = True

                    if isChoiceButton:
                        choiceButton = ChoiceButton(map(str, optionType))
                        page.optionDict[optionName] = AttrRef(choiceButton, 'selectedChoice')

                        rows.append(Row((Label(optionName), choiceButton)))

            elif isinstance(optionType, bool):
                cbox = CheckBox(value=optionType)
                page.optionDict[optionName] = AttrRef(cbox, 'value')

                row = Row((Label(optionName), cbox))
                rows.append(row)

            elif isinstance(optionType, (int, float)):
                rows.append(addNumField(self, optionName, optionType))

            elif optionType == "blocktype" or isinstance(optionType, pymclevel.materials.Block):
                blockButton = BlockButton(tool.editor.level.materials)
                if isinstance(optionType, pymclevel.materials.Block):
                    blockButton.blockInfo = optionType

                row = Column((Label(optionName), blockButton))
                page.optionDict[optionName] = AttrRef(blockButton, 'blockInfo')

                rows.append(row)
            elif optionType == "label":
                rows.append(wrapped_label(optionName, 50))

            elif optionType == "string":
                field = TextFieldWrapped(value="Input String Here", width=200, lines=1)
                page.optionDict[optionName] = AttrRef(field, 'value')

                row = Row((Label(optionName), field))
                rows.append(row)

            elif optionType == "title":
                title = optionName

            else:
                raise ValueError(("Unknown option type", optionType))

        height = sum(r.height for r in rows)

        if height > max_height:
            h = 0
            for i, r in enumerate(rows):
                h += r.height
                if h > height / 2:
                    break

            cols.append(Column(rows[:i]))
            rows = rows[i:]
        #cols.append(Column(rows))

        if len(rows):
            cols.append(Column(rows))

        if len(cols):
            page.add(Row(cols))
        page.shrink_wrap()

        return (title, page, page._rect)

    @property
    def options(self):
        return dict((k, v.get()) for k, v in self.optionDict.iteritems())

    @options.setter
    def options(self, val):
        for k in val:
            if k in self.optionDict:
                self.optionDict[k].set(val[k])


class FilterToolPanel(Panel):
    def __init__(self, tool):
        Panel.__init__(self)

        self.savedOptions = {}

        self.tool = tool
        self.selectedFilterName = None
        if len(self.tool.filterModules):
            self.reload()

    def reload(self):
        for i in list(self.subwidgets):
            self.remove(i)

        tool = self.tool

        if len(tool.filterModules) is 0:
            self.add(Label("No filter modules found!"))
            self.shrink_wrap()
            return

        if self.selectedFilterName is None or self.selectedFilterName not in tool.filterNames:
            self.selectedFilterName = tool.filterNames[0]

        self.filterOptionsPanel = None
        while self.filterOptionsPanel is None:
            module = self.tool.filterModules[self.selectedFilterName]
            try:
                self.filterOptionsPanel = FilterModuleOptions(self.tool, module)
            except Exception, e:
                alert("Error creating filter inputs for {0}: {1}".format(module, e))
                traceback.print_exc()
                self.tool.filterModules.pop(self.selectedFilterName)
                self.selectedFilterName = tool.filterNames[0]

            if len(tool.filterNames) == 0:
                raise ValueError("No filters loaded!")

        self.filterSelect = ChoiceButton(tool.filterNames, choose=self.filterChanged)
        self.filterSelect.selectedChoice = self.selectedFilterName

        self.confirmButton = Button("Filter", action=self.tool.confirm)

        filterLabel = Label("Filter:", fg_color=(177, 177, 255, 255))
        filterLabel.mouse_down = lambda x: mcplatform.platform_open(mcplatform.filtersDir)
        filterLabel.tooltipText = "Click to open filters folder"
        filterSelectRow = Row((filterLabel, self.filterSelect))

        self.add(Column((filterSelectRow, self.filterOptionsPanel, self.confirmButton)))

        self.shrink_wrap()
        if self.parent:
            self.centery = self.parent.centery

        if self.selectedFilterName in self.savedOptions:
            self.filterOptionsPanel.options = self.savedOptions[self.selectedFilterName]

    def filterChanged(self):
        self.saveOptions()
        self.selectedFilterName = self.filterSelect.selectedChoice
        self.reload()

    filterOptionsPanel = None

    def saveOptions(self):
        if self.filterOptionsPanel:
            self.savedOptions[self.selectedFilterName] = self.filterOptionsPanel.options


class FilterOperation(Operation):
    def __init__(self, editor, level, box, filter, options):
        super(FilterOperation, self).__init__(editor, level)
        self.box = box
        self.filter = filter
        self.options = options

    def perform(self, recordUndo=True):
        if recordUndo:
            self.undoLevel = self.extractUndo(self.level, self.box)

        self.filter.perform(self.level, BoundingBox(self.box), self.options)

        pass

    def dirtyBox(self):
        return self.box


class FilterTool(EditorTool):
    tooltipText = "Filter"
    toolIconName = "filter"

    def __init__(self, editor):
        EditorTool.__init__(self, editor)

        self.filterModules = {}

        self.panel = FilterToolPanel(self)

    @property
    def statusText(self):
        return "Choose a filter, then click Filter or press ENTER to apply it."

    def toolEnabled(self):
        return not (self.selectionBox() is None)

    def toolSelected(self):
        self.showPanel()

    @alertException
    def showPanel(self):
        if self.panel.parent:
            self.editor.remove(self.panel)

        self.reloadFilters()

        #self.panel = FilterToolPanel(self)
        self.panel.reload()

        self.panel.left = self.editor.left
        self.panel.centery = self.editor.centery

        self.editor.add(self.panel)

    def hidePanel(self):
        self.panel.saveOptions()
        if self.panel.parent:
            self.panel.parent.remove(self.panel)

    def reloadFilters(self):
        filterDir = mcplatform.filtersDir
        filterFiles = os.listdir(filterDir)
        filterPyfiles = filter(lambda x: x.endswith(".py"), filterFiles)

        def tryImport(name):
            try:
                return __import__(name)
            except Exception, e:
                print traceback.format_exc()
                alert(u"Exception while importing filter module {}. See console for details.\n\n{}".format(name, e))
                return object()

        filterModules = (tryImport(x[:-3]) for x in filterPyfiles)
        filterModules = filter(lambda module: hasattr(module, "perform"), filterModules)

        self.filterModules = collections.OrderedDict(sorted((self.moduleDisplayName(x), x) for x in filterModules))
        for m in self.filterModules.itervalues():
            try:
                reload(m)
            except Exception, e:
                print traceback.format_exc()
                alert(u"Exception while reloading filter module {}. Using previously loaded module. See console for details.\n\n{}".format(m.__file__, e))

    @property
    def filterNames(self):
        return [self.moduleDisplayName(module) for module in self.filterModules.itervalues()]

    def moduleDisplayName(self, module):
        return module.displayName if hasattr(module, 'displayName') else module.__name__.capitalize()

    @alertFilterException
    def confirm(self):

        with setWindowCaption("APPLYING FILTER - "):
            filterModule = self.filterModules[self.panel.filterSelect.selectedChoice]

            op = FilterOperation(self.editor, self.editor.level, self.selectionBox(), filterModule, self.panel.filterOptionsPanel.options)

            self.editor.level.showProgress = showProgress

            self.editor.addOperation(op)
            self.editor.addUnsavedEdit()

            self.editor.invalidateBox(self.selectionBox())

########NEW FILE########
__FILENAME__ = nudgebutton
from numpy.core.umath import absolute
from pygame import key
from albow import Label
from pymclevel.box import Vector
import config
from glbackground import GLBackground

class NudgeButton(GLBackground):
    """ A button that captures movement keys while pressed and sends them to a listener as nudge events.
    Poorly planned. """

    is_gl_container = True

    def __init__(self):
        GLBackground.__init__(self)
        nudgeLabel = Label("Nudge", margin=8)

        self.add(nudgeLabel)
        self.shrink_wrap()

        # tooltipBacking = Panel()
        # tooltipBacking.bg_color = (0, 0, 0, 0.6)
        keys = [config.config.get("Keys", k).upper() for k in ("Forward", "Back", "Left", "Right", "Up", "Down")]

        nudgeLabel.tooltipText = "Click and hold.  While holding, use the movement keys ({0}{1}{2}{3}{4}{5}) to nudge. Hold SHIFT to nudge faster.".format(*keys)
        # tooltipBacking.shrink_wrap()

    def mouse_down(self, event):
        self.focus()

    def mouse_up(self, event):
        self.get_root().mcedit.editor.focus_switch = None  # xxxx restore focus to editor better

    def key_down(self, evt):
        keyname = key.name(evt.key)
        if keyname == config.config.get("Keys", "Up"):
            self.nudge(Vector(0, 1, 0))
        if keyname == config.config.get("Keys", "Down"):
            self.nudge(Vector(0, -1, 0))

        Z = self.get_root().mcedit.editor.mainViewport.cameraVector  # xxx mouthful
        absZ = map(abs, Z)
        if absZ[0] < absZ[2]:
            forward = (0, 0, (-1 if Z[2] < 0 else 1))
        else:
            forward = ((-1 if Z[0] < 0 else 1), 0, 0)

        back = map(int.__neg__, forward)
        left = forward[2], forward[1], -forward[0]
        right = map(int.__neg__, left)

        if keyname == config.config.get("Keys", "Forward"):
            self.nudge(Vector(*forward))
        if keyname == config.config.get("Keys", "Back"):
            self.nudge(Vector(*back))
        if keyname == config.config.get("Keys", "Left"):
            self.nudge(Vector(*left))
        if keyname == config.config.get("Keys", "Right"):
            self.nudge(Vector(*right))

########NEW FILE########
__FILENAME__ = operation
import atexit
import os
import shutil
import tempfile
import albow
from pymclevel import BoundingBox
import numpy
from albow.root import Cancel
import pymclevel
from mceutils import showProgress
from pymclevel.mclevelbase import exhaust

undo_folder = os.path.join(tempfile.gettempdir(), "mcedit_undo", str(os.getpid()))

def mkundotemp():
    if not os.path.exists(undo_folder):
        os.makedirs(undo_folder)

    return tempfile.mkdtemp("mceditundo", dir=undo_folder)

atexit.register(shutil.rmtree, undo_folder, True)

class Operation(object):
    changedLevel = True
    undoLevel = None

    def __init__(self, editor, level):
        self.editor = editor
        self.level = level

    def extractUndo(self, level, box):
        if isinstance(level, pymclevel.MCInfdevOldLevel):
            return self.extractUndoChunks(level, box.chunkPositions, box.chunkCount)
        else:
            return self.extractUndoSchematic(level, box)

    def extractUndoChunks(self, level, chunks, chunkCount = None):
        if not isinstance(level, pymclevel.MCInfdevOldLevel):
            chunks = numpy.array(list(chunks))
            mincx, mincz = numpy.min(chunks, 0)
            maxcx, maxcz = numpy.max(chunks, 0)
            box = BoundingBox((mincx << 4, 0, mincz << 4), (maxcx << 4, level.Height, maxcz << 4))

            return self.extractUndoSchematic(level, box)

        undoLevel = pymclevel.MCInfdevOldLevel(mkundotemp(), create=True)
        if not chunkCount:
            try:
                chunkCount = len(chunks)
            except TypeError:
                chunkCount = -1

        def _extractUndo():
            yield 0, 0, "Recording undo..."
            for i, (cx, cz) in enumerate(chunks):
                undoLevel.copyChunkFrom(level, cx, cz)
                yield i, chunkCount, "Copying chunk %s..." % ((cx, cz),)
            undoLevel.saveInPlace()

        if chunkCount > 25 or chunkCount < 1:
            if "Canceled" == showProgress("Recording undo...", _extractUndo(), cancel=True):
                if albow.ask("Continue with undo disabled?", ["Continue", "Cancel"]) == "Cancel":
                    raise Cancel
                else:
                    return None
        else:
            exhaust(_extractUndo())

        return undoLevel

    def extractUndoSchematic(self, level, box):
        if box.volume > 131072:
            sch = showProgress("Recording undo...", level.extractZipSchematicIter(box), cancel=True)
        else:
            sch = level.extractZipSchematic(box)
        if sch == "Cancel":
            raise Cancel
        if sch:
            sch.sourcePoint = box.origin

        return sch


    # represents a single undoable operation
    def perform(self, recordUndo=True):
        " Perform the operation. Record undo information if recordUndo"

    def undo(self):
        """ Undo the operation. Ought to leave the Operation in a state where it can be performed again.
            Default implementation copies all chunks in undoLevel back into level. Non-chunk-based operations
            should override this."""

        if self.undoLevel:

            def _undo():
                yield 0, 0, "Undoing..."
                if hasattr(self.level, 'copyChunkFrom'):
                    for i, (cx, cz) in enumerate(self.undoLevel.allChunks):
                        self.level.copyChunkFrom(self.undoLevel, cx, cz)
                        yield i, self.undoLevel.chunkCount, "Copying chunk %s..." % ((cx, cz),)
                else:
                    for i in self.level.copyBlocksFromIter(self.undoLevel, self.undoLevel.bounds, self.undoLevel.sourcePoint, biomes=True):
                        yield i, self.undoLevel.chunkCount, "Copying..."

            if self.undoLevel.chunkCount > 25:
                showProgress("Undoing...", _undo())
            else:
                exhaust(_undo())

            self.editor.invalidateChunks(self.undoLevel.allChunks)


    def dirtyBox(self):
        """ The region modified by the operation.
        Return None to indicate no blocks were changed.
        """
        return None

########NEW FILE########
__FILENAME__ = player
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""
from OpenGL import GL
import numpy
from albow import TableView, TableColumn, Label, Button, Column, CheckBox, AttrRef, Row, ask, alert
import config
from editortools.editortool import EditorTool
from editortools.tooloptions import ToolOptions
from glbackground import Panel
from glutils import DisplayList
from mceutils import loadPNGTexture, alertException, drawTerrainCuttingWire, drawCube
from operation import Operation
import pymclevel
from pymclevel.box import BoundingBox, FloatBox
import logging
log = logging.getLogger(__name__)



class PlayerMoveOperation(Operation):
    undoPos = None

    def __init__(self, tool, pos, player="Player", yp=(None, None)):
        super(PlayerMoveOperation, self).__init__(tool.editor, tool.editor.level)
        self.tool = tool
        self.pos = pos
        self.player = player
        self.yp = yp

    def perform(self, recordUndo=True):
        try:
            level = self.tool.editor.level
            try:
                self.undoPos = level.getPlayerPosition(self.player)
                self.undoDim = level.getPlayerDimension(self.player)
                self.undoYP = level.getPlayerOrientation(self.player)
            except Exception, e:
                log.info("Couldn't get player position! ({0!r})".format(e))

            yaw, pitch = self.yp
            if yaw is not None and pitch is not None:
                level.setPlayerOrientation((yaw, pitch), self.player)
            level.setPlayerPosition(self.pos, self.player)
            level.setPlayerDimension(level.dimNo, self.player)
            self.tool.markerList.invalidate()

        except pymclevel.PlayerNotFound, e:
            print "Player move failed: ", e

    def undo(self):
        if not (self.undoPos is None):
            level = self.tool.editor.level
            level.setPlayerPosition(self.undoPos, self.player)
            level.setPlayerDimension(self.undoDim, self.player)
            level.setPlayerOrientation(self.undoYP, self.player)
            self.tool.markerList.invalidate()

    def bufferSize(self):
        return 20


class SpawnPositionInvalid(Exception):
    pass


def okayAt63(level, pos):
    """blocks 63 or 64 must be occupied"""
    return level.blockAt(pos[0], 63, pos[2]) != 0 or level.blockAt(pos[0], 64, pos[2]) != 0


def okayAboveSpawn(level, pos):
    """3 blocks above spawn must be open"""
    return not any([level.blockAt(pos[0], pos[1] + i, pos[2]) for i in range(1, 4)])


def positionValid(level, pos):
    try:
        return okayAt63(level, pos) and okayAboveSpawn(level, pos)
    except EnvironmentError:
        return False


class PlayerSpawnMoveOperation(Operation):
    undoPos = None

    def __init__(self, tool, pos):
        self.tool, self.pos = tool, pos

    def perform(self, recordUndo=True):
        level = self.tool.editor.level
        if isinstance(level, pymclevel.MCInfdevOldLevel):
            if not positionValid(level, self.pos):
                if SpawnSettings.spawnProtection.get():
                    raise SpawnPositionInvalid("You cannot have two air blocks at Y=63 and Y=64 in your spawn point's column. Additionally, you cannot have a solid block in the three blocks above your spawn point. It's weird, I know.")

        self.undoPos = level.playerSpawnPosition()
        level.setPlayerSpawnPosition(self.pos)
        self.tool.markerList.invalidate()

    def undo(self):
        if self.undoPos is not None:
            level = self.tool.editor.level
            level.setPlayerSpawnPosition(self.undoPos)
            self.tool.markerList.invalidate()


class PlayerPositionPanel(Panel):
    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool
        level = tool.editor.level
        if hasattr(level, 'players'):
            players = level.players or ["[No players]"]
        else:
            players = ["Player"]
        self.players = players
        tableview = TableView(columns=[
            TableColumn("Player Name", 200),
        ])
        tableview.index = 0
        tableview.num_rows = lambda: len(players)
        tableview.row_data = lambda i: (players[i],)
        tableview.row_is_selected = lambda x: x == tableview.index
        tableview.zebra_color = (0, 0, 0, 48)

        def selectTableRow(i, evt):
            tableview.index = i

        tableview.click_row = selectTableRow
        self.table = tableview
        l = Label("Player: ")
        col = [l, tableview]

        gotoButton = Button("Goto Player", action=self.tool.gotoPlayer)
        gotoCameraButton = Button("Goto Player's View", action=self.tool.gotoPlayerCamera)
        moveButton = Button("Move Player", action=self.tool.movePlayer)
        moveToCameraButton = Button("Align Player to Camera", action=self.tool.movePlayerToCamera)
        col.extend([gotoButton, gotoCameraButton, moveButton, moveToCameraButton])

        col = Column(col)
        self.add(col)
        self.shrink_wrap()

    @property
    def selectedPlayer(self):
        return self.players[self.table.index]


class PlayerPositionTool(EditorTool):
    surfaceBuild = True
    toolIconName = "player"
    tooltipText = "Move Player"
    movingPlayer = None

    def reloadTextures(self):
        self.charTex = loadPNGTexture('char.png')

    @alertException
    def movePlayer(self):
        self.movingPlayer = self.panel.selectedPlayer

    @alertException
    def movePlayerToCamera(self):
        player = self.panel.selectedPlayer
        pos = self.editor.mainViewport.cameraPosition
        y = self.editor.mainViewport.yaw
        p = self.editor.mainViewport.pitch
        d = self.editor.level.dimNo

        op = PlayerMoveOperation(self, pos, player, (y, p))
        self.movingPlayer = None
        op.perform()
        self.editor.addOperation(op)
        self.editor.addUnsavedEdit()

    def gotoPlayerCamera(self):
        player = self.panel.selectedPlayer
        try:
            pos = self.editor.level.getPlayerPosition(player)
            y, p = self.editor.level.getPlayerOrientation(player)
            self.editor.gotoDimension(self.editor.level.getPlayerDimension(player))

            self.editor.mainViewport.cameraPosition = pos
            self.editor.mainViewport.yaw = y
            self.editor.mainViewport.pitch = p
            self.editor.mainViewport.stopMoving()
            self.editor.mainViewport.invalidate()
        except pymclevel.PlayerNotFound:
            pass

    def gotoPlayer(self):
        player = self.panel.selectedPlayer

        try:
            if self.editor.mainViewport.pitch < 0:
                self.editor.mainViewport.pitch = -self.editor.mainViewport.pitch
                self.editor.mainViewport.cameraVector = self.editor.mainViewport._cameraVector()
            cv = self.editor.mainViewport.cameraVector

            pos = self.editor.level.getPlayerPosition(player)
            pos = map(lambda p, c: p - c * 5, pos, cv)
            self.editor.gotoDimension(self.editor.level.getPlayerDimension(player))

            self.editor.mainViewport.cameraPosition = pos
            self.editor.mainViewport.stopMoving()
        except pymclevel.PlayerNotFound:
            pass

    def __init__(self, *args):
        EditorTool.__init__(self, *args)
        self.reloadTextures()

        textureVertices = numpy.array(
            (
                24, 16,
                24, 8,
                32, 8,
                32, 16,

                8, 16,
                8, 8,
                16, 8,
                16, 16,

                24, 0,
                16, 0,
                16, 8,
                24, 8,

                16, 0,
                16, 8,
                8, 8,
                8, 0,

                8, 8,
                0, 8,
                0, 16,
                8, 16,

                16, 16,
                24, 16,
                24, 8,
                16, 8,

            ), dtype='f4')

        textureVertices.shape = (24, 2)

        textureVertices *= 4
        textureVertices[:, 1] *= 2

        self.texVerts = textureVertices

        self.markerList = DisplayList()

    panel = None

    def showPanel(self):
        if not self.panel:
            self.panel = PlayerPositionPanel(self)

        self.panel.left = self.editor.left
        self.panel.centery = self.editor.centery

        self.editor.add(self.panel)

    def hidePanel(self):
        if self.panel and self.panel.parent:
            self.panel.parent.remove(self.panel)
        self.panel = None

    def drawToolReticle(self):
        if self.movingPlayer is None:
            return

        pos, direction = self.editor.blockFaceUnderCursor
        pos = (pos[0], pos[1] + 2, pos[2])

        x, y, z = pos

        #x,y,z=map(lambda p,d: p+d, pos, direction)
        GL.glEnable(GL.GL_BLEND)
        GL.glColor(1.0, 1.0, 1.0, 0.5)
        self.drawCharacterHead(x + 0.5, y + 0.75, z + 0.5)
        GL.glDisable(GL.GL_BLEND)

        GL.glEnable(GL.GL_DEPTH_TEST)
        self.drawCharacterHead(x + 0.5, y + 0.75, z + 0.5)
        drawTerrainCuttingWire(BoundingBox((x, y, z), (1, 1, 1)))
        drawTerrainCuttingWire(BoundingBox((x, y - 1, z), (1, 1, 1)))
        #drawTerrainCuttingWire( BoundingBox((x,y-2,z), (1,1,1)) )
        GL.glDisable(GL.GL_DEPTH_TEST)

    markerLevel = None

    def drawToolMarkers(self):
        if self.markerLevel != self.editor.level:
            self.markerList.invalidate()
            self.markerLevel = self.editor.level
        self.markerList.call(self._drawToolMarkers)

    def _drawToolMarkers(self):
        GL.glColor(1.0, 1.0, 1.0, 0.5)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glMatrixMode(GL.GL_MODELVIEW)

        for player in self.editor.level.players:
            try:
                pos = self.editor.level.getPlayerPosition(player)
                yaw, pitch = self.editor.level.getPlayerOrientation(player)
                dim = self.editor.level.getPlayerDimension(player)
                if dim != self.editor.level.dimNo:
                    continue
                x, y, z = pos
                GL.glPushMatrix()
                GL.glTranslate(x, y, z)
                GL.glRotate(-yaw, 0, 1, 0)
                GL.glRotate(pitch, 1, 0, 0)
                GL.glColor(1, 1, 1, 1)
                self.drawCharacterHead(0, 0, 0)
                GL.glPopMatrix()
                #GL.glEnable(GL.GL_BLEND)
                drawTerrainCuttingWire(FloatBox((x - .5, y - .5, z - .5), (1, 1, 1)),
                                       c0=(0.3, 0.9, 0.7, 1.0),
                                       c1=(0, 0, 0, 0),
                                       )

                #GL.glDisable(GL.GL_BLEND)

            except Exception, e:
                print repr(e)
                continue

        GL.glDisable(GL.GL_DEPTH_TEST)

    def drawCharacterHead(self, x, y, z):
        GL.glEnable(GL.GL_CULL_FACE)
        origin = (x - 0.25, y - 0.25, z - 0.25)
        size = (0.5, 0.5, 0.5)
        box = FloatBox(origin, size)

        drawCube(box,
                 texture=self.charTex, textureVertices=self.texVerts)
        GL.glDisable(GL.GL_CULL_FACE)

    @property
    def statusText(self):
        if not self.panel:
            return ""
        player = self.panel.selectedPlayer
        if player == "Player":
            return "Click to move the player"

        return "Click to move the player \"{0}\"".format(player)

    @alertException
    def mouseDown(self, evt, pos, direction):
        if self.movingPlayer is None:
            return

        pos = (pos[0] + 0.5, pos[1] + 2.75, pos[2] + 0.5)

        op = PlayerMoveOperation(self, pos, self.movingPlayer)
        self.movingPlayer = None
        op.perform()
        self.editor.addOperation(op)
        self.editor.addUnsavedEdit()

    def levelChanged(self):
        self.markerList.invalidate()

    @alertException
    def toolSelected(self):
        self.showPanel()
        self.movingPlayer = None

    @alertException
    def toolReselected(self):
        if self.panel:
            self.gotoPlayer()


class PlayerSpawnPositionOptions(ToolOptions):
    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool
        self.spawnProtectionCheckBox = CheckBox(ref=AttrRef(tool, "spawnProtection"))
        self.spawnProtectionLabel = Label("Spawn Position Safety")
        self.spawnProtectionLabel.mouse_down = self.spawnProtectionCheckBox.mouse_down

        tooltipText = "Minecraft will randomly move your spawn point if you try to respawn in a column where there are no blocks at Y=63 and Y=64. Only uncheck this box if Minecraft is changed."
        self.spawnProtectionLabel.tooltipText = self.spawnProtectionCheckBox.tooltipText = tooltipText

        row = Row((self.spawnProtectionCheckBox, self.spawnProtectionLabel))
        col = Column((Label("Spawn Point Options"), row, Button("OK", action=self.dismiss)))

        self.add(col)
        self.shrink_wrap()

SpawnSettings = config.Settings("Spawn")
SpawnSettings.spawnProtection = SpawnSettings("Spawn Protection", True)


class PlayerSpawnPositionTool(PlayerPositionTool):
    surfaceBuild = True
    toolIconName = "playerspawn"
    tooltipText = "Move Spawn Point"

    def __init__(self, *args):
        PlayerPositionTool.__init__(self, *args)
        self.optionsPanel = PlayerSpawnPositionOptions(self)

    def toolEnabled(self):
        return self.editor.level.dimNo == 0

    def showPanel(self):
        self.panel = Panel()
        button = Button("Goto Spawn", action=self.gotoSpawn)
        self.panel.add(button)
        self.panel.shrink_wrap()

        self.panel.left = self.editor.left
        self.panel.centery = self.editor.centery
        self.editor.add(self.panel)

    def gotoSpawn(self):
        cv = self.editor.mainViewport.cameraVector

        pos = self.editor.level.playerSpawnPosition()
        pos = map(lambda p, c: p - c * 5, pos, cv)

        self.editor.mainViewport.cameraPosition = pos
        self.editor.mainViewport.stopMoving()

    @property
    def statusText(self):
        return "Click to set the spawn position."

    spawnProtection = SpawnSettings.spawnProtection.configProperty()

    def drawToolReticle(self):
        pos, direction = self.editor.blockFaceUnderCursor
        x, y, z = map(lambda p, d: p + d, pos, direction)

        color = (1.0, 1.0, 1.0, 0.5)
        if isinstance(self.editor.level, pymclevel.MCInfdevOldLevel) and self.spawnProtection:
            if not positionValid(self.editor.level, (x, y, z)):
                color = (1.0, 0.0, 0.0, 0.5)

        GL.glColor(*color)
        GL.glEnable(GL.GL_BLEND)
        self.drawCage(x, y, z)
        self.drawCharacterHead(x + 0.5, y + 0.5, z + 0.5)
        GL.glDisable(GL.GL_BLEND)

        GL.glEnable(GL.GL_DEPTH_TEST)
        self.drawCage(x, y, z)
        self.drawCharacterHead(x + 0.5, y + 0.5, z + 0.5)
        color2 = map(lambda a: a * 0.4, color)
        drawTerrainCuttingWire(BoundingBox((x, y, z), (1, 1, 1)), color2, color)
        GL.glDisable(GL.GL_DEPTH_TEST)

    def _drawToolMarkers(self):
        x, y, z = self.editor.level.playerSpawnPosition()
        GL.glColor(1.0, 1.0, 1.0, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        self.drawCage(x, y, z)
        self.drawCharacterHead(x + 0.5, y + 0.5 + 0.125 * numpy.sin(self.editor.frames * 0.05), z + 0.5)
        GL.glDisable(GL.GL_DEPTH_TEST)

    def drawCage(self, x, y, z):
        cageTexVerts = numpy.array(pymclevel.MCInfdevOldLevel.materials.blockTextures[52, 0])

        pixelScale = 0.5 if self.editor.level.materials.name in ("Pocket", "Alpha") else 1.0
        texSize = 16 * pixelScale
        cageTexVerts *= pixelScale

        cageTexVerts = numpy.array([((tx, ty), (tx + texSize, ty), (tx + texSize, ty + texSize), (tx, ty + texSize)) for (tx, ty) in cageTexVerts], dtype='float32')
        GL.glEnable(GL.GL_ALPHA_TEST)

        drawCube(BoundingBox((x, y, z), (1, 1, 1)), texture=pymclevel.alphaMaterials.terrainTexture, textureVertices=cageTexVerts)
        GL.glDisable(GL.GL_ALPHA_TEST)

    @alertException
    def mouseDown(self, evt, pos, direction):
        pos = map(lambda p, d: p + d, pos, direction)
        op = PlayerSpawnMoveOperation(self, pos)
        try:
            op.perform()

            self.editor.addOperation(op)
            self.editor.addUnsavedEdit()
            self.markerList.invalidate()

        except SpawnPositionInvalid, e:
            if "Okay" != ask(str(e), responses=["Okay", "Fix it for me!"]):
                level = self.editor.level
                status = ""
                if not okayAt63(level, pos):
                    level.setBlockAt(pos[0], 63, pos[2], 1)
                    status += "Block added at y=63.\n"

                if 59 < pos[1] < 63:
                    pos[1] = 63
                    status += "Spawn point moved upward to y=63.\n"

                if not okayAboveSpawn(level, pos):
                    if pos[1] > 63 or pos[1] < 59:
                        lpos = (pos[0], pos[1] - 1, pos[2])
                        if level.blockAt(*pos) == 0 and level.blockAt(*lpos) != 0 and okayAboveSpawn(level, lpos):
                            pos = lpos
                            status += "Spawn point shifted down by one block.\n"
                    if not okayAboveSpawn(level, pos):
                        for i in range(1, 4):
                            level.setBlockAt(pos[0], pos[1] + i, pos[2], 0)

                            status += "Blocks above spawn point cleared.\n"

                self.editor.invalidateChunks([(pos[0] // 16, pos[2] // 16)])
                op = PlayerSpawnMoveOperation(self, pos)
                try:
                    op.perform()
                except SpawnPositionInvalid, e:
                    alert(str(e))
                    return

                self.editor.addOperation(op)
                self.editor.addUnsavedEdit()
                self.markerList.invalidate()
                if len(status):
                    alert("Spawn point fixed. Changes: \n\n" + status)

    @alertException
    def toolReselected(self):
        self.gotoSpawn()

########NEW FILE########
__FILENAME__ = select
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""
import os
import traceback
from OpenGL import GL

from collections import defaultdict
import numpy
import pygame
from albow import Row, Label, Button, AttrRef, Column, ask
import config
from depths import DepthOffset
from editortools.editortool import EditorTool
from editortools.nudgebutton import NudgeButton
from editortools.tooloptions import ToolOptions
from glbackground import Panel
from mceutils import ChoiceButton, CheckBoxLabel, IntInputRow, alertException, drawCube, drawFace, drawTerrainCuttingWire, setWindowCaption, showProgress
import mcplatform
from operation import Operation
import pymclevel
from pymclevel.box import Vector, BoundingBox, FloatBox
from fill import  BlockFillOperation
import tempfile
from pymclevel import nbt

SelectSettings = config.Settings("Selection")
SelectSettings.showPreviousSelection = SelectSettings("Show Previous Selection", True)
SelectSettings.color = SelectSettings("Color", "teal")

ColorSettings = config.Settings("Selection Colors")
ColorSettings.defaultColors = {}


class ColorSetting(config.Setting):
    def __init__(self, section, name, dtype, default):
        super(ColorSetting, self).__init__(section, name, dtype, default)
        ColorSettings.defaultColors[name] = self

    def set(self, val):
        values = str(tuple(val))[1:-1]
        super(ColorSetting, self).set(values)

    def get(self):
        colorValues = super(ColorSetting, self).get()
        return parseValues(colorValues)
ColorSettings.Setting = ColorSetting


def parseValues(colorValues):
    if colorValues is None:
        return 1., 1., 1.

    try:
        values = colorValues.split(",")
        values = [(min(max(float(x), 0.0), 1.0)) for x in values]
    except:
        values = (1.0, 1.0, 1.0)

    return tuple(values)

ColorSettings("white", (1.0, 1.0, 1.0))

ColorSettings("blue", (0.75, 0.75, 1.0))
ColorSettings("green", (0.75, 1.0, 0.75))
ColorSettings("red", (1.0, 0.75, 0.75))

ColorSettings("teal", (0.75, 1.0, 1.0))
ColorSettings("pink", (1.0, 0.75, 1.0))
ColorSettings("yellow", (1.0, 1.0, 0.75))

ColorSettings("grey", (0.6, 0.6, 0.6))
ColorSettings("black", (0.0, 0.0, 0.0))


def GetSelectionColor(colorWord=None):
    if colorWord is None:
        colorWord = SelectSettings.color.get()

    colorValues = config.config.get("Selection Colors", colorWord)
    return parseValues(colorValues)


class SelectionToolOptions(ToolOptions):
    def updateColors(self):
        names = [name.lower() for (name, value) in config.config.items("Selection Colors")]
        self.colorPopupButton.choices = [name.capitalize() for name in names]

        color = SelectSettings.color.get()

        self.colorPopupButton.choiceIndex = names.index(color.lower())

    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool

        self.colorPopupButton = ChoiceButton([], choose=self.colorChanged)
        self.updateColors()

        colorRow = Row((Label("Color: ", align="r"), self.colorPopupButton))
        okButton = Button("OK", action=self.dismiss)
        showPreviousRow = CheckBoxLabel("Show Previous Selection", ref=AttrRef(tool, 'showPreviousSelection'))

        def set_colorvalue(ch):
            i = "RGB".index(ch)

            def _set(val):
                choice = self.colorPopupButton.selectedChoice
                values = GetSelectionColor(choice)
                values = values[:i] + (val / 255.0,) + values[i + 1:]
                setting = str(values)[1:-1]
                config.config.set("Selection Colors", choice, setting)
                self.colorChanged()

            return _set

        def get_colorvalue(ch):
            i = "RGB".index(ch)

            def _get():
                return int(GetSelectionColor()[i] * 255)
            return _get

        colorValuesInputs = [IntInputRow(ch + ":", get_value=get_colorvalue(ch),
                                              set_value=set_colorvalue(ch),
                                              min=0, max=255)
                             for ch in "RGB"]

        colorValuesRow = Row(colorValuesInputs)
        col = Column((Label("Selection Options"), colorRow, colorValuesRow, showPreviousRow, okButton))

        self.add(col)
        self.shrink_wrap()

    def colorChanged(self):
        SelectSettings.color.set(self.colorPopupButton.selectedChoice)
        self.tool.updateSelectionColor()


class SelectionToolPanel(Panel):
    def __init__(self, tool):
        Panel.__init__(self)
        self.tool = tool

        nudgeBlocksButton = NudgeButton()
        nudgeBlocksButton.nudge = tool.nudgeBlocks
        nudgeBlocksButton.bg_color = (0.3, 1.0, 0.3, 0.35)
        self.nudgeBlocksButton = nudgeBlocksButton

        nudgeSelectionButton = NudgeButton()
        nudgeSelectionButton.nudge = tool.nudgeSelection
        nudgeSelectionButton.bg_color = tool.selectionColor + (0.7,)

        deleteBlocksButton = Button("Delete Blocks", action=self.tool.deleteBlocks)
        deleteBlocksButton.tooltipText = "Fill the selection with Air. Shortcut: DELETE"
        deleteEntitiesButton = Button("Delete Entities", action=self.tool.deleteEntities)
        deleteEntitiesButton.tooltipText = "Remove all entities within the selection"
        # deleteTileEntitiesButton = Button("Delete TileEntities", action=self.tool.deleteTileEntities)
        analyzeButton = Button("Analyze", action=self.tool.analyzeSelection)
        analyzeButton.tooltipText = "Count the different blocks and entities in the selection and display the totals."
        cutButton = Button("Cut", action=self.tool.cutSelection)
        cutButton.tooltipText = "Take a copy of all blocks and entities within the selection, then delete everything within the selection. Shortcut: {0}-X".format(mcplatform.cmd_name)
        copyButton = Button("Copy", action=self.tool.copySelection)
        copyButton.tooltipText = "Take a copy of all blocks and entities within the selection. Shortcut: {0}-C".format(mcplatform.cmd_name)
        pasteButton = Button("Paste", action=self.tool.editor.pasteSelection)
        pasteButton.tooltipText = "Import the last item taken by Cut or Copy. Shortcut: {0}-V".format(mcplatform.cmd_name)
        exportButton = Button("Export", action=self.tool.exportSelection)
        exportButton.tooltipText = "Export the selection to a .schematic file. Shortcut: {0}-E".format(mcplatform.cmd_name)

        selectButton = Button("Select Chunks")
        selectButton.tooltipText = "Expand the selection to the edges of the chunks within"
        selectButton.action = tool.selectChunks
        selectButton.highlight_color = (0, 255, 0)

        deselectButton = Button("Deselect")
        deselectButton.tooltipText = "Remove the selection. Shortcut: {0}-D".format(mcplatform.cmd_name)
        deselectButton.action = tool.deselect
        deselectButton.highlight_color = (0, 255, 0)

        nudgeRow = Row((nudgeBlocksButton, nudgeSelectionButton))
        buttonsColumn = (
            nudgeRow,
            deselectButton,
            selectButton,
            deleteBlocksButton,
            deleteEntitiesButton,
            analyzeButton,
            cutButton,
            copyButton,
            pasteButton,
            exportButton,
        )

        buttonsColumn = Column(buttonsColumn)

        self.add(buttonsColumn)
        self.shrink_wrap()


class NudgeBlocksOperation(Operation):
    def __init__(self, editor, level, sourceBox, direction):
        super(NudgeBlocksOperation, self).__init__(editor, level)

        self.sourceBox = sourceBox
        self.destBox = BoundingBox(sourceBox.origin + direction, sourceBox.size)
        self.nudgeSelection = NudgeSelectionOperation(editor.selectionTool, direction)

    def dirtyBox(self):
        return self.sourceBox.union(self.destBox)

    def perform(self, recordUndo=True):
        level = self.editor.level
        tempSchematic = level.extractSchematic(self.sourceBox)
        if tempSchematic:
            dirtyBox = self.dirtyBox()
            if recordUndo:
                self.undoLevel = self.extractUndo(level, dirtyBox)

            level.fillBlocks(self.sourceBox, level.materials.Air)
            level.removeTileEntitiesInBox(self.sourceBox)
            level.removeTileEntitiesInBox(self.destBox)

            level.removeEntitiesInBox(self.sourceBox)
            level.removeEntitiesInBox(self.destBox)
            level.copyBlocksFrom(tempSchematic, tempSchematic.bounds, self.destBox.origin)
            self.editor.invalidateBox(dirtyBox)

            self.nudgeSelection.perform(recordUndo)

    def undo(self):
        super(NudgeBlocksOperation, self).undo()
        self.nudgeSelection.undo()


class SelectionTool(EditorTool):
    # selectionColor = (1.0, .9, .9)
    color = (0.7, 0., 0.7)
    surfaceBuild = False
    toolIconName = "selection"
    tooltipText = "Select\nRight-click for options"

    bottomLeftPoint = topRightPoint = None

    bottomLeftColor = (0., 0., 1.)
    bottomLeftSelectionColor = (0.75, 0.62, 1.0)

    topRightColor = (0.89, 0.89, 0.35)
    topRightSelectionColor = (1, 0.99, 0.65)

    nudgePanel = None

    def __init__(self, editor):
        self.editor = editor
        editor.selectionTool = self
        self.selectionPoint = None

        self.optionsPanel = SelectionToolOptions(self)

        self.updateSelectionColor()

    # --- Tooltips ---

    def describeBlockAt(self, pos):
        blockID = self.editor.level.blockAt(*pos)
        blockdata = self.editor.level.blockDataAt(*pos)
        text = "X: {pos[0]}\nY: {pos[1]}\nZ: {pos[2]}\n".format(pos=pos)
        text += "L: {0} S: {1}\n".format(self.editor.level.blockLightAt(*pos), self.editor.level.skylightAt(*pos))
        text += "{name} ({bid}:{bdata})\n".format(name=self.editor.level.materials.names[blockID][blockdata], bid=blockID, pos=pos, bdata=blockdata)
        t = self.editor.level.tileEntityAt(*pos)
        if t:
            text += "TileEntity:\n"
            try:
                text += "{id}: {pos}\n".format(id=t["id"].value, pos=[t[a].value for a in "xyz"])
            except Exception, e:
                text += repr(e)
            if "Items" in t and not pygame.key.get_mods() & pygame.KMOD_ALT:
                text += "--Items omitted. ALT to view. Double-click to edit.--\n"
                t = nbt.TAG_Compound(list(t.value))
                del t["Items"]

            text += str(t)

        return text

    @property
    def worldTooltipText(self):
        pos, face = self.editor.blockFaceUnderCursor
        if pos is None:
            return
        try:

            size = None
            box = self.selectionBoxInProgress()
            if box:
                size = "{s[0]} W x {s[2]} L x {s[1]} H".format(s=box.size)
                text = size
            if pygame.key.get_mods() & pygame.KMOD_ALT:
                if size:
                    return size
                elif self.dragResizeFace is not None:
                    return None
                else:

                    return self.describeBlockAt(pos)

                return text.strip()

            else:

                return self.worldTooltipForBlock(pos) or size

        except Exception, e:
            return repr(e)

    def worldTooltipForBlock(self, pos):

        x, y, z = pos
        cx, cz = x / 16, z / 16
        if isinstance(self.editor.level, pymclevel.MCInfdevOldLevel):

            if y == 0:
                try:
                    chunk = self.editor.level.getChunk(cx, cz)
                except pymclevel.ChunkNotPresent:
                    return "Chunk not present."
                if not chunk.HeightMap.any():
                    if self.editor.level.blockAt(x, y, z):
                        return "Chunk HeightMap is incorrect! Please relight this chunk as soon as possible!"
                    else:
                        return "Chunk is present and filled with air."

        block = self.editor.level.blockAt(*pos)
        if block in (pymclevel.alphaMaterials.Chest.ID,
                     pymclevel.alphaMaterials.Furnace.ID,
                     pymclevel.alphaMaterials.LitFurnace.ID,
                     pymclevel.alphaMaterials.Dispenser.ID):
            t = self.editor.level.tileEntityAt(*pos)
            if t:
                containerID = t["id"].value
                if "Items" in t:
                    items = t["Items"]
                    d = defaultdict(int)
                    for item in items:
                        if "id" in item and "Count" in item:
                            d[item["id"].value] += item["Count"].value

                    if len(d):
                        items = sorted((v, k) for (k, v) in d.iteritems())
                        try:
                            top = pymclevel.items.items.findItem(items[0][1]).name
                        except Exception, e:
                            top = repr(e)
                        return "{0} contains {len} items. (Mostly {top}) \n\nDouble-click to edit {0}.".format(containerID, len=len(d), top=top)
                    else:
                        return "Empty {0}. \n\nDouble-click to edit {0}.".format(containerID)
            else:
                return "Double-click to initialize the {0}.".format(pymclevel.alphaMaterials.names[block][0])
        if block == pymclevel.alphaMaterials.MonsterSpawner.ID:

            t = self.editor.level.tileEntityAt(*pos)
            if t:
                id = t["EntityId"].value
            else:
                id = "[Undefined]"

            return "{id} spawner. \n\nDouble-click to edit spawner.".format(id=id)

        if block in (pymclevel.alphaMaterials.Sign.ID,
                     pymclevel.alphaMaterials.WallSign.ID):
            t = self.editor.level.tileEntityAt(*pos)
            if t:
                signtext = u"\n".join(t["Text" + str(x)].value for x in range(1, 5))
            else:
                signtext = "Undefined"
            return "Sign text: \n" + signtext + "\n\n" + "Double-click to edit sign."

        absentTexture = (self.editor.level.materials.blockTextures[block, 0, 0] == pymclevel.materials.NOTEX).all()
        if absentTexture:
            return self.describeBlockAt(pos)

    @alertException
    def selectChunks(self):
        box = self.selectionBox()
        newBox = BoundingBox((box.mincx << 4, 0, box.mincz << 4), (box.maxcx - box.mincx << 4, self.editor.level.Height, box.maxcz - box.mincz << 4))
        self.editor.selectionTool.setSelection(newBox)

    def updateSelectionColor(self):

        self.selectionColor = GetSelectionColor()
        from albow import theme
        theme.root.sel_color = tuple(int(x * 112) for x in self.selectionColor)

    # --- Nudge functions ---

    @alertException
    def nudgeBlocks(self, dir):
        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
            dir = dir * (16, 16, 16)
        op = NudgeBlocksOperation(self.editor, self.editor.level, self.selectionBox(), dir)

        self.editor.addOperation(op)
        self.editor.addUnsavedEdit()

    def nudgeSelection(self, dir):
        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
            dir = dir * (16, 16, 16)

        points = self.getSelectionPoints()
        bounds = self.editor.level.bounds

        if not all((p + dir) in bounds for p in points):
            return

        op = NudgeSelectionOperation(self, dir)
        self.editor.addOperation(op)

    def nudgePoint(self, p, n):
        if self.selectionBox() is None:
            return
        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
            n = n * (16, 16, 16)
        self.setSelectionPoint(p, self.getSelectionPoint(p) + n)

    def nudgeBottomLeft(self, n):
        return self.nudgePoint(0, n)

    def nudgeTopRight(self, n):
        return self.nudgePoint(1, n)

    # --- Panel functions ---
    def sizeLabelText(self):
        size = self.selectionSize()
        if self.dragResizeFace is not None:
            size = self.draggingSelectionBox().size

        return "{0}W x {2}L x {1}H".format(*size)

    def showPanel(self):
        if self.selectionBox() is None:
            return

        if self.nudgePanel is None:
            self.nudgePanel = Panel()

            self.nudgePanel.bg_color = map(lambda x: x * 0.5, self.selectionColor) + [0.5, ]

            self.bottomLeftNudge = bottomLeftNudge = NudgeButton()
            bottomLeftNudge.nudge = self.nudgeBottomLeft
            bottomLeftNudge.anchor = "brwh"

            bottomLeftNudge.bg_color = self.bottomLeftColor + (0.33,)

            self.topRightNudge = topRightNudge = NudgeButton()
            topRightNudge.nudge = self.nudgeTopRight
            topRightNudge.anchor = "blwh"

            topRightNudge.bg_color = self.topRightColor + (0.33,)

            self.nudgeRow = Row((bottomLeftNudge, topRightNudge))
            self.nudgeRow.anchor = "blrh"
            self.nudgePanel.add(self.nudgeRow)

            self.editor.add(self.nudgePanel)

        if hasattr(self, 'sizeLabel'):
            self.nudgePanel.remove(self.sizeLabel)
        self.sizeLabel = Label(self.sizeLabelText())
        self.sizeLabel.anchor = "twh"
        self.sizeLabel.tooltipText = "{0:n} blocks".format(self.selectionBox().volume)

        # self.nudgePanelColumn = Column( (self.sizeLabel, self.nudgeRow) )
        self.nudgePanel.top = self.nudgePanel.left = 0

        self.nudgePanel.add(self.sizeLabel)
        self.nudgeRow.top = self.sizeLabel.bottom

        self.nudgePanel.shrink_wrap()
        self.sizeLabel.centerx = self.nudgePanel.centerx
        self.nudgeRow.centerx = self.nudgePanel.centerx

        self.nudgePanel.bottom = self.editor.toolbar.top
        self.nudgePanel.centerx = self.editor.centerx

        self.nudgePanel.anchor = "bwh"

        if self.panel is None and self.editor.currentTool in (self, None):
            if self.bottomLeftPoint is not None and self.topRightPoint is not None:
                self.panel = SelectionToolPanel(self)
                self.panel.left = self.editor.left
                self.panel.centery = self.editor.centery
                self.editor.add(self.panel)

    def hidePanel(self):
        self.editor.remove(self.panel)
        self.panel = None

    def hideNudgePanel(self):
        self.editor.remove(self.nudgePanel)
        self.nudgePanel = None

    selectionInProgress = False
    dragStartPoint = None

    # --- Event handlers ---

    def toolReselected(self):
        self.selectOtherCorner()

    def toolSelected(self):
        # if self.clearSelectionImmediately:
        #    self.setSelectionPoints(None)
        self.showPanel()

    def clampPos(self, pos):
        x, y, z = pos
        w, h, l = self.editor.level.Width, self.editor.level.Height, self.editor.level.Length

        if w > 0:
            if x >= w:
                x = w - 1
            if x < 0:
                x = 0
        if l > 0:
            if z >= l:
                z = l - 1
            if z < 0:
                z = 0

        if y >= h:
            y = h - 1
        if y < 0:
            y = 0

        pos = [x, y, z]
        return pos

    @property
    def currentCornerName(self):
        return ("Blue", "Yellow")[self.currentCorner]

    @property
    def statusText(self):
        # return "selectionInProgress {0} clickSelectionInProgress {1}".format(self.selectionInProgress, self.clickSelectionInProgress)
        if self.selectionInProgress:
            pd = self.editor.blockFaceUnderCursor
            if pd:
                p, d = pd
                if self.dragStartPoint == p:
                    if self.clickSelectionInProgress:

                        return "Click the mouse button again to place the {0} selection corner. Press {1} to switch corners.".format(self.currentCornerName, self.hotkey)
                    else:
                        return "Release the mouse button here to place the {0} selection corner. Press {1} to switch corners.".format(self.currentCornerName, self.hotkey)

            if self.clickSelectionInProgress:
                return "Click the mouse button again to place the other selection corner."

            return "Release the mouse button to finish the selection"

        return "Click or drag to make a selection. Drag the selection walls to resize. Click near the edge to drag the opposite wall.".format(self.currentCornerName, self.hotkey)

    clickSelectionInProgress = False

    def endSelection(self):
        self.selectionInProgress = False
        self.clickSelectionInProgress = False
        self.dragResizeFace = None
        self.dragStartPoint = None

    def cancel(self):
        self.endSelection()
        EditorTool.cancel(self)

    dragResizeFace = None
    dragResizeDimension = None
    dragResizePosition = None

    def mouseDown(self, evt, pos, direction):
        # self.selectNone()

        pos = self.clampPos(pos)
        if self.selectionBox() and not self.selectionInProgress:
            face, point = self.boxFaceUnderCursor(self.selectionBox())

            if face is not None:
                self.dragResizeFace = face
                self.dragResizeDimension = self.findBestTrackingPlane(face)

                # point = map(int, point)
                self.dragResizePosition = point[self.dragResizeDimension]

                return

        if self.selectionInProgress is False:
            self.dragStartPoint = pos
        self.selectionInProgress = True

    def mouseUp(self, evt, pos, direction):
        pos = self.clampPos(pos)
        if self.dragResizeFace is not None:
            box = self.selectionBox()
            if box is not None:
                o, m = self.selectionPointsFromDragResize()

                op = SelectionOperation(self, (o, m))
                self.editor.addOperation(op)

            self.dragResizeFace = None
            return

        if self.editor.viewMode == "Chunk":
            self.clickSelectionInProgress = True

        if self.dragStartPoint is None and not self.clickSelectionInProgress:
            return

        if self.dragStartPoint != pos or self.clickSelectionInProgress:
            op = SelectionOperation(self, (self.dragStartPoint, pos))
            self.editor.addOperation(op)
            self.selectionInProgress = False
            self.currentCorner = 1
            self.clickSelectionInProgress = False
            self.dragStartPoint = None

        else:
            points = self.getSelectionPoints()
            if not all(points):
                points = (pos, pos)  # set both points on the first click
            else:
                points[self.currentCorner] = pos
            if not self.clickSelectionInProgress:
                self.clickSelectionInProgress = True
            else:
                op = SelectionOperation(self, points)
                self.editor.addOperation(op)

                self.selectOtherCorner()
                self.selectionInProgress = False
                self.clickSelectionInProgress = False

        if self.chunkMode:
            self.editor.selectionToChunks(remove=evt.alt, add=evt.shift)
            self.editor.toolbar.selectTool(8)

    @property
    def chunkMode(self):
        return self.editor.viewMode == "Chunk" or self.editor.currentTool is self.editor.toolbar.tools[8]

    def selectionBoxInProgress(self):
        if self.editor.blockFaceUnderCursor is None:
            return
        pos = self.editor.blockFaceUnderCursor[0]
        if self.selectionInProgress or self.clickSelectionInProgress:
            return self.selectionBoxForCorners(pos, self.dragStartPoint)

# requires a selection
    def dragResizePoint(self):
        # returns a point representing the intersection between the mouse ray
        # and an imaginary plane perpendicular to the dragged face

        pos = self.editor.mainViewport.cameraPosition
        dim = self.dragResizeDimension
        distance = self.dragResizePosition - pos[dim]

        mouseVector = self.editor.mainViewport.mouseVector
        scale = distance / (mouseVector[dim] or 0.0001)
        point = map(lambda a, b: a * scale + b, mouseVector, pos)
        return point

    def draggingSelectionBox(self):
        p1, p2 = self.selectionPointsFromDragResize()
        box = self.selectionBoxForCorners(p1, p2)
        return box

    def selectionPointsFromDragResize(self):
        point = self.dragResizePoint()
#        glColor(1.0, 1.0, 0.0, 1.0)
#        glPointSize(9.0)
#        glBegin(GL_POINTS)
#        glVertex3f(*point)
#        glEnd()
#

#        facebox = BoundingBox(box.origin, box.size)
#        facebox.origin[dim] = self.dragResizePosition
#        facebox.size[dim] = 0
#        glEnable(GL_BLEND)
#
#        drawFace(facebox, dim * 2)
#
#        glDisable(GL_BLEND)
#
        side = self.dragResizeFace & 1
        dragdim = self.dragResizeFace >> 1
        box = self.selectionBox()

        o, m = list(box.origin), list(box.maximum)
        (m, o)[side][dragdim] = int(numpy.floor(point[dragdim] + 0.5))
        m = map(lambda a: a - 1, m)
        return o, m

    def option1(self):
        self.selectOtherCorner()

    _currentCorner = 0

    @property
    def currentCorner(self):
        return self._currentCorner

    @currentCorner.setter
    def currentCorner(self, value):
        self._currentCorner = value & 1
        self.toolIconName = ("selection", "selection2")[self._currentCorner]
        self.editor.toolbar.toolTextureChanged()

    def selectOtherCorner(self):
        self.currentCorner = 1 - self.currentCorner

    showPreviousSelection = SelectSettings.showPreviousSelection.configProperty()
    alpha = 0.25

    def drawToolMarkers(self):

        selectionBox = self.selectionBox()
        if(selectionBox):
            widg = self.editor.find_widget(pygame.mouse.get_pos())

            # these corners stay even while using the chunk tool.
            GL.glPolygonOffset(DepthOffset.SelectionCorners, DepthOffset.SelectionCorners)
            lineWidth = 3
            for t, c, n in ((self.bottomLeftPoint, self.bottomLeftColor, self.bottomLeftNudge), (self.topRightPoint, self.topRightColor, self.topRightNudge)):
                if t != None:
                    (sx, sy, sz) = t
                    if self.selectionInProgress:
                        if t == self.getSelectionPoint(self.currentCorner):
                            blockFace = self.editor.blockFaceUnderCursor
                            if blockFace:
                                p, d = blockFace
                                (sx, sy, sz) = p
                        else:
                            sx, sy, sz = self.dragStartPoint

                    # draw a blue or yellow wireframe box at the selection corner
                    r, g, b = c
                    alpha = 0.4
                    try:
                        bt = self.editor.level.blockAt(sx, sy, sz)
                        if(bt):
                            alpha = 0.2
                    except (EnvironmentError, pymclevel.ChunkNotPresent):
                        pass

                    GL.glLineWidth(lineWidth)
                    lineWidth += 1

                    # draw highlighted block faces when nudging
                    if (widg.parent == n or widg == n):
                        GL.glEnable(GL.GL_BLEND)
                        # drawCube(BoundingBox((sx, sy, sz), (1,1,1)))
                        nudgefaces = numpy.array([
                               selectionBox.minx, selectionBox.miny, selectionBox.minz,
                               selectionBox.minx, selectionBox.maxy, selectionBox.minz,
                               selectionBox.minx, selectionBox.maxy, selectionBox.maxz,
                               selectionBox.minx, selectionBox.miny, selectionBox.maxz,
                               selectionBox.minx, selectionBox.miny, selectionBox.minz,
                               selectionBox.maxx, selectionBox.miny, selectionBox.minz,
                               selectionBox.maxx, selectionBox.miny, selectionBox.maxz,
                               selectionBox.minx, selectionBox.miny, selectionBox.maxz,
                               selectionBox.minx, selectionBox.miny, selectionBox.minz,
                               selectionBox.minx, selectionBox.maxy, selectionBox.minz,
                               selectionBox.maxx, selectionBox.maxy, selectionBox.minz,
                               selectionBox.maxx, selectionBox.miny, selectionBox.minz,
                               ], dtype='float32')

                        if sx != selectionBox.minx:
                            nudgefaces[0:12:3] = selectionBox.maxx
                        if sy != selectionBox.miny:
                            nudgefaces[13:24:3] = selectionBox.maxy
                        if sz != selectionBox.minz:
                            nudgefaces[26:36:3] = selectionBox.maxz

                        GL.glColor(r, g, b, 0.3)
                        GL.glVertexPointer(3, GL.GL_FLOAT, 0, nudgefaces)
                        GL.glEnable(GL.GL_DEPTH_TEST)
                        GL.glDrawArrays(GL.GL_QUADS, 0, 12)
                        GL.glDisable(GL.GL_DEPTH_TEST)

                        GL.glDisable(GL.GL_BLEND)

                    GL.glColor(r, g, b, alpha)
                    drawCube(BoundingBox((sx, sy, sz), (1, 1, 1)), GL.GL_LINE_STRIP)

            if not (not self.showPreviousSelection and self.selectionInProgress):
                # draw the current selection as a white box.  hangs around when you use other tools.
                GL.glPolygonOffset(DepthOffset.Selection, DepthOffset.Selection)
                color = self.selectionColor + (self.alpha,)
                if self.dragResizeFace is not None:
                    box = self.draggingSelectionBox()
                else:
                    box = selectionBox

                if self.panel and (widg is self.panel.nudgeBlocksButton or widg.parent is self.panel.nudgeBlocksButton):
                    color = (0.3, 1.0, 0.3, self.alpha)
                self.editor.drawConstructionCube(box, color)

                # highlight the face under the cursor, or the face being dragged
                if self.dragResizeFace is None:
                    if self.selectionInProgress or self.clickSelectionInProgress:
                        pass
                    else:
                        face, point = self.boxFaceUnderCursor(box)

                        if face is not None:
                            GL.glEnable(GL.GL_BLEND)
                            GL.glColor(*color)

                            # Shrink the highlighted face to show the click-through edges

                            offs = [s * self.edge_factor for s in box.size]
                            offs[face >> 1] = 0
                            origin = [o + off for o, off in zip(box.origin, offs)]
                            size = [s - off * 2 for s, off in zip(box.size, offs)]

                            cv = self.editor.mainViewport.cameraVector
                            for i in range(3):
                                if cv[i] > 0:
                                    origin[i] -= offs[i]
                                    size[i] += offs[i]
                                else:
                                    size[i] += offs[i]

                            smallbox = FloatBox(origin, size)

                            drawFace(smallbox, face)

                            GL.glColor(0.9, 0.6, 0.2, 0.8)
                            GL.glLineWidth(2.0)
                            drawFace(box, face, type=GL.GL_LINE_STRIP)
                            GL.glDisable(GL.GL_BLEND)
                else:
                    face = self.dragResizeFace
                    point = self.dragResizePoint()
                    dim = face >> 1
                    pos = point[dim]

                    side = face & 1
                    o, m = selectionBox.origin, selectionBox.maximum
                    otherFacePos = (m, o)[side ^ 1][dim]  # ugly
                    direction = (-1, 1)[side]
                    # print "pos", pos, "otherFace", otherFacePos, "dir", direction
                    # print "m", (pos - otherFacePos) * direction
                    if (pos - otherFacePos) * direction > 0:
                        face ^= 1

                    GL.glColor(0.9, 0.6, 0.2, 0.5)
                    drawFace(box, face, type=GL.GL_LINE_STRIP)
                    GL.glEnable(GL.GL_BLEND)
                    GL.glEnable(GL.GL_DEPTH_TEST)

                    drawFace(box, face)
                    GL.glDisable(GL.GL_BLEND)
                    GL.glDisable(GL.GL_DEPTH_TEST)

        selectionColor = map(lambda a: a * a * a * a, self.selectionColor)

        # draw a colored box representing the possible selection
        otherCorner = self.dragStartPoint
        if self.dragResizeFace is not None:
            self.showPanel()  # xxx do this every frame while dragging because our UI kit is bad

        if ((self.selectionInProgress or self.clickSelectionInProgress) and otherCorner != None):
            GL.glPolygonOffset(DepthOffset.PotentialSelection, DepthOffset.PotentialSelection)

            pos, direction = self.editor.blockFaceUnderCursor
            if pos is not None:
                box = self.selectionBoxForCorners(otherCorner, pos)
                if self.chunkMode:
                    box = box.chunkBox(self.editor.level)
                    if pygame.key.get_mods() & pygame.KMOD_ALT:
                        selectionColor = [1., 0., 0.]
                self.editor.drawConstructionCube(box, selectionColor + [self.alpha, ])
        else:
            # don't draw anything at the mouse cursor if we're resizing the box
            if self.dragResizeFace is None:
                box = self.selectionBox()
                if box:
                    face, point = self.boxFaceUnderCursor(box)
                    if face is not None:
                        return
            else:
                return

    def drawToolReticle(self):
        GL.glPolygonOffset(DepthOffset.SelectionReticle, DepthOffset.SelectionReticle)
        pos, direction = self.editor.blockFaceUnderCursor

        # draw a selection-colored box for the cursor reticle
        selectionColor = map(lambda a: a * a * a * a, self.selectionColor)
        r, g, b = selectionColor
        alpha = 0.3

        try:
            bt = self.editor.level.blockAt(*pos)
            if(bt):
##                textureCoords = materials[bt][0]
                alpha = 0.12
        except (EnvironmentError, pymclevel.ChunkNotPresent):
            pass

        # cube sides
        GL.glColor(r, g, b, alpha)
        GL.glDepthMask(False)
        GL.glEnable(GL.GL_BLEND)
        GL.glEnable(GL.GL_DEPTH_TEST)
        drawCube(BoundingBox(pos, (1, 1, 1)))
        GL.glDepthMask(True)
        GL.glDisable(GL.GL_DEPTH_TEST)

        drawTerrainCuttingWire(BoundingBox(pos, (1, 1, 1)),
                               (r, g, b, 0.4),
                               (1., 1., 1., 1.0)
                               )

        GL.glDisable(GL.GL_BLEND)

    def setSelection(self, box):
        if box is None:
            self.selectNone()
        else:
            self.setSelectionPoints(self.selectionPointsFromBox(box))

    def selectionPointsFromBox(self, box):
        return (box.origin, map(lambda x: x - 1, box.maximum))

    def selectNone(self):
        self.setSelectionPoints(None)

    def selectAll(self):
        box = self.editor.level.bounds
        op = SelectionOperation(self, self.selectionPointsFromBox(box))
        self.editor.addOperation(op)

    def deselect(self):
        op = SelectionOperation(self, None)
        self.editor.addOperation(op)

    def setSelectionPoint(self, pointNumber, newPoint):
        points = self.getSelectionPoints()
        points[pointNumber] = newPoint
        self.setSelectionPoints(points)

    def setSelectionPoints(self, points):
        if points:
            self.bottomLeftPoint, self.topRightPoint = [Vector(*p) if p else None for p in points]
        else:
            self.bottomLeftPoint = self.topRightPoint = None

        self._selectionChanged()
        self.editor.selectionChanged()

    def _selectionChanged(self):
        if self.selectionBox():
            self.showPanel()
        else:
            self.hidePanel()
            self.hideNudgePanel()

    def getSelectionPoint(self, pointNumber):
        return (self.bottomLeftPoint, self.topRightPoint)[pointNumber]  # lisp programmers think this doesn't evaluate 'self.topRightPoint' - lol!

    def getSelectionPoints(self):
        return [self.bottomLeftPoint, self.topRightPoint]

    @alertException
    def deleteBlocks(self):
        box = self.selectionBox()
        if None is box:
            return
        if box == box.chunkBox(self.editor.level):
            resp = ask("You are deleting a chunk-shaped selection. Fill the selection with Air, or delete the chunks themselves?", responses=["Fill with Air", "Delete Chunks", "Cancel"])
            if resp == "Delete Chunks":
                self.editor.toolbar.tools[8].destroyChunks(box.chunkPositions)
            elif resp == "Fill with Air":
                self._deleteBlocks()
        else:
            self._deleteBlocks()

    def _deleteBlocks(self):
        box = self.selectionBox()
        if None is box:
            return
        op = BlockFillOperation(self.editor, self.editor.level, box, self.editor.level.materials.Air, [])
        with setWindowCaption("DELETING - "):
            self.editor.freezeStatus("Deleting {0} blocks".format(box.volume))

            self.editor.addOperation(op)
            self.editor.invalidateBox(box)
            self.editor.addUnsavedEdit()

    @alertException
    def deleteEntities(self, recordUndo=True):
        box = self.selectionBox()

        with setWindowCaption("WORKING - "):
            self.editor.freezeStatus("Removing entities...")
            level = self.editor.level
            editor = self.editor

            class DeleteEntitiesOperation(Operation):
                def perform(self, recordUndo=True):
                    self.undoEntities = level.getEntitiesInBox(box)
                    level.removeEntitiesInBox(box)
                    editor.renderer.invalidateEntitiesInBox(box)

                def undo(self):
                    level.removeEntitiesInBox(box)
                    level.addEntities(self.undoEntities)
                    editor.renderer.invalidateEntitiesInBox(box)

            op = DeleteEntitiesOperation(self.editor, self.editor.level)
            if recordUndo:
                self.editor.addOperation(op)
            self.editor.addUnsavedEdit()

    @alertException
    def analyzeSelection(self):
        box = self.selectionBox()
        self.editor.analyzeBox(self.editor.level, box)

    @alertException
    def cutSelection(self):
        self.copySelection()
        self.deleteBlocks()
        self.deleteEntities(False)

    @alertException
    def copySelection(self):
        schematic = self._copySelection()
        if schematic:
            self.editor.addCopiedSchematic(schematic)

    def _copySelection(self):
        box = self.selectionBox()
        if not box:
            return

        shape = box.size

        self.editor.mouseLookOff()

        print "Clipping: ", shape

        fileFormat = "schematic"
        if box.volume > self.maxBlocks:
            fileFormat = "schematic.zip"

        if fileFormat == "schematic.zip":
            missingChunks = filter(lambda x: not self.editor.level.containsChunk(*x), box.chunkPositions)
            if len(missingChunks):
                if not ((box.origin[0] & 0xf == 0) and (box.origin[2] & 0xf == 0)):
                    if ask("This is an uneven selection with missing chunks. Expand the selection to chunk edges, or copy air within the missing chunks?", ["Expand Selection", "Copy Air"]) == "Expand Selection":
                        self.selectChunks()
                        box = self.selectionBox()

        with setWindowCaption("Copying - "):
            filename = tempfile.mkdtemp(".zip", "mceditcopy")
            os.rmdir(filename)

            status = "Copying {0:n} blocks...".format(box.volume)
            if fileFormat == "schematic":
                schematic = showProgress(status,
                            self.editor.level.extractSchematicIter(box), cancel=True)
            else:
                schematic = showProgress(status,
                            self.editor.level.extractZipSchematicIter(box, filename), cancel=True)
            if schematic == "Canceled":
                return None

            return schematic

    @alertException
    def exportSelection(self):
        schematic = self._copySelection()
        if schematic:
            self.editor.exportSchematic(schematic)


class SelectionOperation(Operation):
    changedLevel = False

    def __init__(self, selectionTool, points):
        super(SelectionOperation, self).__init__(selectionTool.editor, selectionTool.editor.level)
        self.selectionTool = selectionTool
        self.points = points

    def perform(self, recordUndo=True):
        self.undoPoints = self.selectionTool.getSelectionPoints()
        self.selectionTool.setSelectionPoints(self.points)

    def undo(self):
        points = self.points
        self.points = self.undoPoints
        self.perform()
        self.points = points


class NudgeSelectionOperation(Operation):
    changedLevel = False

    def __init__(self, selectionTool, direction):
        super(NudgeSelectionOperation, self).__init__(selectionTool.editor, selectionTool.editor.level)
        self.selectionTool = selectionTool
        self.direction = direction
        self.oldPoints = selectionTool.getSelectionPoints()
        self.newPoints = [p + direction for p in self.oldPoints]

    def perform(self, recordUndo=True):
        self.selectionTool.setSelectionPoints(self.newPoints)

    oldSelection = None

    def undo(self):
        self.selectionTool.setSelectionPoints(self.oldPoints)

########NEW FILE########
__FILENAME__ = thumbview
from OpenGL import GLU, GL
from numpy import array
from albow import Widget
from albow.openglwidgets import GLPerspective
from glutils import FramebufferTexture, gl
import pymclevel
from renderer import PreviewRenderer

class ThumbView(GLPerspective):

    def __init__(self, sch, **kw):
        GLPerspective.__init__(self, **kw)  # self, xmin= -32, xmax=32, ymin= -32, ymax=32, near= -1000, far=1000)
        self.far = 16000
        self.schematic = sch
        self.renderer = PreviewRenderer(sch)
        self.fboSize = (128, 128)
        # self.renderer.position = (sch.Length / 2, 0, sch.Height / 2)

    def setup_modelview(self):
        GLU.gluLookAt(-self.schematic.Width * 2.8, self.schematic.Height * 2.5 + 1, -self.schematic.Length * 1.5,
                      self.schematic.Width, 0, self.schematic.Length,
                      0, 1, 0)
    fbo = None

    def gl_draw_tex(self):
        self.clear()
        self.renderer.draw()

    def clear(self):
        if self.drawBackground:
            GL.glClearColor(0.25, 0.27, 0.77, 1.0)
        else:
            GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        GL.glClear(GL.GL_DEPTH_BUFFER_BIT | GL.GL_COLOR_BUFFER_BIT)

    def gl_draw(self):
        if self.schematic.chunkCount > len(self.renderer.chunkRenderers):
            self.gl_draw_thumb()
        else:
            if self.fbo is None:
                w, h = self.fboSize
                self.fbo = FramebufferTexture(w, h, self.gl_draw_tex)
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glLoadIdentity()
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            GL.glColor(1.0, 1.0, 1.0, 1.0)
            GL.glVertexPointer(2, GL.GL_FLOAT, 0, array([-1, -1,
                         - 1, 1,
                         1, 1,
                         1, -1, ], dtype='float32'))
            GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, array([0, 0, 0, 256, 256, 256, 256, 0], dtype='float32'))
            e = (GL.GL_TEXTURE_2D,)
            if not self.drawBackground:
                e += (GL.GL_ALPHA_TEST,)
            with gl.glEnable(*e):
                self.fbo.bind()
                GL.glDrawArrays(GL.GL_QUADS, 0, 4)
            GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

    drawBackground = True

    def gl_draw_thumb(self):
        GL.glPushAttrib(GL.GL_SCISSOR_BIT)
        r = self.rect
        r = r.move(*self.local_to_global_offset())
        GL.glScissor(r.x, self.get_root().height - r.y - r.height, r.width, r.height)
        with gl.glEnable(GL.GL_SCISSOR_TEST):
            self.clear()
            self.renderer.draw()
        GL.glPopAttrib()


class BlockThumbView(Widget):
    is_gl_container = True

    def __init__(self, materials, blockInfo=None, **kw):
        Widget.__init__(self, **kw)
        self.materials = materials
        self.blockInfo = blockInfo

    thumb = None
    _blockInfo = None

    @property
    def blockInfo(self):
        return self._blockInfo

    @blockInfo.setter
    def blockInfo(self, b):
        if self._blockInfo != b:
            if self.thumb:
                self.thumb.set_parent(None)
            self._blockInfo = b
            if b is None:
                return

            sch = pymclevel.MCSchematic(shape=(1, 1, 1), mats=self.materials)
            if b:
                sch.Blocks[:] = b.ID
                sch.Data[:] = b.blockData

            self.thumb = ThumbView(sch)
            self.add(self.thumb)
            self.thumb.size = self.size
            self.thumb.drawBackground = False
            for i in self.thumb.renderer.chunkWorker:
                pass

########NEW FILE########
__FILENAME__ = tooloptions
from glbackground import Panel

class ToolOptions(Panel):
    @property
    def editor(self):
        return self.tool.editor

########NEW FILE########
__FILENAME__ = AddPotionEffect
# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

from pymclevel import TAG_List
from pymclevel import TAG_Byte
from pymclevel import TAG_Int
from pymclevel import TAG_Compound

displayName = "Add Potion Effect to Mobs"

Effects = {
	"Strength": 5,
	"Jump Boost": 8,
	"Regeneration": 10,
	"Fire Resistance": 12,
	"Water Breathing": 13,
	"Resistance": 11,
	"Weakness": 18,
	"Poison": 19,
	"Speed (no mob effect)": 1,
	"Slowness (no mob effect)": 2,
	"Haste (no mob effect)": 3,
	"Mining Fatigue (no mob effectg)": 4,
	"Nausea (no mob effect)": 9,
	"Blindness (no mob effect)": 15,
	"Hunger (no mob effect)": 17,
	"Invisibility (no effect)": 14,
	"Night Vision (no effect)": 16,
	}
	
EffectKeys = ()
for key in Effects.keys():
	EffectKeys = EffectKeys + (key,)
	

inputs = (
	("Effect", EffectKeys),
	("Level", 1),
	("Duration (Seconds)", 60),
)

def perform(level, box, options):
	effect = Effects[options["Effect"]]
	amp = options["Level"]
	duration = options["Duration (Seconds)"] * 20

	for (chunk, slices, point) in level.getChunkSlices(box):
		for e in chunk.Entities:
			x = e["Pos"][0].value
			y = e["Pos"][1].value
			z = e["Pos"][2].value
			
			if x >= box.minx and x < box.maxx and y >= box.miny and y < box.maxy and z >= box.minz and z < box.maxz:
				if "Health" in e:
					if "ActiveEffects" not in e:
						e["ActiveEffects"] = TAG_List()

					ef = TAG_Compound()
					ef["Amplifier"] = TAG_Byte(amp)
					ef["Id"] = TAG_Byte(effect)
					ef["Duration"] = TAG_Int(duration)
					e["ActiveEffects"].append(ef)
					chunk.dirty = True

########NEW FILE########
__FILENAME__ = BanSlimes
# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

from pymclevel import TAG_Long

# This mimics some of the functionality from the Java Random class.
# Java Random source code can be found here: http://developer.classpath.org/doc/java/util/Random-source.html
class Random:
	def __init__(self, randseed):
		self.setSeed(randseed)

	def setSeed(self, randseed):
		self.randseed = (randseed ^ 0x5DEECE66DL) & ((1L << 48) - 1);
		
	def next(self, bits):
		self.randseed = long(self.randseed * 0x5DEECE66DL + 0xBL) & ((1L << 48) - 1)
		return int(self.randseed >> (48 - bits))

	def nextInt(self, n):
		while True:
			bits = self.next(31)
			val = bits % n
			if int(bits - val + (n-1)) >= 0:
				break
			
		return val

# Algorithm found here: http://www.minecraftforum.net/topic/397835-find-slime-spawning-chunks-125/
def slimeChunk(seed, x, z):
	randseed = long(seed) + long(x * x * 0x4c1906) + long(x * 0x5ac0db) + long(z * z) * 0x4307a7L + long(z * 0x5f24f) ^ 0x3ad8025f
	r = Random(randseed)
	i = r.nextInt(10)
	return i == 0
	
def goodSeed(box, seed):
	minx = int(box.minx/16)*16
	minz = int(box.minz/16)*16

	for x in xrange(minx, box.maxx, 16):
		for z in xrange(minz, box.maxz, 16):
			if slimeChunk(seed, x, z):
				return False
				
	
	return True

inputs = (
	("Max Seed", 100000),
)

def perform(level, box, options):
	for seed in xrange(options["Max Seed"]):
		if goodSeed(box, long(seed)):
			level.root_tag["Data"]["RandomSeed"] = TAG_Long(seed)
			print "Found good seed: " + str(seed)
			return
	
	print "Didn't find good seed."
########NEW FILE########
__FILENAME__ = ChangeMobs
# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

from pymclevel import TAG_List
from pymclevel import TAG_Byte
from pymclevel import TAG_Int
from pymclevel import TAG_Compound
from pymclevel import TAG_Short
from pymclevel import TAG_Double
from pymclevel import TAG_String

displayName = "Change Mob Properties"

Professions = {
	"Farmer (brown)": 0,
	"Librarian (white)": 1,
	"Priest (purple)": 2,
	"Blacksmith (black apron)": 3,
	"Butcher (white apron)": 4,
	"Villager (green)": 5,
	}
	
ProfessionKeys = ("N/A",)
for key in Professions.keys():
	ProfessionKeys = ProfessionKeys + (key,)
	
	

noop = -1337
	
inputs = (
	("Health", noop),
	("VelocityX", noop),
	("VelocityY", noop),
	("VelocityZ", noop),
	("Fire", noop),
	("FallDistance", noop),
	("Air", noop),
	("AttackTime", noop),
	("HurtTime", noop),
	("Lightning Creeper", ("N/A", "Lightning", "No Lightning")),
	("Enderman Block Id", noop),
	("Enderman Block Data", noop),
	("Villager Profession", ProfessionKeys),
	("Slime Size", noop),
	("Breeding Mode Ticks", noop),
	("Child/Adult Age", noop),
)

def perform(level, box, options):
	health = options["Health"]
	vx = options["VelocityX"]
	vy = options["VelocityY"]
	vz = options["VelocityZ"]
	fire = options["Fire"]
	fall = options["FallDistance"]
	air = options["Air"]
	attackTime = options["AttackTime"]
	hurtTime = options["HurtTime"]
	powered = options["Lightning Creeper"]
	blockId = options["Enderman Block Id"]
	blockData = options["Enderman Block Data"]
	profession = options["Villager Profession"]
	size = options["Slime Size"]
	breedTicks = options["Breeding Mode Ticks"]
	age = options["Child/Adult Age"]
	

	for (chunk, slices, point) in level.getChunkSlices(box):
		for e in chunk.Entities:
			x = e["Pos"][0].value
			y = e["Pos"][1].value
			z = e["Pos"][2].value
			
			if x >= box.minx and x < box.maxx and y >= box.miny and y < box.maxy and z >= box.minz and z < box.maxz:
				if "Health" in e:
					if health != noop:
						e["Health"] = TAG_Short(health)
						
					if vx != noop:
						e["Motion"][0] = TAG_Double(vx)
					if vy != noop:
						e["Motion"][1] = TAG_Double(vy)
					if vz != noop:
						e["Motion"][2] = TAG_Double(vz)
					
					if fire != noop:
						e["Fire"] = TAG_Short(fire)
					
					if fall != noop:
						e["FallDistance"] = TAG_Float(fall)
					
					if air != noop:
						e["Air"] = TAG_Short(air)
					
					if attackTime != noop:
						e["AttackTime"] = TAG_Short(attackTime)
					
					if hurtTime != noop:
						e["HurtTime"] = TAG_Short(hurtTime)
					
					if powered != "N/A" and e["id"].value == "Creeper":
						if powered == "Lightning":
							e["powered"] = TAG_Byte(1)
						if powered == "No Lightning":
							e["powered"] = TAG_Byte(0)

					if blockId != noop and e["id"].value == "Enderman":
						e["carried"] = TAG_Short(blockId)
					if blockData != noop and e["id"].value == "Enderman":
						e["carriedData"] = TAG_Short(blockData)
					
					if profession != "N/A" and e["id"].value == "Villager":
						e["Profession"] = TAG_Int(Professions[profession])
					
					if size != noop and e["id"].value == "Slime":
						e["Size"] = TAG_Int(size)
					
					if breedTicks != noop:
						e["InLove"] = TAG_Int(breedTicks)
					
					if age != noop:
						e["Age"] = TAG_Int(age)
					
					chunk.dirty = True

########NEW FILE########
__FILENAME__ = colorwires
def perform(level, box, options):
    groups = RedstoneGroups(level)
    
    for x in xrange(box.minx, box.maxx):
        for y in xrange(box.miny, box.maxy):
            for z in xrange(box.minz, box.maxz):
                groups.testblock((x, y, z))

    groups.changeBlocks()

    

TransparentBlocks = [0, 6, 8, 9, 10, 11, 18, 20, 26, 27, 28, 29, 30, 31, 32, 33, 34, 36, 37, 38, 39, 40, 44, 46, 50, 51, 52, 53, 54, 55, 59, 60, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 75, 76, 77, 78, 79, 81, 83, 85, 89, 90, 92, 93, 94, 95, 96, 97, 101, 102, 104, 105, 106, 107, 108, 109, 111, 113, 114, 115, 116, 117, 118, 119, 120, 122, 126, 127]

class RedstoneGroups:
    group = {}
    currentgroup = 0

    def __init__(self, level):
        self.level = level

    def isRedstone(self, blockid):
        return blockid == 55 or blockid == 93 or blockid == 94

    def testblock(self, pos):
        (x, y, z) = pos
        blockid = self.level.blockAt(x, y, z)
        if self.isRedstone(blockid):
            if (x, y, z) in self.group:
                return
            self.group[pos] = self.currentgroup
            self.testneighbors(pos)
            self.currentgroup = self.currentgroup + 1

    def testneighbors(self, (x, y, z)):
        for dy in xrange(-1, 2, 1):
            if y + dy >= 0 and y + dy <= 255:
                self.testneighbor((x, y, z), (x-1, y+dy, z))
                self.testneighbor((x, y, z), (x+1, y+dy, z))
                self.testneighbor((x, y, z), (x, y+dy, z-1))
                self.testneighbor((x, y, z), (x, y+dy, z+1))

    def testneighbor(self, pos1, pos2):
        if pos2 in self.group:
            return

        if self.connected(pos1, pos2):
            self.group[pos2] = self.currentgroup
            self.testneighbors(pos2)

    def getBlockAt(self, (x, y, z)):
        return self.level.blockAt(x, y, z)

    def repeaterAlignedWith(self, (x1, y1, z1), (x2, y2, z2)):
        blockid = self.getBlockAt((x1, y1, z1))
        if blockid != 93 and blockid != 94:
            return False

        direction = self.level.blockDataAt(x1, y1, z1) % 4

        if (direction == 0 or direction == 2) and abs(z2 - z1) != 1:
            return False
        elif (direction == 1 or direction == 3) and abs(x2 - x1) != 1:
            return False

        return True

    def repeaterPointingTowards(self, (x1, y1, z1), (x2, y2, z2)):
        blockid = self.getBlockAt((x1, y1, z1))
        if blockid != 93 and blockid != 94:
            return False

        direction = self.level.blockDataAt(x1, y1, z1) % 4

        if direction == 0 and z2 - z1 == -1:
            return True
        if direction == 1 and x2 - x1 == 1:
            return True
        if direction == 2 and z2 - z1 == 1:
            return True
        if direction == 3 and x2 - x1 == -1:
            return True

        return False

    def repeaterPointingAway(self, (x1, y1, z1), (x2, y2, z2)):
        blockid = self.getBlockAt((x1, y1, z1))
        if blockid != 93 and blockid != 94:
            return False

        direction = self.level.blockDataAt(x1, y1, z1) % 4

        if direction == 0 and z2 - z1 == 1:
            return True
        if direction == 1 and x2 - x1 == -1:
            return True
        if direction == 2 and z2 - z1 == -1:
            return True
        if direction == 3 and x2 - x1 == 1:
            return True

        return False
    

    def connected(self, (x1, y1, z1), (x2, y2, z2)):
        blockid1 = self.level.blockAt(x1, y1, z1)
        blockid2 = self.level.blockAt(x2, y2, z2)

        pos1 = (x1, y1, z1)
        pos2 = (x2, y2, z2)
        
        if y1 == y2:
            if blockid1 == 55:
                if blockid2 == 55:
                    return True
                elif self.repeaterAlignedWith(pos2, pos1):
                    return True                    
            elif self.repeaterAlignedWith(pos1, pos2) and blockid2 == 55:
                return True
            elif self.repeaterPointingTowards(pos1, pos2) and self.repeaterPointingAway(pos2, pos1):
                return True
            elif self.repeaterPointingAway(pos1, pos2) and self.repeaterPointingTowards(pos2, pos1):
                return True
        elif y2 == y1 - 1:
            aboveid = self.level.blockAt(x2, y2+1, z2)
            
            if blockid1 == 55:
                if blockid2 == 55 and TransparentBlocks.count(aboveid) == 1:
                    return True
                elif self.repeaterAlignedWith(pos2, pos1):
                    return True
            elif self.repeaterPointingTowards(pos1, pos2):
                if blockid2 == 55 and TransparentBlocks.count(aboveid) == 0:
                    return True
        elif y2 == y1 + 1:
            return self.connected(pos2, pos1)

        return False

    SkipBlocks = [23, 61, 62, 89]

    def changeBlocks(self):
        for ((x, y, z), gr) in self.group.items():
            if y > 0:
                blockid = self.level.blockAt(x, y-1, z)
                if self.SkipBlocks.count(blockid) == 1:
                    continue
                self.level.setBlockAt(x, y-1, z, 35)
                self.level.setBlockDataAt(x, y-1, z, gr % 16)
                self.level.getChunk(x / 16, z / 16).dirty = True

########NEW FILE########
__FILENAME__ = CreateBusses
# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

from numpy import sign

displayName = "Create Busses"

def perform(level, box, options):
	level.markDirtyBox(box)
	
	bus = BusCreator(level, box, options)
	bus.getTerminals()
	bus.getGuides()
	bus.pickAllPaths()
	bus.createAllBusses()
	
HorizDirs = [
	(1, 0, 0),
	(-1, 0, 0),
	(0, 0, 1),
	(0, 0, -1),
	]

Down = (0, -1, 0)
Up = (0, 1, 0)

def getHorizDir((x1, y1, z1), (x2, y2, z2)):
	if abs(x2-x1) > abs(z2-z1):
		return (sign(x2-x1), 0, 0)
	else:
		if(z2 == z1):
			return (1, 0, 0)
		else:
			return (0, 0, sign(z2-z1))

def getSecondaryDir((x1, y1, z1), (x2, y2, z2)):
	if abs(x2-x1) > abs(z2-z1):
		return (0, 0, sign(z2-z1))
	else:
		return (sign(x2-x1), 0, 0)
		
def leftOf((dx1, dy1, dz1), (dx2, dy2, dz2)):
	return dx1 == dz2 or dz1 == dx2 * -1

def rotateRight((dx, dy, dz)):
	return ((-dz, dy, dx))

def rotateLeft((dx, dy, dz)):
	return ((dz, dy, -dx))

def allAdjacentSamePlane(dir, secondaryDir):
	right = rotateRight(dir)
	left = rotateLeft(dir)
	back = rotateRight(right)

	if leftOf(secondaryDir, dir):
		return (
			dir,
			left,
			right,
			getDir(dir, Up),
			getDir(dir, Down),
			getDir(left, Up),
			getDir(right, Up),
			getDir(left, Down),
			getDir(right, Down),
			back,
			getDir(back, Up),
			getDir(back, Down),
			)
	else:
		return (
			dir,
			right,
			left,
			getDir(dir, Up),
			getDir(dir, Down),
			getDir(right, Up),
			getDir(left, Up),
			getDir(right, Down),
			getDir(left, Down),
			back,
			getDir(back, Up),
			getDir(back, Down),
			)

def allAdjacentUp(dir, secondaryDir):
	right = rotateRight(dir)
	left = rotateLeft(dir)
	back = rotateRight(right)

	if leftOf(secondaryDir, dir):
		return (
			getDir(dir, Up),
			getDir(left, Up),
			getDir(right, Up),
			getDir(back, Up),
			dir,
			left,
			right,
			back,
			getDir(dir, Down),
			getDir(left, Down),
			getDir(right, Down),
			getDir(back, Down),
			)
	else:
		return (
			getDir(dir, Up),
			getDir(right, Up),
			getDir(left, Up),
			getDir(back, Up),
			dir,
			right,
			left,
			back,
			getDir(dir, Down),
			getDir(right, Down),
			getDir(left, Down),
			getDir(back, Down),
			)
		
def allAdjacentDown(dir, secondaryDir):
	right = rotateRight(dir)
	left = rotateLeft(dir)
	back = rotateRight(right)

	if leftOf(secondaryDir, dir):
		return (
			getDir(dir, Down),
			getDir(left, Down),
			getDir(right, Down),
			getDir(back, Down),
			dir,
			left,
			right,
			back,
			getDir(dir, Up),
			getDir(left, Up),
			getDir(right, Up),
			getDir(back, Up),
			)
	else:
		return (
			getDir(dir, Down),
			getDir(right, Down),
			getDir(left, Down),
			getDir(back, Down),
			dir,
			right,
			left,
			back,
			getDir(dir, Up),
			getDir(right, Up),
			getDir(left, Up),
			getDir(back, Up),
			)
		
def getDir((x, y, z), (dx, dy, dz)):
	return (x+dx, y+dy, z+dz)

def dist((x1, y1, z1), (x2, y2, z2)):
	return abs(x2-x1) + abs(y2-y1) + abs(z2-z1)
	
def above((x1, y1, z1), (x2, y2, z2)):
	return y1 > y2

def below((x1, y1, z1), (x2, y2, z2)):
	return y1 < y2
	
def insideBox(box, (x, y, z)):
	return x >= box.minx and x < box.maxx and y >= box.miny and y < box.maxy and z >= box.minz and z < box.maxz

Colors = {
	0: "white",
	1: "orange",
	2: "magenta",
	3: "light blue",
	4: "yellow",
	5: "lime green",
	6: "pink",
	7: "gray",
	8: "light gray",
	9: "cyan",
	10:"purple",
	11:"blue",
	12:"brown",
	13:"green",
	14:"red",
	15:"black",
	}
	
class BusCreator:
	starts = {}
	ends = {}
	guides = {}
	path = {}

	
	def __init__(self, level, box, options):
		self.level = level
		self.box = box
		self.options = options
	
	def getTerminals(self):
		for x in xrange(self.box.minx, self.box.maxx):
			for y in xrange(self.box.miny, self.box.maxy):
				for z in xrange(self.box.minz, self.box.maxz):
					(color, start) = self.isTerminal((x, y, z))
					if color != None and start != None:
						if start:
							if color in self.starts:
								raise Exception("Duplicate starting point for " + Colors[color] + " bus")
							self.starts[color] = (x, y, z)
						else:
							if color in self.ends:
								raise Exception("Duplicate ending point for " + Colors[color] + " bus")
							self.ends[color] = (x, y, z)
							
	def getGuides(self):
		for x in xrange(self.box.minx, self.box.maxx):
			for y in xrange(self.box.miny, self.box.maxy):
				for z in xrange(self.box.minz, self.box.maxz):
					pos = (x, y, z)
					if self.getBlockAt(pos) == 35:
						color = self.getBlockDataAt(pos)
						
						if color not in self.starts or color not in self.ends:
							continue
						
						if color not in self.guides:
							self.guides[color] = []
						
						rs = getDir(pos, Up)
						if rs == self.starts[color] or rs == self.ends[color]:
							continue
						
						self.guides[color].append(rs)
					
	
	def isTerminal(self, (x, y, z)):
		pos = (x, y, z)
		for dir in HorizDirs:
			otherPos = getDir(pos, dir)
			
			towards = self.repeaterPointingTowards(pos, otherPos)
			away = self.repeaterPointingAway(pos, otherPos)
			if not (away or towards): # it's not a repeater pointing towards or away
				continue
			if self.getBlockAt(otherPos) != 55: # the other block isn't redstone
				continue
			if self.getBlockAt(getDir(pos, Down)) != 35: # it's not sitting on wool
				continue
			if self.getBlockAt(getDir(otherPos, Down)) != 35: # the other block isn't sitting on wool
				continue
			
			data = self.getBlockDataAt(getDir(pos, Down))
			if self.getBlockDataAt(getDir(otherPos, Down)) != data: # the wool colors don't match
				continue
			
			return (data, towards)
		
		return (None, None)
	
	def pickAllPaths(self):
		for color in range(0, 16):
			if color in self.starts and color in self.ends:
				self.pickPath(color)
	
	def pickPath(self, color):
		self.path[color] = ()
		currentPos = self.starts[color]
		
		while True:
			minDist = None
			minGuide = None
			for guide in self.guides[color]:
				guideDist = dist(currentPos, guide)
				if minDist == None or guideDist < minDist:
					minDist = guideDist
					minGuide = guide
			
			if dist(currentPos, self.ends[color]) == 1:
				return
				
			if minGuide == None:
				return
			
			self.path[color] = self.path[color] + (minGuide,)
			currentPos = minGuide
			self.guides[color].remove(minGuide)

	def createAllBusses(self):
		for color in range(0, 16):
			if color in self.path:
				self.connectDots(color)			
			
	def connectDots(self, color):
		prevGuide = None
		self.power = 1
		for guide in self.path[color]:
			if prevGuide != None:
				self.createConnection(prevGuide, guide, color)
			
			prevGuide = guide
			
			
	def createConnection(self, pos1, pos2, color):
		currentPos = pos1
	
		while currentPos != pos2:
			self.power = self.power + 1
			
			hdir = getHorizDir(currentPos, pos2)
			secondaryDir = getSecondaryDir(currentPos, pos2)

			if above(currentPos, pos2):
				dirs = allAdjacentDown(hdir, secondaryDir)
			elif below(currentPos, pos2):
				dirs = allAdjacentUp(hdir, secondaryDir)
			else:
				dirs = allAdjacentSamePlane(hdir, secondaryDir)
				
			if self.power == 1:
				restrictions = 2
			elif self.power == 15:
				restrictions = 1
			else:
				restrictions = 0
			
			placed = False
			for dir in dirs:
				pos = getDir(currentPos, dir)
				if self.canPlaceRedstone(pos, currentPos, pos2, restrictions):
					if self.power == 15:
						self.placeRepeater(pos, dir, color)
						self.power = 0
					else:
						self.placeRedstone(pos, color)
					currentPos = pos
					placed = True
					break
			
			if not placed:
				#raise Exception("Algorithm failed to create bus for " + Colors[color] + " wire.")
				return
					
			
	
	def canPlaceRedstone(self, pos, fromPos, destinationPos, restrictions):
		if restrictions == 1 and above(pos, fromPos): #repeater
			return False
		
		if restrictions == 2 and below(pos, fromPos): #just after repeater
			return False
		
		if restrictions == 2 and not self.repeaterPointingTowards(fromPos, pos): #just after repeater
			return False
	
		if above(pos, fromPos) and self.getBlockAt(getDir(getDir(pos, Down), Down)) == 55:
			return False
		
		if below(pos, fromPos) and self.getBlockAt(getDir(pos, Up)) != 0:
			return False
		
		if getDir(pos, Down) == destinationPos:
			return False
		
		if pos == destinationPos:
			return True
			
		if self.getBlockAt(pos) != 0:
			return False
		
		if self.getBlockAt(getDir(pos, Down)) != 0:
			return False
		
		if not insideBox(self.box, pos):
			return False
	
		for dir in allAdjacentSamePlane((1, 0, 0), (0, 0, 0)):
			testPos = getDir(pos, dir)
			if testPos == fromPos or testPos == getDir(fromPos, Down):
				continue
			
			if testPos == destinationPos or testPos == getDir(destinationPos, Down):
				continue

			blockid = self.getBlockAt(testPos)
			if blockid != 0:
				return False
		
		return True
			
	
	def placeRedstone(self, pos, color):
		self.setBlockAt(pos, 55) #redstone
		self.setBlockAt(getDir(pos, Down), 35, color) # wool
		
	def placeRepeater(self, pos, (dx, dy, dz), color):
		if dz == -1:
			self.setBlockAt(pos, 93, 0) #north
		elif dx == 1:
			self.setBlockAt(pos, 93, 1) #east
		elif dz == 1:
			self.setBlockAt(pos, 93, 2) #south
		elif dx == -1:
			self.setBlockAt(pos, 93, 3) #west
			
		self.setBlockAt(getDir(pos, Down), 35, color) #wool
		
	def getBlockAt(self, (x, y, z)):
		return self.level.blockAt(x, y, z)
		
	def getBlockDataAt(self, (x, y, z)):
		return self.level.blockDataAt(x, y, z)
		
	def setBlockAt(self, (x, y, z), id, dmg = 0):
		self.level.setBlockAt(x, y, z, id)
		self.level.setBlockDataAt(x, y, z, dmg)
				
	def repeaterPointingTowards(self, (x1, y1, z1), (x2, y2, z2)):
		blockid = self.getBlockAt((x1, y1, z1))
		if blockid != 93 and blockid != 94:
			return False

		direction = self.level.blockDataAt(x1, y1, z1) % 4

		if direction == 0 and z2 - z1 == -1:
			return True
		if direction == 1 and x2 - x1 == 1:
			return True
		if direction == 2 and z2 - z1 == 1:
			return True
		if direction == 3 and x2 - x1 == -1:
			return True

		return False

	def repeaterPointingAway(self, (x1, y1, z1), (x2, y2, z2)):
		blockid = self.getBlockAt((x1, y1, z1))
		if blockid != 93 and blockid != 94:
			return False

		direction = self.level.blockDataAt(x1, y1, z1) % 4

		if direction == 0 and z2 - z1 == 1:
			return True
		if direction == 1 and x2 - x1 == -1:
			return True
		if direction == 2 and z2 - z1 == -1:
			return True
		if direction == 3 and x2 - x1 == 1:
			return True

		return False
		
########NEW FILE########
__FILENAME__ = CreateShops
# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

from pymclevel import TAG_Compound
from pymclevel import TAG_Int
from pymclevel import TAG_Short
from pymclevel import TAG_Byte
from pymclevel import TAG_String
from pymclevel import TAG_Float
from pymclevel import TAG_Double
from pymclevel import TAG_List

Professions = {
	"Farmer (brown)": 0,
	"Librarian (white)": 1,
	"Priest (purple)": 2,
	"Blacksmith (black apron)": 3,
	"Butcher (white apron)": 4,
	"Villager (green)": 5,
	}
	
ProfessionKeys = ()
for key in Professions.keys():
	ProfessionKeys = ProfessionKeys + (key,)
	

inputs = (
	("Profession", ProfessionKeys),
	("Add Unusable Trade", False),
	("Invincible Villagers", False),
	("Unlimited Trades", True),
)

displayName = "Create Shops"


def perform(level, box, options):
	emptyTrade = options["Add Unusable Trade"]
	invincible = options["Invincible Villagers"]
	unlimited = options["Unlimited Trades"]
	
	for x in range(box.minx, box.maxx):
		for y in range(box.miny, box.maxy):
			for z in range(box.minz, box.maxz):
				if level.blockAt(x, y, z) == 54:
					createShop(level, x, y, z, emptyTrade, invincible, Professions[options["Profession"]], unlimited)

def createShop(level, x, y, z, emptyTrade, invincible, profession, unlimited):
	chest = level.tileEntityAt(x, y, z)
	if chest == None:
		return

	priceList = {}
	priceListB = {}
	saleList = {}

	for item in chest["Items"]:
		slot = item["Slot"].value
		if slot >= 0 and slot <= 8:
			priceList[slot] = item
		elif slot >= 9 and slot <= 17:
			priceListB[slot-9] = item
		elif slot >= 18 and slot <= 26:
			saleList[slot-18] = item

	villager = TAG_Compound()
	villager["OnGround"] = TAG_Byte(1)
	villager["Air"] = TAG_Short(300)
	villager["AttackTime"] = TAG_Short(0)
	villager["DeathTime"] = TAG_Short(0)
	villager["Fire"] = TAG_Short(-1)
	villager["Health"] = TAG_Short(20)
	villager["HurtTime"] = TAG_Short(0)
	villager["Age"] = TAG_Int(0)
	villager["Profession"] = TAG_Int(profession)
	villager["Riches"] = TAG_Int(0)
	villager["FallDistance"] = TAG_Float(0)
	villager["id"] = TAG_String("Villager")
	villager["Motion"] = TAG_List()
	villager["Motion"].append(TAG_Double(0))
	villager["Motion"].append(TAG_Double(0))
	villager["Motion"].append(TAG_Double(0))
	villager["Pos"] = TAG_List()
	villager["Pos"].append(TAG_Double(x + 0.5))
	villager["Pos"].append(TAG_Double(y))
	villager["Pos"].append(TAG_Double(z + 0.5))
	villager["Rotation"] = TAG_List()
	villager["Rotation"].append(TAG_Float(0))
	villager["Rotation"].append(TAG_Float(0))

	villager["Offers"] = TAG_Compound()
	villager["Offers"]["Recipes"] = TAG_List()
	for i in range(9):
		if (i in priceList or i in priceListB) and i in saleList:
			offer = TAG_Compound()
			if unlimited:
				offer["uses"] = TAG_Int(-2000000000)
			else:
				offer["uses"] = TAG_Int(0)
			
			if i in priceList:
				offer["buy"] = priceList[i]
			if i in priceListB:
				if i in priceList:
					offer["buyB"] = priceListB[i]
				else:
					offer["buy"] = priceListB[i]
			
			offer["sell"] = saleList[i]
			villager["Offers"]["Recipes"].append(offer)

	if emptyTrade:
		offer = TAG_Compound()
		offer["buy"] = TAG_Compound()
		offer["buy"]["Count"] = TAG_Byte(1)
		offer["buy"]["Damage"] = TAG_Short(0)
		offer["buy"]["id"] = TAG_Short(36)
		offer["sell"] = TAG_Compound()
		offer["sell"]["Count"] = TAG_Byte(1)
		offer["sell"]["Damage"] = TAG_Short(0)
		offer["sell"]["id"] = TAG_Short(36)
		villager["Offers"]["Recipes"].append(offer)

	if invincible:
		if "ActiveEffects" not in villager:
			villager["ActiveEffects"] = TAG_List()

			resist = TAG_Compound()
			resist["Amplifier"] = TAG_Byte(4)
			resist["Id"] = TAG_Byte(11)
			resist["Duration"] = TAG_Int(2000000000)
			villager["ActiveEffects"].append(resist)

	level.setBlockAt(x, y, z, 0)

	chunk = level.getChunk(x / 16, z / 16)
	chunk.Entities.append(villager)
	chunk.TileEntities.remove(chest)
	chunk.dirty = True

########NEW FILE########
__FILENAME__ = CreateSpawners
# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

from pymclevel import TAG_Compound
from pymclevel import TAG_Int
from pymclevel import TAG_Short
from pymclevel import TAG_Byte
from pymclevel import TAG_String
from pymclevel import TAG_Float
from pymclevel import TAG_Double
from pymclevel import TAG_List
from pymclevel import TileEntity

displayName = "Create Spawners"

inputs = (
	("Include position data", False),
)

def perform(level, box, options):
	includePos = options["Include position data"]
	entitiesToRemove = []

	for (chunk, slices, point) in level.getChunkSlices(box):
	
		for entity in chunk.Entities:
			x = int(entity["Pos"][0].value)
			y = int(entity["Pos"][1].value)
			z = int(entity["Pos"][2].value)
			
			if x >= box.minx and x < box.maxx and y >= box.miny and y < box.maxy and z >= box.minz and z < box.maxz:
				entitiesToRemove.append((chunk, entity))

				level.setBlockAt(x, y, z, 52)

				spawner = TileEntity.Create("MobSpawner")
				TileEntity.setpos(spawner, (x, y, z))
				spawner["Delay"] = TAG_Short(120)
				spawner["SpawnData"] = entity
				if not includePos:
					del spawner["SpawnData"]["Pos"]
				spawner["EntityId"] = entity["id"]
				
				chunk.TileEntities.append(spawner)
		
	for (chunk, entity) in entitiesToRemove:
		chunk.Entities.remove(entity)

########NEW FILE########
__FILENAME__ = decliff
"""
DeCliff filter contributed by Minecraft Forums user "DrRomz"

Originally posted here:
http://www.minecraftforum.net/topic/13807-mcedit-minecraft-world-editor-compatible-with-mc-beta-18/page__st__3940__p__7648793#entry7648793
"""
from numpy import zeros, array
import itertools
from pymclevel import alphaMaterials
am = alphaMaterials

# Consider below materials when determining terrain height
blocks = [
  am.Stone,
  am.Grass,
  am.Dirt,
  am.Bedrock,
  am.Sand,
  am.Sandstone,
  am.Clay,
  am.Gravel,
  am.GoldOre,
  am.IronOre,
  am.CoalOre,
  am.LapisLazuliOre,
  am.DiamondOre,
  am.RedstoneOre,
  am.RedstoneOreGlowing,
  am.Netherrack,
  am.SoulSand,
  am.Glowstone
]
terrainBlocktypes = [b.ID for b in blocks]
terrainBlockmask = zeros((256,), dtype='bool')

# Truth table used to calculate terrain height
# trees, leaves, etc. sit on top of terrain
terrainBlockmask[terrainBlocktypes] = True

inputs = (
    # Option to limit change to raise_cliff_floor / lower_cliff_top
    # Default is to adjust both and meet somewhere in the middle
    ("Raise/Lower", ("Both", "Lower Only", "Raise Only")),
)


#
# Calculate the maximum adjustment that can be made from
# cliff_pos in direction dir (-1/1) keeping terain at most
# maxstep blocks away from previous column
def maxadj(heightmap, slice_no, cliff_pos, dir, pushup, maxstep, slice_width):
    ret = 0
    if dir < 0:
        if cliff_pos < 2:
            return 0
        end = 0
    else:
        if cliff_pos > slice_width - 2:
            return 0
        end = slice_width - 1

    for cur_pos in range(cliff_pos, end, dir):
        if pushup:
            ret = ret + \
               max([0, maxstep - dir * heightmap[slice_no, cur_pos] + \
               dir * heightmap[slice_no, cur_pos + dir]])
        else:
            ret = ret + \
               min([0, -maxstep + dir * heightmap[slice_no, cur_pos] - \
               dir * heightmap[slice_no, cur_pos + dir]])

    return ret


#
# Raise/lower column at cliff face by adj and decrement change as we move away
# from the face. Each level will be at most maxstep blocks from those beside it.
#
# This function dosn't actually change anything, but just sets array 'new'
# with the desired height.
def adjheight(orig, new, slice_no, cliff_pos, dir, adj, can_adj, maxstep, slice_width):
    cur_adj = adj
    prev = 0
    done_adj = 0

    if dir < 0:
        end = 1
    else:
        end = slice_width - 1

    if adj == 0 or can_adj == 0:
        for cur_pos in range(cliff_pos, end, dir):
            new[slice_no, cur_pos] = orig[slice_no, cur_pos]
    else:

        for cur_pos in range(cliff_pos, end, dir):
            if adj > 0:
                done_adj = done_adj + \
                           max([0, maxstep - orig[slice_no, cur_pos] + \
                           orig[slice_no, cur_pos + dir]])

                if orig[slice_no, cur_pos] - \
                    orig[slice_no, cur_pos + dir] > 0:
                    cur_adj = max([0, cur_adj - orig[slice_no, cur_pos] + \
                            orig[slice_no, cur_pos + dir]])
                    prev = adj - cur_adj
            else:
                done_adj = done_adj + \
                           min([0, -maxstep + \
                               orig[slice_no, cur_pos] - \
                               orig[slice_no, cur_pos + dir]])
                if orig[slice_no, cur_pos] - \
                   orig[slice_no, cur_pos + dir] > 0:
                    cur_adj = min([0, cur_adj + orig[slice_no, cur_pos] - orig[slice_no, cur_pos + dir]])
                    prev = adj - cur_adj
            new[slice_no, cur_pos] = max([0, orig[slice_no, cur_pos] + cur_adj])
            if cur_adj != 0 and \
               abs(prev) < abs(int(adj * done_adj / can_adj)):
                cur_adj = cur_adj + (prev - int(adj * done_adj / can_adj))
                prev = int(adj * done_adj / can_adj)

    new[slice_no, end] = orig[slice_no, end]


def perform(level, box, options):
    if box.volume > 16000000:
        raise ValueError("Volume too big for this filter method!")

    RLOption = options["Raise/Lower"]
    schema = level.extractSchematic(box)
    schema.removeEntitiesInBox(schema.bounds)
    schema.removeTileEntitiesInBox(schema.bounds)

    terrainBlocks = terrainBlockmask[schema.Blocks]

    coords = terrainBlocks.nonzero()

    # Swap values around so long edge of selected rectangle is first
    # - the long edge is assumed to run parallel to the cliff face
    #   and we want to process slices perpendicular to the face
    #  heightmap will have x,z (or z,x) index with highest ground level
    if schema.Width > schema.Length:
        heightmap = zeros((schema.Width, schema.Length), dtype='float32')
        heightmap[coords[0], coords[1]] = coords[2]
        newHeightmap = zeros((schema.Width, schema.Length), dtype='uint16')
        slice_count = schema.Width
        slice_width = schema.Length
    else:
        heightmap = zeros((schema.Length, schema.Width), dtype='float32')
        heightmap[coords[1], coords[0]] = coords[2]
        newHeightmap = zeros((schema.Length, schema.Width), dtype='uint16')
        slice_count = schema.Length
        slice_width = schema.Width

    nonTerrainBlocks = ~terrainBlocks
    nonTerrainBlocks &= schema.Blocks != 0

    for slice_no in range(0, slice_count):

        cliff_height = 0
        # determine pos and height of cliff in this slice
        for cur_pos in range(0, slice_width - 1):
            if abs(heightmap[slice_no, cur_pos] - \
                   heightmap[slice_no, cur_pos + 1]) > abs(cliff_height):
                cliff_height = \
                   heightmap[slice_no, cur_pos] - \
                   heightmap[slice_no, cur_pos + 1]
                cliff_pos = cur_pos

        if abs(cliff_height) < 2:
            # nothing to adjust - just copy heightmap to newHightmap
            adjheight(heightmap, newHeightmap, slice_no, 0, 1, 0, 1, 1, slice_width)
            continue

        # Try to keep adjusted columns within 1 column of their neighbours
        # but ramp up to 4 blocks up/down on each column when needed
        for max_step in range(1, 4):

            can_left = maxadj(heightmap, slice_no, cliff_pos, -1, cliff_height < 0, max_step, slice_width)
            can_right = maxadj(heightmap, slice_no, cliff_pos + 1, 1, cliff_height > 0, max_step, slice_width)

            if can_right < 0 and RLOption == "Raise Only":
                can_right = 0
            if can_right > 0 and RLOption == "Lower Only":
                can_right = 0
            if can_left < 0 and RLOption == "Raise Only":
                can_left = 0
            if can_left > 0 and RLOption == "Lower Only":
                can_left = 0

            if cliff_height < 0 and can_right - can_left < cliff_height:
                if abs(can_left) > abs(can_right):
                    adj_left = -1 * (cliff_height - max([int(cliff_height / 2), can_right]))
                    adj_right = cliff_height + adj_left
                else:
                    adj_right = cliff_height - max([int(cliff_height / 2), -can_left])
                    adj_left = -1 * (cliff_height - adj_right + 1)
            else:
                if cliff_height > 0 and can_right - can_left > cliff_height:
                    if abs(can_left) > abs(can_right):
                        adj_left = -1 * (cliff_height - min([int(cliff_height / 2), can_right]))
                        adj_right = cliff_height + adj_left
                    else:
                        adj_right = cliff_height - min([int(cliff_height / 2), -can_left]) - 1
                        adj_left = -1 * (cliff_height - adj_right)
                else:
                    adj_right = 0
                    adj_left = 0
                    continue
            break

        adjheight(heightmap, newHeightmap, slice_no, cliff_pos, -1, adj_left, can_left, max_step, slice_width)
        adjheight(heightmap, newHeightmap, slice_no, cliff_pos + 1, 1, adj_right, can_right, max_step, slice_width)

    # OK, newHeightMap has new height for each column
    # so it's just a matter of moving everything up/down
    for x, z in itertools.product(xrange(1, schema.Width - 1), xrange(1, schema.Length - 1)):

        if schema.Width > schema.Length:
            oh = heightmap[x, z]
            nh = newHeightmap[x, z]
        else:
            oh = heightmap[z, x]
            nh = newHeightmap[z, x]

        delta = nh - oh

        column = array(schema.Blocks[x, z])
        # Keep bottom 5 blocks, so we don't loose bedrock
        keep = min([5, nh])

        Waterdepth = 0
        # Detect Water on top
        if column[oh + 1:oh + 2] == am.Water.ID or \
           column[oh + 1:oh + 2] == am.Ice.ID:
            for cur_pos in range(oh + 1, schema.Height):
                if column[cur_pos:cur_pos + 1] != am.Water.ID and \
                  column[cur_pos:cur_pos + 1] != am.Ice.ID: break
                Waterdepth = Waterdepth + 1

        if delta == 0:
            column[oh:] = schema.Blocks[x, z, oh:]

        if delta < 0:
            # Moving column down
            column[keep:delta] = schema.Blocks[x, z, keep - delta:]
            column[delta:] = am.Air.ID
            if Waterdepth > 0:
                # Avoid steping small lakes, etc on cliff top
                # replace with dirt 'n grass
                column[nh:nh + 1] = am.Grass.ID
                column[nh + 1:nh + 1 + delta] = am.Air.ID
        if delta > 0:
            # Moving column up
            column[keep + delta:] = schema.Blocks[x, z, keep:-delta]
            # Put stone in gap at the bottom
            column[keep:keep + delta] = am.Stone.ID

            if Waterdepth > 0:
                if Waterdepth > delta:
                    # Retain Ice
                    if column[nh + Waterdepth:nh + Waterdepth + 1] == am.Ice.ID:
                        column[nh + Waterdepth - delta:nh + 1 + Waterdepth - delta] = \
                            am.Ice.ID
                    column[nh + 1 + Waterdepth - delta:nh + 1 + Waterdepth] = am.Air.ID
                else:
                    if Waterdepth < delta - 2:
                        column[nh:nh + 1] = am.Grass.ID
                        column[nh + 1:nh + 1 + Waterdepth] = am.Air.ID
                    else:
                        # Beach at the edge
                        column[nh - 4:nh - 2] = am.Sandstone.ID
                        column[nh - 2:nh + 1] = am.Sand.ID
                        column[nh + 1:nh + 1 + Waterdepth] = am.Air.ID

        schema.Blocks[x, z] = column

    level.copyBlocksFrom(schema, schema.bounds, box.origin)

########NEW FILE########
__FILENAME__ = filterdemo

# the inputs list tells MCEdit what kind of options to present to the user.
# each item is a (name, value) pair.  name is a text string acting
# both as a text label for the input on-screen and a key for the 'options'
# parameter to perform(). value and its type indicate allowable and
# default values for the option:

#    True or False:  creates a checkbox with the given value as default
#    int or float value: creates a value input with the given value as default
#        int values create fields that only accept integers.
#    tuple of numbers: a tuple of ints or floats creates a value input with minimum and
#        maximum values. a 2-tuple specifies (min, max) with min as default.
#        a 3-tuple specifies (default, min, max)
#    tuple of strings: a tuple of strings creates a popup menu whose entries are
#        labeled with the given strings. the first item in the tuple is selected
#        by default. returns one of the strings in the tuple.
#    "blocktype" as a string: creates a button the user can click to choose
#        a block type in a list. returns a Block object. the object has 'ID'
#        and 'blockData' attributes.

# this dictionary creates an integer input with range (-128, 128) and default 4,
# a blocktype picker, a floating-point input with no limits and default 15.0,
# a checkbox initially checked, and a menu of choices

inputs = (
  ("Depth", (4, -128, 128)),
  ("Pick a block:", "blocktype"),
  ("Fractal complexity", 15.0),
  ("Enable thrusters", True),
  ("Access method", ("Use blockAt", "Use temp schematic", "Use chunk slices")),
)

# perform() is the main entry point of a filter. Its parameters are
# a MCLevel instance, a BoundingBox, and an options dictionary.
# The options dictionary will have keys corresponding to the keys specified above,
# and values reflecting the user's input.

# you get undo for free: everything within 'box' is copied to a temporary buffer
# before perform is called, and then copied back when the user asks to undo


def perform(level, box, options):
    blockType = options["Pick a block:"].ID
    complexity = options["Fractal complexity"]
    if options["Enable thrusters"]:
        # Errors will alert the user and print a traceback to the console.
        raise NotImplementedError("Thrusters not attached!")

    method = options["Access method"]

    # There are a few general ways of accessing a level's blocks
    # The first is using level.blockAt and level.setBlockAt
    # These are slower than the other two methods, but easier to start using
    if method == "Use blockAt":
        for x in xrange(box.minx, box.maxx):
            for z in xrange(box.minz, box.maxz):
                for y in xrange(box.miny, box.maxy):  # nested loops can be slow

                    # replaces gold with TNT. straightforward.
                    if level.blockAt(x, y, z) == 14:
                        level.setBlockAt(x, y, z, 46)


    # The second is to extract the segment of interest into a contiguous array
    # using level.extractSchematic. this simplifies using numpy but at the cost
    # of the temporary buffer and the risk of a memory error on 32-bit systems.

    if method == "Use temp schematic":
        temp = level.extractSchematic(box)

        # remove any entities in the temp.  this is an ugly move
        # because copyBlocksFrom actually copies blocks, entities, everything
        temp.removeEntitiesInBox(temp.bounds)
        temp.removeTileEntitiesInBox(temp.bounds)

        # replaces gold with TNT.
        # the expression in [] creates a temporary the same size, using more memory
        temp.Blocks[temp.Blocks == 14] = 46

        level.copyBlocksFrom(temp, temp.bounds, box.origin)

    # The third method iterates over each subslice of every chunk in the area
    # using level.getChunkSlices. this method is a bit arcane, but lets you
    # visit the affected area chunk by chunk without using too much memory.

    if method == "Use chunk slices":
        for (chunk, slices, point) in level.getChunkSlices(box):
            # chunk is an AnvilChunk object with attributes:
            # Blocks, Data, Entities, and TileEntities
            # Blocks and Data can be indexed using slices:
            blocks = chunk.Blocks[slices]

            # blocks now contains a "view" on the part of the chunk's blocks
            # that lie in the selection. This "view" is a numpy object that
            # accesses only a subsection of the original array, without copying

            # once again, gold into TNT
            blocks[blocks == 14] = 46

            # notify the world that the chunk changed
            # this gives finer control over which chunks are dirtied
            # you can call chunk.chunkChanged(False) if you want to dirty it
            # but not run the lighting calc later.

            chunk.chunkChanged()

    # You can also access the level any way you want
    # Beware though, you only get to undo the area within the specified box

    pos = level.getPlayerPosition()
    cpos = pos[0] >> 4, pos[2] >> 4
    chunk = level.getChunk(*cpos)
    chunk.Blocks[::4, ::4, :64] = 46  # replace every 4x4th column of land with TNT

########NEW FILE########
__FILENAME__ = floodwater
from numpy import *
from pymclevel import alphaMaterials, faceDirections, FaceYIncreasing
from collections import deque
import datetime

displayName = "Classic Water Flood"
inputs = (
  ("Makes water in the region flood outwards and downwards, becoming full source blocks in the process. This is similar to Minecraft Classic water.", "label"),
  ("Flood Water", True),
  ("Flood Lava", False),
)


def perform(level, box, options):

    def floodFluid(waterIDs, waterID):
        waterTable = zeros(256, dtype='bool')
        waterTable[waterIDs] = True

        coords = []
        for chunk, slices, point in level.getChunkSlices(box):
            water = waterTable[chunk.Blocks[slices]]
            chunk.Data[slices][water] = 0  # source block

            x, z, y = water.nonzero()
            x = x + (point[0] + box.minx)
            z = z + (point[2] + box.minz)
            y = y + (point[1] + box.miny)
            coords.append(transpose((x, y, z)))

        print "Stacking coords..."
        coords = vstack(tuple(coords))

        def processCoords(coords):
            newcoords = deque()

            for (x, y, z) in coords:
                for _dir, offsets in faceDirections:
                    if _dir == FaceYIncreasing:
                        continue

                    dx, dy, dz = offsets
                    p = (x + dx, y + dy, z + dz)
                    if p not in box:
                        continue

                    nx, ny, nz = p
                    if level.blockAt(nx, ny, nz) == 0:
                        level.setBlockAt(nx, ny, nz, waterID)
                        newcoords.append(p)

            return newcoords

        def spread(coords):
            while len(coords):
                start = datetime.datetime.now()

                num = len(coords)
                print "Did {0} coords in ".format(num),
                coords = processCoords(coords)
                d = datetime.datetime.now() - start
                print d
                yield "Did {0} coords in {1}".format(num, d)

        level.showProgress("Spreading water...", spread(coords), cancel=True)

    if options["Flood Water"]:
        waterIDs = [alphaMaterials.WaterActive.ID, alphaMaterials.Water.ID]
        waterID = alphaMaterials.Water.ID
        floodFluid(waterIDs, waterID)
    if options["Flood Lava"]:
        lavaIDs = [alphaMaterials.LavaActive.ID, alphaMaterials.Lava.ID]
        lavaID = alphaMaterials.Lava.ID
        floodFluid(lavaIDs, lavaID)

########NEW FILE########
__FILENAME__ = Forester
# Version 5
'''This takes a base MineCraft level and adds or edits trees.
Place it in the folder where the save files are (usually .../.minecraft/saves)
Requires mcInterface.py in the same folder.'''

# Here are the variables you can edit.

# This is the name of the map to edit.
# Make a backup if you are experimenting!
LOADNAME = "LevelSave"

# How many trees do you want to add?
TREECOUNT = 12

# Where do you want the new trees?
# X, and Z are the map coordinates
X = 66
Z = -315
# How large an area do you want the trees to be in?
# for example, RADIUS = 10 will make place trees randomly in
# a circular area 20 blocks wide.
RADIUS = 80
# NOTE: tree density will be higher in the center than at the edges.

# Which shapes would you like the trees to be?
# these first three are best suited for small heights, from 5 - 10
# "normal" is the normal minecraft shape, it only gets taller and shorter
# "bamboo" a trunk with foliage, it only gets taller and shorter
# "palm" a trunk with a fan at the top, only gets taller and shorter
# "stickly" selects randomly from "normal", "bamboo" and "palm"
# these last five are best suited for very large trees, heights greater than 8
# "round" procedural spherical shaped tree, can scale up to immense size
# "cone" procedural, like a pine tree, also can scale up to immense size
# "procedural" selects randomly from "round" and "conical"
# "rainforest" many slender trees, most at the lower range of the height,
# with a few at the upper end.
# "mangrove" makes mangrove trees (see PLANTON below).
SHAPE = "procedural"

# What height should the trees be?
# Specifies the average height of the tree
# Examples:
# 5 is normal minecraft tree
# 3 is minecraft tree with foliage flush with the ground
# 10 is very tall trees, they will be hard to chop down
# NOTE: for round and conical, this affects the foliage size as well.

# CENTERHEIGHT is the height of the trees at the center of the area
# ie, when radius = 0
CENTERHEIGHT = 55

# EDGEHEIGHT is the height at the trees at the edge of the area.
# ie, when radius = RADIUS
EDGEHEIGHT = 25

# What should the variation in HEIGHT be?
# actual value +- variation
# default is 1
# Example:
# HEIGHT = 8 and HEIGHTVARIATION = 3 will result in
# trunk heights from 5 to 11
# value is clipped to a max of HEIGHT
# for a good rainforest, set this value not more than 1/2 of HEIGHT
HEIGHTVARIATION = 12

# Do you want branches, trunk, and roots?
# True makes all of that
# False does not create the trunk and branches, or the roots (even if they are
# enabled further down)
WOOD = True

# Trunk thickness multiplyer
# from zero (super thin trunk) to whatever huge number you can think of.
# Only works if SHAPE is not a "stickly" subtype
# Example:
# 1.0 is the default, it makes decently normal sized trunks
# 0.3 makes very thin trunks
# 4.0 makes a thick trunk (good for HOLLOWTRUNK).
# 10.5 will make a huge thick trunk.  Not even kidding. Makes spacious
# hollow trunks though!
TRUNKTHICKNESS = 1.0

# Trunk height, as a fraction of the tree
# Only works on "round" shaped trees
# Sets the height of the crown, where the trunk ends and splits
# Examples:
# 0.7 the default value, a bit more than half of the height
# 0.3 good for a fan-like tree
# 1.0 the trunk will extend to the top of the tree, and there will be no crown
# 2.0 the trunk will extend out the top of the foliage, making the tree appear
# like a cluster of green grapes impaled on a spike.
TRUNKHEIGHT = 0.7

# Do you want the trunk and tree broken off at the top?
# removes about half of the top of the trunk, and any foliage
# and branches that would attach above it.
# Only works if SHAPE is not a "stickly" subtype
# This results in trees that are shorter than the height settings
# True does that stuff
# False makes a normal tree (default)
BROKENTRUNK = False
# Note, this works well with HOLLOWTRUNK (below) turned on as well.

# Do you want the trunk to be hollow (or filled) inside?
# Only works with larger sized trunks.
# Only works if SHAPE is not a "stickly" subtype
# True makes the trunk hollow (or filled with other stuff)
# False makes a solid trunk (default)
HOLLOWTRUNK = False
# Note, this works well with BROKENTRUNK set to true (above)
# Further note, you may want to use a large value for TRUNKTHICKNESS

# How many branches should there be?
# General multiplyer for the number of branches
# However, it will not make more branches than foliage clusters
# so to garuntee a branch to every foliage cluster, set it very high, like 10000
# this also affects the number of roots, if they are enabled.
# Examples:
# 1.0 is normal
# 0.5 will make half as many branches
# 2.0 will make twice as mnay branches
# 10000 will make a branch to every foliage cluster (I'm pretty sure)
BRANCHDENSITY = 1.0

# do you want roots from the bottom of the tree?
# Only works if SHAPE is "round" or "cone" or "procedural"
# "yes" roots will penetrate anything, and may enter underground caves.
# "tostone" roots will be stopped by stone (default see STOPSROOTS below).
#    There may be some penetration.
# "hanging" will hang downward in air.  Good for "floating" type maps
#    (I really miss "floating" terrain as a default option)
# "no" roots will not be generated
ROOTS = "tostone"

# Do you want root buttresses?
# These make the trunk not-round at the base, seen in tropical or old trees.
# This option generally makes the trunk larger.
# Only works if SHAPE is "round" or "cone" or "procedural"
# Options:
# True makes root butresses
# False leaves them out
ROOTBUTTRESSES = True

# Do you want leaves on the trees?
# True there will be leaves
# False there will be no leaves
FOLIAGE = True

# How thick should the foliage be
# General multiplyer for the number of foliage clusters
# Examples:
# 1.0 is normal
# 0.3 will make very sparse spotty trees, half as many foliage clusters
# 2.0 will make dense foliage, better for the "rainforests" SHAPE
FOLIAGEDENSITY = 1.0

# Limit the tree height to the top of the map?
# True the trees will not grow any higher than the top of the map
# False the trees may be cut off by the top of the map
MAPHEIGHTLIMIT = True

# add lights in the middle of foliage clusters
# for those huge trees that get so dark underneath
# or for enchanted forests that should glow and stuff
# Only works if SHAPE is "round" or "cone" or "procedural"
# 0 makes just normal trees
# 1 adds one light inside the foliage clusters for a bit of light
# 2 adds two lights around the base of each cluster, for more light
# 4 adds lights all around the base of each cluster for lots of light
LIGHTTREE = 0

# Do you want to only place trees near existing trees?
# True will only plant new trees near existing trees.
# False will not check for existing trees before planting.
# NOTE: the taller the tree, the larger the forest needs to be to qualify
# OTHER NOTE: this feature has not been extensively tested.
# IF YOU HAVE PROBLEMS: SET TO False
ONLYINFORESTS = False

#####################
# Advanced options! #
#####################

# What kind of material should the "wood" be made of?
# defaults to 17
WOODMAT = 17

# What data value should the wood blocks have?
# Some blocks, like wood, leaves, and cloth change
# apperance with different data values
# defaults to 0
WOODDATA = 0

# What kind of material should the "leaves" be made of?
# defaults to 18
LEAFMAT = 18

# What data value should the leaf blocks have?
# Some blocks, like wood, leaves, and cloth change
# apperance with different data values
# defaults to 0
LEAFDATA = 0

# What kind of material should the "lights" be made of?
# defaults to 89 (glowstone)
LIGHTMAT = 89

# What data value should the light blocks have?
# defaults to 0
LIGHTDATA = 0

# What kind of material would you like the "hollow" trunk filled with?
# defaults to 0 (air)
TRUNKFILLMAT = 0

# What data value would you like the "hollow" trunk filled with?
# defaults to 0
TRUNKFILLDATA = 0

# What kind of blocks should the trees be planted on?
# Use the Minecraft index.
# Examples
# 2 is grass (the default)
# 3 is dirt
# 1 is stone (an odd choice)
# 12 is sand (for beach or desert)
# 9 is water (if you want an aquatic forest)
# this is a list, and comma seperated.
# example: [2, 3]
# will plant trees on grass or dirt
PLANTON = [2]

# What kind of blocks should stop the roots?
# a list of block id numbers like PLANTON
# Only works if ROOTS = "tostone"
# default, [1] (stone)
# if you want it to be stopped by other block types, add it to the list
STOPSROOTS = [1]

# What kind of blocks should stop branches?
# same as STOPSROOTS above, but is always turned on
# defaults to stone, cobblestone, and glass
# set it to [] if you want branches to go through everything
STOPSBRANCHES = [1, 4, 20]

# How do you want to interpolate from center to edge?
# "linear" makes a cone-shaped forest
# This is the only option at present
INTERPOLATION = "linear"

# Do a rough recalculation of the lighting?
# Slows it down to do a very rough and incomplete re-light.
# If you want to really fix the lighting, use a seperate re-lighting tool.
# True  do the rough fix
# False don't bother
LIGHTINGFIX = True

# How many times do you want to try to find a location?
# it will stop planing after MAXTRIES has been exceeded.
# Set to smaller numbers to abort quicker, or larger numbers
# if you want to keep trying for a while.
# NOTE: the number of trees will not exceed this number
# Default: 1000
MAXTRIES = 1000

# Do you want lots of text telling you waht is going on?
# True lots of text (default). Good for debugging.
# False no text
VERBOSE = True

##############################################################
#  Don't edit below here unless you know what you are doing  #
##############################################################

# input filtering
TREECOUNT = int(TREECOUNT)
if TREECOUNT < 0:
    TREECOUNT = 0
if SHAPE not in ["normal", "bamboo", "palm", "stickly",
                 "round", "cone", "procedural",
                 "rainforest", "mangrove"]:
    if VERBOSE:
        print("SHAPE not set correctly, using 'procedural'.")
    SHAPE = "procedural"
if CENTERHEIGHT < 1:
    CENTERHEIGHT = 1
if EDGEHEIGHT < 1:
    EDGEHEIGHT = 1
minheight = min(CENTERHEIGHT, EDGEHEIGHT)
if HEIGHTVARIATION > minheight:
    HEIGHTVARIATION = minheight
if INTERPOLATION not in ["linear"]:
    if VERBOSE:
        print("INTERPOLATION not set correctly, using 'linear'.")
    INTERPOLATION = "linear"
if WOOD not in [True, False]:
    if VERBOSE:
        print("WOOD not set correctly, using True")
    WOOD = True
if TRUNKTHICKNESS < 0.0:
    TRUNKTHICKNESS = 0.0
if TRUNKHEIGHT < 0.0:
    TRUNKHEIGHT = 0.0
if ROOTS not in ["yes", "tostone", "hanging", "no"]:
    if VERBOSE:
        print("ROOTS not set correctly, using 'no' and creating no roots")
    ROOTS = "no"
if ROOTBUTTRESSES not in [True, False]:
    if VERBOSE:
        print("ROOTBUTTRESSES not set correctly, using False")
    ROOTBUTTRESSES = False
if FOLIAGE not in [True, False]:
    if VERBOSE:
        print("FOLIAGE not set correctly, using True")
    ROOTBUTTRESSES = True
if FOLIAGEDENSITY < 0.0:
    FOLIAGEDENSITY = 0.0
if BRANCHDENSITY < 0.0:
    BRANCHDENSITY = 0.0
if MAPHEIGHTLIMIT not in [True, False]:
    if VERBOSE:
        print("MAPHEIGHTLIMIT not set correctly, using False")
    MAPHEIGHTLIMIT = False
if LIGHTTREE not in [0, 1, 2, 4]:
    if VERBOSE:
        print("LIGHTTREE not set correctly, using 0 for no torches")
    LIGHTTREE = 0
# assemble the material dictionaries
WOODINFO = {'B': WOODMAT, 'D': WOODDATA}
LEAFINFO = {'B': LEAFMAT, 'D': LEAFDATA}
LIGHTINFO = {'B': LIGHTMAT, 'D': LIGHTDATA}
TRUNKFILLINFO = {'B': TRUNKFILLMAT, 'D': TRUNKFILLDATA}

# The following is an interface class for .mclevel data for minecraft savefiles.
# The following also includes a useful coordinate to index convertor and several
# other useful functions.

import mcInterface

#some handy functions


def dist_to_mat(cord, vec, matidxlist, mcmap, invert=False, limit=False):
    '''travel from cord along vec and return how far it was to a point of matidx

    the distance is returned in number of iterations.  If the edge of the map
    is reached, then return the number of iterations as well.
    if invert == True, search for anything other than those in matidxlist
    '''
    assert isinstance(mcmap, mcInterface.SaveFile)
    block = mcmap.block
    curcord = [i + .5 for i in cord]
    iterations = 0
    on_map = True
    while on_map:
        x = int(curcord[0])
        y = int(curcord[1])
        z = int(curcord[2])
        return_dict = block(x, y, z)
        if return_dict is None:
            break
        else:
            block_value = return_dict['B']
        if (block_value in matidxlist) and (invert == False):
            break
        elif (block_value not in matidxlist) and invert:
            break
        else:
            curcord = [curcord[i] + vec[i] for i in range(3)]
            iterations += 1
        if limit and iterations > limit:
            break
    return iterations

# This is the end of the MCLevel interface.

# Now, on to the actual code.

from random import random, choice, sample
from math import sqrt, sin, cos, pi


def calc_column_lighting(x, z, mclevel):
    '''Recalculate the sky lighting of the column.'''

    # Begin at the top with sky light level 15.
    cur_light = 15
    # traverse the column until cur_light == 0
    # and the existing light values are also zero.
    y = 127
    get_block = mclevel.block
    set_block = mclevel.set_block
    get_height = mclevel.retrieve_heightmap
    set_height = mclevel.set_heightmap
    #get the current heightmap
    cur_height = get_height(x, z)
    # set a flag that the highest point has been updated
    height_updated = False
    # if this doesn't exist, the block doesn't exist either, abort.
    if cur_height is None:
        return None
    light_reduction_lookup = {0: 0, 20: 0, 18: 1, 8: 2, 79: 2}
    while True:
        #get the block sky light and type
        block_info = get_block(x, y, z, 'BS')
        block_light = block_info['S']
        block_type = block_info['B']
        # update the height map if it hasn't been updated yet,
        # and the current block reduces light
        if (not height_updated) and (block_type not in (0, 20)):
            new_height = y + 1
            if new_height == 128:
                new_height = 127
            set_height(x, new_height, z)
            height_updated = True
        #compare block with cur_light, escape if both 0
        if block_light == 0 and cur_light == 0:
            break
        #set the block light if necessary
        if block_light != cur_light:
            set_block(x, y, z, {'S': cur_light})
        #set the new cur_light
        if block_type in light_reduction_lookup:
            # partial light reduction
            light_reduction = light_reduction_lookup[block_type]
        else:
            # full light reduction
            light_reduction = 16
        cur_light += -light_reduction
        if cur_light < 0:
            cur_light = 0
        #increment and check y
        y += -1
        if y < 0:
            break


class ReLight(object):
    '''keep track of which squares need to be relit, and then relight them'''
    def add(self, x, z):
        coords = (x, z)
        self.all_columns.add(coords)

    def calc_lighting(self):
        mclevel = self.save_file
        for column_coords in self.all_columns:
            # recalculate the lighting
            x = column_coords[0]
            z = column_coords[1]
            calc_column_lighting(x, z, mclevel)

    def __init__(self):
        self.all_columns = set()
        self.save_file = None

relight_master = ReLight()


def assign_value(x, y, z, values, save_file):
    '''Assign an index value to a location in mcmap.

    If the index is outside the bounds of the map, return None.  If the
    assignment succeeds, return True.
    '''
    if y > 127:
        return None
    result = save_file.set_block(x, y, z, values)
    if LIGHTINGFIX:
        relight_master.add(x, z)
    return result


class Tree(object):
    '''Set up the interface for tree objects.  Designed for subclassing.
    '''
    def prepare(self, mcmap):
        '''initialize the internal values for the Tree object.
        '''
        return None

    def maketrunk(self, mcmap):
        '''Generate the trunk and enter it in mcmap.
        '''
        return None

    def makefoliage(self, mcmap):
        """Generate the foliage and enter it in mcmap.

        Note, foliage will disintegrate if there is no log nearby"""
        return None

    def copy(self, other):
        '''Copy the essential values of the other tree object into self.
        '''
        self.pos = other.pos
        self.height = other.height

    def __init__(self, pos=[0, 0, 0], height=1):
        '''Accept values for the position and height of a tree.

        Store them in self.
        '''
        self.pos = pos
        self.height = height


class StickTree(Tree):
    '''Set up the trunk for trees with a trunk width of 1 and simple geometry.

    Designed for sublcassing.  Only makes the trunk.
    '''
    def maketrunk(self, mcmap):
        x = self.pos[0]
        y = self.pos[1]
        z = self.pos[2]
        for i in range(self.height):
            assign_value(x, y, z, WOODINFO, mcmap)
            y += 1


class NormalTree(StickTree):
    '''Set up the foliage for a 'normal' tree.

    This tree will be a single bulb of foliage above a single width trunk.
    This shape is very similar to the default Minecraft tree.
    '''
    def makefoliage(self, mcmap):
        """note, foliage will disintegrate if there is no foliage below, or
        if there is no "log" block within range 2 (square) at the same level or
        one level below"""
        topy = self.pos[1] + self.height - 1
        start = topy - 2
        end = topy + 2
        for y in range(start, end):
            if y > start + 1:
                rad = 1
            else:
                rad = 2
            for xoff in range(-rad, rad + 1):
                for zoff in range(-rad, rad + 1):
                    if (random() > 0.618
                        and abs(xoff) == abs(zoff)
                        and abs(xoff) == rad
                        ):
                        continue

                    x = self.pos[0] + xoff
                    z = self.pos[2] + zoff

                    assign_value(x, y, z, LEAFINFO, mcmap)


class BambooTree(StickTree):
    '''Set up the foliage for a bamboo tree.

    Make foliage sparse and adjacent to the trunk.
    '''
    def makefoliage(self, mcmap):
        start = self.pos[1]
        end = self.pos[1] + self.height + 1
        for y in range(start, end):
            for i in [0, 1]:
                xoff = choice([-1, 1])
                zoff = choice([-1, 1])
                x = self.pos[0] + xoff
                z = self.pos[2] + zoff
                assign_value(x, y, z, LEAFINFO, mcmap)


class PalmTree(StickTree):
    '''Set up the foliage for a palm tree.

    Make foliage stick out in four directions from the top of the trunk.
    '''
    def makefoliage(self, mcmap):
        y = self.pos[1] + self.height
        for xoff in range(-2, 3):
            for zoff in range(-2, 3):
                if abs(xoff) == abs(zoff):
                    x = self.pos[0] + xoff
                    z = self.pos[2] + zoff
                    assign_value(x, y, z, LEAFINFO, mcmap)


class ProceduralTree(Tree):
    '''Set up the methods for a larger more complicated tree.

    This tree type has roots, a trunk, and branches all of varying width,
    and many foliage clusters.
    MUST BE SUBCLASSED.  Specifically, self.foliage_shape must be set.
    Subclass 'prepare' and 'shapefunc' to make different shaped trees.
    '''

    def crossection(self, center, radius, diraxis, matidx, mcmap):
        '''Create a round section of type matidx in mcmap.

        Passed values:
        center = [x, y, z] for the coordinates of the center block
        radius = <number> as the radius of the section.  May be a float or int.
        diraxis: The list index for the axis to make the section
        perpendicular to.  0 indicates the x axis, 1 the y, 2 the z.  The
        section will extend along the other two axies.
        matidx = <int> the integer value to make the section out of.
        mcmap = the array generated by make_mcmap
        matdata = <int> the integer value to make the block data value.
        '''
        rad = int(radius + .618)
        if rad <= 0:
            return None
        secidx1 = (diraxis - 1) % 3
        secidx2 = (1 + diraxis) % 3
        coord = [0, 0, 0]
        for off1 in range(-rad, rad + 1):
            for off2 in range(-rad, rad + 1):
                thisdist = sqrt((abs(off1) + .5) ** 2 + (abs(off2) + .5) ** 2)
                if thisdist > radius:
                    continue
                pri = center[diraxis]
                sec1 = center[secidx1] + off1
                sec2 = center[secidx2] + off2
                coord[diraxis] = pri
                coord[secidx1] = sec1
                coord[secidx2] = sec2
                assign_value(coord[0], coord[1], coord[2], matidx, mcmap)

    def shapefunc(self, y):
        '''Take y and return a radius for the location of the foliage cluster.

        If no foliage cluster is to be created, return None
        Designed for sublcassing.  Only makes clusters close to the trunk.
        '''
        if random() < 100. / (self.height ** 2) and y < self.trunkheight:
            return self.height * .12
        return None

    def foliagecluster(self, center, mcmap):
        '''generate a round cluster of foliage at the location center.

        The shape of the cluster is defined by the list self.foliage_shape.
        This list must be set in a subclass of ProceduralTree.
        '''
        level_radius = self.foliage_shape
        x = center[0]
        y = center[1]
        z = center[2]
        for i in level_radius:
            self.crossection([x, y, z], i, 1, LEAFINFO, mcmap)
            y += 1

    def taperedcylinder(self, start, end, startsize, endsize, mcmap, blockdata):
        '''Create a tapered cylinder in mcmap.

        start and end are the beginning and ending coordinates of form [x, y, z].
        startsize and endsize are the beginning and ending radius.
        The material of the cylinder is WOODMAT.
        '''

        # delta is the coordinate vector for the difference between
        # start and end.
        delta = [int(end[i] - start[i]) for i in range(3)]
        # primidx is the index (0, 1, or 2 for x, y, z) for the coordinate
        # which has the largest overall delta.
        maxdist = max(delta, key=abs)
        if maxdist == 0:
            return None
        primidx = delta.index(maxdist)
        # secidx1 and secidx2 are the remaining indicies out of [0, 1, 2].
        secidx1 = (primidx - 1) % 3
        secidx2 = (1 + primidx) % 3
        # primsign is the digit 1 or -1 depending on whether the limb is headed
        # along the positive or negative primidx axis.
        primsign = int(delta[primidx] / abs(delta[primidx]))
        # secdelta1 and ...2 are the amount the associated values change
        # for every step along the prime axis.
        secdelta1 = delta[secidx1]
        secfac1 = float(secdelta1) / delta[primidx]
        secdelta2 = delta[secidx2]
        secfac2 = float(secdelta2) / delta[primidx]
        # Initialize coord.  These values could be anything, since
        # they are overwritten.
        coord = [0, 0, 0]
        # Loop through each crossection along the primary axis,
        # from start to end.
        endoffset = delta[primidx] + primsign
        for primoffset in range(0, endoffset, primsign):
            primloc = start[primidx] + primoffset
            secloc1 = int(start[secidx1] + primoffset * secfac1)
            secloc2 = int(start[secidx2] + primoffset * secfac2)
            coord[primidx] = primloc
            coord[secidx1] = secloc1
            coord[secidx2] = secloc2
            primdist = abs(delta[primidx])
            radius = endsize + (startsize - endsize) * abs(delta[primidx]
                                - primoffset) / primdist
            self.crossection(coord, radius, primidx, blockdata, mcmap)

    def makefoliage(self, mcmap):
        '''Generate the foliage for the tree in mcmap.
        '''
        """note, foliage will disintegrate if there is no foliage below, or
        if there is no "log" block within range 2 (square) at the same level or
        one level below"""
        foliage_coords = self.foliage_cords
        for coord in foliage_coords:
            self.foliagecluster(coord, mcmap)
        for cord in foliage_coords:
            assign_value(cord[0], cord[1], cord[2], WOODINFO, mcmap)
            if LIGHTTREE == 1:
                assign_value(cord[0], cord[1] + 1, cord[2], LIGHTINFO, mcmap)
            elif LIGHTTREE in [2, 4]:
                assign_value(cord[0] + 1, cord[1], cord[2], LIGHTINFO, mcmap)
                assign_value(cord[0] - 1, cord[1], cord[2], LIGHTINFO, mcmap)
                if LIGHTTREE == 4:
                    assign_value(cord[0], cord[1], cord[2] + 1, LIGHTINFO, mcmap)
                    assign_value(cord[0], cord[1], cord[2] - 1, LIGHTINFO, mcmap)

    def makebranches(self, mcmap):
        '''Generate the branches and enter them in mcmap.
        '''
        treeposition = self.pos
        height = self.height
        topy = treeposition[1] + int(self.trunkheight + 0.5)
        # endrad is the base radius of the branches at the trunk
        endrad = self.trunkradius * (1 - self.trunkheight / height)
        if endrad < 1.0:
            endrad = 1.0
        for coord in self.foliage_cords:
            dist = (sqrt(float(coord[0] - treeposition[0]) ** 2 +
                            float(coord[2] - treeposition[2]) ** 2))
            ydist = coord[1] - treeposition[1]
            # value is a magic number that weights the probability
            # of generating branches properly so that
            # you get enough on small trees, but not too many
            # on larger trees.
            # Very difficult to get right... do not touch!
            value = (self.branchdensity * 220 * height) / ((ydist + dist) ** 3)
            if value < random():
                continue

            posy = coord[1]
            slope = self.branchslope + (0.5 - random()) * .16
            if coord[1] - dist * slope > topy:
                # Another random rejection, for branches between
                # the top of the trunk and the crown of the tree
                threshhold = 1 / float(height)
                if random() < threshhold:
                    continue
                branchy = topy
                basesize = endrad
            else:
                branchy = posy - dist * slope
                basesize = (endrad + (self.trunkradius - endrad) *
                         (topy - branchy) / self.trunkheight)
            startsize = (basesize * (1 + random()) * .618 *
                         (dist / height) ** 0.618)
            rndr = sqrt(random()) * basesize * 0.618
            rndang = random() * 2 * pi
            rndx = int(rndr * sin(rndang) + 0.5)
            rndz = int(rndr * cos(rndang) + 0.5)
            startcoord = [treeposition[0] + rndx,
                          int(branchy),
                          treeposition[2] + rndz]
            if startsize < 1.0:
                startsize = 1.0
            endsize = 1.0
            self.taperedcylinder(startcoord, coord, startsize, endsize,
                             mcmap, WOODINFO)

    def makeroots(self, rootbases, mcmap):
        '''generate the roots and enter them in mcmap.

        rootbases = [[x, z, base_radius], ...] and is the list of locations
        the roots can originate from, and the size of that location.
        '''
        treeposition = self.pos
        height = self.height
        for coord in self.foliage_cords:
            # First, set the threshhold for randomly selecting this
            # coordinate for root creation.
            dist = (sqrt(float(coord[0] - treeposition[0]) ** 2 +
                            float(coord[2] - treeposition[2]) ** 2))
            ydist = coord[1] - treeposition[1]
            value = (self.branchdensity * 220 * height) / ((ydist + dist) ** 3)
            # Randomly skip roots, based on the above threshold
            if value < random():
                continue
            # initialize the internal variables from a selection of
            # starting locations.
            rootbase = choice(rootbases)
            rootx = rootbase[0]
            rootz = rootbase[1]
            rootbaseradius = rootbase[2]
            # Offset the root origin location by a random amount
            # (radialy) from the starting location.
            rndr = (sqrt(random()) * rootbaseradius * .618)
            rndang = random() * 2 * pi
            rndx = int(rndr * sin(rndang) + 0.5)
            rndz = int(rndr * cos(rndang) + 0.5)
            rndy = int(random() * rootbaseradius * 0.5)
            startcoord = [rootx + rndx, treeposition[1] + rndy, rootz + rndz]
            # offset is the distance from the root base to the root tip.
            offset = [startcoord[i] - coord[i] for i in range(3)]
            # If this is a mangrove tree, make the roots longer.
            if SHAPE == "mangrove":
                offset = [int(val * 1.618 - 1.5) for val in offset]
            endcoord = [startcoord[i] + offset[i] for i in range(3)]
            rootstartsize = (rootbaseradius * 0.618 * abs(offset[1]) /
                             (height * 0.618))
            if rootstartsize < 1.0:
                rootstartsize = 1.0
            endsize = 1.0
            # If ROOTS is set to "tostone" or "hanging" we need to check
            # along the distance for collision with existing materials.
            if ROOTS in ["tostone", "hanging"]:
                offlength = sqrt(float(offset[0]) ** 2 +
                                 float(offset[1]) ** 2 +
                                 float(offset[2]) ** 2)
                if offlength < 1:
                    continue
                rootmid = endsize
                # vec is a unit vector along the direction of the root.
                vec = [offset[i] / offlength for i in range(3)]
                if ROOTS == "tostone":
                    searchindex = STOPSROOTS
                elif ROOTS == "hanging":
                    searchindex = [0]
                # startdist is how many steps to travel before starting to
                # search for the material.  It is used to ensure that large
                # roots will go some distance before changing directions
                # or stopping.
                startdist = int(random() * 6 * sqrt(rootstartsize) + 2.8)
                # searchstart is the coordinate where the search should begin
                searchstart = [startcoord[i] + startdist * vec[i]
                               for i in range(3)]
                # dist stores how far the search went (including searchstart)
                # before encountering the expected marterial.
                dist = startdist + dist_to_mat(searchstart, vec,
                                        searchindex, mcmap, limit=offlength)
                # If the distance to the material is less than the length
                # of the root, change the end point of the root to where
                # the search found the material.
                if dist < offlength:
                    # rootmid is the size of the crossection at endcoord.
                    rootmid += (rootstartsize -
                                         endsize) * (1 - dist / offlength)
                    # endcoord is the midpoint for hanging roots,
                    # and the endpoint for roots stopped by stone.
                    endcoord = [startcoord[i] + int(vec[i] * dist)
                                for i in range(3)]
                    if ROOTS == "hanging":
                        # remaining_dist is how far the root had left
                        # to go when it was stopped.
                        remaining_dist = offlength - dist
                        # Initialize bottomcord to the stopping point of
                        # the root, and then hang straight down
                        # a distance of remaining_dist.
                        bottomcord = endcoord[:]
                        bottomcord[1] += -int(remaining_dist)
                        # Make the hanging part of the hanging root.
                        self.taperedcylinder(endcoord, bottomcord,
                             rootmid, endsize, mcmap, WOODINFO)

                # make the beginning part of hanging or "tostone" roots
                self.taperedcylinder(startcoord, endcoord,
                     rootstartsize, rootmid, mcmap, WOODINFO)

            # If you aren't searching for stone or air, just make the root.
            else:
                self.taperedcylinder(startcoord, endcoord,
                             rootstartsize, endsize, mcmap, WOODINFO)

    def maketrunk(self, mcmap):
        '''Generate the trunk, roots, and branches in mcmap.
        '''
        height = self.height
        trunkheight = self.trunkheight
        trunkradius = self.trunkradius
        treeposition = self.pos
        starty = treeposition[1]
        midy = treeposition[1] + int(trunkheight * .382)
        topy = treeposition[1] + int(trunkheight + 0.5)
        # In this method, x and z are the position of the trunk.
        x = treeposition[0]
        z = treeposition[2]
        end_size_factor = trunkheight / height
        midrad = trunkradius * (1 - end_size_factor * .5)
        endrad = trunkradius * (1 - end_size_factor)
        if endrad < 1.0:
            endrad = 1.0
        if midrad < endrad:
            midrad = endrad
        # Make the root buttresses, if indicated
        if ROOTBUTTRESSES or SHAPE == "mangrove":
            # The start radius of the trunk should be a little smaller if we
            # are using root buttresses.
            startrad = trunkradius * .8
            # rootbases is used later in self.makeroots(...) as
            # starting locations for the roots.
            rootbases = [[x, z, startrad]]
            buttress_radius = trunkradius * 0.382
            # posradius is how far the root buttresses should be offset
            # from the trunk.
            posradius = trunkradius
            # In mangroves, the root buttresses are much more extended.
            if SHAPE == "mangrove":
                posradius = posradius * 2.618
            num_of_buttresses = int(sqrt(trunkradius) + 3.5)
            for i in range(num_of_buttresses):
                rndang = random() * 2 * pi
                thisposradius = posradius * (0.9 + random() * .2)
                # thisx and thisz are the x and z position for the base of
                # the root buttress.
                thisx = x + int(thisposradius * sin(rndang))
                thisz = z + int(thisposradius * cos(rndang))
                # thisbuttressradius is the radius of the buttress.
                # Currently, root buttresses do not taper.
                thisbuttressradius = buttress_radius * (0.618 + random())
                if thisbuttressradius < 1.0:
                    thisbuttressradius = 1.0
                # Make the root buttress.
                self.taperedcylinder([thisx, starty, thisz], [x, midy, z],
                                 thisbuttressradius, thisbuttressradius,
                                 mcmap, WOODINFO)
                # Add this root buttress as a possible location at
                # which roots can spawn.
                rootbases += [[thisx, thisz, thisbuttressradius]]
        else:
            # If root buttresses are turned off, set the trunk radius
            # to normal size.
            startrad = trunkradius
            rootbases = [[x, z, startrad]]
        # Make the lower and upper sections of the trunk.
        self.taperedcylinder([x, starty, z], [x, midy, z], startrad, midrad,
                         mcmap, WOODINFO)
        self.taperedcylinder([x, midy, z], [x, topy, z], midrad, endrad,
                         mcmap, WOODINFO)
        #Make the branches
        self.makebranches(mcmap)
        #Make the roots, if indicated.
        if ROOTS in ["yes", "tostone", "hanging"]:
            self.makeroots(rootbases, mcmap)
        # Hollow the trunk, if specified
        # check to make sure that the trunk is large enough to be hollow
        if trunkradius > 2 and HOLLOWTRUNK:
            # wall thickness is actually the double the wall thickness
            # it is a diameter difference, not a radius difference.
            wall_thickness = (1 + trunkradius * 0.1 * random())
            if wall_thickness < 1.3:
                wall_thickness = 1.3
            base_radius = trunkradius - wall_thickness
            if base_radius < 1:
                base_radius = 1.0
            mid_radius = midrad - wall_thickness
            top_radius = endrad - wall_thickness
            # the starting x and y can be offset by up to the wall thickness.
            base_offset = int(wall_thickness)
            x_choices = [i for i in range(x - base_offset,
                                          x + base_offset + 1)]
            start_x = choice(x_choices)
            z_choices = [i for i in range(z - base_offset,
                                          z + base_offset + 1)]
            start_z = choice(z_choices)
            self.taperedcylinder([start_x, starty, start_z], [x, midy, z],
                                 base_radius, mid_radius,
                         mcmap, TRUNKFILLINFO)
            hollow_top_y = int(topy + trunkradius + 1.5)
            self.taperedcylinder([x, midy, z], [x, hollow_top_y, z],
                                 mid_radius, top_radius,
                                 mcmap, TRUNKFILLINFO)

    def prepare(self, mcmap):
        '''Initialize the internal values for the Tree object.

        Primarily, sets up the foliage cluster locations.
        '''
        treeposition = self.pos
        self.trunkradius = .618 * sqrt(self.height * TRUNKTHICKNESS)
        if self.trunkradius < 1:
            self.trunkradius = 1
        if BROKENTRUNK:
            self.trunkheight = self.height * (.3 + random() * .4)
            yend = int(treeposition[1] + self.trunkheight + .5)
        else:
            self.trunkheight = self.height
            yend = int(treeposition[1] + self.height)
        self.branchdensity = BRANCHDENSITY / FOLIAGEDENSITY
        topy = treeposition[1] + int(self.trunkheight + 0.5)
        foliage_coords = []
        ystart = treeposition[1]
        num_of_clusters_per_y = int(1.5 + (FOLIAGEDENSITY *
                                           self.height / 19.) ** 2)
        if num_of_clusters_per_y < 1:
            num_of_clusters_per_y = 1
        # make sure we don't spend too much time off the top of the map
        if yend > 127:
            yend = 127
        if ystart > 127:
            ystart = 127
        for y in range(yend, ystart, -1):
            for i in range(num_of_clusters_per_y):
                shapefac = self.shapefunc(y - ystart)
                if shapefac is None:
                    continue
                r = (sqrt(random()) + .328) * shapefac

                theta = random() * 2 * pi
                x = int(r * sin(theta)) + treeposition[0]
                z = int(r * cos(theta)) + treeposition[2]
                # if there are values to search in STOPSBRANCHES
                # then check to see if this cluster is blocked
                # by stuff, like dirt or rock, or whatever
                if len(STOPSBRANCHES):
                    dist = (sqrt(float(x - treeposition[0]) ** 2 +
                                float(z - treeposition[2]) ** 2))
                    slope = self.branchslope
                    if y - dist * slope > topy:
                        # the top of the tree
                        starty = topy
                    else:
                        starty = y - dist * slope
                    # the start position of the search
                    start = [treeposition[0], starty, treeposition[2]]
                    offset = [x - treeposition[0],
                              y - starty,
                              z - treeposition[2]]
                    offlength = sqrt(offset[0] ** 2 + offset[1] ** 2 + offset[2] ** 2)
                    # if the branch is as short as... nothing, don't bother.
                    if offlength < 1:
                        continue
                    # unit vector for the search
                    vec = [offset[i] / offlength for i in range(3)]
                    mat_dist = dist_to_mat(start, vec, STOPSBRANCHES,
                                           mcmap, limit=offlength + 3)
                    # after all that, if you find something, don't add
                    # this coordinate to the list
                    if mat_dist < offlength + 2:
                        continue
                foliage_coords += [[x, y, z]]

        self.foliage_cords = foliage_coords


class RoundTree(ProceduralTree):
    '''This kind of tree is designed to resemble a deciduous tree.
    '''
    def prepare(self, mcmap):
        self.branchslope = 0.382
        ProceduralTree.prepare(self, mcmap)
        self.foliage_shape = [2, 3, 3, 2.5, 1.6]
        self.trunkradius = self.trunkradius * 0.8
        self.trunkheight = TRUNKHEIGHT * self.trunkheight

    def shapefunc(self, y):
        twigs = ProceduralTree.shapefunc(self, y)
        if twigs is not None:
            return twigs
        if y < self.height * (.282 + .1 * sqrt(random())):
            return None
        radius = self.height / 2.
        adj = self.height / 2. - y
        if adj == 0:
            dist = radius
        elif abs(adj) >= radius:
            dist = 0
        else:
            dist = sqrt((radius ** 2) - (adj ** 2))
        dist = dist * .618
        return dist


class ConeTree(ProceduralTree):
    '''this kind of tree is designed to resemble a conifer tree.
    '''
    # woodType is the kind of wood the tree has, a data value
    woodType = 1

    def prepare(self, mcmap):
        self.branchslope = 0.15
        ProceduralTree.prepare(self, mcmap)
        self.foliage_shape = [3, 2.6, 2, 1]
        self.trunkradius = self.trunkradius * 0.5

    def shapefunc(self, y):
        twigs = ProceduralTree.shapefunc(self, y)
        if twigs is not None:
            return twigs
        if y < self.height * (.25 + .05 * sqrt(random())):
            return None
        radius = (self.height - y) * 0.382
        if radius < 0:
            radius = 0
        return radius


class RainforestTree(ProceduralTree):
    '''This kind of tree is designed to resemble a rainforest tree.
    '''
    def prepare(self, mcmap):
        self.foliage_shape = [3.4, 2.6]
        self.branchslope = 1.0
        ProceduralTree.prepare(self, mcmap)
        self.trunkradius = self.trunkradius * 0.382
        self.trunkheight = self.trunkheight * .9

    def shapefunc(self, y):
        if y < self.height * 0.8:
            if EDGEHEIGHT < self.height:
                twigs = ProceduralTree.shapefunc(self, y)
                if (twigs is not None) and random() < 0.07:
                    return twigs
            return None
        else:
            width = self.height * .382
            topdist = (self.height - y) / (self.height * 0.2)
            dist = width * (0.618 + topdist) * (0.618 + random()) * 0.382
            return dist


class MangroveTree(RoundTree):
    '''This kind of tree is designed to resemble a mangrove tree.
    '''
    def prepare(self, mcmap):
        self.branchslope = 1.0
        RoundTree.prepare(self, mcmap)
        self.trunkradius = self.trunkradius * 0.618

    def shapefunc(self, y):
        val = RoundTree.shapefunc(self, y)
        if val is None:
            return val
        val = val * 1.618
        return val


def planttrees(mcmap, treelist):
    '''Take mcmap and add trees to random locations on the surface to treelist.
    '''
    assert isinstance(mcmap, mcInterface.SaveFile)
    # keep looping until all the trees are placed
    # calc the radius difference, for interpolation
    in_out_dif = EDGEHEIGHT - CENTERHEIGHT
    if VERBOSE:
        print('Tree Locations: x, y, z, tree height')
    tries = 0
    max_tries = MAXTRIES
    while len(treelist) < TREECOUNT:
        if tries > max_tries:
            if VERBOSE:
                print("Stopping search for tree locations after {0} tries".format(tries))
                print("If you don't have enough trees, check X, Y, RADIUS, and PLANTON")
            break
        tries += 1
        # choose a location
        rad_fraction = random()
        # this is some kind of square interpolation
        rad_fraction = 1.0 - rad_fraction
        rad_fraction **= 2
        rad_fraction = 1.0 - rad_fraction

        rad = rad_fraction * RADIUS
        ang = random() * pi * 2
        x = X + int(rad * sin(ang) + .5)
        z = Z + int(rad * cos(ang) + .5)
        # check to see if this location is suitable
        y_top = mcmap.surface_block(x, z)
        if y_top is None:
            # this location is off the map!
            continue
        if y_top['B'] in PLANTON:
            # plant the tree on the block above the ground
            # hence the " + 1"
            y = y_top['y'] + 1
        else:
            continue
        # this is linear interpolation also.
        base_height = CENTERHEIGHT + (in_out_dif * rad_fraction)
        height_rand = (random() - .5) * 2 * HEIGHTVARIATION
        height = int(base_height + height_rand)
        # if the option is set, check the surrounding area for trees
        if ONLYINFORESTS:
            '''we are looking for foliage
            it should show up in the "surface_block" search
            check every fifth block in a square pattern,
            offset around the trunk
            and equal to the trees height
            if the area is not at least one third foliage,
            don't build the tree'''
            # spacing is how far apart each sample should be
            spacing = 5
            # search_size is how many blocks to check
            # along each axis
            search_size = 2 + (height // spacing)
            # check at least 3 x 3
            search_size = max([search_size, 3])
            # set up the offset values to offset the starting corner
            offset = ((search_size - 1) * spacing) // 2
            # foliage_count is the total number of foliage blocks found
            foliage_count = 0
            # check each sample location for foliage
            for step_x in range(search_size):
                # search_x is the x location to search this sample
                search_x = x - offset + (step_x * spacing)
                for step_z in range(search_size):
                    # same as for search_x
                    search_z = z - offset + (step_z * spacing)
                    search_block = mcmap.surface_block(search_x, search_z)
                    if search_block is None:
                        continue
                    if search_block['B'] == 18:
                        # this sample contains foliage!
                        # add it to the total
                        foliage_count += 1
            #now that we have the total count, find the ratio
            total_searched = search_size ** 2
            foliage_ratio = foliage_count / total_searched
            # the acceptable amount is about a third
            acceptable_ratio = .3
            if foliage_ratio < acceptable_ratio:
                # after all that work, there wasn't enough foliage around!
                # try again!
                continue

        # generate the new tree
        newtree = Tree([x, y, z], height)
        if VERBOSE:
            print(x, y, z, height)
        treelist += [newtree]


def processtrees(mcmap, treelist):
    '''Initalize all of the trees in treelist.

    Set all of the trees to the right type, and run prepare.  If indicated
    limit the height of the trees to the top of the map.
    '''
    assert isinstance(mcmap, mcInterface.SaveFile)
    if SHAPE == "stickly":
        shape_choices = ["normal", "bamboo", "palm"]
    elif SHAPE == "procedural":
        shape_choices = ["round", "cone"]
    else:
        shape_choices = [SHAPE]

    # initialize mapheight, just in case
    mapheight = 127
    for i in range(len(treelist)):
        newshape = choice(shape_choices)
        if newshape == "normal":
            newtree = NormalTree()
        elif newshape == "bamboo":
            newtree = BambooTree()
        elif newshape == "palm":
            newtree = PalmTree()
        elif newshape == "round":
            newtree = RoundTree()
        elif newshape == "cone":
            newtree = ConeTree()
        elif newshape == "rainforest":
            newtree = RainforestTree()
        elif newshape == "mangrove":
            newtree = MangroveTree()

        # Get the height and position of the existing trees in
        # the list.
        newtree.copy(treelist[i])
        # Now check each tree to ensure that it doesn't stick
        # out the top of the map.  If it does, shorten it until
        # the top of the foliage just touches the top of the map.
        if MAPHEIGHTLIMIT:
            height = newtree.height
            ybase = newtree.pos[1]
            if SHAPE == "rainforest":
                foliageheight = 2
            else:
                foliageheight = 4
            if ybase + height + foliageheight > mapheight:
                newheight = mapheight - ybase - foliageheight
                newtree.height = newheight
        # Even if it sticks out the top of the map, every tree
        # should be at least one unit tall.
        if newtree.height < 1:
            newtree.height = 1
        newtree.prepare(mcmap)
        treelist[i] = newtree


def main(the_map):
    '''create the trees
    '''
    treelist = []
    if VERBOSE:
        print("Planting new trees")
    planttrees(the_map, treelist)
    if VERBOSE:
        print("Processing tree changes")
    processtrees(the_map, treelist)
    if FOLIAGE:
        if VERBOSE:
            print("Generating foliage ")
        for i in treelist:
            i.makefoliage(the_map)
        if VERBOSE:
            print(' completed')
    if WOOD:
        if VERBOSE:
            print("Generating trunks, roots, and branches ")
        for i in treelist:
            i.maketrunk(the_map)
        if VERBOSE:
            print(' completed')
    return None


def standalone():
    if VERBOSE:
        print("Importing the map")
    try:
        the_map = mcInterface.SaveFile(LOADNAME)
    except IOError:
        if VERBOSE:
            print('File name invalid or save file otherwise corrupted. Aborting')
        return None
    main(the_map)
    if LIGHTINGFIX:
        if VERBOSE:
            print("Rough re-lighting the map")
        relight_master.save_file = the_map
        relight_master.calc_lighting()
    if VERBOSE:
        print("Saving the map, this could be a while")
    the_map.write()
    if VERBOSE:
        print("finished")

if __name__ == '__main__':
    standalone()

# to do:
# get height limits from map
# set "limit height" or somesuch to respect level height limits

########NEW FILE########
__FILENAME__ = Invincible
# Feel free to modify and use this filter however you wish. If you do,
# please give credit to SethBling.
# http://youtube.com/SethBling

from pymclevel import TAG_List
from pymclevel import TAG_Byte
from pymclevel import TAG_Int
from pymclevel import TAG_Compound

displayName = "Make Mobs Invincible"

def perform(level, box, options):
    for (chunk, slices, point) in level.getChunkSlices(box):
        for e in chunk.Entities:
            x = e["Pos"][0].value
            y = e["Pos"][1].value
            z = e["Pos"][2].value

            if x >= box.minx and x < box.maxx and y >= box.miny and y < box.maxy and z >= box.minz and z < box.maxz:
                if "Health" in e:
                    if "ActiveEffects" not in e:
                        e["ActiveEffects"] = TAG_List()

                    resist = TAG_Compound()
                    resist["Amplifier"] = TAG_Byte(4)
                    resist["Id"] = TAG_Byte(11)
                    resist["Duration"] = TAG_Int(2000000000)
                    e["ActiveEffects"].append(resist)
                    chunk.dirty = True

########NEW FILE########
__FILENAME__ = MCEditForester
'''MCEditForester.py
   Tree-generating script by dudecon
   http://www.minecraftforum.net/viewtopic.php?f=1022&t=219461

   Needs the dummy mcInterface for MCEdit, and the default Forester script.
'''

from pymclevel.materials import alphaMaterials
import Forester
import mcInterface

displayName = "Forester"

inputs = (
    ("Forester script by dudecon", "label"),
    ("Shape", ("Procedural",
               "Normal",
               "Bamboo",
               "Palm",
               "Stickly",
               "Round",
               "Cone",
               "Rainforest",
               "Mangrove",
               )),

    ("Tree Count", 2),
    ("Tree Height", 35),
    ("Height Variation", 12),

    ("Branch Density", 1.0),
    ("Trunk Thickness", 1.0),
    ("Broken Trunk", False),
    ("Hollow Trunk", False),
    ("Wood", True),

    ("Foliage", True),
    ("Foliage Density", 1.0),

    ("Roots", ("Yes", "To Stone", "Hanging", "No")),
    ("Root Buttresses", False),

    ("Wood Material", alphaMaterials.Wood),
    ("Leaf Material", alphaMaterials.Leaves),
    ("Plant On", alphaMaterials.Grass),

)


def perform(level, box, options):
    '''Load the file, create the trees, and save the new file.
    '''
    # set up the non 1 to 1 mappings of options to Forester global names
    optmap = {
        "Tree Height": "CENTERHEIGHT",
    }
    # automatically set the options that map 1 to 1 from options to Forester

    def setOption(opt):
        OPT = optmap.get(opt, opt.replace(" ", "").upper())
        if OPT in dir(Forester):
            val = options[opt]
            if isinstance(val, str):
                val = val.replace(" ", "").lower()

            setattr(Forester, OPT, val)

    # set all of the options
    for option in options:
        setOption(option)
    # set the EDGEHEIGHT the same as CENTERHEIGHT
    Forester.EDGEHEIGHT = Forester.CENTERHEIGHT
    # set the materials
    wood = options["Wood Material"]
    leaf = options["Leaf Material"]
    grass = options["Plant On"]

    Forester.WOODINFO = {"B": wood.ID, "D": wood.blockData}
    Forester.LEAFINFO = {"B": leaf.ID, "D": leaf.blockData}
    Forester.PLANTON = [grass.ID]

    # calculate the plant-on center and radius
    x_center = int(box.minx + (box.width / 2))
    z_center = int(box.minz + (box.length / 2))
    edge_padding = int(Forester.EDGEHEIGHT * 0.618)
    max_dim = min(box.width, box.length)
    planting_radius = (max_dim / 2) - edge_padding
    if planting_radius <= 1:
        planting_radius = 1
        Forester.TREECOUNT = 1
        print("Box isn't wide and/or long enough. Only planting one tree.")
    # set the position to plant
    Forester.X = x_center
    Forester.Z = z_center
    Forester.RADIUS = planting_radius
    print("Plant radius = " + str(planting_radius))

    # set the Forester settings that are not in the inputs
    # and should be a specific value
    # take these out if added to settings
    Forester.LIGHTINGFIX = False
    Forester.MAXTRIES = 5000
    Forester.VERBOSE = True

    # create the dummy map object
    mcmap = mcInterface.MCLevelAdapter(level, box)
    # call forester's main function on the map object.
    Forester.main(mcmap)

    level.markDirtyBox(box)

########NEW FILE########
__FILENAME__ = mcInterface
#dummy mcInterface to adapt dudecon's interface to MCEdit's


class MCLevelAdapter(object):
    def __init__(self, level, box):
        self.level = level
        self.box = box

    def check_box_2d(self, x, z):
        box = self.box
        if x < box.minx or x >= box.maxx:
            return False
        if z < box.minz or z >= box.maxz:
            return False
        return True

    def check_box_3d(self, x, y, z):
        '''If the coordinates are within the box, return True, else return False'''
        box = self.box
        if not self.check_box_2d(x, z):
            return False
        if y < box.miny or y >= box.maxy:
            return False
        return True

    def block(self, x, y, z):
        if not self.check_box_3d(x, y, z):
            return None
        d = {}
        d['B'] = self.level.blockAt(x, y, z)
        d['D'] = self.level.blockDataAt(x, y, z)
        return d

    def set_block(self, x, y, z, d):
        if not self.check_box_3d(x, y, z):
            return None
        if 'B' in d:
            self.level.setBlockAt(x, y, z, d['B'])
        if 'D' in d:
            self.level.setBlockDataAt(x, y, z, d['D'])

    def surface_block(self, x, z):
        if not self.check_box_2d(x, z):
            return None
        y = self.level.heightMapAt(x, z)
        y = max(0, y - 1)

        d = self.block(x, y, z)
        if d:
            d['y'] = y

        return d

SaveFile = MCLevelAdapter

        #dict['L'] = self.level.blockLightAt(x,y,z)
        #dict['S'] = self.level.skyLightAt(x,y,z)

########NEW FILE########
__FILENAME__ = setbiome
# SethBling's SetBiome Filter
# Directions: Just select a region and use this filter, it will apply the
# biome to all columns within the selected region. It can be used on regions
# of any size, they need not correspond to chunks.
#
# If you modify and redistribute this code, please credit SethBling

from pymclevel import MCSchematic
from pymclevel import TAG_Compound
from pymclevel import TAG_Short
from pymclevel import TAG_Byte
from pymclevel import TAG_Byte_Array
from pymclevel import TAG_String
from numpy import zeros

inputs = (
    ("Biome", ( "Ocean",
				"Plains",
				"Desert",
				"Extreme Hills",
				"Forest",
				"Taiga",
				"Swamppland",
				"River",
				"Hell (Nether)",
				"Sky (End)",
				"Frozen Ocean",
				"Frozen River",
				"Ice Plains",
				"Ice Mountains",
				"Mushroom Island",
				"Mushroom Island Shore",
				"Beach",
				"Desert Hills",
				"Forest Hills",
				"Taiga Hills",
				"Extreme Hills Edge",
				"Jungle",
				"Jungle Hills",
				"Jungle Edge",
				"Deep Ocean",
				"Stone Beach",
				"Cold Beach",
				"Birch Forest",
				"Birch Forest Hills",
				"Roofed Forest",
				"Cold Taiga",
				"Cold Taiga Hills",
				"Mega Taiga",
				"Mega Taiga Hills",
				"Extreme Hills+",
				"Savanna",
				"Savanna Plateau",
				"Messa",
				"Messa Plateau F",
				"Messa Plateau",
				"Sunflower Plains",
				"Desert M",
				"Extreme Hills M",
				"Flower Forest",
				"Taiga M",
				"Swampland M",
				"Ice Plains Spikes",
				"Ice Mountains Spikes",
				"Jungle M",
				"JungleEdge M",
				"Birch Forest M",
				"Birch Forest Hills M",
				"Roofed Forest M",
				"Cold Taiga M",
				"Mega Spruce Taiga",
				"Mega Spruce Taiga ",
				"Extreme Hills+ M",
				"Savanna M",
				"Savanna Plateau M",
				"Mesa (Bryce)",
				"Mesa Plateau F M",
				"Mesa Plateau M",
				"(Uncalculated)",
				)),
)

biomes = {
    "Ocean":0,
    "Plains":1,
    "Desert":2,
    "Extreme Hills":3,
    "Forest":4,
    "Taiga":5,
    "Swamppland":6,
    "River":7,
    "Hell (Nether)":8,
    "Sky (End)":9,
    "Frozen Ocean":10,
    "Frozen River":11,
    "Ice Plains":12,
    "Ice Mountains":13,
    "Mushroom Island":14,
    "Mushroom Island Shore":15,
    "Beach":16,
    "Desert Hills":17,
    "Forest Hills":18,
    "Taiga Hills":19,
    "Extreme Hills Edge":20,
    "Jungle":21,
    "Jungle Hills":22,
    "Jungle Edge":23,
    "Deep Ocean":24,
    "Stone Beach":25,
    "Cold Beach":26,
    "Birch Forest":27,
    "Birch Forest Hills":28,
    "Roofed Forest":29,
    "Cold Taiga":30,
    "Cold Taiga Hills":31,
    "Mega Taiga":32,
    "Mega Taiga Hills":33,
    "Extreme Hills+":34,
    "Savanna":35,
    "Savanna Plateau":36,
    "Messa":37,
    "Messa Plateau F":38,
    "Messa Plateau":39,
    "Sunflower Plains":129,
    "Desert M":130,
    "Extreme Hills M":131,
    "Flower Forest":132,
    "Taiga M":133,
    "Swampland M":134,
    "Ice Plains Spikes":140,
    "Ice Mountains Spikes":141,
    "Jungle M":149,
    "JungleEdge M":151,
    "Birch Forest M":155,
    "Birch Forest Hills M":156,
    "Roofed Forest M":157,
    "Cold Taiga M":158,
    "Mega Spruce Taiga":160,
    "Mega Spruce Taiga 2":161,
    "Extreme Hills+ M":162,
    "Savanna M":163,
    "Savanna Plateau M":164,
    "Mesa (Bryce)":165,
    "Mesa Plateau F M":166,
    "Mesa Plateau M":167,
    "(Uncalculated)":-1,
    }

def perform(level, box, options):
    biome = biomes[options["Biome"]]

    minx = int(box.minx/16)*16
    minz = int(box.minz/16)*16

    for x in xrange(minx, box.maxx, 16):
        for z in xrange(minz, box.maxz, 16):
            chunk = level.getChunk(x / 16, z / 16)
            chunk.dirty = True
            array = chunk.root_tag["Level"]["Biomes"].value

            chunkx = int(x/16)*16
            chunkz = int(z/16)*16

            for bx in xrange(max(box.minx, chunkx), min(box.maxx, chunkx+16)):
                for bz in xrange(max(box.minz, chunkz), min(box.maxz, chunkz+16)):
                    idx = 16*(bz-chunkz)+(bx-chunkx)
                    array[idx] = biome

            chunk.root_tag["Level"]["Biomes"].value = array

########NEW FILE########
__FILENAME__ = smooth
from numpy import zeros, array
import itertools
from pymclevel.level import extractHeights

terrainBlocktypes = [1, 2, 3, 7, 12, 13, 14, 15, 16, 56, 73, 74, 87, 88, 89]
terrainBlockmask = zeros((256,), dtype='bool')
terrainBlockmask[terrainBlocktypes] = True

#
inputs = (
    ("Repeat count", (1, 50)),
)


def perform(level, box, options):
    if box.volume > 16000000:
        raise ValueError("Volume too big for this filter method!")

    repeatCount = options["Repeat count"]
    schema = level.extractSchematic(box)
    schema.removeEntitiesInBox(schema.bounds)
    schema.removeTileEntitiesInBox(schema.bounds)

    for i in xrange(repeatCount):

        terrainBlocks = terrainBlockmask[schema.Blocks]

        heightmap = extractHeights(terrainBlocks)

        #terrainBlocks |= schema.Blocks == 0
        nonTerrainBlocks = ~terrainBlocks
        nonTerrainBlocks &= schema.Blocks != 0

        newHeightmap = (heightmap[1:-1, 1:-1] + (heightmap[0:-2, 1:-1] + heightmap[2:, 1:-1] + heightmap[1:-1, 0:-2] + heightmap[1:-1, 2:]) * 0.7) / 3.8
        #heightmap -= 0.5;
        newHeightmap += 0.5
        newHeightmap[newHeightmap < 0] = 0
        newHeightmap[newHeightmap > schema.Height] = schema.Height

        newHeightmap = array(newHeightmap, dtype='uint16')

        for x, z in itertools.product(xrange(1, schema.Width - 1), xrange(1, schema.Length - 1)):
            oh = heightmap[x, z]
            nh = newHeightmap[x - 1, z - 1]
            d = nh - oh

            column = array(schema.Blocks[x, z])
            column[nonTerrainBlocks[x, z]] = 0
            #schema.Blocks[x,z][nonTerrainBlocks[x,z]] = 0

            if nh > oh:

                column[d:] = schema.Blocks[x, z, :-d]
                if d > oh:
                    column[:d] = schema.Blocks[x, z, 0]
            if nh < oh:
                column[:d] = schema.Blocks[x, z, -d:]
                column[d:oh + 1] = schema.Blocks[x, z, min(oh + 1, schema.Height - 1)]

            #preserve non-terrain blocks
            column[~terrainBlockmask[column]] = 0
            column[nonTerrainBlocks[x, z]] = schema.Blocks[x, z][nonTerrainBlocks[x, z]]

            schema.Blocks[x, z] = column

    level.copyBlocksFrom(schema, schema.bounds, box.origin)

########NEW FILE########
__FILENAME__ = surfacerepair

from numpy import zeros, array
import itertools

#naturally occuring materials
from pymclevel.level import extractHeights

blocktypes = [1, 2, 3, 7, 12, 13, 14, 15, 16, 56, 73, 74, 87, 88, 89]
blockmask = zeros((256,), dtype='bool')

#compute a truth table that we can index to find out whether a block
# is naturally occuring and should be considered in a heightmap
blockmask[blocktypes] = True

displayName = "Chunk Surface Repair"

inputs = (
  ("Repairs the backwards surfaces made by old versions of Minecraft.", "label"),
)


def perform(level, box, options):

    #iterate through the slices of each chunk in the selection box
    for chunk, slices, point in level.getChunkSlices(box):
        # slicing the block array is straightforward. blocks will contain only
        # the area of interest in this chunk.
        blocks = chunk.Blocks
        data = chunk.Data

        # use indexing to look up whether or not each block in blocks is
        # naturally-occuring. these blocks will "count" for column height.
        maskedBlocks = blockmask[blocks]

        heightmap = extractHeights(maskedBlocks)

        for x in range(heightmap.shape[0]):
            for z in range(x + 1, heightmap.shape[1]):

                h = heightmap[x, z]
                h2 = heightmap[z, x]

                b2 = blocks[z, x, h2]

                if blocks[x, z, h] == 1:
                    h += 2  # rock surface - top 4 layers become 2 air and 2 rock
                if blocks[z, x, h2] == 1:
                    h2 += 2  # rock surface - top 4 layers become 2 air and 2 rock

                # topsoil is 4 layers deep
                def swap(s1, s2):
                    a2 = array(s2)
                    s2[:] = s1[:]
                    s1[:] = a2[:]

                swap(blocks[x, z, h - 3:h + 1], blocks[z, x, h2 - 3:h2 + 1])
                swap(data[x, z, h - 3:h + 1], data[z, x, h2 - 3:h2 + 1])

        # remember to do this to make sure the chunk is saved
        chunk.chunkChanged()

########NEW FILE########
__FILENAME__ = topsoil

from numpy import zeros
import itertools
from pymclevel import alphaMaterials
from pymclevel.level import extractHeights

am = alphaMaterials

#naturally occuring materials
blocks = [
  am.Grass,
  am.Dirt,
  am.Stone,
  am.Bedrock,
  am.Sand,
  am.Gravel,
  am.GoldOre,
  am.IronOre,
  am.CoalOre,
  am.LapisLazuliOre,
  am.DiamondOre,
  am.RedstoneOre,
  am.RedstoneOreGlowing,
  am.Netherrack,
  am.SoulSand,
  am.Clay,
  am.Glowstone
]
blocktypes = [b.ID for b in blocks]


def naturalBlockmask():
    blockmask = zeros((256,), dtype='bool')
    blockmask[blocktypes] = True
    return blockmask

inputs = (
  ("Depth", (4, -128, 128)),
  ("Pick a block:", alphaMaterials.Grass),
)


def perform(level, box, options):
    depth = options["Depth"]
    blocktype = options["Pick a block:"]

    #compute a truth table that we can index to find out whether a block
    # is naturally occuring and should be considered in a heightmap
    blockmask = naturalBlockmask()

    # always consider the chosen blocktype to be "naturally occuring" to stop
    # it from adding extra layers
    blockmask[blocktype.ID] = True

    #iterate through the slices of each chunk in the selection box
    for chunk, slices, point in level.getChunkSlices(box):
        # slicing the block array is straightforward. blocks will contain only
        # the area of interest in this chunk.
        blocks = chunk.Blocks[slices]
        data = chunk.Data[slices]

        # use indexing to look up whether or not each block in blocks is
        # naturally-occuring. these blocks will "count" for column height.
        maskedBlocks = blockmask[blocks]

        heightmap = extractHeights(maskedBlocks)

        for x, z in itertools.product(*map(xrange, heightmap.shape)):
            h = heightmap[x, z]
            if depth > 0:
                blocks[x, z, max(0, h - depth):h] = blocktype.ID
                data[x, z, max(0, h - depth):h] = blocktype.blockData
            else:
                #negative depth values mean to put a layer above the surface
                blocks[x, z, h:min(blocks.shape[2], h - depth)] = blocktype.ID
                data[x, z, h:min(blocks.shape[2], h - depth)] = blocktype.blockData

        #remember to do this to make sure the chunk is saved
        chunk.chunkChanged()

########NEW FILE########
__FILENAME__ = frustum
"""View frustum modeling as series of clipping planes

The Frustum object itself is only responsible for
extracting the clipping planes from an OpenGL model-view
matrix.  The bulk of the frustum-culling algorithm is
implemented in the bounding volume objects found in the
OpenGLContext.scenegraph.boundingvolume module.

Based on code from:
    http://www.markmorley.com/opengl/frustumculling.html
"""

import logging
import numpy
from OpenGL import GL
context_log = logging.getLogger()


def viewingMatrix(projection=None, model=None):
    """Calculate the total viewing matrix from given data

    projection -- the projection matrix, if not provided
        than the result of glGetDoublev( GL_PROJECTION_MATRIX)
        will be used.
    model -- the model-view matrix, if not provided
        than the result of glGetDoublev( GL_MODELVIEW_MATRIX )
        will be used.

    Note:
        Unless there is a valid projection and model-view
        matrix, the function will raise a RuntimeError
    """
    if projection is None:
        projection = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
    if model is None:
        model = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
    # hmm, this will likely fail on 64-bit platforms :(
    if projection is None or model is None:
        context_log.warn(
            """A NULL matrix was returned from glGetDoublev: proj=%s modelView=%s""",
            projection, model,
        )
        if projection:
            return projection
        if model:
            return model
        else:
            return numpy.identity(4, 'd')
    if numpy.allclose(projection, -1.79769313e+308):
        context_log.warn(
            """Attempt to retrieve projection matrix when uninitialised %s, model=%s""",
            projection, model,
        )
        return model
    if numpy.allclose(model, -1.79769313e+308):
        context_log.warn(
            """Attempt to retrieve model-view matrix when uninitialised %s, projection=%s""",
            model, projection,
        )
        return projection
    return numpy.dot(model, projection)


class Frustum (object):
    """Holder for frustum specification for intersection tests

    Note:
        the Frustum can include an arbitrary number of
        clipping planes, though the most common usage
        is to define 6 clipping planes from the OpenGL
        model-view matrices.
    """
    def visible(self, points, radius):
        """Determine whether this sphere is visible in frustum

        frustum -- Frustum object holding the clipping planes
            for the view
        matrix -- a matrix which transforms the local
            coordinates to the (world-space) coordinate
            system in which the frustum is defined.

        This version of the method uses a pure-python loop
        to do the actual culling once the points are
        multiplied by the matrix. (i.e. it does not use the
        frustcullaccel C extension module)
        """

        distances = numpy.sum(self.planes[numpy.newaxis, :, :] * points[:, numpy.newaxis, :], -1)
        return ~numpy.any(distances < -radius, -1)

    def visible1(self, point, radius):
        #return self.visible(array(point[numpy.newaxis, :]), radius)

        distance = numpy.sum(self.planes * point, -1)
        vis = ~numpy.any(distance < -radius, -1)
        #assert vis == self.visible(array(point)[numpy.newaxis, :], radius)

        return vis

    @classmethod
    def fromViewingMatrix(cls, matrix=None, normalize=1):
        """Extract and calculate frustum clipping planes from OpenGL

        The default initializer allows you to create
        Frustum objects with arbitrary clipping planes,
        while this alternate initializer provides
        automatic clipping-plane extraction from the
        model-view matrix.

        matrix -- the combined model-view matrix
        normalize -- whether to normalize the plane equations
            to allow for sphere bounding-volumes and use of
            distance equations for LOD-style operations.
        """
        if matrix is None:
            matrix = viewingMatrix()
        clip = numpy.ravel(matrix)
        frustum = numpy.zeros((6, 4), 'd')
        # right
        frustum[0][0] = clip[3] - clip[0]
        frustum[0][1] = clip[7] - clip[4]
        frustum[0][2] = clip[11] - clip[8]
        frustum[0][3] = clip[15] - clip[12]
        # left
        frustum[1][0] = clip[3] + clip[0]
        frustum[1][1] = clip[7] + clip[4]
        frustum[1][2] = clip[11] + clip[8]
        frustum[1][3] = clip[15] + clip[12]
        # bottoming
        frustum[2][0] = clip[3] + clip[1]
        frustum[2][1] = clip[7] + clip[5]
        frustum[2][2] = clip[11] + clip[9]
        frustum[2][3] = clip[15] + clip[13]
        # top
        frustum[3][0] = clip[3] - clip[1]
        frustum[3][1] = clip[7] - clip[5]
        frustum[3][2] = clip[11] - clip[9]
        frustum[3][3] = clip[15] - clip[13]
        # far
        frustum[4][0] = clip[3] - clip[2]
        frustum[4][1] = clip[7] - clip[6]
        frustum[4][2] = clip[11] - clip[10]
        frustum[4][3] = clip[15] - clip[14]
        # near
        frustum[5][0] = clip[3] + clip[2]
        frustum[5][1] = clip[7] + clip[6]
        frustum[5][2] = clip[11] + clip[10]
        frustum[5][3] = (clip[15] + clip[14])
        if normalize:
            frustum = cls.normalize(frustum)
        obj = cls()
        obj.planes = frustum
        obj.matrix = matrix
        return obj

    @classmethod
    def normalize(cls, frustum):
        """Normalize clipping plane equations"""
        magnitude = numpy.sqrt(frustum[:, 0] * frustum[:, 0] + frustum[:, 1] * frustum[:, 1] + frustum[:, 2] * frustum[:, 2])
        # eliminate any planes which have 0-length vectors,
        # those planes can't be used for excluding anything anyway...
        frustum = numpy.compress(magnitude, frustum, 0)
        magnitude = numpy.compress(magnitude, magnitude, 0)
        magnitude = numpy.reshape(magnitude.astype('d'), (len(frustum), 1))
        return frustum / magnitude

########NEW FILE########
__FILENAME__ = glbackground
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""

"""
glbackground.py

A UI element that only draws a single OpenGL quad.
"""

from albow.openglwidgets import GLOrtho
from OpenGL.GL import glEnable, glColor, glVertexPointer, glDrawArrays, glDisable, GL_BLEND, GL_FLOAT, GL_QUADS
from numpy import array
from pygame import mouse


class GLBackground(GLOrtho):
    margin = 8
    bg_color = (0.0, 0.0, 0.0, 0.6)

    #bg_color = (30/255.0,0,255/255.0, 100/255.0)
    def gl_draw(self):
        #if hasattr(self, 'highlight_bg_color') and self in self.get_root().find_widget(mouse.get_pos()).all_parents():
        #    color = self.highlight_bg_color
        #else:
        color = tuple(self.bg_color) + (1.0,)

        glEnable(GL_BLEND)
        glColor(color[0], color[1], color[2], color[3])
        glVertexPointer(2, GL_FLOAT, 0, array([-1, -1, -1, 1, 1, 1, 1, -1], dtype='float32'))
        glDrawArrays(GL_QUADS, 0, 4)
        glDisable(GL_BLEND)


class Panel(GLBackground):
    pass

########NEW FILE########
__FILENAME__ = glutils
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""

"""
glutils.py

Pythonesque wrappers around certain OpenGL functions.
"""

from OpenGL import GL
from OpenGL.GL.ARB import window_pos
import numpy
import functools
from contextlib import contextmanager

from albow import Label
from albow.openglwidgets import GLOrtho
import config

import weakref
from OpenGL.GL import framebufferobjects as FBO
import sys


class gl(object):
    @classmethod
    def ResetGL(cls):
        DisplayList.invalidateAllLists()

    @classmethod
    @contextmanager
    def glPushMatrix(cls, matrixmode):
        try:
            GL.glMatrixMode(matrixmode)
            GL.glPushMatrix()
            yield
        finally:
            GL.glMatrixMode(matrixmode)
            GL.glPopMatrix()

    @classmethod
    @contextmanager
    def glPushAttrib(cls, attribs):
        try:
            GL.glPushAttrib(attribs)
            yield
        finally:
            GL.glPopAttrib()

    @classmethod
    @contextmanager
    def glBegin(cls, type):
        try:
            GL.glBegin(type)
            yield
        finally:
            GL.glEnd()

    @classmethod
    @contextmanager
    def glEnable(cls, *enables):
        try:
            GL.glPushAttrib(GL.GL_ENABLE_BIT)
            for e in enables:
                GL.glEnable(e)

            yield
        finally:
            GL.glPopAttrib()

    @classmethod
    @contextmanager
    def glEnableClientState(cls, *enables):
        try:
            GL.glPushClientAttrib(GL.GL_CLIENT_ALL_ATTRIB_BITS)
            for e in enables:
                GL.glEnableClientState(e)

            yield
        finally:
            GL.glPopClientAttrib()

    listCount = 0

    @classmethod
    def glGenLists(cls, n):
        cls.listCount += n
        return GL.glGenLists(n)

    @classmethod
    def glDeleteLists(cls, base, n):
        cls.listCount -= n
        return GL.glDeleteLists(base, n)


class DisplayList(object):
    allLists = []

    def __init__(self, drawFunc=None):
        self.drawFunc = drawFunc
        self._list = None

        def _delete(r):
            DisplayList.allLists.remove(r)
        self.allLists.append(weakref.ref(self, _delete))

    def __del__(self):
        self.invalidate()

    @classmethod
    def invalidateAllLists(self):
        allLists = []
        for listref in self.allLists:
            list = listref()
            if list:
                list.invalidate()
                allLists.append(listref)

        self.allLists = allLists

    def invalidate(self):
        if self._list:
            gl.glDeleteLists(self._list[0], 1)
            self._list = None

    def makeList(self, drawFunc):
        if self._list:
            return

        drawFunc = (drawFunc or self.drawFunc)
        if drawFunc is None:
            return

        l = gl.glGenLists(1)
        GL.glNewList(l, GL.GL_COMPILE)
        drawFunc()
        #try:
        GL.glEndList()
        #except GL.GLError:
        #    print "Error while compiling display list. Retrying display list code to pinpoint error"
        #    self.drawFunc()

        self._list = numpy.array([l], 'uintc')

    def getList(self, drawFunc=None):
        self.makeList(drawFunc)
        return self._list

    if "-debuglists" in sys.argv:
        def call(self, drawFunc=None):
            drawFunc = (drawFunc or self.drawFunc)
            if drawFunc is None:
                return
            drawFunc()
    else:
        def call(self, drawFunc=None):
            self.makeList(drawFunc)
            GL.glCallLists(self._list)


class Texture(object):
    allTextures = []
    defaultFilter = GL.GL_NEAREST

    def __init__(self, textureFunc=None, minFilter=None, magFilter=None):
        minFilter = minFilter or self.defaultFilter
        magFilter = magFilter or self.defaultFilter
        if textureFunc is None:
            textureFunc = lambda: None

        self.textureFunc = textureFunc
        self._texID = GL.glGenTextures(1)

        def _delete(r):
            Texture.allTextures.remove(r)
        self.allTextures.append(weakref.ref(self, _delete))
        self.bind()
        GL.glTexParameter(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, minFilter)
        GL.glTexParameter(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, magFilter)

        self.textureFunc()

    def __del__(self):
        self.delete()

    def delete(self):
        if self._texID is not None:
            GL.glDeleteTextures(self._texID)

    def bind(self):
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)

    def invalidate(self):
        self.dirty = True


class FramebufferTexture(Texture):
    def __init__(self, width, height, drawFunc):
        tex = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        GL.glTexParameter(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameter(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA8, width, height, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, None)
        self.enabled = False
        self._texID = tex
        if bool(FBO.glGenFramebuffers) and "Intel" not in GL.glGetString(GL.GL_VENDOR):
            buf = FBO.glGenFramebuffers(1)
            depthbuffer = FBO.glGenRenderbuffers(1)

            FBO.glBindFramebuffer(FBO.GL_FRAMEBUFFER, buf)

            FBO.glBindRenderbuffer(FBO.GL_RENDERBUFFER, depthbuffer)
            FBO.glRenderbufferStorage(FBO.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT, width, height)

            FBO.glFramebufferRenderbuffer(FBO.GL_FRAMEBUFFER, FBO.GL_DEPTH_ATTACHMENT, FBO.GL_RENDERBUFFER, depthbuffer)
            FBO.glFramebufferTexture2D(FBO.GL_FRAMEBUFFER, FBO.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, tex, 0)

            status = FBO.glCheckFramebufferStatus(FBO.GL_FRAMEBUFFER)
            if status != FBO.GL_FRAMEBUFFER_COMPLETE:
                print "glCheckFramebufferStatus", status
                self.enabled = False
                return

            FBO.glBindFramebuffer(FBO.GL_FRAMEBUFFER, buf)

            with gl.glPushAttrib(GL.GL_VIEWPORT_BIT):
                GL.glViewport(0, 0, width, height)
                drawFunc()

            FBO.glBindFramebuffer(FBO.GL_FRAMEBUFFER, 0)
            FBO.glDeleteFramebuffers(1, [buf])
            FBO.glDeleteRenderbuffers(1, [depthbuffer])
            self.enabled = True
        else:
            GL.glReadBuffer(GL.GL_BACK)

            GL.glPushAttrib(GL.GL_VIEWPORT_BIT | GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT | GL.GL_STENCIL_TEST | GL.GL_STENCIL_BUFFER_BIT)
            GL.glDisable(GL.GL_STENCIL_TEST)

            GL.glViewport(0, 0, width, height)
            GL.glScissor(0, 0, width, height)
            with gl.glEnable(GL.GL_SCISSOR_TEST):
                drawFunc()

            GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
            GL.glReadBuffer(GL.GL_BACK)
            GL.glCopyTexSubImage2D(GL.GL_TEXTURE_2D, 0, 0, 0, 0, 0, width, height)

            GL.glPopAttrib()



def debugDrawPoint(point):
    GL.glColor(1.0, 1.0, 0.0, 1.0)
    GL.glPointSize(9.0)
    with gl.glBegin(GL.GL_POINTS):
        GL.glVertex3f(*point)

########NEW FILE########
__FILENAME__ = leveleditor
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""
import sys
from compass import CompassOverlay
from editortools.thumbview import ThumbView
from pymclevel.infiniteworld import SessionLockLost

"""
leveleditor.py

Viewport objects for Camera and Chunk views, which respond to some keyboard and
mouse input. LevelEditor object responds to some other keyboard and mouse
input, plus handles the undo stack and implements tile entity editors for
chests, signs, and more. Toolbar object which holds instances of EditorTool
imported from editortools/

"""

import gc
import os
import math
import csv
import copy
import time
import numpy
import config
import frustum
import logging
import glutils
import release
import mceutils
import platform
import functools
import editortools
import itertools
import mcplatform
import pymclevel
import renderer

from math import isnan
from os.path import dirname, isdir
from datetime import datetime, timedelta
from collections import defaultdict, deque

from OpenGL import GL
from OpenGL import GLU

from albow import alert, ask, AttrRef, Button, Column, get_font, Grid, input_text, IntField, Menu, root, Row, TableColumn, TableView, TextField, TimeField, Widget, CheckBox
from albow.controls import Label, SmallValueDisplay, ValueDisplay
from albow.dialogs import Dialog, QuickDialog, wrapped_label
from albow.openglwidgets import GLOrtho, GLViewport
from pygame import display, event, key, KMOD_ALT, KMOD_CTRL, KMOD_LALT, KMOD_META, KMOD_RALT, KMOD_SHIFT, mouse, MOUSEMOTION

from depths import DepthOffset
from editortools.operation import Operation
from editortools.chunk import GeneratorPanel
from glbackground import GLBackground, Panel
from glutils import gl, Texture
from mcplatform import askSaveFile
from pymclevel.minecraft_server import alphanum_key #?????
from renderer import MCRenderer

# Label = GLLabel

Settings = config.Settings("Settings")
Settings.flyMode = Settings("Fly Mode", False)
Settings.enableMouseLag = Settings("Enable Mouse Lag", False)
Settings.longDistanceMode = Settings("Long Distance Mode", False)
Settings.shouldResizeAlert = Settings("Window Size Alert", True)
Settings.closeMinecraftWarning = Settings("Close Minecraft Warning", True)
Settings.skin = Settings("MCEdit Skin", "[Current]")
Settings.fov = Settings("Field of View", 70.0)
Settings.spaceHeight = Settings("Space Height", 64)
Settings.blockBuffer = Settings("Block Buffer", 256 * 1048576)
Settings.reportCrashes = Settings("report crashes new", False)
Settings.reportCrashesAsked = Settings("report crashes asked", False)

Settings.viewDistance = Settings("View Distance", 8)
Settings.targetFPS = Settings("Target FPS", 30)

Settings.windowWidth = Settings("window width", 1024)
Settings.windowHeight = Settings("window height", 768)
Settings.windowX = Settings("window x", 0)
Settings.windowY = Settings("window y", 0)
Settings.windowShowCmd = Settings("window showcmd", 1)
Settings.setWindowPlacement = Settings("SetWindowPlacement", True)

Settings.showHiddenOres = Settings("show hidden ores", False)
Settings.fastLeaves = Settings("fast leaves", True)
Settings.roughGraphics = Settings("rough graphics", False)
Settings.showChunkRedraw = Settings("show chunk redraw", True)
Settings.drawSky = Settings("draw sky", True)
Settings.drawFog = Settings("draw fog", True)
Settings.showCeiling = Settings("show ceiling", True)
Settings.drawEntities = Settings("draw entities", True)
Settings.drawMonsters = Settings("draw monsters", True)
Settings.drawItems = Settings("draw items", True)
Settings.drawTileEntities = Settings("draw tile entities", True)
Settings.drawTileTicks = Settings("draw tile ticks", False)
Settings.drawUnpopulatedChunks = Settings("draw unpopulated chunks", True)
Settings.vertexBufferLimit = Settings("vertex buffer limit", 384)

Settings.vsync = Settings("vertical sync", 0)
Settings.visibilityCheck = Settings("visibility check", False)
Settings.viewMode = Settings("View Mode", "Camera")

Settings.undoLimit = Settings("Undo Limit", 20)

ControlSettings = config.Settings("Controls")
ControlSettings.mouseSpeed = ControlSettings("mouse speed", 5.0)
ControlSettings.cameraAccel = ControlSettings("camera acceleration", 125.0)
ControlSettings.cameraDrag = ControlSettings("camera drag", 100.0)
ControlSettings.cameraMaxSpeed = ControlSettings("camera maximum speed", 60.0)
ControlSettings.cameraBrakingSpeed = ControlSettings("camera braking speed", 8.0)
ControlSettings.invertMousePitch = ControlSettings("invert mouse pitch", False)
ControlSettings.autobrake = ControlSettings("autobrake", True)
ControlSettings.swapAxes = ControlSettings("swap axes looking down", False)

arch = platform.architecture()[0]


def remapMouseButton(button):
    buttons = [0, 1, 3, 2, 4, 5]  # mouse2 is right button, mouse3 is middle
    if button < len(buttons):
        return buttons[button]
    return button


class ControlPanel(Panel):
    @classmethod
    def getHeader(cls):
        header = Label("MCEdit {0} ({1})".format(release.release, arch), font=get_font(18, "VeraBd.ttf"))
        return header

    def __init__(self, editor):
        Panel.__init__(self)
        self.editor = editor

        self.bg_color = (0, 0, 0, 0.8)

        header = self.getHeader()
        keysColumn = [Label("")]
        buttonsColumn = [header]

        cmd = mcplatform.cmd_name
        hotkeys = ([(cmd + "-N", "Create New World", editor.mcedit.createNewWorld),
                    (cmd + "-O", "Open World...", editor.askOpenFile),
                    (cmd + "-L", "Load World...", editor.askLoadWorld),
                    (cmd + "-S", "Save", editor.saveFile),
                    (cmd + "-R", "Reload", editor.reload),
                    (cmd + "-W", "Close", editor.closeEditor),
                    ("", "", lambda: None),

                    (cmd + "G", "Goto", editor.showGotoPanel),
                    (cmd + "-I", "World Info", editor.showWorldInfo),
                    (cmd + "-Z", "Undo", editor.undo),
                    (cmd + "-A", "Select All", editor.selectAll),
                    (cmd + "-D", "Deselect", editor.deselect),
                    (cmd + "-F", AttrRef(editor, 'viewDistanceLabelText'), editor.swapViewDistance),
                    ("Alt-F4", "Quit", editor.quit),
                    ])

        if cmd == "Cmd":
            hotkeys[-1] = ("Cmd-Q", hotkeys[-1][1], hotkeys[-1][2])

        buttons = mceutils.HotkeyColumn(hotkeys, keysColumn, buttonsColumn)

        sideColumn = editor.mcedit.makeSideColumn()

        self.add(Row([buttons, sideColumn]))
        self.shrink_wrap()

    def key_down(self, evt):
        if key.name(evt.key) == 'escape':
            self.dismiss()
        else:
            self.editor.key_down(evt)

    def mouse_down(self, e):
        if e not in self:
            self.dismiss()


def unproject(x, y, z):
    try:
        return GLU.gluUnProject(x, y, z)
    except ValueError:  # projection failed
        return 0, 0, 0


def DebugDisplay(obj, *attrs):
    col = []
    for attr in attrs:
        def _get(attr):
            return lambda: str(getattr(obj, attr))

        col.append(Row((Label(attr + " = "), ValueDisplay(width=600, get_value=_get(attr)))))

    col = Column(col, align="l")
    b = GLBackground()
    b.add(col)
    b.shrink_wrap()
    return b


class CameraViewport(GLViewport):
    anchor = "tlbr"

    oldMousePosition = None

    def __init__(self, editor):
        self.editor = editor
        rect = editor.mcedit.rect
        GLViewport.__init__(self, rect)

        near = 0.5
        far = 4000.0

        self.near = near
        self.far = far

        self.brake = False
        self.lastTick = datetime.now()
        # self.nearheight = near * tang

        self.cameraPosition = (16., 45., 16.)
        self.velocity = [0., 0., 0.]

        self.yaw = -45.  # degrees
        self._pitch = 0.1

        self.cameraVector = self._cameraVector()

        # A state machine to dodge an apparent bug in pygame that generates erroneous mouse move events
        #   0 = bad event already happened
        #   1 = app just started or regained focus since last bad event
        #   2 = mouse cursor was hidden after state 1, next event will be bad
        self.avoidMouseJumpBug = 1

        Settings.drawSky.addObserver(self)
        Settings.drawFog.addObserver(self)
        Settings.showCeiling.addObserver(self)
        ControlSettings.cameraAccel.addObserver(self, "accelFactor")
        ControlSettings.cameraMaxSpeed.addObserver(self, "maxSpeed")
        ControlSettings.cameraBrakingSpeed.addObserver(self, "brakeMaxSpeed")
        ControlSettings.invertMousePitch.addObserver(self)
        ControlSettings.autobrake.addObserver(self)
        ControlSettings.swapAxes.addObserver(self)

        Settings.visibilityCheck.addObserver(self)
        Settings.fov.addObserver(self, "fovSetting", callback=self.updateFov)

        self.mouseVector = (0, 0, 0)
        # self.add(DebugDisplay(self, "cameraPosition", "blockFaceUnderCursor", "mouseVector", "mouse3dPoint"))

    @property
    def pitch(self):
        return self._pitch

    @pitch.setter
    def pitch(self, val):
        self._pitch = min(89.999, max(-89.999, val))

    def updateFov(self, val=None):
        hfov = self.fovSetting
        fov = numpy.degrees(2.0 * numpy.arctan(self.size[0] / self.size[1] * numpy.tan(numpy.radians(hfov) * 0.5)))

        self.fov = fov
        self.tang = numpy.tan(numpy.radians(fov))

    def stopMoving(self):
        self.velocity = [0, 0, 0]

    def brakeOn(self):
        self.brake = True

    def brakeOff(self):
        self.brake = False

    tickInterval = 1000 / 30

    oldPosition = (0, 0, 0)

    flyMode = Settings.flyMode.configProperty()

    def tickCamera(self, frameStartTime, inputs, inSpace):
        if (frameStartTime - self.lastTick).microseconds > self.tickInterval * 1000:
            timeDelta = frameStartTime - self.lastTick
            self.lastTick = frameStartTime
        else:
            return

        timeDelta = float(timeDelta.microseconds) / 1000000.
        timeDelta = min(timeDelta, 0.125)  # 8fps lower limit!
        drag = ControlSettings.cameraDrag.get()
        accel_factor = drag + ControlSettings.cameraAccel.get()

        # if we're in space, move faster

        drag_epsilon = 10.0 * timeDelta
        max_speed = self.maxSpeed

        if self.brake:
            max_speed = self.brakeMaxSpeed

        if inSpace:
            accel_factor *= 3.0
            max_speed *= 3.0

        pi = self.editor.cameraPanKeys
        mouseSpeed = ControlSettings.mouseSpeed.get()
        self.yaw += pi[0] * mouseSpeed
        self.pitch += pi[1] * mouseSpeed

        alignMovementToAxes = key.get_mods() & KMOD_SHIFT

        if self.flyMode:
            (dx, dy, dz) = self._anglesToVector(self.yaw, 0)
        elif self.swapAxesLookingDown or alignMovementToAxes:
            p = self.pitch
            if p > 80 or alignMovementToAxes:
                p = 0

            (dx, dy, dz) = self._anglesToVector(self.yaw, p)

        else:
            (dx, dy, dz) = self._cameraVector()

        velocity = self.velocity  # xxx learn to use matrix/vector libs
        i = inputs
        yaw = numpy.radians(self.yaw)
        cosyaw = -numpy.cos(yaw)
        sinyaw = numpy.sin(yaw)
        if alignMovementToAxes:
            cosyaw = int(cosyaw * 1.4)
            sinyaw = int(sinyaw * 1.4)
            dx = int(dx * 1.4)
            dy = int(dy * 1.6)
            dz = int(dz * 1.4)

        directedInputs = mceutils.normalize((
            i[0] * cosyaw + i[2] * dx,
            i[1] + i[2] * dy,
            i[2] * dz - i[0] * sinyaw,
        ))

        # give the camera an impulse according to the state of the inputs and in the direction of the camera
        cameraAccel = map(lambda x: x * accel_factor * timeDelta, directedInputs)
        # cameraImpulse = map(lambda x: x*impulse_factor, directedInputs)

        newVelocity = map(lambda a, b: a + b, velocity, cameraAccel)
        velocityDir, speed = mceutils.normalize_size(newVelocity)

        # apply drag
        if speed:
            if self.autobrake and not any(inputs):
                speed = 0.15 * speed
            else:

                sign = speed / abs(speed)
                speed = abs(speed)
                speed = speed - (drag * timeDelta)
                if speed < 0.0:
                    speed = 0.0
                speed *= sign

        speed = max(-max_speed, min(max_speed, speed))

        if abs(speed) < drag_epsilon:
            speed = 0

        velocity = map(lambda a: a * speed, velocityDir)

        # velocity = map(lambda p,d: p + d, velocity, cameraImpulse)
        d = map(lambda a, b: abs(a - b), self.cameraPosition, self.oldPosition)
        if d[0] + d[2] > 32.0:
            self.oldPosition = self.cameraPosition
            self.updateFloorQuad()

        self.cameraPosition = map(lambda p, d: p + d * timeDelta, self.cameraPosition, velocity)
        if self.cameraPosition[1] > 3800.:
            self.cameraPosition[1] = 3800.
        if self.cameraPosition[1] < -1000.:
            self.cameraPosition[1] = -1000.

        self.velocity = velocity
        self.cameraVector = self._cameraVector()

        self.editor.renderer.position = self.cameraPosition
        if self.editor.currentTool.previewRenderer:
            self.editor.currentTool.previewRenderer.position = self.cameraPosition

    def setModelview(self):
        pos = self.cameraPosition
        look = numpy.array(self.cameraPosition)
        look += self.cameraVector
        up = (0, 1, 0)
        GLU.gluLookAt(pos[0], pos[1], pos[2],
                  look[0], look[1], look[2],
                  up[0], up[1], up[2])

    def _cameraVector(self):
        return self._anglesToVector(self.yaw, self.pitch)

    def _anglesToVector(self, yaw, pitch):
        def nanzero(x):
            if isnan(x):
                return 0
            else:
                return x

        dx = -math.sin(math.radians(yaw)) * math.cos(math.radians(pitch))
        dy = -math.sin(math.radians(pitch))
        dz = math.cos(math.radians(yaw)) * math.cos(math.radians(pitch))
        return map(nanzero, [dx, dy, dz])

    def updateMouseVector(self):
        self.mouseVector = self._mouseVector()

    def _mouseVector(self):
        """
            returns a vector reflecting a ray cast from the camera
        position to the mouse position on the near plane
        """
        x, y = mouse.get_pos()
        # if (x, y) not in self.rect:
        #    return (0, 0, 0);  # xxx

        y = self.get_root().height - y
        point1 = unproject(x, y, 0.0)
        point2 = unproject(x, y, 1.0)
        v = numpy.array(point2) - point1
        v = mceutils.normalize(v)
        return v

    def _blockUnderCursor(self, center=False):
        """
            returns a point in 3d space that was determined by
         reading the depth buffer value
        """
        try:
            GL.glReadBuffer(GL.GL_BACK)
        except Exception:
            logging.exception('Exception during glReadBuffer')
        ws = self.get_root().size
        if center:
            x, y = ws
            x //= 2
            y //= 2
        else:
            x, y = mouse.get_pos()
        if (x < 0 or y < 0 or x >= ws[0] or
            y >= ws[1]):
                return 0, 0, 0

        y = ws[1] - y

        try:
            pixel = GL.glReadPixels(x, y, 1, 1, GL.GL_DEPTH_COMPONENT, GL.GL_FLOAT)
            newpoint = unproject(x, y, pixel[0])
        except Exception:
            return 0, 0, 0

        return newpoint

    def updateBlockFaceUnderCursor(self):
        focusPair = None
        if not self.enableMouseLag or self.editor.frames & 1:
            self.updateMouseVector()
            if self.editor.mouseEntered:
                if not self.mouseMovesCamera:
                    mouse3dPoint = self._blockUnderCursor()
                    focusPair = self.findBlockFaceUnderCursor(mouse3dPoint)
                elif self.editor.longDistanceMode:
                    mouse3dPoint = self._blockUnderCursor(True)
                    focusPair = self.findBlockFaceUnderCursor(mouse3dPoint)

            # otherwise, find the block at a controllable distance in front of the camera
            if focusPair is None:
                focusPair = (self.getCameraPoint(), (0, 0, 0))

            self.blockFaceUnderCursor = focusPair

    def findBlockFaceUnderCursor(self, projectedPoint):
        """Returns a (pos, Face) pair or None if one couldn't be found"""

        d = [0, 0, 0]

        try:
            intProjectedPoint = map(int, map(numpy.floor, projectedPoint))
        except ValueError:
            return None  # catch NaNs
        intProjectedPoint[1] = max(0, intProjectedPoint[1])

        # find out which face is under the cursor.  xxx do it more precisely
        faceVector = ((projectedPoint[0] - (intProjectedPoint[0] + 0.5)),
             (projectedPoint[1] - (intProjectedPoint[1] + 0.5)),
             (projectedPoint[2] - (intProjectedPoint[2] + 0.5))
             )

        av = map(abs, faceVector)

        i = av.index(max(av))
        delta = faceVector[i]
        if delta < 0:
            d[i] = -1
        else:
            d[i] = 1

        potentialOffsets = []

        try:
            block = self.editor.level.blockAt(*intProjectedPoint)
        except (EnvironmentError, pymclevel.ChunkNotPresent):
            return intProjectedPoint, d

        if block == pymclevel.alphaMaterials.SnowLayer.ID:
            potentialOffsets.append((0, 1, 0))
        else:
            # discard any faces that aren't likely to be exposed
            for face, offsets in pymclevel.faceDirections:
                point = map(lambda a, b: a + b, intProjectedPoint, offsets)
                try:
                    neighborBlock = self.editor.level.blockAt(*point)
                    if block != neighborBlock:
                        potentialOffsets.append(offsets)
                except (EnvironmentError, pymclevel.ChunkNotPresent):
                    pass

        # check each component of the face vector to see if that face is exposed
        if tuple(d) not in potentialOffsets:
            av[i] = 0
            i = av.index(max(av))
            d = [0, 0, 0]
            delta = faceVector[i]
            if delta < 0:
                d[i] = -1
            else:
                d[i] = 1
            if tuple(d) not in potentialOffsets:
                av[i] = 0
                i = av.index(max(av))
                d = [0, 0, 0]
                delta = faceVector[i]
                if delta < 0:
                    d[i] = -1
                else:
                    d[i] = 1

                if tuple(d) not in potentialOffsets:
                    if len(potentialOffsets):
                        d = potentialOffsets[0]
                    else:
                        # use the top face as a fallback
                        d = [0, 1, 0]

        return intProjectedPoint, d

    @property
    def ratio(self):
        return self.width / float(self.height)

    startingMousePosition = None

    def mouseLookOn(self):
        root.get_root().capture_mouse(self)
        self.focus_switch = None
        self.startingMousePosition = mouse.get_pos()

        if self.avoidMouseJumpBug == 1:
            self.avoidMouseJumpBug = 2

    def mouseLookOff(self):
        root.get_root().capture_mouse(None)
        if self.startingMousePosition:
            mouse.set_pos(*self.startingMousePosition)
        self.startingMousePosition = None

    @property
    def mouseMovesCamera(self):
        return root.get_root().captured_widget is not None

    def toggleMouseLook(self):
        if not self.mouseMovesCamera:
            self.mouseLookOn()
        else:
            self.mouseLookOff()

    mobs = pymclevel.Entity.monsters + ["[Custom]"]

    @mceutils.alertException
    def editMonsterSpawner(self, point):
        mobs = self.mobs

        tileEntity = self.editor.level.tileEntityAt(*point)
        if not tileEntity:
            tileEntity = pymclevel.TAG_Compound()
            tileEntity["id"] = pymclevel.TAG_String("MobSpawner")
            tileEntity["x"] = pymclevel.TAG_Int(point[0])
            tileEntity["y"] = pymclevel.TAG_Int(point[1])
            tileEntity["z"] = pymclevel.TAG_Int(point[2])
            tileEntity["Delay"] = pymclevel.TAG_Short(120)
            tileEntity["EntityId"] = pymclevel.TAG_String(mobs[0])

        self.editor.level.addTileEntity(tileEntity)
        self.editor.addUnsavedEdit()

        panel = Dialog()

        def addMob(id):
            if id not in mobs:
                mobs.insert(0, id)
                mobTable.selectedIndex = 0

        def selectTableRow(i, evt):
            if mobs[i] == "[Custom]":
                id = input_text("Type in an EntityID for this spawner. Invalid IDs may crash Minecraft.", 150)
                if id:
                    addMob(id)
                else:
                    return
                mobTable.selectedIndex = mobs.index(id)
            else:
                mobTable.selectedIndex = i

            if evt.num_clicks == 2:
                panel.dismiss()

        mobTable = TableView(columns=(
            TableColumn("", 200),
            )
        )
        mobTable.num_rows = lambda: len(mobs)
        mobTable.row_data = lambda i: (mobs[i],)
        mobTable.row_is_selected = lambda x: x == mobTable.selectedIndex
        mobTable.click_row = selectTableRow
        mobTable.selectedIndex = 0

        def selectedMob():
            return mobs[mobTable.selectedIndex]

        id = tileEntity["EntityId"].value
        addMob(id)

        mobTable.selectedIndex = mobs.index(id)

        choiceCol = Column((ValueDisplay(width=200, get_value=lambda: selectedMob() + " spawner"), mobTable))

        okButton = Button("OK", action=panel.dismiss)
        panel.add(Column((choiceCol, okButton)))
        panel.shrink_wrap()
        panel.present()

        tileEntity["EntityId"] = pymclevel.TAG_String(selectedMob())

    @mceutils.alertException
    def editSign(self, point):

        block = self.editor.level.blockAt(*point)
        tileEntity = self.editor.level.tileEntityAt(*point)

        linekeys = ["Text" + str(i) for i in range(1, 5)]

        if not tileEntity:
            tileEntity = pymclevel.TAG_Compound()
            tileEntity["id"] = pymclevel.TAG_String("Sign")
            tileEntity["x"] = pymclevel.TAG_Int(point[0])
            tileEntity["y"] = pymclevel.TAG_Int(point[1])
            tileEntity["z"] = pymclevel.TAG_Int(point[2])
            for l in linekeys:
                tileEntity[l] = pymclevel.TAG_String("")

        self.editor.level.addTileEntity(tileEntity)

        panel = Dialog()

        lineFields = [TextField(width=150) for l in linekeys]
        for l, f in zip(linekeys, lineFields):
            f.value = tileEntity[l].value

        colors = [
            "Black",
            "Blue",
            "Green",
            "Cyan",
            "Red",
            "Purple",
            "Yellow",
            "Light Gray",
            "Dark Gray",
            "Light Blue",
            "Bright Green",
            "Bright Blue",
            "Bright Red",
            "Bright Purple",
            "Bright Yellow",
            "White",
        ]

        def menu_picked(index):
            c = u'\xa7' + hex(index)[-1]
            currentField = panel.focus_switch.focus_switch
            currentField.text += c  # xxx view hierarchy
            currentField.insertion_point = len(currentField.text)

        colorMenu = mceutils.MenuButton("Color Code...", colors, menu_picked=menu_picked)

        column = [Label("Edit Sign")] + lineFields + [colorMenu, Button("OK", action=panel.dismiss)]

        panel.add(Column(column))
        panel.shrink_wrap()
        if panel.present():

            self.editor.addUnsavedEdit()
            for l, f in zip(linekeys, lineFields):
                tileEntity[l].value = f.value[:15]

    @mceutils.alertException
    def editContainer(self, point, containerID):
        tileEntityTag = self.editor.level.tileEntityAt(*point)
        if tileEntityTag is None:
            tileEntityTag = pymclevel.TileEntity.Create(containerID)
            pymclevel.TileEntity.setpos(tileEntityTag, point)
            self.editor.level.addTileEntity(tileEntityTag)

        if tileEntityTag["id"].value != containerID:
            return

        backupEntityTag = copy.deepcopy(tileEntityTag)

        def itemProp(key):
            # xxx do validation here
            def getter(self):
                if 0 == len(tileEntityTag["Items"]):
                    return "N/A"
                return tileEntityTag["Items"][self.selectedItemIndex][key].value

            def setter(self, val):
                if 0 == len(tileEntityTag["Items"]):
                    return
                self.dirty = True
                tileEntityTag["Items"][self.selectedItemIndex][key].value = val
            return property(getter, setter)

        class ChestWidget(Widget):
            dirty = False
            Slot = itemProp("Slot")
            id = itemProp("id")
            Damage = itemProp("Damage")
            Count = itemProp("Count")
            itemLimit = pymclevel.TileEntity.maxItems.get(containerID, 255)

        def slotFormat(slot):
            slotNames = pymclevel.TileEntity.slotNames.get(containerID)
            if slotNames:
                return slotNames.get(slot, slot)
            return slot

        chestWidget = ChestWidget()
        chestItemTable = TableView(columns=[
            TableColumn("Slot", 80, "l", fmt=slotFormat),
            TableColumn("ID", 50, "l"),
            TableColumn("DMG", 50, "l"),
            TableColumn("Count", 65, "l"),

            TableColumn("Name", 200, "l"),
        ])

        def itemName(id, damage):
            try:
                return pymclevel.items.items.findItem(id, damage).name
            except pymclevel.items.ItemNotFound:
                return "Unknown Item"

        def getRowData(i):
            item = tileEntityTag["Items"][i]
            slot, id, damage, count = item["Slot"].value, item["id"].value, item["Damage"].value, item["Count"].value
            return slot, id, damage, count, itemName(id, damage)

        chestWidget.selectedItemIndex = 0

        def selectTableRow(i, evt):
            chestWidget.selectedItemIndex = i

        chestItemTable.num_rows = lambda: len(tileEntityTag["Items"])
        chestItemTable.row_data = getRowData
        chestItemTable.row_is_selected = lambda x: x == chestWidget.selectedItemIndex
        chestItemTable.click_row = selectTableRow

        fieldRow = (
            # mceutils.IntInputRow("Slot: ", ref=AttrRef(chestWidget, 'Slot'), min= -128, max=127),
            mceutils.IntInputRow("ID: ", ref=AttrRef(chestWidget, 'id'), min=0, max=32767),
            mceutils.IntInputRow("DMG: ", ref=AttrRef(chestWidget, 'Damage'), min=-32768, max=32767),
            mceutils.IntInputRow("Count: ", ref=AttrRef(chestWidget, 'Count'), min=-128, max=127),
        )

        def deleteFromWorld():
            i = chestWidget.selectedItemIndex
            item = tileEntityTag["Items"][i]
            id = item["id"].value
            Damage = item["Damage"].value

            deleteSameDamage = mceutils.CheckBoxLabel("Only delete items with the same damage value")
            deleteBlocksToo = mceutils.CheckBoxLabel("Also delete blocks placed in the world")
            if id not in (8, 9, 10, 11):  # fluid blocks
                deleteBlocksToo.value = True

            w = wrapped_label("WARNING: You are about to modify the entire world. This cannot be undone. Really delete all copies of this item from all land, chests, furnaces, dispensers, dropped items, item-containing tiles, and player inventories in this world?", 60)
            col = (w, deleteSameDamage)
            if id < 256:
                col += (deleteBlocksToo,)

            d = Dialog(Column(col), ["OK", "Cancel"])

            if d.present() == "OK":
                def deleteItemsIter():
                    i = 0
                    if deleteSameDamage.value:
                        def matches(t):
                            return t["id"].value == id and t["Damage"].value == Damage
                    else:
                        def matches(t):
                            return t["id"].value == id

                    def matches_itementity(e):
                        if e["id"].value != "Item":
                            return False
                        if "Item" not in e:
                            return False
                        t = e["Item"]
                        return matches(t)
                    for player in self.editor.level.players:
                        tag = self.editor.level.getPlayerTag(player)
                        l = len(tag["Inventory"])
                        tag["Inventory"].value = [t for t in tag["Inventory"].value if not matches(t)]

                    for chunk in self.editor.level.getChunks():
                        if id < 256 and deleteBlocksToo.value:
                            matchingBlocks = chunk.Blocks == id
                            if deleteSameDamage.value:
                                matchingBlocks &= chunk.Data == Damage
                            if any(matchingBlocks):
                                chunk.Blocks[matchingBlocks] = 0
                                chunk.Data[matchingBlocks] = 0
                                chunk.chunkChanged()
                                self.editor.invalidateChunks([chunk.chunkPosition])

                        for te in chunk.TileEntities:
                            if "Items" in te:
                                l = len(te["Items"])

                                te["Items"].value = [t for t in te["Items"].value if not matches(t)]
                                if l != len(te["Items"]):
                                    chunk.dirty = True
                        entities = [e for e in chunk.Entities if matches_itementity(e)]
                        if len(entities) != len(chunk.Entities):
                            chunk.Entities.value = entities
                            chunk.dirty = True

                        yield (i, self.editor.level.chunkCount)
                        i += 1

                progressInfo = "Deleting the item {0} from the entire world ({1} chunks)".format(itemName(chestWidget.id, 0), self.editor.level.chunkCount)

                mceutils.showProgress(progressInfo, deleteItemsIter(), cancel=True)

                self.editor.addUnsavedEdit()
                chestWidget.selectedItemIndex = min(chestWidget.selectedItemIndex, len(tileEntityTag["Items"]) - 1)

        def deleteItem():
            i = chestWidget.selectedItemIndex
            item = tileEntityTag["Items"][i]
            tileEntityTag["Items"].value = [t for t in tileEntityTag["Items"].value if t is not item]
            chestWidget.selectedItemIndex = min(chestWidget.selectedItemIndex, len(tileEntityTag["Items"]) - 1)

        def deleteEnable():
            return len(tileEntityTag["Items"]) and chestWidget.selectedItemIndex != -1

        def addEnable():
            return len(tileEntityTag["Items"]) < chestWidget.itemLimit

        def addItem():
            slot = 0
            for item in tileEntityTag["Items"]:
                if slot == item["Slot"].value:
                    slot += 1
            if slot >= chestWidget.itemLimit:
                return
            item = pymclevel.TAG_Compound()
            item["id"] = pymclevel.TAG_Short(0)
            item["Damage"] = pymclevel.TAG_Short(0)
            item["Slot"] = pymclevel.TAG_Byte(slot)
            item["Count"] = pymclevel.TAG_Byte(0)
            tileEntityTag["Items"].append(item)

        addItemButton = Button("Add Item", action=addItem, enable=addEnable)
        deleteItemButton = Button("Delete This Item", action=deleteItem, enable=deleteEnable)
        deleteFromWorldButton = Button("Delete Item ID From Entire World", action=deleteFromWorld, enable=deleteEnable)
        deleteCol = Column((addItemButton, deleteItemButton, deleteFromWorldButton), align="l")

        fieldRow = Row(fieldRow)
        col = Column((chestItemTable, fieldRow, deleteCol))

        chestWidget.add(col)
        chestWidget.shrink_wrap()

        Dialog(client=chestWidget, responses=["Done"]).present()
        level = self.editor.level

        class ChestEditOperation(Operation):
            def perform(self, recordUndo=True):
                level.addTileEntity(tileEntityTag)

            def undo(self):
                level.addTileEntity(backupEntityTag)
                return pymclevel.BoundingBox(pymclevel.TileEntity.pos(tileEntityTag), (1, 1, 1))

        if chestWidget.dirty:
            op = ChestEditOperation(self.editor, self.editor.level)
            op.perform()
            self.editor.addOperation(op)
            self.editor.addUnsavedEdit()

    rightMouseDragStart = None

    def rightClickDown(self, evt):

        self.rightMouseDragStart = datetime.now()
        self.toggleMouseLook()

    def rightClickUp(self, evt):
        x, y = evt.pos
        if self.rightMouseDragStart is None:
            return

        td = datetime.now() - self.rightMouseDragStart
        # except AttributeError:
        #    return
        # print "RightClickUp: ", td
        if td.seconds > 0 or td.microseconds > 280000:
            self.mouseLookOff()

    def leftClickDown(self, evt):
        self.editor.toolMouseDown(evt, self.blockFaceUnderCursor)

        if evt.num_clicks == 2:
            def distance2(p1, p2):
                return numpy.sum(map(lambda a, b: (a - b) ** 2, p1, p2))

            point, face = self.blockFaceUnderCursor
            if point is not None:
                point = map(lambda x: int(numpy.floor(x)), point)
                if self.editor.currentTool is self.editor.selectionTool:
                    try:
                        block = self.editor.level.blockAt(*point)
                        if distance2(point, self.cameraPosition) > 4:
                            blockEditors = {
                                pymclevel.alphaMaterials.MonsterSpawner.ID:   self.editMonsterSpawner,
                                pymclevel.alphaMaterials.Sign.ID:             self.editSign,
                                pymclevel.alphaMaterials.WallSign.ID:         self.editSign,
                            }
                            edit = blockEditors.get(block)
                            if edit:
                                self.editor.endSelection()
                                edit(point)
                            else:
                                # detect "container" tiles
                                te = self.editor.level.tileEntityAt(*point)
                                if te and "Items" in te and "id" in te:
                                    self.editor.endSelection()
                                    self.editContainer(point, te["id"].value)
                    except (EnvironmentError, pymclevel.ChunkNotPresent):
                        pass

    def leftClickUp(self, evt):
        self.editor.toolMouseUp(evt, self.blockFaceUnderCursor)

    # --- Event handlers ---

    def mouse_down(self, evt):
        button = remapMouseButton(evt.button)
        logging.debug("Mouse down %d @ %s", button, evt.pos)

        if button == 1:
            if sys.platform == "darwin" and evt.ctrl:
                self.rightClickDown(evt)
            else:
                self.leftClickDown(evt)
        elif button == 2:
            self.rightClickDown(evt)
        else:
            evt.dict['keyname'] = "mouse{0}".format(button)
            self.editor.key_down(evt)

        self.editor.focus_on(None)
        # self.focus_switch = None

    def mouse_up(self, evt):
        button = remapMouseButton(evt.button)
        logging.debug("Mouse up   %d @ %s", button, evt.pos)
        if button == 1:
            if sys.platform == "darwin" and evt.ctrl:
                self.rightClickUp(evt)
            else:
                self.leftClickUp(evt)
        elif button == 2:
            self.rightClickUp(evt)
        else:
            evt.dict['keyname'] = "mouse{0}".format(button)
            self.editor.key_up(evt)

    def mouse_drag(self, evt):
        self.mouse_move(evt)
        self.editor.mouse_drag(evt)

    lastRendererUpdate = datetime.now()

    def mouse_move(self, evt):
        if self.avoidMouseJumpBug == 2:
            self.avoidMouseJumpBug = 0
            return

        def sensitivityAdjust(d):
            return d * ControlSettings.mouseSpeed.get() / 10.0

        self.editor.mouseEntered = True
        if self.mouseMovesCamera:

            pitchAdjust = sensitivityAdjust(evt.rel[1])
            if self.invertMousePitch:
                pitchAdjust = -pitchAdjust
            self.yaw += sensitivityAdjust(evt.rel[0])
            self.pitch += pitchAdjust
            if datetime.now() - self.lastRendererUpdate > timedelta(0, 0, 500000):
                self.editor.renderer.loadNearbyChunks()
                self.lastRendererUpdate = datetime.now()

            # adjustLimit = 2

            # self.oldMousePosition = (x, y)
            # if (self.startingMousePosition[0] - x > adjustLimit or self.startingMousePosition[1] - y > adjustLimit or
            #   self.startingMousePosition[0] - x < -adjustLimit or self.startingMousePosition[1] - y < -adjustLimit):
            #    mouse.set_pos(*self.startingMousePosition)
            #    event.get(MOUSEMOTION)
            #    self.oldMousePosition = (self.startingMousePosition)

    def activeevent(self, evt):
        if evt.state & 0x2 and evt.gain != 0:
            self.avoidMouseJumpBug = 1

    @property
    def tooltipText(self):
        return self.editor.currentTool.worldTooltipText

    floorQuad = numpy.array(((-4000.0, 0.0, -4000.0),
                     (-4000.0, 0.0, 4000.0),
                     (4000.0, 0.0, 4000.0),
                     (4000.0, 0.0, -4000.0),
                     ), dtype='float32')

    def updateFloorQuad(self):
        floorQuad = ((-4000.0, 0.0, -4000.0),
                     (-4000.0, 0.0, 4000.0),
                     (4000.0, 0.0, 4000.0),
                     (4000.0, 0.0, -4000.0),
                     )

        floorQuad = numpy.array(floorQuad, dtype='float32')
        if self.editor.renderer.inSpace():
            floorQuad *= 8.0
        floorQuad += (self.cameraPosition[0], 0.0, self.cameraPosition[2])
        self.floorQuad = floorQuad
        self.floorQuadList.invalidate()

    def drawFloorQuad(self):
        self.floorQuadList.call(self._drawFloorQuad)

    def _drawCeiling(self):
        lines = []
        minz = minx = -256
        maxz = maxx = 256
        for x in range(minx, maxx + 1, 16):
            lines.append((x, 0, minz))
            lines.append((x, 0, maxz))
        for z in range(minz, maxz + 1, 16):
            lines.append((minx, 0, z))
            lines.append((maxx, 0, z))

        GL.glColor(0.3, 0.7, 0.9)
        GL.glVertexPointer(3, GL.GL_FLOAT, 0, numpy.array(lines, dtype='float32'))

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(False)
        GL.glDrawArrays(GL.GL_LINES, 0, len(lines))
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(True)

    def drawCeiling(self):
        GL.glMatrixMode(GL.GL_MODELVIEW)
        # GL.glPushMatrix()
        x, y, z = self.cameraPosition
        x -= x % 16
        z -= z % 16
        y = self.editor.level.Height
        GL.glTranslate(x, y, z)
        self.ceilingList.call(self._drawCeiling)
        GL.glTranslate(-x, -y, -z)

    _floorQuadList = None

    @property
    def floorQuadList(self):
        if not self._floorQuadList:
            self._floorQuadList = glutils.DisplayList()
        return self._floorQuadList

    _ceilingList = None

    @property
    def ceilingList(self):
        if not self._ceilingList:
            self._ceilingList = glutils.DisplayList()
        return self._ceilingList

    @property
    def floorColor(self):
        if self.drawSky:
            return 0.0, 0.0, 1.0, 0.3
        else:
            return 0.0, 1.0, 0.0, 0.15

#    floorColor = (0.0, 0.0, 1.0, 0.1)

    def _drawFloorQuad(self):
        GL.glDepthMask(True)
        GL.glPolygonOffset(DepthOffset.ChunkMarkers + 2, DepthOffset.ChunkMarkers + 2)
        GL.glVertexPointer(3, GL.GL_FLOAT, 0, self.floorQuad)
        GL.glColor(*self.floorColor)
        with gl.glEnable(GL.GL_BLEND, GL.GL_DEPTH_TEST, GL.GL_POLYGON_OFFSET_FILL):
            GL.glDrawArrays(GL.GL_QUADS, 0, 4)

    @property
    def drawSky(self):
        return self._drawSky

    @drawSky.setter
    def drawSky(self, val):
        self._drawSky = val
        if self.skyList:
            self.skyList.invalidate()
        if self._floorQuadList:
            self._floorQuadList.invalidate()

    skyList = None

    def drawSkyBackground(self):
        if self.skyList is None:
            self.skyList = glutils.DisplayList()
        self.skyList.call(self._drawSkyBackground)

    def _drawSkyBackground(self):
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        quad = numpy.array([-1, -1, -1, 1, 1, 1, 1, -1], dtype='float32')
        colors = numpy.array([0x48, 0x49, 0xBA, 0xff,
                         0x8a, 0xaf, 0xff, 0xff,
                         0x8a, 0xaf, 0xff, 0xff,
                         0x48, 0x49, 0xBA, 0xff, ], dtype='uint8')

        alpha = 1.0

        if alpha > 0.0:
            if alpha < 1.0:
                GL.glEnable(GL.GL_BLEND)

            GL.glVertexPointer(2, GL.GL_FLOAT, 0, quad)
            GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, 0, colors)
            GL.glDrawArrays(GL.GL_QUADS, 0, 4)

            if alpha < 1.0:
                GL.glDisable(GL.GL_BLEND)

        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPopMatrix()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()

    enableMouseLag = Settings.enableMouseLag.configProperty()

    @property
    def drawFog(self):
        return self._drawFog and not self.editor.renderer.inSpace()

    @drawFog.setter
    def drawFog(self, val):
        self._drawFog = val

    fogColor = numpy.array([0.6, 0.8, 1.0, 1.0], dtype='float32')
    fogColorBlack = numpy.array([0.0, 0.0, 0.0, 1.0], dtype='float32')

    def enableFog(self):
        GL.glEnable(GL.GL_FOG)
        if self.drawSky:
            GL.glFogfv(GL.GL_FOG_COLOR, self.fogColor)
        else:
            GL.glFogfv(GL.GL_FOG_COLOR, self.fogColorBlack)

        GL.glFogf(GL.GL_FOG_DENSITY, 0.002)

    def disableFog(self):
        GL.glDisable(GL.GL_FOG)

    def getCameraPoint(self):
        distance = self.editor.currentTool.cameraDistance
        return [i for i in itertools.imap(lambda p, d: int(numpy.floor(p + d * distance)),
                                                      self.cameraPosition,
                                                      self.cameraVector)]

    blockFaceUnderCursor = (0, 0, 0), (0, 0, 0)

    viewingFrustum = None

    def setup_projection(self):
        distance = 1.0
        if self.editor.renderer.inSpace():
            distance = 8.0
        GLU.gluPerspective(max(self.fov, 25.0), self.ratio, self.near * distance, self.far * distance)

    def setup_modelview(self):
        self.setModelview()

    def gl_draw(self):
        self.tickCamera(self.editor.frameStartTime, self.editor.cameraInputs, self.editor.renderer.inSpace())
        self.render()

    def render(self):
        # if self.visibilityCheck:
        if True:
            self.viewingFrustum = frustum.Frustum.fromViewingMatrix()
        else:
            self.viewingFrustum = None

        # self.editor.drawStars()
        if self.drawSky:
            self.drawSkyBackground()
        if self.drawFog:
            self.enableFog()

        self.drawFloorQuad()

        self.editor.renderer.viewingFrustum = self.viewingFrustum
        self.editor.renderer.draw()
        focusPair = None

        if self.showCeiling and not self.editor.renderer.inSpace():
            self.drawCeiling()

        if self.editor.level:
            try:
                self.updateBlockFaceUnderCursor()
            except (EnvironmentError, pymclevel.ChunkNotPresent) as e:
                logging.debug("Updating cursor block: %s", e)
                self.blockFaceUnderCursor = (None, None)

            root.get_root().update_tooltip()

            focusPair = self.blockFaceUnderCursor

            (blockPosition, faceDirection) = focusPair
            if None != blockPosition:
                self.editor.updateInspectionString(blockPosition)
                # for t in self.toolbar.tools:

                if self.find_widget(mouse.get_pos()) == self:
                    ct = self.editor.currentTool
                    if ct:
                        ct.drawTerrainReticle()
                        ct.drawToolReticle()
                    else:
                        self.editor.drawWireCubeReticle()

            for t in self.editor.toolbar.tools:
                t.drawTerrainMarkers()
            for t in self.editor.toolbar.tools:
                t.drawToolMarkers()

        if self.drawFog:
            self.disableFog()

        if self._compass is None:
            self._compass = CompassOverlay()

        self._compass.yawPitch = self.yaw, 0

        with gl.glPushMatrix(GL.GL_PROJECTION):
            GL.glLoadIdentity()
            GL.glOrtho(0., 1., float(self.height) / self.width, 0, -200, 200)

            self._compass.draw()

    _compass = None

class ChunkViewport(CameraViewport):
    defaultScale = 1.0  # pixels per block

    def __init__(self, *a, **kw):
        CameraViewport.__init__(self, *a, **kw)

    def setup_projection(self):
        w, h = (0.5 * s / self.defaultScale
                for s in self.size)

        minx, maxx = - w,  w
        miny, maxy = - h,  h
        minz, maxz = -4000, 4000
        GL.glOrtho(minx, maxx, miny, maxy, minz, maxz)

    def setup_modelview(self):
        x, y, z = self.cameraPosition

        GL.glRotate(90.0, 1.0, 0.0, 0.0)
        GL.glTranslate(-x, 0, -z)

    def zoom(self, f):
        x, y, z = self.cameraPosition
        mx, my, mz = self.blockFaceUnderCursor[0]
        dx, dz = mx - x, mz - z
        s = min(4.0, max(1 / 16., self.defaultScale / f))
        if s != self.defaultScale:
            self.defaultScale = s
            f = 1.0 - f

            self.cameraPosition = x + dx * f, self.editor.level.Height, z + dz * f
            self.editor.renderer.loadNearbyChunks()

    incrementFactor = 1.4

    def zoomIn(self):
        self.zoom(1.0 / self.incrementFactor)

    def zoomOut(self):
        self.zoom(self.incrementFactor)

    def mouse_down(self, evt):
        if evt.button == 4:  # wheel up - zoom in
#            if self.defaultScale == 4.0:
#                self.editor.swapViewports()
#            else:
            self.zoomIn()
        elif evt.button == 5:  # wheel down - zoom out
            self.zoomOut()
        else:
            super(ChunkViewport, self).mouse_down(evt)

    def rightClickDown(self, evt):
        pass

    def rightClickUp(self, evt):
        pass

    def mouse_move(self, evt):
        pass

    @mceutils.alertException
    def mouse_drag(self, evt):

        if evt.buttons[2]:
            x, y, z = self.cameraPosition
            dx, dz = evt.rel
            self.cameraPosition = (
                x - dx / self.defaultScale,
                y,
                z - dz / self.defaultScale)
        else:
            super(ChunkViewport, self).mouse_drag(evt)

    def render(self):
        super(ChunkViewport, self).render()

    @property
    def tooltipText(self):
        text = super(ChunkViewport, self).tooltipText
        if text == "1 W x 1 L x 1 H":
            return None
        return text

    def drawCeiling(self):
        pass
#        if self.defaultScale >= 0.5:
#            return super(ChunkViewport, self).drawCeiling()


class LevelEditor(GLViewport):
    anchor = "tlbr"

    def __init__(self, mcedit):
        self.mcedit = mcedit
        rect = mcedit.rect
        GLViewport.__init__(self, rect)

        self.frames = 0
        self.frameStartTime = datetime.now()
        self.oldFrameStartTime = self.frameStartTime

        self.dragInProgress = False

        self.debug = 0
        self.debugString = ""

        self.perfSamples = 5
        self.frameSamples = [timedelta(0, 0, 0)] * 5

        self.unsavedEdits = 0
        self.undoStack = []
        self.copyStack = []

        self.level = None

        self.cameraInputs = [0., 0., 0.]
        self.cameraPanKeys = [0., 0.]
        self.cameraToolDistance = self.defaultCameraToolDistance

        self.createRenderers()

        self.sixteenBlockTex = self.genSixteenBlockTexture()

        # self.Font = Font("Verdana, Arial", 18)

        self.generateStars()

        self.optionsBar = Widget()

        mcEditButton = Button("MCEdit", action=self.showControls)
        viewDistanceDown = Button("<", action=self.decreaseViewDistance)
        viewDistanceUp = Button(">", action=self.increaseViewDistance)
        viewDistanceReadout = ValueDisplay(width=40, ref=AttrRef(self.renderer, "viewDistance"))

        chunksReadout = SmallValueDisplay(width=140,
            get_value=lambda: "Chunks: %d" % len(self.renderer.chunkRenderers),
            tooltipText="Number of chunks loaded into the renderer.")
        fpsReadout = SmallValueDisplay(width=80,
            get_value=lambda: "fps: %0.1f" % self.averageFPS,
            tooltipText="Frames per second.")
        cpsReadout = SmallValueDisplay(width=100,
            get_value=lambda: "cps: %0.1f" % self.averageCPS,
            tooltipText="Chunks per second.")
        mbReadout = SmallValueDisplay(width=60,
            get_value=lambda: "MBv: %0.1f" % (self.renderer.bufferUsage / 1000000.),
            tooltipText="Memory used for vertexes")


        def showViewOptions():
            col = []
            col.append(mceutils.CheckBoxLabel("Entities", fg_color=(0xff, 0x22, 0x22), ref=Settings.drawEntities.propertyRef()))
            col.append(mceutils.CheckBoxLabel("Items", fg_color=(0x22, 0xff, 0x22), ref=Settings.drawItems.propertyRef()))
            col.append(mceutils.CheckBoxLabel("TileEntities", fg_color=(0xff, 0xff, 0x22), ref=Settings.drawTileEntities.propertyRef()))
            col.append(mceutils.CheckBoxLabel("TileTicks", ref=Settings.drawTileTicks.propertyRef()))
            col.append(mceutils.CheckBoxLabel("Unpopulated Chunks", fg_color=renderer.TerrainPopulatedRenderer.color,
                                     ref=Settings.drawUnpopulatedChunks.propertyRef()))

            col.append(mceutils.CheckBoxLabel("Sky", ref=Settings.drawSky.propertyRef()))
            col.append(mceutils.CheckBoxLabel("Fog", ref=Settings.drawFog.propertyRef()))
            col.append(mceutils.CheckBoxLabel("Ceiling",
                ref=Settings.showCeiling.propertyRef()))

            col.append(mceutils.CheckBoxLabel("Hidden Ores",
                ref=Settings.showHiddenOres.propertyRef()))

            col.append(mceutils.CheckBoxLabel("Chunk Redraw", fg_color=(0xff, 0x99, 0x99),
                ref=Settings.showChunkRedraw.propertyRef()))

            col = Column(col, align="r")

            d = QuickDialog()
            d.add(col)
            d.shrink_wrap()
            d.topleft = viewButton.bottomleft
            d.present(centered=False)

        viewButton = Button("Show...", action=showViewOptions)

        mbReadoutRow = Row((mbReadout, Label("")))
        readoutGrid = Grid(((chunksReadout, fpsReadout), (mbReadoutRow, cpsReadout), ), 0, 0)

        self.viewportButton = Button("Camera View", action=self.swapViewports,
            tooltipText="Shortcut: TAB")

        self.recordUndoButton = mceutils.CheckBoxLabel("Record Undo", ref=AttrRef(self, 'recordUndo'))

        row = (mcEditButton, viewDistanceDown, Label("View Distance:"), viewDistanceReadout, viewDistanceUp,
               readoutGrid, viewButton, self.viewportButton, self.recordUndoButton)

        # row += (Button("CR Info", action=self.showChunkRendererInfo), )
        row = Row(row)
        self.add(row)
        self.statusLabel = ValueDisplay(width=self.width, ref=AttrRef(self, "statusText"))

        self.mainViewport = CameraViewport(self)
        self.chunkViewport = ChunkViewport(self)

        self.mainViewport.height -= row.height

        self.mainViewport.height -= self.statusLabel.height
        self.statusLabel.bottom = self.bottom
        self.statusLabel.anchor = "blrh"

        self.add(self.statusLabel)

        self.viewportContainer = Widget(is_gl_container=True, anchor="tlbr")
        self.viewportContainer.top = row.bottom
        self.viewportContainer.size = self.mainViewport.size
        self.add(self.viewportContainer)

        Settings.viewMode.addObserver(self)
        Settings.undoLimit.addObserver(self)

        self.reloadToolbar()

        self.currentTool = None
        self.toolbar.selectTool(0)

        self.controlPanel = ControlPanel(self)
        self.controlPanel.topleft = mcEditButton.bottomleft


    def __del__(self):
        self.deleteAllCopiedSchematics()

    _viewMode = None

    @property
    def viewMode(self):
        return self._viewMode

    @viewMode.setter
    def viewMode(self, val):
        if val == self._viewMode:
            return
        ports = {"Chunk": self.chunkViewport, "Camera": self.mainViewport}
        for p in ports.values():
            p.set_parent(None)
        port = ports.get(val, self.mainViewport)
        self.mainViewport.mouseLookOff()
        self._viewMode = val

        if val == "Camera":
            x, y, z = self.chunkViewport.cameraPosition
            try:
                h = self.level.heightMapAt(int(x), int(z))
            except:
                h = 0
            y = max(self.mainViewport.cameraPosition[1], h + 2)
            self.mainViewport.cameraPosition = x, y, z
            # self.mainViewport.yaw = 180.0
            # self.mainViewport.pitch = 90.0
            self.mainViewport.cameraVector = self.mainViewport._cameraVector()
            self.renderer.overheadMode = False
            self.viewportButton.text = "Chunk View"
        else:
            x, y, z = self.mainViewport.cameraPosition
            self.chunkViewport.cameraPosition = x, y, z
            self.renderer.overheadMode = True
            self.viewportButton.text = "Camera View"

        self.viewportContainer.add(port)
        self.currentViewport = port
        self.chunkViewport.size = self.mainViewport.size = self.viewportContainer.size
        self.renderer.loadNearbyChunks()

    def swapViewports(self):
        if Settings.viewMode.get() == "Chunk":
            Settings.viewMode = "Camera"
        else:
            Settings.viewMode = "Chunk"

    maxCopies = 10

    def addCopiedSchematic(self, sch):
        self.copyStack.insert(0, sch)
        if len(self.copyStack) > self.maxCopies:
            self.deleteCopiedSchematic(self.copyStack[-1])
        self.updateCopyPanel()

    def _deleteSchematic(self, sch):
        if hasattr(sch, 'close'):
            sch.close()
        if sch.filename and os.path.exists(sch.filename):
            os.remove(sch.filename)

    def deleteCopiedSchematic(self, sch):
        self._deleteSchematic(sch)
        self.copyStack = [s for s in self.copyStack if s is not sch]
        self.updateCopyPanel()

    def deleteAllCopiedSchematics(self):
        for s in self.copyStack:
            self._deleteSchematic(s)

    copyPanel = None

    def updateCopyPanel(self):
        if self.copyPanel:
            self.copyPanel.set_parent(None)
        if 0 == len(self.copyStack):
            return

        self.copyPanel = self.createCopyPanel()
        self.copyPanel.topright = self.topright
        self.add(self.copyPanel)

    thumbCache = None
    fboCache = None

    def createCopyPanel(self):
        panel = GLBackground()
        panel.bg_color = (0.0, 0.0, 0.0, 0.5)
        self.thumbCache = thumbCache = self.thumbCache or {}
        self.fboCache = self.fboCache or {}
        for k in self.thumbCache.keys():
            if k not in self.copyStack:
                del self.thumbCache[k]

        def createOneCopyPanel(sch):
            p = GLBackground()
            p.bg_color = (0.0, 0.0, 0.0, 0.4)
            thumb = thumbCache.get(sch)
            if thumb is None:
                thumb = ThumbView(sch)
                thumb.mouse_down = lambda e: self.pasteSchematic(sch)
                thumb.tooltipText = "Click to import this item."
                thumbCache[sch] = thumb
            self.addWorker(thumb.renderer)
            deleteButton = Button("Delete", action=lambda: (self.deleteCopiedSchematic(sch)))
            saveButton = Button("Save", action=lambda: (self.exportSchematic(sch)))
            sizeLabel = Label("{0} x {1} x {2}".format(sch.Length, sch.Width, sch.Height))

            p.add(Row((thumb, Column((sizeLabel, Row((deleteButton, saveButton))), spacing=5))))
            p.shrink_wrap()
            return p

        copies = [createOneCopyPanel(sch) for sch in self.copyStack]

        panel.add(Column(copies, align="l"))
        panel.shrink_wrap()
        panel.anchor = "whrt"
        return panel

    @mceutils.alertException
    def showAnalysis(self, schematic):
        self.analyzeBox(schematic, schematic.bounds)

    def analyzeBox(self, level, box):
        entityCounts = defaultdict(int)
        tileEntityCounts = defaultdict(int)
        types = numpy.zeros(65536, dtype='uint32')

        def _analyzeBox():
            i = 0
            for (chunk, slices, point) in level.getChunkSlices(box):
                i += 1
                yield i, box.chunkCount
                blocks = numpy.array(chunk.Blocks[slices], dtype='uint16')
                blocks |= (numpy.array(chunk.Data[slices], dtype='uint16') << 12)
                b = numpy.bincount(blocks.ravel())
                types[:b.shape[0]] += b

                for ent in chunk.getEntitiesInBox(box):
                    if ent["id"].value == "Item":
                        v = pymclevel.items.items.findItem(ent["Item"]["id"].value,
                                                 ent["Item"]["Damage"].value).name
                    else:
                        v = ent["id"].value
                    entityCounts[(ent["id"].value, v)] += 1
                for ent in chunk.getTileEntitiesInBox(box):
                    tileEntityCounts[ent["id"].value] += 1

        with mceutils.setWindowCaption("ANALYZING - "):
            mceutils.showProgress("Analyzing {0} blocks...".format(box.volume), _analyzeBox(), cancel=True)

        entitySum = numpy.sum(entityCounts.values())
        tileEntitySum = numpy.sum(tileEntityCounts.values())
        presentTypes = types.nonzero()

        blockCounts = sorted([(level.materials[t & 0xfff, t >> 12], types[t]) for t in presentTypes[0]])

        counts = []

        c = 0
        b = level.materials.Air
        for block, count in blockCounts:
            # Collapse waters and lavas together so different fluid levels are counted together
            # xxx optional
            if block.idStr not in ("water", "lava") or b.idStr != block.idStr:
                counts.append((b, c))
                b = block
                c = 0

            c += count
        counts.append((b, c))

        blockRows = [("({0}:{1})".format(block.ID, block.blockData), block.name, count)  for block, count in counts]
        # blockRows.sort(key=lambda x: alphanum_key(x[2]), reverse=True)

        rows = list(blockRows)

        def extendEntities():
            if entitySum:
                rows.extend([("", "", ""), ("", "<Entities>", entitySum)])
                rows.extend([(id[0], id[1], count) for (id, count) in sorted(entityCounts.iteritems())])
            if tileEntitySum:
                rows.extend([("", "", ""), ("", "<TileEntities>", tileEntitySum)])
                rows.extend([(id, id, count) for (id, count) in sorted(tileEntityCounts.iteritems())])
        extendEntities()

        columns = [
            TableColumn("ID", 120),
            TableColumn("Name", 250),
            TableColumn("Count", 100),
        ]
        table = TableView(columns=columns)
        table.sortColumn = columns[2]
        table.reverseSort = True

        def sortColumn(col):
            if table.sortColumn == col:
                table.reverseSort = not table.reverseSort
            else:
                table.reverseSort = (col.title == "Count")
            colnum = columns.index(col)

            def sortKey(x):
                val = x[colnum]
                if isinstance(val, basestring):
                    alphanum_key(val)
                return val

            blockRows.sort(key=sortKey,
                           reverse=table.reverseSort)
            table.sortColumn = col
            rows[:] = blockRows
            extendEntities()

        table.num_rows = lambda: len(rows)
        table.row_data = lambda i: rows[i]
        table.row_is_selected = lambda x: False
        table.click_column_header = sortColumn

        tableBacking = Widget()
        tableBacking.add(table)
        tableBacking.shrink_wrap()

        def saveToFile():
            filename = askSaveFile(mcplatform.docsFolder,
                                   title='Save analysis...',
                                   defaultName=self.level.displayName + "_analysis",
                                   filetype='Comma Separated Values\0*.txt\0\0',
                                   suffix="",
                                   )

            if filename:
                try:
                    csvfile = csv.writer(open(filename, "wb"))
                except Exception, e:
                    alert(str(e))
                else:
                    csvfile.writerows(rows)

        saveButton = Button("Save to file...", action=saveToFile)
        col = Column((Label("Volume: {0} blocks.".format(box.volume)), tableBacking, saveButton))
        Dialog(client=col, responses=["OK"]).present()

    def exportSchematic(self, schematic):
        filename = mcplatform.askSaveSchematic(
            mcplatform.schematicsDir, self.level.displayName, "schematic")

        if filename:
            schematic.saveToFile(filename)

    def getLastCopiedSchematic(self):
        if len(self.copyStack) == 0:
            return None
        return self.copyStack[0]

    toolbar = None

    def reloadToolbar(self):
        self.toolbar = EditorToolbar(self, tools=[editortools.SelectionTool(self),
                      editortools.BrushTool(self),
                      editortools.CloneTool(self),
                      editortools.FillTool(self),
                      editortools.FilterTool(self),
                      editortools.ConstructionTool(self),
                      editortools.PlayerPositionTool(self),
                      editortools.PlayerSpawnPositionTool(self),
                      editortools.ChunkTool(self),
                      ])

        self.toolbar.anchor = 'bwh'
        self.add(self.toolbar)
        self.toolbar.bottom = self.viewportContainer.bottom  # bottoms are touching
        self.toolbar.centerx = self.centerx

    is_gl_container = True

    maxDebug = 1
    allBlend = False
    onscreen = True
    mouseEntered = True
    defaultCameraToolDistance = 10
    mouseSensitivity = 5.0

    longDistanceMode = Settings.longDistanceMode.configProperty()

    def genSixteenBlockTexture(self):
        has12 = GL.glGetString(GL.GL_VERSION) >= "1.2"
        if has12:
            maxLevel = 2
            mode = GL.GL_LINEAR_MIPMAP_NEAREST
        else:
            maxLevel = 1
            mode = GL.GL_LINEAR

        def makeSixteenBlockTex():
            darkColor = (0x30, 0x30, 0x30, 0xff)
            lightColor = (0x80, 0x80, 0x80, 0xff)
            w, h, = 256, 256

            teximage = numpy.zeros((w, h, 4), dtype='uint8')
            teximage[:] = 0xff
            teximage[:, ::16] = lightColor
            teximage[::16, :] = lightColor
            teximage[:2] = darkColor
            teximage[-1:] = darkColor
            teximage[:, -1:] = darkColor
            teximage[:, :2] = darkColor
            # GL.glTexParameter(GL.GL_TEXTURE_2D,
            #                  GL.GL_TEXTURE_MIN_FILTER,
            #                  GL.GL_NEAREST_MIPMAP_NEAREST),
            GL.glTexParameter(GL.GL_TEXTURE_2D,
                              GL.GL_TEXTURE_MAX_LEVEL,
                              maxLevel - 1)

            for lev in range(maxLevel):
                step = 1 << lev
                if lev:
                    teximage[::16] = 0xff
                    teximage[:, ::16] = 0xff
                    teximage[:2] = darkColor
                    teximage[-1:] = darkColor
                    teximage[:, -1:] = darkColor
                    teximage[:, :2] = darkColor

                GL.glTexImage2D(GL.GL_TEXTURE_2D, lev, GL.GL_RGBA8,
                         w / step, h / step, 0,
                         GL.GL_RGBA, GL.GL_UNSIGNED_BYTE,
                         teximage[::step, ::step].ravel())

        return Texture(makeSixteenBlockTex, mode)

    def showProgress(self, *a, **kw):
        return mceutils.showProgress(*a, **kw)

    def drawConstructionCube(self, box, color, texture=None):
        if texture == None:
            texture = self.sixteenBlockTex
        # textured cube faces

        GL.glEnable(GL.GL_BLEND)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(False)

        # edges within terrain
        GL.glDepthFunc(GL.GL_GREATER)
        try:
            GL.glColor(color[0], color[1], color[2], max(color[3], 0.35))
        except IndexError:
            raise
        GL.glLineWidth(1.0)
        mceutils.drawCube(box, cubeType=GL.GL_LINE_STRIP)

        # edges on or outside terrain
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glColor(color[0], color[1], color[2], max(color[3] * 2, 0.75))
        GL.glLineWidth(2.0)
        mceutils.drawCube(box, cubeType=GL.GL_LINE_STRIP)

        GL.glDepthFunc(GL.GL_LESS)
        GL.glColor(color[0], color[1], color[2], color[3])
        GL.glDepthFunc(GL.GL_LEQUAL)
        mceutils.drawCube(box, texture=texture, selectionBox=True)
        GL.glDepthMask(True)

        GL.glDisable(GL.GL_BLEND)
        GL.glDisable(GL.GL_DEPTH_TEST)

    def loadFile(self, filename):
        """
        Called when the user picks a level using Load World or Open File.
        """
        if self.level and self.unsavedEdits > 0:
            resp = ask("Save unsaved edits before loading?", ["Cancel", "Don't Save", "Save"], default=2, cancel=0)
            if resp == "Cancel":
                return
            if resp == "Save":
                self.saveFile()


        self.freezeStatus("Loading " + filename)
        if self.level:
            self.level.close()

        try:
            level = pymclevel.fromFile(filename)
        except Exception, e:
            logging.exception(
                'Wasn\'t able to open a file {file => %s}' % filename
            )
            alert(u"I don't know how to open {0}:\n\n{1!r}".format(filename, e))
            return

        assert level

        self.mcedit.addRecentWorld(filename)

        try:
            self.currentViewport.cameraPosition = level.getPlayerPosition()

            y, p = level.getPlayerOrientation()
            if p == -90.0:
                p += 0.000000001
            if p == 90.0:
                p -= 0.000000001
            self.mainViewport.yaw, self.mainViewport.pitch = y, p

            pdim = level.getPlayerDimension()
            if pdim and pdim in level.dimensions:
                level = level.dimensions[pdim]

        except (KeyError, pymclevel.PlayerNotFound):  # TagNotFound
            # player tag not found, maybe
            try:
                self.currentViewport.cameraPosition = level.playerSpawnPosition()
            except KeyError:  # TagNotFound
                self.currentViewport.cameraPosition = numpy.array((0, level.Height * 0.75, 0))
                self.mainViewport.yaw = -45.
                self.mainViewport.pitch = 0.0

        self.removeNetherPanel()

        self.undoStack = []
        self.loadLevel(level)
        self.recordUndo = True
        self.clearUnsavedEdits()

        self.renderer.position = self.currentViewport.cameraPosition
        self.renderer.loadNearbyChunks()

    def loadLevel(self, level):
        """
        Called to load a level, world, or dimension into the editor and display it in the viewport.
        """
        self.level = level

        self.toolbar.selectTool(-1)
        self.toolbar.removeToolPanels()
        self.selectedChunks = set()

        self.mainViewport.stopMoving()

        self.renderer.level = level
        self.addWorker(self.renderer)

        self.initWindowCaption()
        self.selectionTool.selectNone()

        [t.levelChanged() for t in self.toolbar.tools]

        if isinstance(self.level, pymclevel.MCInfdevOldLevel):
            if self.level.parentWorld:
                dimensions = self.level.parentWorld.dimensions
            else:
                dimensions = self.level.dimensions

            dimensionsMenu = [("Earth", "0")]
            dimensionsMenu += [(pymclevel.MCAlphaDimension.dimensionNames.get(dimNo, "Dimension {0}".format(dimNo)), str(dimNo)) for dimNo in dimensions]
            for dim, name in pymclevel.MCAlphaDimension.dimensionNames.iteritems():
                if dim not in dimensions:
                    dimensionsMenu.append((name, str(dim)))

            menu = Menu("", dimensionsMenu)

            def presentMenu():
                x, y = self.netherPanel.topleft
                dimIdx = menu.present(self, (x, y - menu.height))
                if dimIdx == -1:
                    return
                dimNo = int(dimensionsMenu[dimIdx][1])
                self.gotoDimension(dimNo)

            self.netherPanel = Panel()
            self.netherButton = Button("Goto Dimension", action=presentMenu)
            self.netherPanel.add(self.netherButton)
            self.netherPanel.shrink_wrap()
            self.netherPanel.bottomright = self.viewportContainer.bottomright
            self.netherPanel.anchor = "brwh"
            self.add(self.netherPanel)

        if len(list(self.level.allChunks)) == 0:
            resp = ask("It looks like this level is completely empty!  You'll have to create some chunks before you can get started.", responses=["Create Chunks", "Cancel"])
            if resp == "Create Chunks":
                x, y, z = self.mainViewport.cameraPosition
                box = pymclevel.BoundingBox((x - 128, 0, z - 128), (256, self.level.Height, 256))
                self.selectionTool.setSelection(box)
                self.toolbar.selectTool(8)
                self.toolbar.tools[8].createChunks()
                self.mainViewport.cameraPosition = (x, self.level.Height, z)

    def removeNetherPanel(self):
        if self.netherPanel:
            self.remove(self.netherPanel)
            self.netherPanel = None

    @mceutils.alertException
    def gotoEarth(self):
        assert self.level.parentWorld
        self.removeNetherPanel()
        self.loadLevel(self.level.parentWorld)

        x, y, z = self.mainViewport.cameraPosition
        self.mainViewport.cameraPosition = [x * 8, y, z * 8]

    @mceutils.alertException
    def gotoNether(self):
        self.removeNetherPanel()
        x, y, z = self.mainViewport.cameraPosition
        self.mainViewport.cameraPosition = [x / 8, y, z / 8]
        self.loadLevel(self.level.getDimension(-1))

    def gotoDimension(self, dimNo):
        if dimNo == self.level.dimNo:
            return
        elif dimNo == -1 and self.level.dimNo == 0:
            self.gotoNether()
        elif dimNo == 0 and self.level.dimNo == -1:
            self.gotoEarth()
        else:
            self.removeNetherPanel()
            if dimNo:
                if dimNo == 1:
                    self.mainViewport.cameraPosition = (0, 96, 0)
                self.loadLevel(self.level.getDimension(dimNo))

            else:
                self.loadLevel(self.level.parentWorld)

    netherPanel = None

    def initWindowCaption(self):
        filename = self.level.filename
        s = os.path.split(filename)
        title = os.path.split(s[0])[1] + os.sep + s[1] + u" - MCEdit " + release.release
        title = title.encode('ascii', 'replace')
        display.set_caption(title)

    @mceutils.alertException
    def reload(self):
        filename = self.level.filename
        # self.discardAllChunks()
        self.loadFile(filename)

    @mceutils.alertException
    def saveFile(self):
        with mceutils.setWindowCaption("SAVING - "):
            if isinstance(self.level, pymclevel.ChunkedLevelMixin):  # xxx relight indev levels?
                level = self.level
                if level.parentWorld:
                    level = level.parentWorld

                if hasattr(level, 'checkSessionLock'):
                    try:
                        level.checkSessionLock()
                    except SessionLockLost, e:
                        alert(e.message + "\n\nYour changes cannot be saved.")
                        return

                for level in itertools.chain(level.dimensions.itervalues(), [level]):

                    if "Canceled" == mceutils.showProgress("Lighting chunks", level.generateLightsIter(), cancel=True):
                        return

                    if self.level == level:
                        if isinstance(level, pymclevel.MCInfdevOldLevel):
                            needsRefresh = [c.chunkPosition for c in level._loadedChunkData.itervalues() if c.dirty]
                            needsRefresh.extend(level.unsavedWorkFolder.listChunks())
                        else:
                            needsRefresh = [c for c in level.allChunks if level.getChunk(*c).dirty]
                        #xxx change MCInfdevOldLevel to monitor changes since last call
                        self.invalidateChunks(needsRefresh)

            self.freezeStatus("Saving...")
            self.level.saveInPlace()

        self.recordUndo = True
        self.clearUnsavedEdits()

    def addUnsavedEdit(self):
        if self.unsavedEdits:
            self.remove(self.saveInfoBackground)

        self.unsavedEdits += 1

        saveInfoBackground = GLBackground()
        saveInfoBackground.bg_color = (0.0, 0.0, 0.0, 0.6)

        saveInfoLabel = Label(self.saveInfoLabelText)
        saveInfoLabel.anchor = "blwh"
        # saveInfoLabel.width = 500

        saveInfoBackground.add(saveInfoLabel)
        saveInfoBackground.shrink_wrap()

        saveInfoBackground.left = 50
        saveInfoBackground.bottom = self.toolbar.toolbarRectInWindowCoords()[1]

        self.add(saveInfoBackground)
        self.saveInfoBackground = saveInfoBackground

    def clearUnsavedEdits(self):
        if self.unsavedEdits:
            self.unsavedEdits = 0
            self.remove(self.saveInfoBackground)

    @property
    def saveInfoLabelText(self):
        if self.unsavedEdits == 0:
            return ""
        return "{0} unsaved edits.  CTRL-S to save.  {1}".format(self.unsavedEdits, "" if self.recordUndo else "(UNDO DISABLED)")

    @property
    def viewDistanceLabelText(self):
        return "View Distance ({0})".format(self.renderer.viewDistance)

    def createRenderers(self):
        self.renderer = MCRenderer()

        self.workers = deque()

        if self.level:
            self.renderer.level = self.level
            self.addWorker(self.renderer)

        self.renderer.viewDistance = int(Settings.viewDistance.get())

    def addWorker(self, chunkWorker):
        if chunkWorker not in self.workers:
            self.workers.appendleft(chunkWorker)

    def removeWorker(self, chunkWorker):
        if chunkWorker in self.workers:
            self.workers.remove(chunkWorker)

    def getFrameDuration(self):
        frameDuration = timedelta(0, 1, 0) / self.renderer.targetFPS
        return frameDuration

    lastRendererDraw = datetime.now()

    def idleevent(self, e):
        if any(self.cameraInputs) or any(self.cameraPanKeys):
            self.postMouseMoved()

        if(self.renderer.needsImmediateRedraw or
           (self.renderer.needsRedraw and datetime.now() - self.lastRendererDraw > timedelta(0, 1, 0) / 3)):
            self.invalidate()
            self.lastRendererDraw = datetime.now()
        if self.renderer.needsImmediateRedraw:
            self.invalidate()

        if self.get_root().do_draw:
            frameDuration = self.getFrameDuration()

            while frameDuration > (datetime.now() - self.frameStartTime):
                self.doWorkUnit()
            else:
                return

        self.doWorkUnit()

    def activeevent(self, evt):
        self.mainViewport.activeevent(evt)

        if evt.state & 0x4:  # minimized
            if evt.gain == 0:
                logging.debug("Offscreen")
                self.onscreen = False

                self.mouseLookOff()

            else:
                logging.debug("Onscreen")
                self.onscreen = True
                self.invalidate()

        if evt.state & 0x1:  # mouse enter/leave
            if evt.gain == 0:
                logging.debug("Mouse left")
                self.mouseEntered = False
                self.mouseLookOff()

            else:
                logging.debug("Mouse entered")
                self.mouseEntered = True

    def swapDebugLevels(self):
        self.debug += 1
        if self.debug > self.maxDebug:
            self.debug = 0

        if self.debug:
            self.showDebugPanel()
        else:
            self.hideDebugPanel()

    def showDebugPanel(self):
        dp = GLBackground()
        debugLabel = ValueDisplay(width=1100, ref=AttrRef(self, "debugString"))
        inspectLabel = ValueDisplay(width=1100, ref=AttrRef(self, "inspectionString"))
        dp.add(Column((debugLabel, inspectLabel)))
        dp.shrink_wrap()
        dp.bg_color = (0, 0, 0, 0.6)
        self.add(dp)
        dp.top = 40
        self.debugPanel = dp

    def hideDebugPanel(self):
        self.remove(self.debugPanel)

    @property
    def statusText(self):
        try:
            return self.currentTool.statusText
        except Exception, e:
            return repr(e)

    def toolMouseDown(self, evt, f):  # xxx f is a tuple
        if self.level:
            if None != f:
                (focusPoint, direction) = f
                self.currentTool.mouseDown(evt, focusPoint, direction)

    def toolMouseUp(self, evt, f):  # xxx f is a tuple
        if self.level:
            if None != f:
                (focusPoint, direction) = f
                self.currentTool.mouseUp(evt, focusPoint, direction)

    def mouse_up(self, evt):
        button = remapMouseButton(evt.button)
        evt.dict['keyname'] = "mouse{0}".format(button)
        self.key_up(evt)

    def mouse_drag(self, evt):
        # if 'button' not in evt.dict or evt.button != 1:
        #    return
        if self.level:
            f = self.blockFaceUnderCursor
            if None != f:
                (focusPoint, direction) = f
                self.currentTool.mouseDrag(evt, focusPoint, direction)

    def mouse_down(self, evt):
        button = remapMouseButton(evt.button)

        evt.dict['keyname'] = "mouse{0}".format(button)
        self.mcedit.focus_switch = self
        self.focus_switch = None
        self.key_down(evt)

    '''
    def mouseDragOn(self):

        x,y = mouse.get_pos(0)
        if None != self.currentOperation:
            self.dragInProgress = True
            self.dragStartPoint = (x,y)
            self.currentOperation.dragStart(x,y)

    def mouseDragOff(self):
        if self.dragInProgress:
            self.dragInProgress = False
            '''

    def mouseLookOff(self):
        self.mouseWasCaptured = False
        self.mainViewport.mouseLookOff()

    def mouseLookOn(self):
        self.mainViewport.mouseLookOn()

    @property
    def blockFaceUnderCursor(self):
        return self.currentViewport.blockFaceUnderCursor

#    @property
#    def worldTooltipText(self):
#        try:
#            if self.blockFaceUnderCursor:
#                pos = self.blockFaceUnderCursor[0]
#                blockID = self.level.blockAt(*pos)
#                blockData = self.level.blockDataAt(*pos)
#
#                return "{name} ({bid})\n{pos}".format(name=self.level.materials.names[blockID][blockData], bid=blockID,pos=pos)
#
#        except Exception, e:
#            return None
#

    def generateStars(self):
        starDistance = 999.0
        starCount = 2000

        r = starDistance

        randPoints = (numpy.random.random(size=starCount * 3)) * 2.0 * r
        randPoints.shape = (starCount, 3)

        nearbyPoints = (randPoints[:, 0] < r) & (randPoints[:, 1] < r) & (randPoints[:, 2] < r)
        randPoints[nearbyPoints] += r

        randPoints[:starCount / 2, 0] = -randPoints[:starCount / 2, 0]
        randPoints[::2, 1] = -randPoints[::2, 1]
        randPoints[::4, 2] = -randPoints[::4, 2]
        randPoints[1::4, 2] = -randPoints[1::4, 2]

        randsizes = numpy.random.random(size=starCount) * 6 + 0.8

        vertsPerStar = 4

        vertexBuffer = numpy.zeros((starCount, vertsPerStar, 3), dtype='float32')

        def normvector(x):
            return x / numpy.sqrt(numpy.sum(x * x, 1))[:, numpy.newaxis]

        viewVector = normvector(randPoints)

        rmod = numpy.random.random(size=starCount * 3) * 2.0 - 1.0
        rmod.shape = (starCount, 3)
        referenceVector = viewVector + rmod

        rightVector = normvector(numpy.cross(referenceVector, viewVector)) * randsizes[:, numpy.newaxis]  # vector perpendicular to viewing line
        upVector = normvector(numpy.cross(rightVector, viewVector)) * randsizes[:, numpy.newaxis]  # vector perpendicular previous vector and viewing line

        p = randPoints
        p1 = p + (- upVector - rightVector)
        p2 = p + (upVector - rightVector)
        p3 = p + (upVector + rightVector)
        p4 = p + (- upVector + rightVector)

        vertexBuffer[:, 0, :] = p1
        vertexBuffer[:, 1, :] = p2
        vertexBuffer[:, 2, :] = p3
        vertexBuffer[:, 3, :] = p4

        self.starVertices = vertexBuffer.ravel()

    starColor = None

    def drawStars(self):
        pos = self.mainViewport.cameraPosition
        self.mainViewport.cameraPosition = map(lambda x: x / 128.0, pos)
        self.mainViewport.setModelview()

        GL.glColor(.5, .5, .5, 1.)

        GL.glVertexPointer(3, GL.GL_FLOAT, 0, self.starVertices)
        GL.glDrawArrays(GL.GL_QUADS, 0, len(self.starVertices) / 3)

        self.mainViewport.cameraPosition = pos
        self.mainViewport.setModelview()

    fractionalReachAdjustment = True

    def postMouseMoved(self):
        evt = event.Event(MOUSEMOTION, rel=(0, 0), pos=mouse.get_pos(), buttons=mouse.get_pressed())
        event.post(evt)

    def resetReach(self):
        self.postMouseMoved()
        if self.currentTool.resetToolReach():
            return
        self.cameraToolDistance = self.defaultCameraToolDistance

    def increaseReach(self):
        self.postMouseMoved()
        if self.currentTool.increaseToolReach():
            return
        self.cameraToolDistance = self._incrementReach(self.cameraToolDistance)

    def decreaseReach(self):
        self.postMouseMoved()
        if self.currentTool.decreaseToolReach():
            return
        self.cameraToolDistance = self._decrementReach(self.cameraToolDistance)

    def _incrementReach(self, reach):
        reach += 1
        if reach > 30 and self.fractionalReachAdjustment:
            reach *= 1.05
        return reach

    def _decrementReach(self, reach):
        reach -= 1
        if reach > 30 and self.fractionalReachAdjustment:
            reach *= 0.95
        return reach

    def key_up(self, evt):
        d = self.cameraInputs
        keyname = getattr(evt, 'keyname', None) or key.name(evt.key)

        if keyname == config.config.get('Keys', 'Brake'):
            self.mainViewport.brakeOff()

        # if keyname == 'left ctrl' or keyname == 'right ctrl':
        #    self.hideControls()

        if keyname == config.config.get('Keys', 'Left'):
            d[0] = 0.
        if keyname == config.config.get('Keys', 'Right'):
            d[0] = 0.
        if keyname == config.config.get('Keys', 'Forward'):
            d[2] = 0.
        if keyname == config.config.get('Keys', 'Back'):
            d[2] = 0.
        if keyname == config.config.get('Keys', 'Up'):
            d[1] = 0.
        if keyname == config.config.get('Keys', 'Down'):
            d[1] = 0.

        cp = self.cameraPanKeys
        if keyname == config.config.get('Keys', 'Pan Left'):
            cp[0] = 0.
        if keyname == config.config.get('Keys', 'Pan Right'):
            cp[0] = 0.
        if keyname == config.config.get('Keys', 'Pan Up'):
            cp[1] = 0.
        if keyname == config.config.get('Keys', 'Pan Down'):
            cp[1] = 0.

        # if keyname in ("left alt", "right alt"):

    def key_down(self, evt):
        keyname = evt.dict.get('keyname', None) or key.name(evt.key)
        if keyname == 'enter':
            keyname = 'return'

        d = self.cameraInputs
        im = [0., 0., 0.]
        mods = evt.dict.get('mod', 0)

        if keyname == 'f4' and (mods & (KMOD_ALT | KMOD_LALT | KMOD_RALT)):
            self.quit()
            return

        if mods & KMOD_ALT:
            if keyname == "z":
                self.longDistanceMode = not self.longDistanceMode
            if keyname in "12345":
                name = "option" + keyname
                if hasattr(self.currentTool, name):
                    getattr(self.currentTool, name)()

        elif hasattr(evt, 'cmd') and evt.cmd:
            if keyname == 'q' and mcplatform.cmd_name == "Cmd":
                self.quit()
                return

            if keyname == 'f':
                self.swapViewDistance()
            if keyname == 'a':
                self.selectAll()
            if keyname == 'd':
                self.deselect()
            if keyname == 'x':
                self.cutSelection()
            if keyname == 'c':
                self.copySelection()
            if keyname == 'v':
                self.pasteSelection()

            if keyname == 'r':
                self.reload()

            if keyname == 'o':
                self.askOpenFile()
            if keyname == 'l':
                self.askLoadWorld()
            if keyname == 'z':
                self.undo()
            if keyname == 's':
                self.saveFile()
            if keyname == 'n':
                self.createNewLevel()
            if keyname == 'w':
                self.closeEditor()
            if keyname == 'i':
                self.showWorldInfo()
            if keyname == 'g':
                self.showGotoPanel()

            if keyname == 'e':
                self.selectionTool.exportSelection()

            if keyname == 'f9':
                if mods & KMOD_ALT:
                    self.parent.reloadEditor()
                    # ===========================================================
                    # debugPanel = Panel()
                    # buttonColumn = [
                    #    Button("Reload Editor", action=self.parent.reloadEditor),
                    # ]
                    # debugPanel.add(Column(buttonColumn))
                    # debugPanel.shrink_wrap()
                    # self.add_centered(debugPanel)
                    # ===========================================================

                elif mods & KMOD_SHIFT:
                    raise GL.GLError(err=1285, description="User pressed CONTROL-SHIFT-F9, requesting a GL Memory Error")
                else:
                    try:
                        expr = input_text(">>> ", 600)
                        expr = compile(expr, 'eval', 'single')
                        alert("Result: {0!r}".format(eval(expr, globals(), locals())))
                    except Exception, e:
                        alert("Exception: {0!r}".format(e))

            if keyname == 'f10':
                def causeError():
                    raise ValueError("User pressed CONTROL-F10, requesting a program error.")

                if mods & KMOD_ALT:
                    alert("MCEdit, a Minecraft World Editor\n\nCopyright 2010 David Rio Vierra")
                elif mods & KMOD_SHIFT:
                    mceutils.alertException(causeError)()
                else:
                    causeError()

        else:
            if keyname == 'tab':
                self.swapViewports()

            if keyname == config.config.get('Keys', 'Brake'):
                self.mainViewport.brakeOn()

            if keyname == config.config.get('Keys', 'Reset Reach'):
                self.resetReach()
            if keyname == config.config.get('Keys', 'Increase Reach'):
                self.increaseReach()
            if keyname == config.config.get('Keys', 'Decrease Reach'):
                self.decreaseReach()

            if keyname == config.config.get('Keys', 'Flip'):
                self.currentTool.flip()
            if keyname == config.config.get('Keys', 'Roll'):
                self.currentTool.roll()
            if keyname == config.config.get('Keys', 'Rotate'):
                self.currentTool.rotate()
            if keyname == config.config.get('Keys', 'Mirror'):
                self.currentTool.mirror()
            if keyname == config.config.get('Keys', 'Swap'):
                self.currentTool.swap()

            if keyname == 'escape':
                self.toolbar.tools[0].endSelection()
                self.mouseLookOff()
                self.showControls()

            # movement
            if keyname == config.config.get('Keys', 'Left'):
                d[0] = -1.
                im[0] = -1.
            if keyname == config.config.get('Keys', 'Right'):
                d[0] = 1.
                im[0] = 1.
            if keyname == config.config.get('Keys', 'Forward'):
                d[2] = 1.
                im[2] = 1.
            if keyname == config.config.get('Keys', 'Back'):
                d[2] = -1.
                im[2] = -1.
            if keyname == config.config.get('Keys', 'Up'):
                d[1] = 1.
                im[1] = 1.
            if keyname == config.config.get('Keys', 'Down'):
                d[1] = -1.
                im[1] = -1.

            cp = self.cameraPanKeys
            if keyname == config.config.get('Keys', 'Pan Left'):
                cp[0] = -1.
            if keyname == config.config.get('Keys', 'Pan Right'):
                cp[0] = 1.
            if keyname == config.config.get('Keys', 'Pan Up'):
                cp[1] = -1.
            if keyname == config.config.get('Keys', 'Pan Down'):
                cp[1] = 1.

            if keyname == config.config.get('Keys', 'Confirm Construction'):
                self.confirmConstruction()

            # =======================================================================
            # if keyname == config.config.get('Keys','Toggle Flat Shading'):
            #    self.renderer.swapMipmapping()
            # if keyname == config.config.get('Keys','Toggle Lighting'):
            #    self.renderer.toggleLighting()
            # =======================================================================

            if keyname == config.config.get('Keys', 'Toggle FPS Counter'):
                self.swapDebugLevels()

            if keyname == config.config.get('Keys', 'Toggle Renderer'):
                self.renderer.render = not self.renderer.render

            if keyname == config.config.get('Keys', 'Delete Blocks'):
                self.deleteSelectedBlocks()

            if keyname in "123456789":
                self.toolbar.selectTool(int(keyname) - 1)

            if keyname in ('f1', 'f2', 'f3', 'f4', 'f5'):
                self.mcedit.loadRecentWorldNumber(int(keyname[1]))

    def showGotoPanel(self):

        gotoPanel = Widget()
        gotoPanel.X, gotoPanel.Y, gotoPanel.Z = map(int, self.mainViewport.cameraPosition)

        inputRow = (
          Label("X: "), IntField(ref=AttrRef(gotoPanel, "X")),
          Label("Y: "), IntField(ref=AttrRef(gotoPanel, "Y")),
          Label("Z: "), IntField(ref=AttrRef(gotoPanel, "Z")),
        )
        inputRow = Row(inputRow)
        column = (
          Label("Goto Position:"),
          Label("(click anywhere to teleport)"),
          inputRow,
          # Row( (Button("Cancel"), Button("Goto")), align="r" )
        )
        column = Column(column)
        gotoPanel.add(column)
        gotoPanel.shrink_wrap()
        d = Dialog(client=gotoPanel, responses=["Goto", "Cancel"])

        def click_outside(event):
            if event not in d:
                x, y, z = self.blockFaceUnderCursor[0]
                if y == 0:
                    y = 64
                y += 3
                gotoPanel.X, gotoPanel.Y, gotoPanel.Z = x, y, z
                if event.num_clicks == 2:
                    d.dismiss("Goto")

        d.mouse_down = click_outside
        d.top = self.viewportContainer.top + 10
        d.centerx = self.viewportContainer.centerx
        if d.present(centered=False) == "Goto":
            destPoint = gotoPanel.X, gotoPanel.Y, gotoPanel.Z
            if self.currentViewport is self.chunkViewport:
                self.swapViewports()
            self.mainViewport.cameraPosition = destPoint

    def closeEditor(self):
        if self.unsavedEdits:
            answer = ask("Save unsaved edits before closing?", ["Cancel", "Don't Save", "Save"], default=-1, cancel=0)
            if answer == "Save":
                self.saveFile()
            if answer == "Cancel":
                return

        self.unsavedEdits = 0
        self.mainViewport.mouseLookOff()
        self.level = None
        self.renderer.stopWork()
        self.removeWorker(self.renderer)
        self.renderer.level = None
        self.mcedit.removeEditor()

    def repairRegions(self):
        worldFolder = self.level.worldFolder
        for filename in worldFolder.findRegionFiles():
            rf = worldFolder.tryLoadRegionFile(filename)
            if rf:
                rf.repair()

        alert("Repairs complete.  See the console window for details.")

    @mceutils.alertException
    def showWorldInfo(self):
            ticksPerDay = 24000
            ticksPerHour = ticksPerDay / 24
            ticksPerMinute = ticksPerDay / (24 * 60)

            def decomposeMCTime(time):
                day = time / ticksPerDay
                tick = time % ticksPerDay
                hour = tick / ticksPerHour
                tick %= ticksPerHour
                minute = tick / ticksPerMinute
                tick %= ticksPerMinute

                return day, hour, minute, tick

            def composeMCTime(d, h, m, t):
                time = d * ticksPerDay + h * ticksPerHour + m * ticksPerMinute + t
                return time

            worldInfoPanel = Dialog()
            items = []

            t = functools.partial(isinstance, self.level)
            if t(pymclevel.MCInfdevOldLevel):
                if self.level.version == pymclevel.MCInfdevOldLevel.VERSION_ANVIL:
                    levelFormat = "Minecraft Infinite World (Anvil Format)"
                elif self.level.version == pymclevel.MCInfdevOldLevel.VERSION_MCR:
                    levelFormat = "Minecraft Infinite World (Region Format)"
                else:
                    levelFormat = "Minecraft Infinite World (Old Chunk Format)"
            elif t(pymclevel.MCIndevLevel):
                levelFormat = "Minecraft Indev (.mclevel format)"
            elif t(pymclevel.MCSchematic):
                levelFormat = "MCEdit Schematic"
            elif t(pymclevel.ZipSchematic):
                levelFormat = "MCEdit Schematic (Zipped Format)"
            elif t(pymclevel.MCJavaLevel):
                levelFormat = "Minecraft Classic or raw block array"
            else:
                levelFormat = "Unknown"
            formatLabel = Label(levelFormat)
            items.append(Label("Format:"))
            items.append(formatLabel)

            if hasattr(self.level, 'Time'):
                time = self.level.Time
                # timezone adjust -
                # minecraft time shows 0:00 on day 0 at the first sunrise
                # I want that to be 6:00 on day 1, so I add 30 hours
                timezoneAdjust = ticksPerHour * 30
                time += timezoneAdjust

                d, h, m, tick = decomposeMCTime(time)

                dayInput = IntField(value=d, min=1)  # ref=AttrRef(self, "Day"))
                items.append(Row((Label("Day: "), dayInput)))

                timeInput = TimeField(value=(h, m))
                timeInputRow = Row((Label("Time of day:"), timeInput))
                items.append(timeInputRow)

            if hasattr(self.level, 'RandomSeed'):
                seed = self.level.RandomSeed
                seedInputRow = mceutils.IntInputRow("RandomSeed: ", width=250, ref=AttrRef(self.level, "RandomSeed"))
                items.append(seedInputRow)

            if hasattr(self.level, 'GameType'):
                t = self.level.GameType
                types = ["Survival", "Creative"]

                def gametype(t):
                    if t < len(types):
                        return types[t]
                    return "Unknown"

                def action():
                    if b.gametype < 2:
                        b.gametype = 1 - b.gametype
                        b.text = gametype(b.gametype)
                        self.level.GameType = b.gametype
                        self.addUnsavedEdit()

                b = Button(gametype(t), action=action)
                b.gametype = t

                gametypeRow = Row((Label("Game Type: "), b))

                items.append(gametypeRow)

            if isinstance(self.level, pymclevel.MCInfdevOldLevel):
                chunkCount = self.level.chunkCount
                chunkCountLabel = Label("Number of chunks: {0}".format(chunkCount))

                items.append(chunkCountLabel)


            if hasattr(self.level, 'worldFolder'):
                if hasattr(self.level.worldFolder, 'regionFiles'):
                    worldFolder = self.level.worldFolder
                    regionCount = len(worldFolder.regionFiles)
                    regionCountLabel = Label("Number of regions: {0}".format(regionCount))
                    items.append(regionCountLabel)

                button = Button("Repair regions", action=self.repairRegions)
                items.append(button)

            def openFolder():
                filename = self.level.filename
                if not isdir(filename):
                    filename = dirname(filename)
                mcplatform.platform_open(filename)

            revealButton = Button("Open Folder", action=openFolder)
            items.append(revealButton)

            # if all(hasattr(self.level, i) for i in ("Length", "Width", "Height")):
            size = self.level.size
            sizelabel = Label("{L}L x {W}W x {H}H".format(L=size[2], H=size[1], W=size[0]))
            items.append(sizelabel)

            if hasattr(self.level, "Entities"):
                label = Label("{0} Entities".format(len(self.level.Entities)))
                items.append(label)
            if hasattr(self.level, "TileEntities"):
                label = Label("{0} TileEntities".format(len(self.level.TileEntities)))
                items.append(label)

            col = Column(items)

            col = Column((col, Button("OK", action=worldInfoPanel.dismiss)))

            worldInfoPanel.add(col)
            worldInfoPanel.shrink_wrap()

            worldInfoPanel.present()
            if hasattr(self.level, 'Time'):
                h, m = timeInput.value
                time = composeMCTime(dayInput.value, h, m, tick)
                time -= timezoneAdjust
                if self.level.Time != time:
                    self.level.Time = time
                    # xxx TimeChangeOperation
                    self.addUnsavedEdit()

            if hasattr(self.level, 'RandomSeed'):
                if seed != self.level.RandomSeed:
                    self.addUnsavedEdit()

    def swapViewDistance(self):
        if self.renderer.viewDistance >= self.renderer.maxViewDistance:
            self.renderer.viewDistance = self.renderer.minViewDistance
        else:
            self.renderer.viewDistance += 2

        self.addWorker(self.renderer)
        Settings.viewDistance.set(self.renderer.viewDistance)

    def increaseViewDistance(self):
        self.renderer.viewDistance = min(self.renderer.maxViewDistance, self.renderer.viewDistance + 2)
        self.addWorker(self.renderer)
        Settings.viewDistance.set(self.renderer.viewDistance)

    def decreaseViewDistance(self):
        self.renderer.viewDistance = max(self.renderer.minViewDistance, self.renderer.viewDistance - 2)
        self.addWorker(self.renderer)
        Settings.viewDistance.set(self.renderer.viewDistance)

    @mceutils.alertException
    def askLoadWorld(self):
        if not os.path.isdir(pymclevel.saveFileDir):
            alert(u"Could not find the Minecraft saves directory!\n\n({0} was not found or is not a directory)".format(pymclevel.saveFileDir))
            return

        worldPanel = Widget()

        potentialWorlds = os.listdir(pymclevel.saveFileDir)
        potentialWorlds = [os.path.join(pymclevel.saveFileDir, p) for p in potentialWorlds]
        worldFiles = [p for p in potentialWorlds if pymclevel.MCInfdevOldLevel.isLevel(p)]
        worlds = []
        for f in worldFiles:
            try:
                lev = pymclevel.MCInfdevOldLevel(f, readonly=True)
            except Exception:
                continue
            else:
                worlds.append(lev)
        if len(worlds) == 0:
            alert("No worlds found! You should probably play Minecraft to create your first world.")
            return

        def loadWorld():
            self.mcedit.loadFile(worldData[worldTable.selectedWorldIndex][3].filename)

        def click_row(i, evt):
            worldTable.selectedWorldIndex = i
            if evt.num_clicks == 2:
                loadWorld()
                d.dismiss("Cancel")

        worldTable = TableView(columns=[
            TableColumn("Last Played", 250, "l"),
            TableColumn("Level Name (filename)", 400, "l"),
            TableColumn("Dims", 100, "r"),

        ])

        def dateobj(lp):
            try:
                return datetime.utcfromtimestamp(lp / 1000.0)
            except:
                return datetime.utcfromtimestamp(0.0)

        def dateFormat(lp):
            try:
                return lp.strftime("%x %X").decode('utf-8')
            except:
                return u"{0} seconds since the epoch.".format(lp)

        def nameFormat(w):
            if w.LevelName == w.displayName:
                return w.LevelName
            return u"{0} ({1})".format(w.LevelName, w.displayName)

        worldData = [[dateFormat(d), nameFormat(w), str(w.dimensions.keys())[1:-1], w, d]
            for w, d in ((w, dateobj(w.LastPlayed)) for w in worlds)]
        worldData.sort(key=lambda (a, b, dim, w, d): d, reverse=True)
        # worlds = [w[2] for w in worldData]

        worldTable.selectedWorldIndex = 0
        worldTable.num_rows = lambda: len(worldData)
        worldTable.row_data = lambda i: worldData[i]
        worldTable.row_is_selected = lambda x: x == worldTable.selectedWorldIndex
        worldTable.click_row = click_row

        worldPanel.add(worldTable)
        worldPanel.shrink_wrap()

        d = Dialog(worldPanel, ["Load", "Cancel"])
        if d.present() == "Load":
            loadWorld()

    def askOpenFile(self):
        self.mouseLookOff()
        try:
            filename = mcplatform.askOpenFile()
            if filename:
                self.parent.loadFile(filename)
        except Exception:
            logging.exception('Error while asking user for filename')
            return

    def createNewLevel(self):
        self.mouseLookOff()

        newWorldPanel = Widget()
        newWorldPanel.w = newWorldPanel.h = 16
        newWorldPanel.x = newWorldPanel.z = newWorldPanel.f = 0
        newWorldPanel.y = 64
        newWorldPanel.seed = 0

        label = Label("Creating a new world.")
        generatorPanel = GeneratorPanel()

        xinput = mceutils.IntInputRow("X: ", ref=AttrRef(newWorldPanel, "x"))
        yinput = mceutils.IntInputRow("Y: ", ref=AttrRef(newWorldPanel, "y"))
        zinput = mceutils.IntInputRow("Z: ", ref=AttrRef(newWorldPanel, "z"))
        finput = mceutils.IntInputRow("f: ", ref=AttrRef(newWorldPanel, "f"), min=0, max=3)
        xyzrow = Row([xinput, yinput, zinput, finput])
        seedinput = mceutils.IntInputRow("Seed: ", width=250, ref=AttrRef(newWorldPanel, "seed"))

        winput = mceutils.IntInputRow("East-West Chunks: ", ref=AttrRef(newWorldPanel, "w"), min=0)
        hinput = mceutils.IntInputRow("North-South Chunks: ", ref=AttrRef(newWorldPanel, "h"), min=0)
        # grassinputrow = Row( (Label("Grass: ")
        # from editortools import BlockButton
        # blockInput = BlockButton(pymclevel.alphaMaterials, pymclevel.alphaMaterials.Grass)
        # blockInputRow = Row( (Label("Surface: "), blockInput) )

        types = ["Survival", "Creative"]

        def gametype(t):
            if t < len(types):
                return types[t]
            return "Unknown"

        def action():
            if gametypeButton.gametype < 2:
                gametypeButton.gametype = 1 - gametypeButton.gametype
                gametypeButton.text = gametype(gametypeButton.gametype)

        gametypeButton = Button(gametype(0), action=action)
        gametypeButton.gametype = 0
        gametypeRow = Row((Label("Game Type:"), gametypeButton))
        newWorldPanel.add(Column((label, Row([winput, hinput]), xyzrow, seedinput, gametypeRow, generatorPanel), align="l"))
        newWorldPanel.shrink_wrap()

        result = Dialog(client=newWorldPanel, responses=["Create", "Cancel"]).present()
        if result == "Cancel":
            return
        filename = mcplatform.askCreateWorld(pymclevel.saveFileDir)

        if not filename:
            return

        w = newWorldPanel.w
        h = newWorldPanel.h
        x = newWorldPanel.x
        y = newWorldPanel.y
        z = newWorldPanel.z
        f = newWorldPanel.f
        seed = newWorldPanel.seed or None

        self.freezeStatus("Creating world...")
        try:
            newlevel = pymclevel.MCInfdevOldLevel(filename=filename, create=True, random_seed=seed)
            # chunks = list(itertools.product(xrange(w / 2 - w + cx, w / 2 + cx), xrange(h / 2 - h + cz, h / 2 + cz)))

            if generatorPanel.generatorChoice.selectedChoice == "Flatland":
                y = generatorPanel.chunkHeight

            newlevel.setPlayerPosition((x + 0.5, y + 2.8, z + 0.5))
            newlevel.setPlayerOrientation((f * 90.0, 0.0))

            newlevel.setPlayerSpawnPosition((x, y + 1, z))
            newlevel.GameType = gametypeButton.gametype
            newlevel.saveInPlace()
            worker = generatorPanel.generate(newlevel, pymclevel.BoundingBox((x - w * 8, 0, z - h * 8), (w * 16, newlevel.Height, h * 16)))

            if "Canceled" == mceutils.showProgress("Generating chunks...", worker, cancel=True):
                raise RuntimeError("Canceled.")

            if y < 64:
                y = 64
                newlevel.setBlockAt(x, y, z, pymclevel.alphaMaterials.Sponge.ID)

            newlevel.saveInPlace()

            self.loadFile(filename)
        except Exception:
            logging.exception(
                'Error while creating world. {world => %s}' % filename
            )
            return

        return newlevel

    def confirmConstruction(self):
        self.currentTool.confirm()

    def selectionToChunks(self, remove=False, add=False):
        box = self.selectionBox()
        if box:
            if box == self.level.bounds:
                self.selectedChunks = set(self.level.allChunks)
                return

            selectedChunks = self.selectedChunks
            boxedChunks = set(box.chunkPositions)
            if boxedChunks.issubset(selectedChunks):
                remove = True

            if remove and not add:
                selectedChunks.difference_update(boxedChunks)
            else:
                selectedChunks.update(boxedChunks)

        self.selectionTool.selectNone()

    def selectAll(self):

        if self.currentViewport is self.chunkViewport:
            self.selectedChunks = set(self.level.allChunks)
        else:
            self.selectionTool.selectAll()

    def deselect(self):
        self.selectionTool.deselect()
        self.selectedChunks.clear()

    def endSelection(self):
        self.selectionTool.endSelection()

    def cutSelection(self):
        self.selectionTool.cutSelection()

    def copySelection(self):
        self.selectionTool.copySelection()

    def pasteSelection(self):
        schematic = self.getLastCopiedSchematic()
        self.pasteSchematic(schematic)

    def pasteSchematic(self, schematic):
        if schematic == None:
            return
        self.currentTool.cancel()
        craneTool = self.toolbar.tools[5]  # xxx
        self.currentTool = craneTool
        craneTool.loadLevel(schematic)

    def deleteSelectedBlocks(self):
        self.selectionTool.deleteBlocks()

    @mceutils.alertException
    def undo(self):
        if len(self.undoStack) == 0:
            return
        with mceutils.setWindowCaption("UNDOING - "):
            self.freezeStatus("Undoing the previous operation...")
            op = self.undoStack.pop()
            op.undo()
            changedBox = op.dirtyBox()
            if changedBox is not None:
                self.invalidateBox(changedBox)
            if op.changedLevel:
                self.addUnsavedEdit()

    def invalidateBox(self, box):
        self.renderer.invalidateChunksInBox(box)

    def invalidateChunks(self, c):
        self.renderer.invalidateChunks(c)

    def invalidateAllChunks(self):
        self.renderer.invalidateAllChunks()

    def discardAllChunks(self):
        self.renderer.discardAllChunks()

    def addDebugString(self, string):
        if self.debug:
            self.debugString += string

    averageFPS = 0.0
    averageCPS = 0.0
    shouldLoadAndRender = True
    showWorkInfo = False

    def gl_draw(self):
        self.debugString = ""
        self.inspectionString = ""

        if not self.level:
            return

        if not self.shouldLoadAndRender:
            return

        self.renderer.loadVisibleChunks()
        self.addWorker(self.renderer)

        if self.currentTool.previewRenderer:
            self.currentTool.previewRenderer.loadVisibleChunks()
            self.addWorker(self.currentTool.previewRenderer)

        self.frames += 1
        frameDuration = self.getFrameDuration()
        while frameDuration > (datetime.now() - self.frameStartTime):  # if it's less than 0ms until the next frame, go draw.  otherwise, go work.
            self.doWorkUnit()
        if self.showWorkInfo:
            self.updateWorkInfoPanel()

        frameStartTime = datetime.now()
        timeDelta = frameStartTime - self.frameStartTime

        # self.addDebugString("FrameStart: {0}  CameraTick: {1}".format(frameStartTime, self.mainViewport.lastTick))
        # self.addDebugString("D: %d, " % () )

        self.currentFrameDelta = timeDelta
        self.frameSamples.pop(0)
        self.frameSamples.append(timeDelta)

        frameTotal = numpy.sum(self.frameSamples)

        self.averageFPS = 1000000. / ((frameTotal.microseconds + 1000000 * frameTotal.seconds) / float(len(self.frameSamples)) + 0.00001)

        r = self.renderer

        chunkTotal = numpy.sum(r.chunkSamples)
        cps = 1000000. / ((chunkTotal.microseconds + 1000000 * chunkTotal.seconds) / float(len(r.chunkSamples)) + 0.00001)
        self.averageCPS = cps

        self.oldFrameStartTime = self.frameStartTime
        self.frameStartTime = frameStartTime

        if self.debug > 0:
            self.debugString = "FPS: %0.1f/%0.1f, CPS: %0.1f, VD: %d, W: %d, WF: %d, " % (1000000. / (float(timeDelta.microseconds) + 0.000001),
                                                                           self.averageFPS,
                                                                           cps,
                                                                           self.renderer.viewDistance,
                                                                           len(self.workers),
                                                                           self.renderer.workFactor)

            if True:  # xxx
                self.debugString += "DL: {dl} ({dlcount}), Tx: {t}, gc: {g}, ".format(
                    dl=len(glutils.DisplayList.allLists), dlcount=glutils.gl.listCount,
                    t=len(glutils.Texture.allTextures), g=len(gc.garbage))

            if self.renderer:
                self.renderer.addDebugInfo(self.addDebugString)

                # if self.onscreen:

    def createWorkInfoPanel(self):
        infos = []
        for w in sorted(self.workers):
            if isinstance(w, MCRenderer):
                label = Label("Rendering chunks" + ((datetime.now().second / 3) % 3) * ".")
                progress = Label("{0} chunks ({1} pending updates)".format(len(w.chunkRenderers), len(w.invalidChunkQueue)))
                col = Column((label, progress), align="l", width=200)
                infos.append(col)
            elif isinstance(w, RunningOperation):  # **FIXME** Where is RunningOperation supposed to come from?  -David Sowder 20120311
                label = Label(w.description)
                progress = Label(w.progress)
                col = Column((label, progress), align="l", width=200)
                infos.append(col)

        panel = Panel()
        if len(infos):
            panel.add(Column(infos))
            panel.shrink_wrap()
            return panel

    workInfoPanel = None

    def updateWorkInfoPanel(self):
        if self.workInfoPanel:
            self.workInfoPanel.set_parent(None)
        self.workInfoPanel = self.createWorkInfoPanel()
        if self.workInfoPanel:
            self.workInfoPanel.topright = self.topright
            self.add(self.workInfoPanel)

    def doWorkUnit(self):
        if len(self.workers):
            try:
                w = self.workers.popleft()
                w.next()
                self.workers.append(w)
            except StopIteration:
                if hasattr(w, "needsRedraw") and w.needsRedraw:
                    self.invalidate()

        else:
            time.sleep(0.001)

    def updateInspectionString(self, blockPosition):
        self.inspectionString += str(blockPosition) + ": "
        x, y, z = blockPosition
        cx, cz = x // 16, z // 16

        try:
            if self.debug:

                if isinstance(self.level, pymclevel.MCIndevLevel):
                    bl = self.level.blockLightAt(*blockPosition)
                    blockID = self.level.blockAt(*blockPosition)
                    bdata = self.level.blockDataAt(*blockPosition)
                    self.inspectionString += "ID: %d:%d (%s), " % (
                        blockID, bdata, self.level.materials.names[blockID][bdata])
                    self.inspectionString += "Data: %d, Light: %d, " % (bdata, bl)

                elif isinstance(self.level, pymclevel.ChunkedLevelMixin):
                    sl = self.level.skylightAt(*blockPosition)
                    bl = self.level.blockLightAt(*blockPosition)
                    bdata = self.level.blockDataAt(*blockPosition)
                    blockID = self.level.blockAt(*blockPosition)
                    self.inspectionString += "ID: %d:%d (%s), " % (
                        blockID, bdata, self.level.materials.names[blockID][bdata])

                    try:
                        path = self.level.getChunk(cx, cz).filename
                    except:
                        path = "chunks.dat"

                    self.inspectionString += "Data: %d, L: %d, SL: %d" % (
                        bdata, bl, sl)

                    try:
                        hm = self.level.heightMapAt(x, z)
                        self.inspectionString += ", H: %d" % hm
                    except:
                        pass
                    try:
                        tp = self.level.getChunk(cx, cz).TerrainPopulated
                        self.inspectionString += ", TP: %d" % tp
                    except:
                        pass

                    self.inspectionString += ", D: %d" % self.level.getChunk(cx, cz).dirty
                    self.inspectionString += ", NL: %d" % self.level.getChunk(cx, cz).needsLighting
                    try:
                        biome = self.level.getChunk(cx, cz).Biomes[x & 15, z & 15]
                        from pymclevel import biome_types

                        self.inspectionString += ", Bio: %s" % biome_types.biome_types[biome]
                    except AttributeError:
                        pass

                    if isinstance(self.level, pymclevel.pocket.PocketWorld):
                        ch = self.level.getChunk(cx, cz)
                        self.inspectionString += ", DC: %s" % ch.DirtyColumns[z & 15, x & 15]

                    self.inspectionString += ", Ch(%d, %d): %s" % (cx, cz, path)

                else:  # classic
                    blockID = self.level.blockAt(*blockPosition)
                    self.inspectionString += "ID: %d (%s), " % (
                        blockID, self.level.materials.names[blockID][0])

        except Exception, e:
            self.inspectionString += "Chunk {0} had an error: {1!r}".format((int(numpy.floor(blockPosition[0])) >> 4, int(numpy.floor(blockPosition[2])) >> 4), e)
            pass

    def drawWireCubeReticle(self, color=(1.0, 1.0, 1.0, 1.0), position=None):
        GL.glPolygonOffset(DepthOffset.TerrainWire, DepthOffset.TerrainWire)
        GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)

        blockPosition, faceDirection = self.blockFaceUnderCursor
        blockPosition = position or blockPosition

        mceutils.drawTerrainCuttingWire(pymclevel.BoundingBox(blockPosition, (1, 1, 1)), c1=color)

        GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)

    def drawString(self, x, y, color, string):
        return

    def freezeStatus(self, string):
        return

#        GL.glColor(1.0, 0., 0., 1.0)
#
#        # glDrawBuffer(GL.GL_FRONT)
#        GL.glMatrixMode(GL.GL_PROJECTION)
#        GL.glPushMatrix()
#        glRasterPos(50, 100)
#        for i in string:
#            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(i))
#
#        # glDrawBuffer(GL.GL_BACK)
#        GL.glMatrixMode(GL.GL_PROJECTION)
#        GL.glPopMatrix()
#        glFlush()
#        display.flip()
#        # while(True): pass

    def selectionSize(self):
        return self.selectionTool.selectionSize()

    def selectionBox(self):
        return self.selectionTool.selectionBox()

    def selectionChanged(self):
        if not self.currentTool.toolEnabled():
            self.toolbar.selectTool(-1)

        self.currentTool.selectionChanged()

    def addOperation(self, op):
        if self.recordUndo:
            self.undoStack.append(op)
            if len(self.undoStack) > self.undoLimit:
                self.undoStack.pop(0)

        self.performWithRetry(op)

    recordUndo = True

    def performWithRetry(self, op):
        try:
            op.perform(self.recordUndo)
        except MemoryError:
            self.invalidateAllChunks()
            op.perform(self.recordUndo)

    def quit(self):
        self.mouseLookOff()
        self.mcedit.confirm_quit()

    mouseWasCaptured = False

    def showControls(self):
        self.controlPanel.present(False)

    infoPanel = None

    def showChunkRendererInfo(self):
        if self.infoPanel:
            self.infoPanel.set_parent(None)
            return

        self.infoPanel = infoPanel = Widget(bg_color=(0, 0, 0, 80))
        infoPanel.add(Label(""))

        def idleHandler(evt):

            x, y, z = self.blockFaceUnderCursor[0]
            cx, cz = x // 16, z // 16
            cr = self.renderer.chunkRenderers.get((cx, cz))
            if None is cr:
                return

            crNames = ["%s - %0.1fkb" % (type(br).__name__, br.bufferSize() / 1000.0) for br in cr.blockRenderers]
            infoLabel = Label("\n".join(crNames))

            infoPanel.remove(infoPanel.subwidgets[0])
            infoPanel.add(infoLabel)
            infoPanel.shrink_wrap()
            self.invalidate()
        infoPanel.idleevent = idleHandler

        infoPanel.topleft = self.viewportContainer.topleft
        self.add(infoPanel)
        infoPanel.click_outside_response = -1
        # infoPanel.present()

##    def testGLSL(self):
##        print "Hello"
##        level = MCLevel.fromFile("mrchunk.schematic")
##        blocks = level.Blocks
##        blockCount = level.Width * level.Length * level.Height,
##        fbo = glGenFramebuffersEXT(1)
##        glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, fbo)
##
##        print blockCount, fbo
##
##        destBlocks = numpy.zeros(blockCount, 'uint8')
##        (sourceTex, destTex) = glGenTextures(2)
##
##        glBindTexture(GL_TEXTURE_3D, sourceTex)
##        glTexImage3D(GL_TEXTURE_3D, 0, 1,
##                     level.Width, level.Length, level.Height,
##                     0, GL_RED, GL.GL_UNSIGNED_BYTE,
##                     blocks)
##
##        # return
##
##        glBindTexture(GL.GL_TEXTURE_2D, destTex)
##        glTexImage2D(GL.GL_TEXTURE_2D, 0, 1,
##                     level.Width, level.Length,
##                     0, GL_RED, GL.GL_UNSIGNED_BYTE, destBlocks)
##        glTexParameter(GL.GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
##        glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT, GL_COLOR_ATTACHMENT0_EXT, GL.GL_TEXTURE_2D, destTex, 0)
##
##        vertShader = glCreateShader(GL_VERTEX_SHADER)
##
##        vertShaderSource = """
##        void main()
##        {
##            gl_Position = gl_Vertex
##        }
##        """
##
##        glShaderSource(vertShader, vertShaderSource);
##        glCompileShader(vertShader);
##
##        fragShader = glCreateShader(GL_FRAGMENT_SHADER)
##
##        fragShaderSource = """
##        void main()
##        {
##            gl_FragColor = vec4(1.0, 0.0, 1.0, 0.75);
##        }
##        """
##
##        glShaderSource(fragShader, fragShaderSource);
##        glCompileShader(fragShader);
##
##
##
##        prog = glCreateProgram()
##
##        glAttachShader(prog, vertShader)
##        glAttachShader(prog, fragShader)
##        glLinkProgram(prog)
##
##        glUseProgram(prog);
##        # return
##        GL.glDisable(GL.GL_DEPTH_TEST);
##        GL.glVertexPointer(2, GL.GL_FLOAT, 0, [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0]);
##        GL.glDrawArrays(GL.GL_QUADS, 0, 4);
##        GL.glEnable(GL.GL_DEPTH_TEST);
##
##        glFlush();
##        destBlocks = glGetTexImage(GL.GL_TEXTURE_2D, 0, GL_RED, GL.GL_UNSIGNED_BYTE);
##        print destBlocks, destBlocks[0:8];
##        raise SystemExit;

    def handleMemoryError(self):
        if self.renderer.viewDistance <= 2:
            raise MemoryError("Out of memory. Please restart MCEdit.")
        if hasattr(self.level, 'compressAllChunks'):
            self.level.compressAllChunks()
        self.toolbar.selectTool(-1)

        self.renderer.viewDistance = self.renderer.viewDistance - 4
        self.renderer.discardAllChunks()

        logging.warning(
            'Out of memory, decreasing view distance. {view => %s}' % (
                self.renderer.viewDistance
            )
        )

        Settings.viewDistance.set(self.renderer.viewDistance)
        config.saveConfig()


class EditorToolbar(GLOrtho):
    # is_gl_container = True
    toolbarSize = (184, 24)
    tooltipsUp = True

    toolbarTextureSize = (182., 22.)

    currentToolTextureRect = (0., 22., 24., 24.)
    toolbarWidthRatio = 0.5  # toolbar's width as fraction of screen width.

    def toolbarSizeForScreenWidth(self, width):
        f = max(1, int(width + 398) / 400)

        return map(lambda x: x * f, self.toolbarSize)

        # return ( self.toolbarWidthRatio * width,
        #         self.toolbarWidthRatio * width * self.toolbarTextureSize[1] / self.toolbarTextureSize[0] )

    def __init__(self, rect, tools, *args, **kw):
        GLOrtho.__init__(self, xmin=0, ymin=0,
                               xmax=self.toolbarSize[0], ymax=self.toolbarSize[1],
                               near=-4.0, far=4.0)
        self.size = self.toolbarTextureSize
        self.tools = tools
        for i, t in enumerate(tools):
            t.toolNumber = i
            t.hotkey = i + 1

        self.toolTextures = {}
        self.toolbarDisplayList = glutils.DisplayList()
        self.reloadTextures()

    def set_parent(self, parent):
        GLOrtho.set_parent(self, parent)
        self.parent_resized(0, 0)

    def parent_resized(self, dw, dh):
        self.size = self.toolbarSizeForScreenWidth(self.parent.width)
        self.centerx = self.parent.centerx
        self.bottom = self.parent.viewportContainer.bottom
        # xxx resize children when get

    def getTooltipText(self):
        toolNumber = self.toolNumberUnderMouse(mouse.get_pos())
        return self.tools[toolNumber].tooltipText

    tooltipText = property(getTooltipText)

    def toolNumberUnderMouse(self, pos):
        x, y = self.global_to_local(pos)

        (tx, ty, tw, th) = self.toolbarRectInWindowCoords()

        toolNumber = 9. * x / tw
        return min(int(toolNumber), 8)

    def mouse_down(self, evt):
        if self.parent.level:
            toolNo = self.toolNumberUnderMouse(evt.pos)
            if toolNo < 0 or toolNo > 8:
                return
            if evt.button == 1:
                self.selectTool(toolNo)
            if evt.button == 3:
                self.showToolOptions(toolNo)

    def showToolOptions(self, toolNumber):
        if toolNumber < len(self.tools) and toolNumber >= 0:
            t = self.tools[toolNumber]
            # if not t.toolEnabled():
            #    return
            if t.optionsPanel:
                t.optionsPanel.present()

    def selectTool(self, toolNumber):
        ''' pass a number outside the bounds to pick the selection tool'''
        if toolNumber >= len(self.tools) or toolNumber < 0:
            toolNumber = 0

        t = self.tools[toolNumber]
        if not t.toolEnabled():
            return
        if self.parent.currentTool == t:
            self.parent.currentTool.toolReselected()
        else:
            self.parent.selectionTool.hidePanel()
            if self.parent.currentTool != None:
                self.parent.currentTool.cancel()
            self.parent.currentTool = t
            self.parent.currentTool.toolSelected()

    def removeToolPanels(self):
        for tool in self.tools:
            tool.hidePanel()

    def toolbarRectInWindowCoords(self):
        """returns a rectangle (x, y, w, h) representing the toolbar's
        location in the window.  use for hit testing."""

        (pw, ph) = self.parent.size
        pw = float(pw)
        ph = float(ph)
        x, y = self.toolbarSizeForScreenWidth(pw)
        tw = x * 180. / 182.
        th = y * 20. / 22.

        tx = (pw - tw) / 2
        ty = ph - th * 22. / 20.

        return tx, ty, tw, th

    def toolTextureChanged(self):
        self.toolbarDisplayList.invalidate()

    def reloadTextures(self):
        self.toolTextureChanged()
        self.guiTexture = mceutils.loadPNGTexture('gui.png')
        self.toolTextures = {}

        for tool in self.tools:
            if hasattr(tool, 'reloadTextures'):
                tool.reloadTextures()
            if hasattr(tool, 'markerList'):
                tool.markerList.invalidate()

    def drawToolbar(self):
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        GL.glColor(1., 1., 1., 1.)
        w, h = self.toolbarTextureSize

        self.guiTexture.bind()

        GL.glVertexPointer(3, GL.GL_FLOAT, 0, numpy.array((
                               1, h + 1, 0.5,
                               w + 1, h + 1, 0.5,
                               w + 1, 1, 0.5,
                               1, 1, 0.5,
                            ), dtype="f4"))
        GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, numpy.array((
                             0, 0,
                             w, 0,
                             w, h,
                             0, h,
                             ), dtype="f4"))

        GL.glDrawArrays(GL.GL_QUADS, 0, 4)

        for i in range(len(self.tools)):
            tool = self.tools[i]
            if tool.toolIconName is None:
                continue
            try:
                if not tool.toolIconName in self.toolTextures:
                    filename = "toolicons" + os.sep + "{0}.png".format(tool.toolIconName)
                    self.toolTextures[tool.toolIconName] = mceutils.loadPNGTexture(filename)
                x = 20 * i + 4
                y = 4
                w = 16
                h = 16

                self.toolTextures[tool.toolIconName].bind()
                GL.glVertexPointer(3, GL.GL_FLOAT, 0, numpy.array((
                                   x, y + h, 1,
                                   x + w, y + h, 1,
                                   x + w, y, 1,
                                   x, y, 1,
                                ), dtype="f4"))
                GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, numpy.array((
                                 0, 0,
                                 w * 16, 0,
                                 w * 16, h * 16,
                                 0, h * 16,
                                 ), dtype="f4"))

                GL.glDrawArrays(GL.GL_QUADS, 0, 4)
            except Exception:
                logging.exception('Error while drawing toolbar.')
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)

    gfont = None

    def gl_draw(self):

        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glEnable(GL.GL_BLEND)
        self.toolbarDisplayList.call(self.drawToolbar)
        GL.glColor(1.0, 1.0, 0.0)

        # GL.glEnable(GL.GL_BLEND)

        # with gl.glPushMatrix(GL_TEXTURE):
        #    GL.glLoadIdentity()
        #    self.gfont.flatPrint("ADLADLADLADLADL")

        try:
            currentToolNumber = self.tools.index(self.parent.currentTool)
        except ValueError:
            pass
        else:
            # draw a bright rectangle around the current tool
            (texx, texy, texw, texh) = self.currentToolTextureRect
            # ===================================================================
            # tx = tx + tw * float(currentToolNumber) / 9.
            # tx = tx - (2./20.)*float(tw) / 9
            # ty = ty - (2./20.)*th
            # # tw = th
            # tw = (24./20.)* th
            # th = tw
            #
            # ===================================================================
            tx = 20. * float(currentToolNumber)
            ty = 0.
            tw = 24.
            th = 24.
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

            self.guiTexture.bind()
            GL.glVertexPointer(3, GL.GL_FLOAT, 0, numpy.array((
                            tx, ty, 2,
                            tx + tw, ty, 2,
                            tx + tw, ty + th, 2,
                            tx, ty + th, 2,
                            ), dtype="f4"))

            GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, numpy.array((
                              texx, texy + texh,
                              texx + texw, texy + texh,
                              texx + texw, texy,
                              texx, texy,
                               ), dtype="f4"))

            GL.glDrawArrays(GL.GL_QUADS, 0, 4)

        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisable(GL.GL_TEXTURE_2D)

        redOutBoxes = numpy.zeros(9 * 4 * 2, dtype='float32')
        cursor = 0
        for i in range(len(self.tools)):
            t = self.tools[i]
            if t.toolEnabled():
                continue
            redOutBoxes[cursor:cursor + 8] = [
                4 + i * 20, 4,
                4 + i * 20, 20,
                20 + i * 20, 20,
                20 + i * 20, 4,
            ]
            cursor += 8

        if cursor:
            GL.glColor(1.0, 0.0, 0.0, 0.3)
            GL.glVertexPointer(2, GL.GL_FLOAT, 0, redOutBoxes)
            GL.glDrawArrays(GL.GL_QUADS, 0, cursor / 2)

        GL.glDisable(GL.GL_BLEND)

########NEW FILE########
__FILENAME__ = make_huge_world
import pymclevel
from pymclevel.minecraft_server import MCServerChunkGenerator
from pymclevel import BoundingBox
import logging
logging.basicConfig(level=logging.INFO)

gen = MCServerChunkGenerator()

half_width = 4096

gen.createLevel("HugeWorld", BoundingBox((-half_width, 0, -half_width), (half_width, 0, half_width)))

########NEW FILE########
__FILENAME__ = mcedit
#!/usr/bin/env python2.7
# -*- coding: utf8 -*_
"""
mcedit.py

Startup, main menu, keyboard configuration, automatic updating.
"""
import OpenGL
import sys
import os

if "-debug" not in sys.argv:
    OpenGL.ERROR_CHECKING = False

import logging

# Setup file and stderr logging.
logger = logging.getLogger()

# Set the log level up while importing OpenGL.GL to hide some obnoxious warnings about old array handlers
logger.setLevel(logging.WARN)
from OpenGL import GL
logger.setLevel(logging.DEBUG)

logfile = 'mcedit.log'
if hasattr(sys, 'frozen'):
    if sys.platform == "win32":
        import esky
        app = esky.Esky(sys.executable)

        logfile = os.path.join(app.appdir, logfile)
    elif sys.platform == "darwin":
        logfile = os.path.expanduser("~/Library/Logs/" + logfile)

fh = logging.FileHandler(logfile, mode="w")
fh.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.WARN)

if "-v" in sys.argv:
    ch.setLevel(logging.INFO)
if "-vv" in sys.argv:
    ch.setLevel(logging.DEBUG)


class FileLineFormatter(logging.Formatter):

    def format(self, record):
        record.__dict__['fileline'] = "%(module)s.py:%(lineno)d" % record.__dict__
        record.__dict__['nameline'] = "%(name)s.py:%(lineno)d" % record.__dict__
        return super(FileLineFormatter, self).format(record)



fmt = FileLineFormatter(
    '[%(levelname)8s][%(nameline)30s]:%(message)s'
)
fh.setFormatter(fmt)
ch.setFormatter(fmt)

logger.addHandler(fh)
logger.addHandler(ch)

import albow
from albow.dialogs import Dialog
from albow.openglwidgets import GLViewport
from albow.root import RootWidget
import config
import directories
import functools
from glbackground import Panel
import glutils
import leveleditor
from leveleditor import ControlSettings, Settings
import mceutils
import mcplatform
from mcplatform import platform_open
import numpy


import os
import os.path
import pygame
from pygame import display, key, rect
import pymclevel
import release
import shutil
import sys
import traceback

ESCAPE = '\033'

class FileOpener(albow.Widget):
    is_gl_container = True

    def __init__(self, mcedit, *args, **kwargs):
        kwargs['rect'] = mcedit.rect
        albow.Widget.__init__(self, *args, **kwargs)
        self.anchor = 'tlbr'
        self.mcedit = mcedit

        helpColumn = []

        label = albow.Label("{0} {1} {2} {3} {4} {5}".format(
            config.config.get('Keys', 'Forward'),
            config.config.get('Keys', 'Left'),
            config.config.get('Keys', 'Back'),
            config.config.get('Keys', 'Right'),
            config.config.get('Keys', 'Up'),
            config.config.get('Keys', 'Down'),
        ).upper() + " to move")
        label.anchor = 'whrt'
        label.align = 'r'
        helpColumn.append(label)

        def addHelp(text):
            label = albow.Label(text)
            label.anchor = 'whrt'
            label.align = "r"
            helpColumn.append(label)

        addHelp("{0}".format(config.config.get('Keys', 'Brake').upper()) + " to slow down")
        addHelp("Right-click to toggle camera control")
        addHelp("Mousewheel to control tool distance")
        addHelp("Hold SHIFT to move along a major axis")
        addHelp("Hold ALT for details")

        helpColumn = albow.Column(helpColumn, align="r")
        helpColumn.topright = self.topright
        helpColumn.anchor = "whrt"
        #helpColumn.is_gl_container = True
        self.add(helpColumn)

        keysColumn = [albow.Label("")]
        buttonsColumn = [leveleditor.ControlPanel.getHeader()]

        shortnames = []
        for world in self.mcedit.recentWorlds():
            shortname = os.path.basename(world)
            try:
                if pymclevel.MCInfdevOldLevel.isLevel(world):
                    lev = pymclevel.MCInfdevOldLevel(world, readonly=True)
                    shortname = lev.LevelName
                    if lev.LevelName != lev.displayName:
                        shortname = u"{0} ({1})".format(lev.LevelName, lev.displayName)
            except Exception, e:
                logging.warning(
                    'Couldn\'t get name from recent world: {0!r}'.format(e))

            if shortname == "level.dat":
                shortname = os.path.basename(os.path.dirname(world))

            if len(shortname) > 40:
                shortname = shortname[:37] + "..."
            shortnames.append(shortname)

        hotkeys = ([('N', 'Create New World', self.createNewWorld),
            ('L', 'Load World...', self.mcedit.editor.askLoadWorld),
            ('O', 'Open a level...', self.promptOpenAndLoad)] + [
            ('F{0}'.format(i + 1), shortnames[i], self.createLoadButtonHandler(world))
            for i, world in enumerate(self.mcedit.recentWorlds())])

        commandRow = mceutils.HotkeyColumn(hotkeys, keysColumn, buttonsColumn)
        commandRow.anchor = 'lrh'

        sideColumn = mcedit.makeSideColumn()
        sideColumn.anchor = 'wh'

        contentRow = albow.Row((commandRow, sideColumn))
        contentRow.center = self.center
        contentRow.anchor = "rh"
        self.add(contentRow)
        self.sideColumn = sideColumn

    def gl_draw_self(self, root, offset):
        #self.mcedit.editor.mainViewport.setPerspective();
        self.mcedit.editor.drawStars()

    def idleevent(self, evt):
        self.mcedit.editor.doWorkUnit()
        #self.invalidate()

    def key_down(self, evt):
        keyname = key.name(evt.key)
        if keyname == 'f4' and (key.get_mods() & (pygame.KMOD_ALT | pygame.KMOD_LALT | pygame.KMOD_RALT)):
            raise SystemExit
        if keyname in ('f1', 'f2', 'f3', 'f4', 'f5'):
            self.mcedit.loadRecentWorldNumber(int(keyname[1]))
        if keyname is "o":
            self.promptOpenAndLoad()
        if keyname is "n":
            self.createNewWorld()
        if keyname is "l":
            self.mcedit.editor.askLoadWorld()

    def promptOpenAndLoad(self):
        try:
            filename = mcplatform.askOpenFile()
            if filename:
                self.mcedit.loadFile(filename)
        except Exception, e:
            logging.error('Error during proptOpenAndLoad: {0!r}'.format(e))

    def createNewWorld(self):
        self.parent.createNewWorld()

    def createLoadButtonHandler(self, filename):
        return lambda: self.mcedit.loadFile(filename)


class KeyConfigPanel(Dialog):
    keyConfigKeys = [
        "<Movement Controls>",
        "Forward",
        "Back",
        "Left",
        "Right",
        "Up",
        "Down",
        "Brake",
        "",
        "<Camera Controls>",
        "Pan Left",
        "Pan Right",
        "Pan Up",
        "Pan Down",
        "",
        "<Tool Controls>",
        "Rotate",
        "Roll",
        "Flip",
        "Mirror",
        "Swap",
        "Increase Reach",
        "Decrease Reach",
        "Reset Reach",
    ]

    presets = {"WASD": [
        ("Forward", "w"),
        ("Back", "s"),
        ("Left", "a"),
        ("Right", "d"),
        ("Up", "q"),
        ("Down", "z"),
        ("Brake", "space"),

        ("Rotate", "e"),
        ("Roll", "r"),
        ("Flip", "f"),
        ("Mirror", "g"),
        ("Swap", "x"),
        ("Increase Reach", "mouse4"),
        ("Decrease Reach", "mouse5"),
        ("Reset Reach", "mouse3"),
    ],
    "Arrows": [
        ("Forward", "up"),
        ("Back", "down"),
        ("Left", "left"),
        ("Right", "right"),
        ("Up", "page up"),
        ("Down", "page down"),
        ("Brake", "space"),

        ("Rotate", "home"),
        ("Roll", "end"),
        ("Flip", "insert"),
        ("Mirror", "delete"),
        ("Swap", "\\"),
        ("Increase Reach", "mouse4"),
        ("Decrease Reach", "mouse5"),
        ("Reset Reach", "mouse3"),
    ],
    "Numpad": [
        ("Forward", "[8]"),
        ("Back", "[5]"),
        ("Left", "[4]"),
        ("Right", "[6]"),
        ("Up", "[9]"),
        ("Down", "[3]"),
        ("Brake", "[0]"),

        ("Rotate", "[-]"),
        ("Roll", "[+]"),
        ("Flip", "[/]"),
        ("Mirror", "[*]"),
        ("Swap", "[.]"),
        ("Increase Reach", "mouse4"),
        ("Decrease Reach", "mouse5"),
        ("Reset Reach", "mouse3"),
    ]}

    selectedKeyIndex = 0

    def __init__(self):
        Dialog.__init__(self)
        keyConfigTable = albow.TableView(columns=[albow.TableColumn("Command", 400, "l"), albow.TableColumn("Assigned Key", 150, "r")])
        keyConfigTable.num_rows = lambda: len(self.keyConfigKeys)
        keyConfigTable.row_data = self.getRowData
        keyConfigTable.row_is_selected = lambda x: x == self.selectedKeyIndex
        keyConfigTable.click_row = self.selectTableRow
        tableWidget = albow.Widget()
        tableWidget.add(keyConfigTable)
        tableWidget.shrink_wrap()

        self.keyConfigTable = keyConfigTable

        buttonRow = (albow.Button("Assign Key...", action=self.askAssignSelectedKey),
                     albow.Button("Done", action=self.dismiss))

        buttonRow = albow.Row(buttonRow)

        choiceButton = mceutils.ChoiceButton(["WASD", "Arrows", "Numpad"], choose=self.choosePreset)
        if config.config.get("Keys", "Forward") == "up":
            choiceButton.selectedChoice = "Arrows"
        if config.config.get("Keys", "Forward") == "[8]":
            choiceButton.selectedChoice = "Numpad"

        choiceRow = albow.Row((albow.Label("Presets: "), choiceButton))
        self.choiceButton = choiceButton

        col = albow.Column((tableWidget, choiceRow, buttonRow))
        self.add(col)
        self.shrink_wrap()

    def choosePreset(self):
        preset = self.choiceButton.selectedChoice
        keypairs = self.presets[preset]
        for configKey, key in keypairs:
            config.config.set("Keys", configKey, key)

    def getRowData(self, i):
        configKey = self.keyConfigKeys[i]
        if self.isConfigKey(configKey):
            key = config.config.get("Keys", configKey)
        else:
            key = ""
        return configKey, key

    def isConfigKey(self, configKey):
        return not (len(configKey) == 0 or configKey[0] == "<")

    def selectTableRow(self, i, evt):
        self.selectedKeyIndex = i
        if evt.num_clicks == 2:
            self.askAssignSelectedKey()

    def askAssignSelectedKey(self):
        self.askAssignKey(self.keyConfigKeys[self.selectedKeyIndex])

    def askAssignKey(self, configKey, labelString=None):
        if not self.isConfigKey(configKey):
            return

        panel = Panel()
        panel.bg_color = (0.5, 0.5, 0.6, 1.0)

        if labelString is None:
            labelString = "Press a key to assign to the action \"{0}\"\n\nPress ESC to cancel.".format(configKey)
        label = albow.Label(labelString)
        panel.add(label)
        panel.shrink_wrap()

        def panelKeyDown(evt):
            keyname = key.name(evt.key)
            panel.dismiss(keyname)

        def panelMouseDown(evt):
            button = leveleditor.remapMouseButton(evt.button)
            if button > 2:
                keyname = "mouse{0}".format(button)
                panel.dismiss(keyname)

        panel.key_down = panelKeyDown
        panel.mouse_down = panelMouseDown

        keyname = panel.present()
        if keyname != "escape":
            occupiedKeys = [(v, k) for (k, v) in config.config.items("Keys") if v == keyname]
            oldkey = config.config.get("Keys", configKey)
            config.config.set("Keys", configKey, keyname)
            for keyname, setting in occupiedKeys:
                if self.askAssignKey(setting,
                                     "The key {0} is no longer bound to {1}.\n"
                                     "Press a new key for the action \"{1}\"\n\n"
                                     "Press ESC to cancel."
                                     .format(keyname, setting)):
                    config.config.set("Keys", configKey, oldkey)
                    return True
        else:
            return True


class GraphicsPanel(Panel):
    def __init__(self, mcedit):
        Panel.__init__(self)

        self.mcedit = mcedit
#
#        def getPacks():
#            return ["[Default]", "[Current]"] + mcplatform.getTexturePacks()
#
#        def packChanged():
#            self.texturePack = self.texturePackChoice.selectedChoice
#            packs = getPacks()
#            if self.texturePack not in packs:
#                self.texturePack = "[Default]"
#            self.texturePackChoice.selectedChoice = self.texturePack
#            self.texturePackChoice.choices = packs
#
#        self.texturePackChoice = texturePackChoice = mceutils.ChoiceButton(getPacks(), choose=packChanged)
#        if self.texturePack in self.texturePackChoice.choices:
#            self.texturePackChoice.selectedChoice = self.texturePack
#
#        texturePackRow = albow.Row((albow.Label("Skin: "), texturePackChoice))

        fieldOfViewRow = mceutils.FloatInputRow("Field of View: ",
            ref=Settings.fov.propertyRef(), width=100, min=25, max=120)

        targetFPSRow = mceutils.IntInputRow("Target FPS: ",
            ref=Settings.targetFPS.propertyRef(), width=100, min=1, max=60)

        bufferLimitRow = mceutils.IntInputRow("Vertex Buffer Limit (MB): ",
            ref=Settings.vertexBufferLimit.propertyRef(), width=100, min=0)

        fastLeavesRow = mceutils.CheckBoxLabel("Fast Leaves",
            ref=Settings.fastLeaves.propertyRef(),
            tooltipText="Leaves are solid, like Minecraft's 'Fast' graphics")

        roughGraphicsRow = mceutils.CheckBoxLabel("Rough Graphics",
            ref=Settings.roughGraphics.propertyRef(),
            tooltipText="All blocks are drawn the same way (overrides 'Fast Leaves')")

        enableMouseLagRow = mceutils.CheckBoxLabel("Enable Mouse Lag",
            ref=Settings.enableMouseLag.propertyRef(),
            tooltipText="Enable choppy mouse movement for faster loading.")

        settingsColumn = albow.Column((fastLeavesRow,
                                  roughGraphicsRow,
                                  enableMouseLagRow,
#                                  texturePackRow,
                                  fieldOfViewRow,
                                  targetFPSRow,
                                  bufferLimitRow,
                                  ), align='r')

        settingsColumn = albow.Column((albow.Label("Settings"),
                                 settingsColumn))

        settingsRow = albow.Row((settingsColumn,))

        optionsColumn = albow.Column((settingsRow, albow.Button("OK", action=mcedit.removeGraphicOptions)))
        self.add(optionsColumn)
        self.shrink_wrap()

    def _reloadTextures(self, pack):
        if hasattr(pymclevel.alphaMaterials, "terrainTexture"):
            self.mcedit.displayContext.loadTextures()

    texturePack = Settings.skin.configProperty(_reloadTextures)


class OptionsPanel(Dialog):
    anchor = 'wh'

    def __init__(self, mcedit):
        Dialog.__init__(self)

        self.mcedit = mcedit

        autoBrakeRow = mceutils.CheckBoxLabel("Autobrake",
            ref=ControlSettings.autobrake.propertyRef(),
            tooltipText="Apply brake when not pressing movement keys")

        swapAxesRow = mceutils.CheckBoxLabel("Swap Axes Looking Down",
            ref=ControlSettings.swapAxes.propertyRef(),
            tooltipText="Change the direction of the Forward and Backward keys when looking down")

        cameraAccelRow = mceutils.FloatInputRow("Camera Acceleration: ",
            ref=ControlSettings.cameraAccel.propertyRef(), width=100, min=5.0)

        cameraDragRow = mceutils.FloatInputRow("Camera Drag: ",
            ref=ControlSettings.cameraDrag.propertyRef(), width=100, min=1.0)

        cameraMaxSpeedRow = mceutils.FloatInputRow("Camera Max Speed: ",
            ref=ControlSettings.cameraMaxSpeed.propertyRef(), width=100, min=1.0)

        cameraBrakeSpeedRow = mceutils.FloatInputRow("Camera Braking Speed: ",
            ref=ControlSettings.cameraBrakingSpeed.propertyRef(), width=100, min=1.0)

        mouseSpeedRow = mceutils.FloatInputRow("Mouse Speed: ",
            ref=ControlSettings.mouseSpeed.propertyRef(), width=100, min=0.1, max=20.0)

        undoLimitRow = mceutils.IntInputRow("Undo Limit: ",
            ref=Settings.undoLimit.propertyRef(), width=100, min=0)

        invertRow = mceutils.CheckBoxLabel("Invert Mouse",
            ref=ControlSettings.invertMousePitch.propertyRef(),
            tooltipText="Reverse the up and down motion of the mouse.")

        spaceHeightRow = mceutils.IntInputRow("Low Detail Height",
            ref=Settings.spaceHeight.propertyRef(),
            tooltipText="When you are this far above the top of the world, move fast and use low-detail mode.")

        blockBufferRow = mceutils.IntInputRow("Block Buffer (MB):",
            ref=albow.AttrRef(self, 'blockBuffer'), min=1,
            tooltipText="Amount of memory used for temporary storage.  When more than this is needed, the disk is used instead.")

        setWindowPlacementRow = mceutils.CheckBoxLabel("Set Window Placement",
            ref=Settings.setWindowPlacement.propertyRef(),
            tooltipText="Try to save and restore the window position.")

        windowSizeRow = mceutils.CheckBoxLabel("Window Resize Alert",
            ref=Settings.shouldResizeAlert.propertyRef(),
            tooltipText="Reminds you that the cursor won't work correctly after resizing the window.")

        visibilityCheckRow = mceutils.CheckBoxLabel("Visibility Check",
            ref=Settings.visibilityCheck.propertyRef(),
            tooltipText="Do a visibility check on chunks while loading. May cause a crash.")

        longDistanceRow = mceutils.CheckBoxLabel("Long-Distance Mode",
            ref=Settings.longDistanceMode.propertyRef(),
            tooltipText="Always target the farthest block under the cursor, even in mouselook mode. Shortcut: ALT-Z")

        flyModeRow = mceutils.CheckBoxLabel("Fly Mode",
            ref=Settings.flyMode.propertyRef(),
            tooltipText="Moving forward and backward will not change your altitude in Fly Mode.")

        self.goPortableButton = goPortableButton = albow.Button("Change", action=self.togglePortable)

        goPortableButton.tooltipText = self.portableButtonTooltip()
        goPortableRow = albow.Row((albow.ValueDisplay(ref=albow.AttrRef(self, 'portableLabelText'), width=250, align='r'), goPortableButton))

        reportRow = mceutils.CheckBoxLabel("Report Errors",
            ref=Settings.reportCrashes.propertyRef(),
            tooltipText="Automatically report errors to the developer.")

        inputs = (
            spaceHeightRow,
            cameraAccelRow,
            cameraDragRow,
            cameraMaxSpeedRow,
            cameraBrakeSpeedRow,
            blockBufferRow,
            mouseSpeedRow,
            undoLimitRow,
        )

        options = (
            longDistanceRow,
            flyModeRow,
            autoBrakeRow,
            swapAxesRow,
            invertRow,
            visibilityCheckRow,
            ) + (
            ((sys.platform == "win32" and pygame.version.vernum == (1, 9, 1)) and (windowSizeRow,) or ())
            ) + (
            reportRow,
            ) + (
            (sys.platform == "win32") and (setWindowPlacementRow,) or ()
            ) + (
            goPortableRow,
        )

        rightcol = albow.Column(options, align='r')
        leftcol = albow.Column(inputs, align='r')

        optionsColumn = albow.Column((albow.Label("Options"),
                                albow.Row((leftcol, rightcol), align="t")))

        settingsRow = albow.Row((optionsColumn,))

        optionsColumn = albow.Column((settingsRow, albow.Button("OK", action=self.dismiss)))

        self.add(optionsColumn)
        self.shrink_wrap()

    @property
    def blockBuffer(self):
        return Settings.blockBuffer.get() / 1048576

    @blockBuffer.setter
    def blockBuffer(self, val):
        Settings.blockBuffer.set(int(val * 1048576))

    def portableButtonTooltip(self):
        return ("Click to make your MCEdit install self-contained by moving the settings and schematics into the program folder",
                "Click to make your MCEdit install persistent by moving the settings and schematics into your Documents folder")[mcplatform.portable]

    @property
    def portableLabelText(self):
        return ("Install Mode: Portable", "Install Mode: Fixed")[1 - mcplatform.portable]

    def togglePortable(self):
        textChoices = [
             "This will make your MCEdit \"portable\" by moving your settings and schematics into the same folder as {0}. Continue?".format((sys.platform == "darwin" and "the MCEdit application" or "MCEditData")),
             "This will move your settings and schematics to your Documents folder. Continue?",
        ]
        if sys.platform == "darwin":
            textChoices[1] = "This will move your schematics to your Documents folder and your settings to your Preferences folder. Continue?"

        alertText = textChoices[mcplatform.portable]
        if albow.ask(alertText) == "OK":
            try:
                [mcplatform.goPortable, mcplatform.goFixed][mcplatform.portable]()
            except Exception, e:
                traceback.print_exc()
                albow.alert(u"Error while moving files: {0}".format(repr(e)))

        self.goPortableButton.tooltipText = self.portableButtonTooltip()


class MCEdit(GLViewport):
    #debug_resize = True

    def __init__(self, displayContext, *args):
        ws = displayContext.getWindowSize()
        r = rect.Rect(0, 0, ws[0], ws[1])
        GLViewport.__init__(self, r)
        self.displayContext = displayContext
        self.bg_color = (0, 0, 0, 1)
        self.anchor = 'tlbr'

        if not config.config.has_section("Recent Worlds"):
            config.config.add_section("Recent Worlds")
            self.setRecentWorlds([""] * 5)

        self.optionsPanel = OptionsPanel(self)
        self.graphicOptionsPanel = GraphicsPanel(self)

        self.keyConfigPanel = KeyConfigPanel()

        self.droppedLevel = None
        self.reloadEditor()

        """
        check command line for files dropped from explorer
        """
        if len(sys.argv) > 1:
            for arg in sys.argv[1:]:
                f = arg.decode(sys.getfilesystemencoding())
                if os.path.isdir(os.path.join(pymclevel.saveFileDir, f)):
                    f = os.path.join(pymclevel.saveFileDir, f)
                    self.droppedLevel = f
                    break
                if os.path.exists(f):
                    self.droppedLevel = f
                    break

        self.fileOpener = FileOpener(self)
        self.add(self.fileOpener)

        self.fileOpener.focus()

    editor = None

    def reloadEditor(self):
        reload(leveleditor)
        level = None

        pos = None

        if self.editor:
            level = self.editor.level
            self.remove(self.editor)
            c = self.editor.mainViewport
            pos, yaw, pitch = c.position, c.yaw, c.pitch

        self.editor = leveleditor.LevelEditor(self)
        self.editor.anchor = 'tlbr'
        if level:
            self.add(self.editor)
            self.editor.gotoLevel(level)
            self.focus_switch = self.editor

            if pos is not None:
                c = self.editor.mainViewport

                c.position, c.yaw, c.pitch = pos, yaw, pitch

    def removeGraphicOptions(self):
        self.removePanel(self.graphicOptionsPanel)

    def removePanel(self, panel):
        if panel.parent:
            panel.set_parent(None)
            if self.editor.parent:
                self.focus_switch = self.editor
            elif self.fileOpener.parent:
                self.focus_switch = self.fileOpener

    def add_right(self, widget):
        w, h = self.size
        widget.centery = h // 2
        widget.right = w
        self.add(widget)

    def showPanel(self, optionsPanel):
        if optionsPanel.parent:
            optionsPanel.set_parent(None)

        optionsPanel.anchor = "whr"
        self.add_right(optionsPanel)
        self.editor.mouseLookOff()

    def showOptions(self):
        self.optionsPanel.present()

    def showGraphicOptions(self):
        self.showPanel(self.graphicOptionsPanel)

    def showKeyConfig(self):
        self.keyConfigPanel.present()

    def loadRecentWorldNumber(self, i):
        worlds = list(self.recentWorlds())
        if i - 1 < len(worlds):
            self.loadFile(worlds[i - 1])

    numRecentWorlds = 5

    def removeLevelDat(self, filename):
        if filename.endswith("level.dat"):
            filename = os.path.dirname(filename)
        return filename

    def recentWorlds(self):
        worlds = []
        for i in range(self.numRecentWorlds):
            if config.config.has_option("Recent Worlds", str(i)):
                try:
                    filename = (config.config.get("Recent Worlds", str(i)).decode('utf-8'))
                    worlds.append(self.removeLevelDat(filename))
                except Exception, e:
                    logging.error(repr(e))

        return list((f for f in worlds if f and os.path.exists(f)))

    def addRecentWorld(self, filename):
        filename = self.removeLevelDat(filename)
        rw = list(self.recentWorlds())
        if filename in rw:
            return
        rw = [filename] + rw[:self.numRecentWorlds - 1]
        self.setRecentWorlds(rw)

    def setRecentWorlds(self, worlds):
        for i, filename in enumerate(worlds):
            config.config.set("Recent Worlds", str(i), filename.encode('utf-8'))

    def makeSideColumn(self):
        def showLicense():
            platform_open(os.path.join(directories.dataDir, "LICENSE.txt"))

        readmePath = os.path.join(directories.dataDir, "README.html")

        hotkeys = ([("",
                  "Keys",
                  self.showKeyConfig),
                  ("",
                  "Graphics",
                  self.showGraphicOptions),
                  ("",
                  "Options",
                  self.showOptions),
                  ("",
                  "Homepage",
                  lambda: platform_open("http://www.mcedit.net/")),
                  ("",
                  "About MCEdit",
                  lambda: platform_open("http://www.mcedit.net/about.html")),
                  ("",
                  "Recent Changes",
                  lambda: platform_open("http://www.mcedit.net/changes/%s.html" % release.release)),
                  ("",
                  "License",
                  showLicense),
                  ])

        c = mceutils.HotkeyColumn(hotkeys)

        return c

    def resized(self, dw, dh):
        """
        Handle window resizing events.
        """
        GLViewport.resized(self, dw, dh)

        (w, h) = self.size
        if w == 0 and h == 0:
            # The window has been minimized, no need to draw anything.
            self.editor.renderer.render = False
            return

        if not self.editor.renderer.render:
            self.editor.renderer.render = True

        surf = pygame.display.get_surface()
        assert isinstance(surf, pygame.Surface)
        dw, dh = surf.get_size()

        if w > 0 and h > 0:
            Settings.windowWidth.set(w)
            Settings.windowHeight.set(h)
            config.saveConfig()

        if pygame.version.vernum == (1, 9, 1):
            if sys.platform == "win32":
                if w - dw > 20 or h - dh > 20:
                    if not hasattr(self, 'resizeAlert'):
                        self.resizeAlert = self.shouldResizeAlert
                    if self.resizeAlert:
                        albow.alert("Window size increased. You may have problems using the cursor until MCEdit is restarted.")
                        self.resizeAlert = False

    shouldResizeAlert = Settings.shouldResizeAlert.configProperty()

    def loadFile(self, filename):
        self.removeGraphicOptions()
        if os.path.exists(filename):
            try:
                self.editor.loadFile(filename)
            except Exception, e:
                logging.error(u'Failed to load file {0}: {1!r}'.format(
                    filename, e))
                return None

            self.remove(self.fileOpener)
            self.fileOpener = None
            if self.editor.level:
                self.editor.size = self.size
                self.add(self.editor)
                self.focus_switch = self.editor

    def createNewWorld(self):
        level = self.editor.createNewLevel()
        if level:
            self.remove(self.fileOpener)
            self.editor.size = self.size

            self.add(self.editor)

            self.focus_switch = self.editor
            albow.alert("World created. To expand this infinite world, explore the world in Minecraft or use the Chunk Control tool to add or delete chunks.")

    def removeEditor(self):
        self.remove(self.editor)
        self.fileOpener = FileOpener(self)
        self.add(self.fileOpener)
        self.focus_switch = self.fileOpener

    def confirm_quit(self):
        if self.editor.unsavedEdits:
            result = albow.ask("There are {0} unsaved changes.".format(self.editor.unsavedEdits),
                     responses=["Save and Quit", "Quit", "Cancel"])
            if result == "Save and Quit":
                self.saveAndQuit()
            elif result == "Quit":
                self.justQuit()
            elif result == "Cancel":
                return False
        else:
            raise SystemExit

    def saveAndQuit(self):
        self.editor.saveFile()
        raise SystemExit

    def justQuit(self):
        raise SystemExit

    closeMinecraftWarning = Settings.closeMinecraftWarning.configProperty()

    @classmethod
    def main(self):
        displayContext = GLDisplayContext()

        rootwidget = RootWidget(displayContext.display)
        mcedit = MCEdit(displayContext)
        rootwidget.displayContext = displayContext
        rootwidget.confirm_quit = mcedit.confirm_quit
        rootwidget.mcedit = mcedit

        rootwidget.add(mcedit)
        rootwidget.focus_switch = mcedit
        if 0 == len(pymclevel.alphaMaterials.yamlDatas):
            albow.alert("Failed to load minecraft.yaml. Check the console window for details.")

        if mcedit.droppedLevel:
            mcedit.loadFile(mcedit.droppedLevel)

        if hasattr(sys, 'frozen'):
            # We're being run from a bundle, check for updates.
            import esky

            app = esky.Esky(
                sys.executable.decode(sys.getfilesystemencoding()),
                'https://bitbucket.org/codewarrior0/mcedit/downloads'
            )
            try:
                update_version = app.find_update()
            except:
                # FIXME: Horrible, hacky kludge.
                update_version = None
                logging.exception('Error while checking for updates')

            if update_version:
                answer = albow.ask(
                    'Version "%s" is available, would you like to '
                    'download it?' % update_version,
                    [
                        'Yes',
                        'No',
                    ],
                    default=0,
                    cancel=1
                )
                if answer == 'Yes':
                    def callback(args):
                        status = args['status']
                        status_texts = {
                            'searching': u"Finding updates...",
                            'found':  u"Found version {new_version}",
                            'downloading': u"Downloading: {received} / {size}",
                            'ready': u"Downloaded {path}",
                            'installing': u"Installing {new_version}",
                            'cleaning up': u"Cleaning up...",
                            'done': u"Done."
                        }
                        text = status_texts.get(status, 'Unknown').format(**args)

                        panel = Dialog()
                        panel.idleevent = lambda event: panel.dismiss()
                        label = albow.Label(text, width=600)
                        panel.add(label)
                        panel.size = (500, 250)
                        panel.present()

                    try:
                        app.auto_update(callback)
                    except (esky.EskyVersionError, EnvironmentError):
                        albow.alert("Failed to install update %s" % update_version)
                    else:
                        albow.alert("Version %s installed. Restart MCEdit to begin using it." % update_version)
                        raise SystemExit()

        if mcedit.closeMinecraftWarning:
            answer = albow.ask("Warning: Only open a world in one program at a time. If you open a world at the same time in MCEdit and in Minecraft, you will lose your work and possibly damage your save file.\n\n If you are using Minecraft 1.3 or earlier, you need to close Minecraft completely before you use MCEdit.", ["Don't remind me again.", "OK"], default=1, cancel=1)
            if answer == "Don't remind me again.":
                mcedit.closeMinecraftWarning = False

        if not Settings.reportCrashesAsked.get():
            answer = albow.ask(
                "When an error occurs, MCEdit can report the details of the error to its developers. "
                "The error report will include your operating system version, MCEdit version, "
                "OpenGL version, plus the make and model of your CPU and graphics processor. No personal "
                "information will be collected.\n\n"
                "Error reporting can be enabled or disabled in the Options dialog.\n\n"
                "Enable error reporting?",
                ["Yes", "No"],
                default=0)
            Settings.reportCrashes.set(answer == "Yes")
            Settings.reportCrashesAsked.set(True)

        config.saveConfig()
        if "-causeError" in sys.argv:
            raise ValueError, "Error requested via -causeError"

        while True:
            try:
                rootwidget.run()
            except SystemExit:
                if sys.platform == "win32" and Settings.setWindowPlacement.get():
                    (flags, showCmd, ptMin, ptMax, rect) = mcplatform.win32gui.GetWindowPlacement(display.get_wm_info()['window'])
                    X, Y, r, b = rect
                    #w = r-X
                    #h = b-Y
                    if (showCmd == mcplatform.win32con.SW_MINIMIZE or
                       showCmd == mcplatform.win32con.SW_SHOWMINIMIZED):
                        showCmd = mcplatform.win32con.SW_SHOWNORMAL

                    Settings.windowX.set(X)
                    Settings.windowY.set(Y)
                    Settings.windowShowCmd.set(showCmd)

                config.saveConfig()
                mcedit.editor.renderer.discardAllChunks()
                mcedit.editor.deleteAllCopiedSchematics()
                raise
            except MemoryError:
                traceback.print_exc()
                mcedit.editor.handleMemoryError()


def main(argv):
    """
    Setup display, bundled schematics. Handle unclean
    shutdowns.
    """
    try:
        import squash_python
        squash_python.uploader.SquashUploader.headers.pop("Content-encoding", None)
        squash_python.uploader.SquashUploader.headers.pop("Accept-encoding", None)

        version = release.get_version()
        client = squash_python.get_client()
        client.APIKey = "6ea52b17-ac76-4fd8-8db4-2d7303473ca2"
        client.environment = "testing" if "build" in version else "production"
        client.host = "http://bugs.mcedit.net"
        client.notifyPath = "/bugs.php"
        client.revision = release.get_commit()
        client.build = version
        client.timeout = 5
        client.disabled = not config.config.getboolean("Settings", "report crashes new")
        def _reportingChanged(val):
            client.disabled = not val

        Settings.reportCrashes.addObserver(client, '_enabled', _reportingChanged)
        client.reportErrors()
        client.hook()
    except (ImportError, UnicodeError) as e:
        pass

    try:
        display.init()
    except pygame.error, e:
        os.environ['SDL_VIDEODRIVER'] = 'directx'
        try:
            display.init()
        except pygame.error:
            os.environ['SDL_VIDEODRIVER'] = 'windib'
            display.init()

    pygame.font.init()

    try:
        if not os.path.exists(mcplatform.schematicsDir):
            shutil.copytree(
                os.path.join(directories.dataDir, u'stock-schematics'),
                mcplatform.schematicsDir
            )
    except Exception, e:
        logging.warning('Error copying bundled schematics: {0!r}'.format(e))
        try:
            os.mkdir(mcplatform.schematicsDir)
        except Exception, e:
            logging.warning('Error creating schematics folder: {0!r}'.format(e))

    try:
        MCEdit.main()
    except Exception as e:
        logging.error("MCEdit version %s", release.get_version())
        display.quit()
        if hasattr(sys, 'frozen') and sys.platform == 'win32':
            logging.exception("%s", e)
            print "Press RETURN or close this window to dismiss."
            raw_input()

        raise

    return 0


class GLDisplayContext(object):
    def __init__(self):
        self.reset()

    def getWindowSize(self):
        w, h = (Settings.windowWidth.get(), Settings.windowHeight.get())
        return max(20, w), max(20, h)

    def displayMode(self):
        return pygame.OPENGL | pygame.RESIZABLE | pygame.DOUBLEBUF

    def reset(self):
        pygame.key.set_repeat(500, 100)

        try:
            display.gl_set_attribute(pygame.GL_SWAP_CONTROL, Settings.vsync.get())
        except Exception, e:
            logging.warning('Unable to set vertical sync: {0!r}'.format(e))

        display.gl_set_attribute(pygame.GL_ALPHA_SIZE, 8)

        d = display.set_mode(self.getWindowSize(), self.displayMode())
        try:
            pygame.scrap.init()
        except:
            logging.warning('PyGame clipboard integration disabled.')

        display.set_caption('MCEdit ~ ' + release.release, 'MCEdit')
        if sys.platform == 'win32' and Settings.setWindowPlacement.get():
            Settings.setWindowPlacement.set(False)
            config.saveConfig()
            X, Y = Settings.windowX.get(), Settings.windowY.get()

            if X:
                w, h = self.getWindowSize()
                hwndOwner = display.get_wm_info()['window']

                flags, showCmd, ptMin, ptMax, rect = mcplatform.win32gui.GetWindowPlacement(hwndOwner)
                realW = rect[2] - rect[0]
                realH = rect[3] - rect[1]

                showCmd = Settings.windowShowCmd.get()
                rect = (X, Y, X + realW, Y + realH)

                mcplatform.win32gui.SetWindowPlacement(hwndOwner, (0, showCmd, ptMin, ptMax, rect))

            Settings.setWindowPlacement.set(True)
            config.saveConfig()

        try:
            iconpath = os.path.join(directories.dataDir, 'favicon.png')
            iconfile = file(iconpath, 'rb')
            icon = pygame.image.load(iconfile, 'favicon.png')
            display.set_icon(icon)
        except Exception, e:
            logging.warning('Unable to set icon: {0!r}'.format(e))

        self.display = d

        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glAlphaFunc(GL.GL_NOTEQUAL, 0)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        # textures are 256x256, so with this we can specify pixel coordinates
        GL.glMatrixMode(GL.GL_TEXTURE)
        GL.glScale(1 / 256., 1 / 256., 1 / 256.)

        self.loadTextures()

    def getTerrainTexture(self, level):
        return self.terrainTextures.get(level.materials.name, self.terrainTextures["Alpha"])

    def loadTextures(self):
        self.terrainTextures = {}

        def makeTerrainTexture(mats):
            w, h = 1, 1
            teximage = numpy.zeros((w, h, 4), dtype='uint8')
            teximage[:] = 127, 127, 127, 255

            GL.glTexImage2D(
                GL.GL_TEXTURE_2D,
                0,
                GL.GL_RGBA8,
                w,
                h,
                0,
                GL.GL_RGBA,
                GL.GL_UNSIGNED_BYTE,
                teximage
            )

        textures = (
            (pymclevel.classicMaterials, 'terrain-classic.png'),
            (pymclevel.indevMaterials, 'terrain-classic.png'),
            (pymclevel.alphaMaterials, 'terrain.png'),
            (pymclevel.pocketMaterials, 'terrain-pocket.png')
        )

        for mats, matFile in textures:
            try:
                if mats.name == 'Alpha':
                    tex = mceutils.loadAlphaTerrainTexture()
                else:
                    tex = mceutils.loadPNGTexture(matFile)
                self.terrainTextures[mats.name] = tex
            except Exception, e:
                logging.warning(
                    'Unable to load terrain from {0}, using flat colors.'
                    'Error was: {1!r}'.format(matFile, e)
                )
                self.terrainTextures[mats.name] = glutils.Texture(
                    functools.partial(makeTerrainTexture, mats)
                )
            mats.terrainTexture = self.terrainTextures[mats.name]


def weird_fix():
    try:
        from OpenGL.platform import win32
        win32
    except Exception:
        pass

if __name__ == "__main__":
    sys.exit(main(sys.argv))

########NEW FILE########
__FILENAME__ = mceutils
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""

"""
mceutils.py

Exception catching, some basic box drawing, texture pack loading, oddball UI elements
"""

from albow.controls import ValueDisplay
from albow import alert, ask, Button, Column, Label, root, Row, ValueButton, Widget
import config
from cStringIO import StringIO
from datetime import datetime
import directories
import httplib
import mcplatform
import numpy
from OpenGL import GL, GLU
import os
import platform
import png
from pygame import display, image, Surface
import pymclevel
import release
import sys
import traceback
import zipfile

import logging

def alertException(func):
    def _alertException(*args, **kw):
        try:
            return func(*args, **kw)
        except root.Cancel:
            alert("Canceled.")
        except pymclevel.infiniteworld.SessionLockLost as e:
            alert(e.message + "\n\nYour changes cannot be saved.")

        except Exception, e:
            logging.exception("Exception:")
            if ask("Error during {0}: {1!r}".format(func, e)[:1000], ["Report Error", "Okay"], default=1, cancel=0) == "Report Error":
                try:
                    import squash_python
                    squash_python.get_client().recordException(*sys.exc_info())
                except ImportError:
                    pass
                except Exception:
                    logging.exception("Error while recording exception data:")

    return _alertException


def drawFace(box, face, type=GL.GL_QUADS):
    x, y, z, = box.origin
    x2, y2, z2 = box.maximum

    if face == pymclevel.faces.FaceXDecreasing:

        faceVertices = numpy.array(
            (x, y2, z2,
            x, y2, z,
            x, y, z,
            x, y, z2,
            ), dtype='f4')

    elif face == pymclevel.faces.FaceXIncreasing:

        faceVertices = numpy.array(
            (x2, y, z2,
            x2, y, z,
            x2, y2, z,
            x2, y2, z2,
            ), dtype='f4')

    elif face == pymclevel.faces.FaceYDecreasing:
        faceVertices = numpy.array(
            (x2, y, z2,
            x, y, z2,
            x, y, z,
            x2, y, z,
            ), dtype='f4')

    elif face == pymclevel.faces.FaceYIncreasing:
        faceVertices = numpy.array(
            (x2, y2, z,
            x, y2, z,
            x, y2, z2,
            x2, y2, z2,
            ), dtype='f4')

    elif face == pymclevel.faces.FaceZDecreasing:
        faceVertices = numpy.array(
            (x, y, z,
            x, y2, z,
            x2, y2, z,
            x2, y, z,
            ), dtype='f4')

    elif face == pymclevel.faces.FaceZIncreasing:
        faceVertices = numpy.array(
            (x2, y, z2,
            x2, y2, z2,
            x, y2, z2,
            x, y, z2,
            ), dtype='f4')

    faceVertices.shape = (4, 3)
    dim = face >> 1
    dims = [0, 1, 2]
    dims.remove(dim)

    texVertices = numpy.array(
        faceVertices[:, dims],
        dtype='f4'
    ).flatten()
    faceVertices.shape = (12,)

    texVertices *= 16
    GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

    GL.glVertexPointer(3, GL.GL_FLOAT, 0, faceVertices)
    GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, texVertices)

    GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
    GL.glEnable(GL.GL_POLYGON_OFFSET_LINE)

    if type is GL.GL_LINE_STRIP:
        indexes = numpy.array((0, 1, 2, 3, 0), dtype='uint32')
        GL.glDrawElements(type, 5, GL.GL_UNSIGNED_INT, indexes)
    else:
        GL.glDrawArrays(type, 0, 4)
    GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
    GL.glDisable(GL.GL_POLYGON_OFFSET_LINE)
    GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)


def drawCube(box, cubeType=GL.GL_QUADS, blockType=0, texture=None, textureVertices=None, selectionBox=False):
    """ pass a different cubeType e.g. GL_LINE_STRIP for wireframes """
    x, y, z, = box.origin
    x2, y2, z2 = box.maximum
    dx, dy, dz = x2 - x, y2 - y, z2 - z
    cubeVertices = numpy.array(
        (
        x, y, z,
        x, y2, z,
        x2, y2, z,
        x2, y, z,

        x2, y, z2,
        x2, y2, z2,
        x, y2, z2,
        x, y, z2,

        x2, y, z2,
        x, y, z2,
        x, y, z,
        x2, y, z,

        x2, y2, z,
        x, y2, z,
        x, y2, z2,
        x2, y2, z2,

        x, y2, z2,
        x, y2, z,
        x, y, z,
        x, y, z2,

        x2, y, z2,
        x2, y, z,
        x2, y2, z,
        x2, y2, z2,
                            ), dtype='f4')
    if textureVertices == None:
        textureVertices = numpy.array(
        (
        0, -dy * 16,
        0, 0,
        dx * 16, 0,
        dx * 16, -dy * 16,

        dx * 16, -dy * 16,
        dx * 16, 0,
        0, 0,
        0, -dy * 16,

        dx * 16, -dz * 16,
        0, -dz * 16,
        0, 0,
        dx * 16, 0,

        dx * 16, 0,
        0, 0,
        0, -dz * 16,
        dx * 16, -dz * 16,

        dz * 16, 0,
        0, 0,
        0, -dy * 16,
        dz * 16, -dy * 16,

        dz * 16, -dy * 16,
        0, -dy * 16,
        0, 0,
        dz * 16, 0,

        ), dtype='f4')

        textureVertices.shape = (6, 4, 2)

        if selectionBox:
            textureVertices[0:2] += (16 * (x & 15), 16 * (y2 & 15))
            textureVertices[2:4] += (16 * (x & 15), -16 * (z & 15))
            textureVertices[4:6] += (16 * (z & 15), 16 * (y2 & 15))
            textureVertices[:] += 0.5

    GL.glVertexPointer(3, GL.GL_FLOAT, 0, cubeVertices)
    if texture != None:
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

        texture.bind()
        GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, textureVertices),

    GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
    GL.glEnable(GL.GL_POLYGON_OFFSET_LINE)

    GL.glDrawArrays(cubeType, 0, 24)
    GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
    GL.glDisable(GL.GL_POLYGON_OFFSET_LINE)

    if texture != None:
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisable(GL.GL_TEXTURE_2D)


def drawTerrainCuttingWire(box,
                           c0=(0.75, 0.75, 0.75, 0.4),
                           c1=(1.0, 1.0, 1.0, 1.0)):

    # glDepthMask(False)
    GL.glEnable(GL.GL_DEPTH_TEST)

    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glColor(*c1)
    GL.glLineWidth(2.0)
    drawCube(box, cubeType=GL.GL_LINE_STRIP)

    GL.glDepthFunc(GL.GL_GREATER)
    GL.glColor(*c0)
    GL.glLineWidth(1.0)
    drawCube(box, cubeType=GL.GL_LINE_STRIP)

    GL.glDepthFunc(GL.GL_LEQUAL)
    GL.glDisable(GL.GL_DEPTH_TEST)
    # glDepthMask(True)

# texturePacksDir = os.path.join(pymclevel.minecraftDir, "texturepacks")


def loadAlphaTerrainTexture():
    pngFile = None

    texW, texH, terraindata = loadPNGFile(os.path.join(directories.dataDir, "terrain.png"))

    def _loadFunc():
        loadTextureFunc(texW, texH, terraindata)

    tex = glutils.Texture(_loadFunc)
    tex.data = terraindata
    return tex


def loadPNGData(filename_or_data):
    reader = png.Reader(filename_or_data)
    (w, h, data, metadata) = reader.read_flat()
    data = numpy.array(data, dtype='uint8')
    data.shape = (h, w, metadata['planes'])
    if data.shape[2] == 1:
        # indexed color. remarkably straightforward.
        data.shape = data.shape[:2]
        data = numpy.array(reader.palette(), dtype='uint8')[data]

    if data.shape[2] < 4:
        data = numpy.insert(data, 3, 255, 2)

    return w, h, data


def loadPNGFile(filename):
    (w, h, data) = loadPNGData(filename)

    powers = (16, 32, 64, 128, 256, 512, 1024, 2048, 4096)
    assert (w in powers) and (h in powers)  # how crude

    return w, h, data


def loadTextureFunc(w, h, ndata):
    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, w, h, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, ndata)
    return w, h


def loadPNGTexture(filename, *a, **kw):
    filename = os.path.join(directories.dataDir, filename)
    try:
        w, h, ndata = loadPNGFile(filename)

        tex = glutils.Texture(functools.partial(loadTextureFunc, w, h, ndata), *a, **kw)
        tex.data = ndata
        return tex
    except Exception, e:
        print "Exception loading ", filename, ": ", repr(e)
        return glutils.Texture()


import glutils


def normalize(x):
    l = x[0] * x[0] + x[1] * x[1] + x[2] * x[2]
    if l <= 0.0:
        return [0, 0, 0]
    size = numpy.sqrt(l)
    if size <= 0.0:
        return [0, 0, 0]
    return map(lambda a: a / size, x)


def normalize_size(x):
    l = x[0] * x[0] + x[1] * x[1] + x[2] * x[2]
    if l <= 0.0:
        return [0., 0., 0.], 0.
    size = numpy.sqrt(l)
    if size <= 0.0:
        return [0, 0, 0], 0
    return (x / size), size


# Label = GLLabel

class HotkeyColumn(Widget):
    is_gl_container = True

    def __init__(self, items, keysColumn=None, buttonsColumn=None):
        if keysColumn is None:
            keysColumn = []
        if buttonsColumn is None:
            buttonsColumn = []

        Widget.__init__(self)
        for (hotkey, title, action) in items:
            if isinstance(title, (str, unicode)):
                button = Button(title, action=action)
            else:
                button = ValueButton(ref=title, action=action, width=200)
            button.anchor = self.anchor

            label = Label(hotkey, width=75, margin=button.margin)
            label.anchor = "wh"

            label.height = button.height

            keysColumn.append(label)
            buttonsColumn.append(button)

        self.buttons = list(buttonsColumn)

        buttonsColumn = Column(buttonsColumn)
        buttonsColumn.anchor = self.anchor
        keysColumn = Column(keysColumn)

        commandRow = Row((keysColumn, buttonsColumn))
        self.add(commandRow)
        self.shrink_wrap()


from albow import CheckBox, AttrRef, Menu


class MenuButton(Button):
    def __init__(self, title, choices, **kw):
        Button.__init__(self, title, **kw)
        self.choices = choices
        self.menu = Menu(title, ((c, c) for c in choices))

    def action(self):
        index = self.menu.present(self, (0, 0))
        if index == -1:
            return
        self.menu_picked(index)

    def menu_picked(self, index):
        pass


class ChoiceButton(ValueButton):
    align = "c"
    choose = None

    def __init__(self, choices, scrolling=True, scroll_items=30, **kw):
        # passing an empty list of choices is ill-advised

        if 'choose' in kw:
            self.choose = kw.pop('choose')

        ValueButton.__init__(self, action=self.showMenu, **kw)

        self.scrolling = scrolling
        self.scroll_items = scroll_items
        self.choices = choices or ["[UNDEFINED]"]

        widths = [self.font.size(c)[0] for c in choices] + [self.width]
        if len(widths):
            self.width = max(widths) + self.margin * 2

        self.choiceIndex = 0

    def showMenu(self):
        choiceIndex = self.menu.present(self, (0, 0))
        if choiceIndex != -1:
            self.choiceIndex = choiceIndex
            if self.choose:
                self.choose()

    def get_value(self):
        return self.selectedChoice

    @property
    def selectedChoice(self):
        if self.choiceIndex >= len(self.choices) or self.choiceIndex < 0:
            return ""
        return self.choices[self.choiceIndex]

    @selectedChoice.setter
    def selectedChoice(self, val):
        idx = self.choices.index(val)
        if idx != -1:
            self.choiceIndex = idx

    @property
    def choices(self):
        return self._choices

    @choices.setter
    def choices(self, ch):
        self._choices = ch
        self.menu = Menu("", ((name, "pickMenu") for name in self._choices),
                         self.scrolling, self.scroll_items)


def CheckBoxLabel(title, *args, **kw):
    tooltipText = kw.pop('tooltipText', None)

    cb = CheckBox(*args, **kw)
    lab = Label(title, fg_color=cb.fg_color)
    lab.mouse_down = cb.mouse_down

    if tooltipText:
        cb.tooltipText = tooltipText
        lab.tooltipText = tooltipText

    class CBRow(Row):
        margin = 0

        @property
        def value(self):
            return self.checkbox.value

        @value.setter
        def value(self, val):
            self.checkbox.value = val

    row = CBRow((lab, cb))
    row.checkbox = cb
    return row

from albow import FloatField, IntField


def FloatInputRow(title, *args, **kw):
    return Row((Label(title, tooltipText=kw.get('tooltipText')), FloatField(*args, **kw)))


def IntInputRow(title, *args, **kw):
    return Row((Label(title, tooltipText=kw.get('tooltipText')), IntField(*args, **kw)))

from albow.dialogs import Dialog
from datetime import timedelta


def setWindowCaption(prefix):
    caption = display.get_caption()[0]

    class ctx:
        def __enter__(self):
            display.set_caption(prefix + caption)

        def __exit__(self, *args):
            display.set_caption(caption)
    return ctx()


def showProgress(progressText, progressIterator, cancel=False):
    """Show the progress for a long-running synchronous operation.
    progressIterator should be a generator-like object that can return
    either None, for an indeterminate indicator,
    A float value between 0.0 and 1.0 for a determinate indicator,
    A string, to update the progress info label
    or a tuple of (float value, string) to set the progress and update the label"""
    class ProgressWidget(Dialog):
        progressFraction = 0.0
        firstDraw = False

        def draw(self, surface):
            Widget.draw(self, surface)
            frameStart = datetime.now()
            frameInterval = timedelta(0, 1, 0) / 2
            amount = None

            try:
                while datetime.now() < frameStart + frameInterval:
                    amount = progressIterator.next()
                    if self.firstDraw is False:
                        self.firstDraw = True
                        break

            except StopIteration:
                self.dismiss()

            infoText = ""
            if amount is not None:

                if isinstance(amount, tuple):
                    if len(amount) > 2:
                        infoText = ": " + amount[2]

                    amount, max = amount[:2]

                else:
                    max = amount
                maxwidth = (self.width - self.margin * 2)
                if amount is None:
                    self.progressBar.width = maxwidth
                    self.progressBar.bg_color = (255, 255, 25, 255)
                elif isinstance(amount, basestring):
                    self.statusText = amount
                else:
                    self.progressAmount = amount
                    if isinstance(amount, (int, float)):
                        self.progressFraction = float(amount) / (float(max) or 1)
                        self.progressBar.width = maxwidth * self.progressFraction
                        self.statusText = str("{0} / {1}".format(amount, max))
                    else:
                        self.statusText = str(amount)

                if infoText:
                    self.statusText += infoText

        @property
        def estimateText(self):
            delta = ((datetime.now() - self.startTime))
            progressPercent = (int(self.progressFraction * 10000))
            left = delta * (10000 - progressPercent) / (progressPercent or 1)
            return "Time left: {0}".format(left)

        def cancel(self):
            if cancel:
                self.dismiss(False)

        def idleevent(self, evt):
            self.invalidate()

    widget = ProgressWidget()
    widget.progressText = progressText
    widget.statusText = ""
    widget.progressAmount = 0.0

    progressLabel = ValueDisplay(ref=AttrRef(widget, 'progressText'), width=550)
    statusLabel = ValueDisplay(ref=AttrRef(widget, 'statusText'), width=550)
    estimateLabel = ValueDisplay(ref=AttrRef(widget, 'estimateText'), width=550)

    progressBar = Widget(size=(550, 20), bg_color=(150, 150, 150, 255))
    widget.progressBar = progressBar
    col = (progressLabel, statusLabel, estimateLabel, progressBar)
    if cancel:
        cancelButton = Button("Cancel", action=widget.cancel, fg_color=(255, 0, 0, 255))
        col += (Column((cancelButton,), align="r"),)

    widget.add(Column(col))
    widget.shrink_wrap()
    widget.startTime = datetime.now()
    if widget.present():
        return widget.progressAmount
    else:
        return "Canceled"

from glutils import DisplayList

import functools

########NEW FILE########
__FILENAME__ = mcplatform
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""
from pymclevel.minecraft_server import ServerJarStorage, MCServerChunkGenerator

"""
mcplatform.py

Platform-specific functions, folder paths, and the whole fixed/portable nonsense.
"""

import directories
import os
from os.path import dirname, exists, join
import sys

enc = sys.getfilesystemencoding()

if sys.platform == "win32":
    import platform
    if platform.architecture()[0] == "32bit":
        plat = "win32"
    if platform.architecture()[0] == "64bit":
        plat = "win-amd64"
    sys.path.append(join(directories.dataDir, "pymclevel", "build", "lib." + plat + "-2.6").encode(enc))

os.environ["YAML_ROOT"] = join(directories.dataDir, "pymclevel").encode(enc)

from pygame import display

from albow import request_new_filename, request_old_filename
from pymclevel import saveFileDir, minecraftDir
from pymclevel import items

import shutil

texturePacksDir = os.path.join(minecraftDir, "texturepacks")


def getTexturePacks():
    try:
        return os.listdir(texturePacksDir)
    except:
        return []

# for k,v in os.environ.iteritems():
#    try:
#        os.environ[k] = v.decode(sys.getfilesystemencoding())
#    except:
#        continue
if sys.platform == "win32":
    try:
        from win32 import win32gui
        from win32 import win32api

        from win32.lib import win32con
    except ImportError:
        import win32gui
        import win32api

        import win32con

    try:
        import win32com.client
        from win32com.shell import shell, shellcon  # @UnresolvedImport
    except:
        pass

AppKit = None

if sys.platform.startswith('darwin') or sys.platform.startswith('mac'):
    cmd_name = "Cmd"
    option_name = "Opt"
else:
    cmd_name = "Ctrl"
    option_name = "Alt"

if sys.platform == "darwin":
    try:
        import AppKit
    except ImportError:
        pass


def Lion():
    try:
        import distutils.version
        import platform
        lionver = distutils.version.StrictVersion('10.7')
        curver = distutils.version.StrictVersion(platform.release())
        return curver >= lionver
    except Exception, e:
        print "Error getting system version: ", repr(e)
        return False

lastSchematicsDir = None
lastSaveDir = None


def askOpenFile(title='Select a Minecraft level....', schematics=False):
    global lastSchematicsDir, lastSaveDir

    initialDir = lastSaveDir or saveFileDir
    if schematics:
        initialDir = lastSchematicsDir or schematicsDir

    def _askOpen():
        suffixes = ["mclevel", "dat", "mine", "mine.gz"]
        if schematics:
            suffixes.append("schematic")
            suffixes.append("schematic.gz")
            suffixes.append("zip")

            suffixes.append("inv")

        if sys.platform == "win32":
            return askOpenFileWin32(title, schematics, initialDir)
        elif sys.platform == "darwin" and AppKit is not None and not Lion():

            op = AppKit.NSOpenPanel.openPanel()
            op.setPrompt_(title)
            op.setAllowedFileTypes_(suffixes)
            op.setAllowsOtherFileTypes_(True)

            op.setDirectory_(initialDir)
            if op.runModal() == 0:
                return  # pressed cancel

            AppKit.NSApp.mainWindow().makeKeyWindow()

            return op.filename()

        else:  # linux

            return request_old_filename(suffixes=suffixes, directory=initialDir)

    filename = _askOpen()
    if filename:
        if schematics:
            lastSchematicsDir = dirname(filename)
        else:
            lastSaveDir = dirname(filename)

    return filename


def askOpenFileWin32(title, schematics, initialDir):
    try:
        # if schematics:
        f = ('Levels and Schematics\0*.mclevel;*.dat;*.mine;*.mine.gz;*.schematic;*.zip;*.schematic.gz;*.inv\0' +
              '*.*\0*.*\0\0')
        #        else:
#            f = ('Levels (*.mclevel, *.dat;*.mine;*.mine.gz;)\0' +
#                 '*.mclevel;*.dat;*.mine;*.mine.gz;*.zip;*.lvl\0' +
#                 '*.*\0*.*\0\0')

        (filename, customfilter, flags) = win32gui.GetOpenFileNameW(
            hwndOwner=display.get_wm_info()['window'],
            InitialDir=initialDir,
            Flags=(win32con.OFN_EXPLORER
                   | win32con.OFN_NOCHANGEDIR
                   | win32con.OFN_FILEMUSTEXIST
                   | win32con.OFN_LONGNAMES
                   # |win32con.OFN_EXTENSIONDIFFERENT
                   ),
            Title=title,
            Filter=f,
            )
    except Exception, e:
        print "Open File: ", e
        pass
    else:
        return filename


def askSaveSchematic(initialDir, displayName, fileFormat):
    return askSaveFile(initialDir,
                title='Save this schematic...',
                defaultName=displayName + "." + fileFormat,
                filetype='Minecraft Schematics (*.{0})\0*.{0}\0\0'.format(fileFormat),
                suffix=fileFormat,
                )


def askCreateWorld(initialDir):
    defaultName = name = "Untitled World"
    i = 0
    while exists(join(initialDir, name)):
        i += 1
        name = defaultName + " " + str(i)

    return askSaveFile(initialDir,
                title='Name this new world.',
                defaultName=name,
                filetype='Minecraft World\0*.*\0\0',
                suffix="",
                )


def askSaveFile(initialDir, title, defaultName, filetype, suffix):
    if sys.platform == "win32":
        try:
            (filename, customfilter, flags) = win32gui.GetSaveFileNameW(
                hwndOwner=display.get_wm_info()['window'],
                InitialDir=initialDir,
                Flags=win32con.OFN_EXPLORER | win32con.OFN_NOCHANGEDIR | win32con.OFN_OVERWRITEPROMPT,
                File=defaultName,
                DefExt=suffix,
                Title=title,
                Filter=filetype,
                )
        except Exception, e:
            print "Error getting file name: ", e
            return

        try:
            filename = filename[:filename.index('\0')]
            filename = filename.decode(sys.getfilesystemencoding())
        except:
            pass

    elif sys.platform == "darwin" and AppKit is not None:
        sp = AppKit.NSSavePanel.savePanel()
        sp.setDirectory_(initialDir)
        sp.setAllowedFileTypes_([suffix])
        # sp.setFilename_(self.editor.level.displayName)

        if sp.runModal() == 0:
            return  # pressed cancel

        filename = sp.filename()
        AppKit.NSApp.mainWindow().makeKeyWindow()

    else:
        filename = request_new_filename(prompt=title,
                                        suffix=("." + suffix) if suffix else "",
                                        directory=initialDir,
                                        filename=defaultName,
                                        pathname=None)

    return filename

#
#    if sys.platform == "win32":
#        try:
#
#            (filename, customfilter, flags) = win32gui.GetSaveFileNameW(
#                hwndOwner = display.get_wm_info()['window'],
#                # InitialDir=saveFileDir,
#                Flags=win32con.OFN_EXPLORER | win32con.OFN_NOCHANGEDIR | win32con.OFN_OVERWRITEPROMPT,
#                File=initialDir + os.sep + displayName,
#                DefExt=fileFormat,
#                Title=,
#                Filter=,
#                )
#        except Exception, e:
#            print "Error getting filename: {0!r}".format(e)
#            return
#
#    elif sys.platform == "darwin" and AppKit is not None:
#        sp = AppKit.NSSavePanel.savePanel()
#        sp.setDirectory_(initialDir)
#        sp.setAllowedFileTypes_([fileFormat])
#        # sp.setFilename_(self.editor.level.displayName)
#
#        if sp.runModal() == 0:
#            return;  # pressed cancel
#
#        filename = sp.filename()
#        AppKit.NSApp.mainWindow().makeKeyWindow()
#
#    else:
#
#        filename = request_new_filename(prompt = "Save this schematic...",
#                                        suffix = ".{0}".format(fileFormat),
#                                        directory = initialDir,
#                                        filename = displayName,
#                                        pathname = None)
#
#    return filename


def documents_folder():
    docsFolder = None

    if sys.platform == "win32":
        try:
            objShell = win32com.client.Dispatch("WScript.Shell")
            docsFolder = objShell.SpecialFolders("MyDocuments")

        except Exception, e:
            print e
            try:
                docsFolder = shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, 0, 0)
            except Exception, e:
                userprofile = os.environ['USERPROFILE'].decode(sys.getfilesystemencoding())
                docsFolder = os.path.join(userprofile, "Documents")

    elif sys.platform == "darwin":
        docsFolder = os.path.expanduser(u"~/Documents/")
    else:
        docsFolder = os.path.expanduser(u"~/.mcedit")
    try:
        os.mkdir(docsFolder)
    except:
        pass

    return docsFolder


def platform_open(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)
            # os.system('start ' + path + '\'')
        elif sys.platform == "darwin":
            # os.startfile(path)
            os.system('open "' + path + '"')
        else:
            os.system('xdg-open "' + path + '"')

    except Exception, e:
        print "platform_open failed on {0}: {1}".format(sys.platform, e)

win32_window_size = True

ini = u"mcedit.ini"
parentDir = dirname(directories.dataDir)
docsFolder = documents_folder()
portableConfigFilePath = os.path.join(parentDir, ini)
portableSchematicsDir = os.path.join(parentDir, u"MCEdit-schematics")
fixedConfigFilePath = os.path.join(docsFolder, ini)
fixedSchematicsDir = os.path.join(docsFolder, u"MCEdit-schematics")

if sys.platform == "darwin":
    # parentDir is MCEdit.app/Contents/
    folderContainingAppPackage = dirname(dirname(parentDir))
    oldPath = fixedConfigFilePath
    fixedConfigFilePath = os.path.expanduser("~/Library/Preferences/mcedit.ini")

    if os.path.exists(oldPath):
        try:
            os.rename(oldPath, fixedConfigFilePath)
        except Exception, e:
            print repr(e)

    portableConfigFilePath = os.path.join(folderContainingAppPackage, ini)
    portableSchematicsDir = os.path.join(folderContainingAppPackage, u"MCEdit-schematics")


def goPortable():
    global configFilePath, schematicsDir, portable

    if os.path.exists(fixedSchematicsDir):
        move_displace(fixedSchematicsDir, portableSchematicsDir)
    if os.path.exists(fixedConfigFilePath):
        move_displace(fixedConfigFilePath, portableConfigFilePath)

    configFilePath = portableConfigFilePath
    schematicsDir = portableSchematicsDir
    portable = True


def move_displace(src, dst):
    dstFolder = os.path.basename(os.path.dirname(dst))
    if not os.path.exists(dst):

        print "Moving {0} to {1}".format(os.path.basename(src), dstFolder)
        shutil.move(src, dst)
    else:
        olddst = dst + ".old"
        i = 0
        while os.path.exists(olddst):
            olddst = dst + ".old" + str(i)
            i += 1

        print "{0} already found in {1}! Renamed it to {2}.".format(os.path.basename(src), dstFolder, dst)
        os.rename(dst, olddst)
        shutil.move(src, dst)


def goFixed():
    global configFilePath, schematicsDir, portable

    if os.path.exists(portableSchematicsDir):
        move_displace(portableSchematicsDir, fixedSchematicsDir)
    if os.path.exists(portableConfigFilePath):
        move_displace(portableConfigFilePath, fixedConfigFilePath)

    configFilePath = fixedConfigFilePath
    schematicsDir = fixedSchematicsDir
    portable = False


def portableConfigExists():
    return (os.path.exists(portableConfigFilePath)  # mcedit.ini in MCEdit folder
        or (sys.platform != 'darwin' and not os.path.exists(fixedConfigFilePath)))  # no mcedit.ini in Documents folder (except on OS X when we always want it in Library/Preferences

if portableConfigExists():
    print "Running in portable mode. MCEdit-schematics and mcedit.ini are stored alongside " + (sys.platform == "darwin" and "the MCEdit app bundle" or "MCEditData")
    portable = True
    schematicsDir = portableSchematicsDir
    configFilePath = portableConfigFilePath

else:
    print "Running in fixed install mode. MCEdit-schematics and mcedit.ini are in your Documents folder."
    configFilePath = fixedConfigFilePath
    schematicsDir = fixedSchematicsDir
    portable = False

filtersDir = os.path.join(directories.dataDir, "filters")
if filtersDir not in [s.decode(sys.getfilesystemencoding())
                      if isinstance(s, str)
                      else s
                      for s in sys.path]:

    sys.path.append(filtersDir.encode(sys.getfilesystemencoding()))

if portable:
    serverJarStorageDir = (os.path.join(parentDir, "ServerJarStorage"))
    ServerJarStorage.defaultCacheDir = serverJarStorageDir
    jarStorage = ServerJarStorage(serverJarStorageDir)
else:
    jarStorage = ServerJarStorage()


########NEW FILE########
__FILENAME__ = png
#!/usr/bin/env python

# $URL: http://pypng.googlecode.com/svn/trunk/code/png.py $
# $Rev: 201 $

# png.py - PNG encoder/decoder in pure Python
#
# Copyright (C) 2006 Johann C. Rocholl <johann@browsershots.org>
# Portions Copyright (C) 2009 David Jones <drj@pobox.com>
# And probably portions Copyright (C) 2006 Nicko van Someren <nicko@nicko.org>
#
# Original concept by Johann C. Rocholl.
#
# LICENSE (The MIT License)
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Changelog (recent first):
# 2009-03-11 David: interlaced bit depth < 8 (writing).
# 2009-03-10 David: interlaced bit depth < 8 (reading).
# 2009-03-04 David: Flat and Boxed pixel formats.
# 2009-02-26 David: Palette support (writing).
# 2009-02-23 David: Bit-depths < 8; better PNM support.
# 2006-06-17 Nicko: Reworked into a class, faster interlacing.
# 2006-06-17 Johann: Very simple prototype PNG decoder.
# 2006-06-17 Nicko: Test suite with various image generators.
# 2006-06-17 Nicko: Alpha-channel, grey-scale, 16-bit/plane support.
# 2006-06-15 Johann: Scanline iterator interface for large input files.
# 2006-06-09 Johann: Very simple prototype PNG encoder.

# Incorporated into Bangai-O Development Tools by drj on 2009-02-11 from
# http://trac.browsershots.org/browser/trunk/pypng/lib/png.py?rev=2885

# Incorporated into pypng by drj on 2009-03-12 from
# //depot/prj/bangaio/master/code/png.py#67

"""
Pure Python PNG Reader/Writer

This Python module implements support for PNG images (see PNG
specification at http://www.w3.org/TR/2003/REC-PNG-20031110/ ). It reads
and writes PNG files with all allowable bit depths (1/2/4/8/16/24/32/48/64
bits per pixel) and colour combinations: greyscale (1/2/4/8/16 bit); RGB,
RGBA, LA (greyscale with alpha) with 8/16 bits per channel; colour mapped
images (1/2/4/8 bit).  Adam7 interlacing is supported for reading and
writing.  A number of optional chunks can be specified (when writing)
and understood (when reading): ``tRNS``, ``bKGD``, ``gAMA``.

For help, type ``import png; help(png)`` in your python interpreter.

A good place to start is the :class:`Reader` and :class:`Writer` classes.

Requires Python 2.3.  Limited support is available for Python 2.2, but
not everything works.  Best with Python 2.4 and higher.  Installation is
trivial, but see the ``README.txt`` file (with the source distribution)
for details.

This file can also be used as a command-line utility to convert
`Netpbm <http://netpbm.sourceforge.net/>`_ PNM files to PNG, and the reverse conversion from PNG to
PNM. The interface is similar to that of the ``pnmtopng`` program from
Netpbm.  Type ``python png.py --help`` at the shell prompt
for usage and a list of options.

A note on spelling and terminology
----------------------------------

Generally British English spelling is used in the documentation.  So
that's "greyscale" and "colour".  This not only matches the author's
native language, it's also used by the PNG specification.

The major colour models supported by PNG (and hence by PyPNG) are:
greyscale, RGB, greyscale--alpha, RGB--alpha.  These are sometimes
referred to using the abbreviations: L, RGB, LA, RGBA.  In this case
each letter abbreviates a single channel: *L* is for Luminance or Luma or
Lightness which is the channel used in greyscale images; *R*, *G*, *B* stand
for Red, Green, Blue, the components of a colour image; *A* stands for
Alpha, the opacity channel (used for transparency effects, but higher
values are more opaque, so it makes sense to call it opacity).

A note on formats
-----------------

When getting pixel data out of this module (reading) and presenting
data to this module (writing) there are a number of ways the data could
be represented as a Python value.  Generally this module uses one of
three formats called "flat row flat pixel", "boxed row flat pixel", and
"boxed row boxed pixel".  Basically the concern is whether each pixel
and each row comes in its own little tuple (box), or not.

Consider an image that is 3 pixels wide by 2 pixels high, and each pixel
has RGB components:

Boxed row flat pixel::

  list([R,G,B, R,G,B, R,G,B],
       [R,G,B, R,G,B, R,G,B])

Each row appears as its own list, but the pixels are flattened so that
three values for one pixel simply follow the three values for the previous
pixel.  This is the most common format used, because it provides a good
compromise between space and convenience.  PyPNG regards itself as
at liberty to replace any sequence type with any sufficiently compatible
other sequence type; in practice each row is an array (from the array
module), and the outer list is sometimes an iterator rather than an
explicit list (so that streaming is possible).

Flat row flat pixel::

  [R,G,B, R,G,B, R,G,B,
   R,G,B, R,G,B, R,G,B]

The entire image is one single giant sequence of colour values.
Generally an array will be used (to save space), not a list.

Boxed row boxed pixel::

  list([ (R,G,B), (R,G,B), (R,G,B) ],
       [ (R,G,B), (R,G,B), (R,G,B) ])

Each row appears in its own list, but each pixel also appears in its own
tuple.  A serious memory burn in Python.

In all cases the top row comes first, and for each row the pixels are
ordered from left-to-right.  Within a pixel the values appear in the
order, R-G-B-A (or L-A for greyscale--alpha).

There is a fourth format, mentioned because it is used internally,
is close to what lies inside a PNG file itself, and has some support
from the public API.  This format is called packed.  When packed,
each row is a sequence of bytes (integers from 0 to 255), just as
it is before PNG scanline filtering is applied.  When the bit depth
is 8 this is essentially the same as boxed row flat pixel; when the
bit depth is less than 8, several pixels are packed into each byte;
when the bit depth is 16 (the only value more than 8 that is supported
by the PNG image format) each pixel value is decomposed into 2 bytes
(and `packed` is a misnomer).  This format is used by the
:meth:`Writer.write_packed` method.  It isn't usually a convenient
format, but may be just right if the source data for the PNG image
comes from something that uses a similar format (for example, 1-bit
BMPs, or another PNG file).

And now, my famous members
--------------------------
"""

# http://www.python.org/doc/2.2.3/whatsnew/node5.html
from __future__ import generators

__version__ = "$URL: http://pypng.googlecode.com/svn/trunk/code/png.py $ $Rev: 201 $"

from array import array
try:  # See :pyver:old
    import itertools
except:
    pass
import math
# http://www.python.org/doc/2.4.4/lib/module-operator.html
import operator
import struct
import sys
import zlib
# http://www.python.org/doc/2.4.4/lib/module-warnings.html
import warnings

__all__ = ['Reader', 'Writer', 'write_chunks']

# The PNG signature.
# http://www.w3.org/TR/PNG/#5PNG-file-signature
_signature = struct.pack('8B', 137, 80, 78, 71, 13, 10, 26, 10)

_adam7 = ((0, 0, 8, 8),
          (4, 0, 8, 8),
          (0, 4, 4, 8),
          (2, 0, 4, 4),
          (0, 2, 2, 4),
          (1, 0, 2, 2),
          (0, 1, 1, 2))


def group(s, n):
    # See
    # http://www.python.org/doc/2.6/library/functions.html#zip
    return zip(*[iter(s)] * n)


def isarray(x):
    """Same as ``isinstance(x, array)`` except on Python 2.2, where it
    always returns ``False``.  This helps PyPNG work on Python 2.2.
    """

    try:
        return isinstance(x, array)
    except:
        return False

try:  # see :pyver:old
    array.tostring
except:
    def tostring(row):
        l = len(row)
        return struct.pack('%dB' % l, *row)
else:
    def tostring(row):
        """Convert row of bytes to string.  Expects `row` to be an
        ``array``.
        """
        return row.tostring()


def interleave_planes(ipixels, apixels, ipsize, apsize):
    """
    Interleave (colour) planes, e.g. RGB + A = RGBA.

    Return an array of pixels consisting of the `ipsize` elements of data
    from each pixel in `ipixels` followed by the `apsize` elements of data
    from each pixel in `apixels`.  Conventionally `ipixels` and
    `apixels` are byte arrays so the sizes are bytes, but it actually
    works with any arrays of the same type.  The returned array is the
    same type as the input arrays which should be the same type as each other.
    """

    itotal = len(ipixels)
    atotal = len(apixels)
    newtotal = itotal + atotal
    newpsize = ipsize + apsize
    # Set up the output buffer
    # See http://www.python.org/doc/2.4.4/lib/module-array.html#l2h-1356
    out = array(ipixels.typecode)
    # It's annoying that there is no cheap way to set the array size :-(
    out.extend(ipixels)
    out.extend(apixels)
    # Interleave in the pixel data
    for i in range(ipsize):
        out[i:newtotal:newpsize] = ipixels[i:itotal:ipsize]
    for i in range(apsize):
        out[i + ipsize:newtotal:newpsize] = apixels[i:atotal:apsize]
    return out


def check_palette(palette):
    """Check a palette argument (to the :class:`Writer` class) for validity.
    Returns the palette as a list if okay; raises an exception otherwise.
    """

    # None is the default and is allowed.
    if palette is None:
        return None

    p = list(palette)
    if not (0 < len(p) <= 256):
        raise ValueError("a palette must have between 1 and 256 entries")
    seen_triple = False
    for i, t in enumerate(p):
        if len(t) not in (3, 4):
            raise ValueError(
              "palette entry %d: entries must be 3- or 4-tuples." % i)
        if len(t) == 3:
            seen_triple = True
        if seen_triple and len(t) == 4:
            raise ValueError(
              "palette entry %d: all 4-tuples must precede all 3-tuples" % i)
        for x in t:
            if int(x) != x or not(0 <= x <= 255):
                raise ValueError(
                  "palette entry %d: values must be integer: 0 <= x <= 255" % i)
    return p


class Error(Exception):
    prefix = 'Error'

    def __str__(self):
        return self.prefix + ': ' + ' '.join(self.args)


class FormatError(Error):
    """Problem with input file format.  In other words, PNG file does
    not conform to the specification in some way and is invalid.
    """

    prefix = 'FormatError'


class ChunkError(FormatError):
    prefix = 'ChunkError'


class Writer:
    """
    PNG encoder in pure Python.
    """

    def __init__(self, width=None, height=None,
                 size=None,
                 greyscale=False,
                 alpha=False,
                 bitdepth=8,
                 palette=None,
                 transparent=None,
                 background=None,
                 gamma=None,
                 compression=None,
                 interlace=False,
                 bytes_per_sample=None,  # deprecated
                 planes=None,
                 colormap=None,
                 maxval=None,
                 chunk_limit=2 ** 20):
        """
        Create a PNG encoder object.

        Arguments:

        width, height
          Image size in pixels, as two separate arguments.
        size
          Image size (w,h) in pixels, as single argument.
        greyscale
          Input data is greyscale, not RGB.
        alpha
          Input data has alpha channel (RGBA or LA).
        bitdepth
          Bit depth: from 1 to 16.
        palette
          Create a palette for a colour mapped image (colour type 3).
        transparent
          Specify a transparent colour (create a ``tRNS`` chunk).
        background
          Specify a default background colour (create a ``bKGD`` chunk).
        gamma
          Specify a gamma value (create a ``gAMA`` chunk).
        compression
          zlib compression level (1-9).
        interlace
          Create an interlaced image.
        chunk_limit
          Write multiple ``IDAT`` chunks to save memory.

        The image size (in pixels) can be specified either by using the
        `width` and `height` arguments, or with the single `size`
        argument.  If `size` is used it should be a pair (*width*,
        *height*).

        `greyscale` and `alpha` are booleans that specify whether
        an image is greyscale (or colour), and whether it has an
        alpha channel (or not).

        `bitdepth` specifies the bit depth of the source pixel values.
        Each source pixel values must be an integer between 0 and
        ``2**bitdepth-1``.  For example, 8-bit images have values
        between 0 and 255.  PNG only stores images with bit depths of
        1,2,4,8, or 16.  When `bitdepth` is not one of these values,
        the next highest valid bit depth is selected, and an ``sBIT``
        (significant bits) chunk is generated that specifies the original
        precision of the source image.  In this case the supplied pixel
        values will be rescaled to fit the range of the selected bit depth.

        The details of which bit depth / colour model combinations the
        PNG file format supports directly, are allowed are somewhat arcane
        (refer to the PNG specification for full details).  Briefly:
        "small" bit depths (1,2,4) are only allowed with greyscale and
        colour mapped images; colour mapped images cannot have bit depth
        16.

        For colour mapped images (in other words, when the `palette`
        argument is specified) the `bitdepth` argument must match one of
        the valid PNG bit depths: 1, 2, 4, or 8.  (It is valid to have a
        PNG image with a palette and an ``sBIT`` chunk, but the meaning
        is slightly different; it would be awkward to press the
        `bitdepth` argument into service for this.)

        The `palette` option, when specified, causes a colour mapped image
    to be created: the PNG colour type is set to 3; greyscale
    must not be set; alpha must not be set; transparent must
    not be set; the bit depth must be 1,2,4, or 8.  When a colour
        mapped image is created, the pixel values are palette indexes
        and the `bitdepth` argument specifies the size of these indexes
        (not the size of the colour values in the palette).

        The palette argument value should be a sequence of 3- or
        4-tuples.  3-tuples specify RGB palette entries; 4-tuples
        specify RGBA palette entries.  If both 4-tuples and 3-tuples
        appear in the sequence then all the 4-tuples must come
        before all the 3-tuples.  A ``PLTE`` chunk is created; if there
        are 4-tuples then a ``tRNS`` chunk is created as well.  The
        ``PLTE`` chunk will contain all the RGB triples in the same
        sequence; the ``tRNS`` chunk will contain the alpha channel for
        all the 4-tuples, in the same sequence.  Palette entries
        are always 8-bit.

        If specified, the `transparent` and `background` parameters must
        be a tuple with three integer values for red, green, blue, or
        a simple integer (or singleton tuple) for a greyscale image.

        If specified, the `gamma` parameter must be a positive number
        (generally, a float).  A ``gAMA`` chunk will be created.  Note that
        this will not change the values of the pixels as they appear in
        the PNG file, they are assumed to have already been converted
        appropriately for the gamma specified.

    The `compression` argument specifies the compression level
    to be used by the ``zlib`` module.  Higher values are likely
    to compress better, but will be slower to compress.  The
    default for this argument is ``None``; this does not mean
    no compression, rather it means that the default from the
    ``zlib`` module is used (which is generally acceptable).

        If `interlace` is true then an interlaced image is created
        (using PNG's so far only interace method, *Adam7*).  This does not
        affect how the pixels should be presented to the encoder, rather
        it changes how they are arranged into the PNG file.  On slow
        connexions interlaced images can be partially decoded by the
        browser to give a rough view of the image that is successively
        refined as more image data appears.

        .. note ::

          Enabling the `interlace` option requires the entire image
          to be processed in working memory.

        `chunk_limit` is used to limit the amount of memory used whilst
        compressing the image.  In order to avoid using large amounts of
        memory, multiple ``IDAT`` chunks may be created.
        """

        # At the moment the `planes` argument is ignored;
        # its purpose is to act as a dummy so that
        # ``Writer(x, y, **info)`` works, where `info` is a dictionary
        # returned by Reader.read and friends.
        # Ditto for `colormap`.

        # A couple of helper functions come first.  Best skipped if you
        # are reading through.

        def isinteger(x):
            try:
                return int(x) == x
            except:
                return False

        def check_color(c, which):
            """Checks that a colour argument for transparent or
            background options is the right form.  Also "corrects" bare
            integers to 1-tuples.
            """

            if c is None:
                return c
            if greyscale:
                try:
                    l = len(c)
                except TypeError:
                    c = (c,)
                if len(c) != 1:
                    raise ValueError("%s for greyscale must be 1-tuple" %
                        which)
                if not isinteger(c[0]):
                    raise ValueError(
                        "%s colour for greyscale must be integer" %
                        which)
            else:
                if not (len(c) == 3 and
                        isinteger(c[0]) and
                        isinteger(c[1]) and
                        isinteger(c[2])):
                    raise ValueError(
                        "%s colour must be a triple of integers" %
                        which)
            return c

        if size:
            if len(size) != 2:
                raise ValueError(
                  "size argument should be a pair (width, height)")
            if width is not None and width != size[0]:
                raise ValueError(
                  "size[0] (%r) and width (%r) should match when both are used."
                    % (size[0], width))
            if height is not None and height != size[1]:
                raise ValueError(
                  "size[1] (%r) and height (%r) should match when both are used."
                    % (size[1], height))
            width, height = size
        del size

        if width <= 0 or height <= 0:
            raise ValueError("width and height must be greater than zero")
        if not isinteger(width) or not isinteger(height):
            raise ValueError("width and height must be integers")
        # http://www.w3.org/TR/PNG/#7Integers-and-byte-order
        if width > 2 ** 32 - 1 or height > 2 ** 32 - 1:
            raise ValueError("width and height cannot exceed 2**32-1")

        if alpha and transparent is not None:
            raise ValueError(
                "transparent colour not allowed with alpha channel")

        if bytes_per_sample is not None:
            warnings.warn('please use bitdepth instead of bytes_per_sample',
                          DeprecationWarning)
            if bytes_per_sample not in (0.125, 0.25, 0.5, 1, 2):
                raise ValueError(
                    "bytes per sample must be .125, .25, .5, 1, or 2")
            bitdepth = int(8 * bytes_per_sample)
        del bytes_per_sample
        if not isinteger(bitdepth) or bitdepth < 1 or 16 < bitdepth:
            raise ValueError("bitdepth (%r) must be a postive integer <= 16" %
              bitdepth)

        self.rescale = None
        if palette:
            if bitdepth not in (1, 2, 4, 8):
                raise ValueError("with palette, bitdepth must be 1, 2, 4, or 8")
            if transparent is not None:
                raise ValueError("transparent and palette not compatible")
            if alpha:
                raise ValueError("alpha and palette not compatible")
            if greyscale:
                raise ValueError("greyscale and palette not compatible")
        else:
            # No palette, check for sBIT chunk generation.
            if alpha or not greyscale:
                if bitdepth not in (8, 16):
                    targetbitdepth = (8, 16)[bitdepth > 8]
                    self.rescale = (bitdepth, targetbitdepth)
                    bitdepth = targetbitdepth
                    del targetbitdepth
            else:
                assert greyscale
                assert not alpha
                if bitdepth not in (1, 2, 4, 8, 16):
                    if bitdepth > 8:
                        targetbitdepth = 16
                    elif bitdepth == 3:
                        targetbitdepth = 4
                    else:
                        assert bitdepth in (5, 6, 7)
                        targetbitdepth = 8
                    self.rescale = (bitdepth, targetbitdepth)
                    bitdepth = targetbitdepth
                    del targetbitdepth

        if bitdepth < 8 and (alpha or not greyscale and not palette):
            raise ValueError(
              "bitdepth < 8 only permitted with greyscale or palette")
        if bitdepth > 8 and palette:
            raise ValueError(
                "bit depth must be 8 or less for images with palette")

        transparent = check_color(transparent, 'transparent')
        background = check_color(background, 'background')

        # It's important that the true boolean values (greyscale, alpha,
        # colormap, interlace) are converted to bool because Iverson's
        # convention is relied upon later on.
        self.width = width
        self.height = height
        self.transparent = transparent
        self.background = background
        self.gamma = gamma
        self.greyscale = bool(greyscale)
        self.alpha = bool(alpha)
        self.colormap = bool(palette)
        self.bitdepth = int(bitdepth)
        self.compression = compression
        self.chunk_limit = chunk_limit
        self.interlace = bool(interlace)
        self.palette = check_palette(palette)

        self.color_type = 4 * self.alpha + 2 * (not greyscale) + 1 * self.colormap
        assert self.color_type in (0, 2, 3, 4, 6)

        self.color_planes = (3, 1)[self.greyscale or self.colormap]
        self.planes = self.color_planes + self.alpha
        # :todo: fix for bitdepth < 8
        self.psize = (self.bitdepth / 8) * self.planes

    def make_palette(self):
        """Create the byte sequences for a ``PLTE`` and if necessary a
        ``tRNS`` chunk.  Returned as a pair (*p*, *t*).  *t* will be
        ``None`` if no ``tRNS`` chunk is necessary.
        """

        p = array('B')
        t = array('B')

        for x in self.palette:
            p.extend(x[0:3])
            if len(x) > 3:
                t.append(x[3])
        p = tostring(p)
        t = tostring(t)
        if t:
            return p, t
        return p, None

    def write(self, outfile, rows):
        """Write a PNG image to the output file.  `rows` should be
        an iterable that yields each row in boxed row flat pixel format.
        The rows should be the rows of the original image, so there
        should be ``self.height`` rows of ``self.width * self.planes`` values.
        If `interlace` is specified (when creating the instance), then
        an interlaced PNG file will be written.  Supply the rows in the
        normal image order; the interlacing is carried out internally.

        .. note ::

          Interlacing will require the entire image to be in working memory.
        """

        if self.interlace:
            fmt = 'BH'[self.bitdepth > 8]
            a = array(fmt, itertools.chain(*rows))
            return self.write_array(outfile, a)
        else:
            nrows = self.write_passes(outfile, rows)
            if nrows != self.height:
                raise ValueError(
                  "rows supplied (%d) does not match height (%d)" %
                  (nrows, self.height))

    def write_passes(self, outfile, rows, packed=False):
        """
        Write a PNG image to the output file.

    Most users are expected to find the :meth:`write` or
    :meth:`write_array` method more convenient.

    The rows should be given to this method in the order that
    they appear in the output file.  For straightlaced images,
    this is the usual top to bottom ordering, but for interlaced
    images the rows should have already been interlaced before
    passing them to this function.

    `rows` should be an iterable that yields each row.  When
        `packed` is ``False`` the rows should be in boxed row flat pixel
        format; when `packed` is ``True`` each row should be a packed
        sequence of bytes.

        """

        # http://www.w3.org/TR/PNG/#5PNG-file-signature
        outfile.write(_signature)

        # http://www.w3.org/TR/PNG/#11IHDR
        write_chunk(outfile, 'IHDR',
                    struct.pack("!2I5B", self.width, self.height,
                                self.bitdepth, self.color_type,
                                0, 0, self.interlace))

        # See :chunk:order
        # http://www.w3.org/TR/PNG/#11gAMA
        if self.gamma is not None:
            write_chunk(outfile, 'gAMA',
                        struct.pack("!L", int(round(self.gamma * 1e5))))

        # See :chunk:order
        # http://www.w3.org/TR/PNG/#11sBIT
        if self.rescale:
            write_chunk(outfile, 'sBIT',
                struct.pack('%dB' % self.planes,
                            *[self.rescale[0]] * self.planes))

        # :chunk:order: Without a palette (PLTE chunk), ordering is
        # relatively relaxed.  With one, gAMA chunk must precede PLTE
        # chunk which must precede tRNS and bKGD.
        # See http://www.w3.org/TR/PNG/#5ChunkOrdering
        if self.palette:
            p, t = self.make_palette()
            write_chunk(outfile, 'PLTE', p)
            if t:
                # tRNS chunk is optional.  Only needed if palette entries
                # have alpha.
                write_chunk(outfile, 'tRNS', t)

        # http://www.w3.org/TR/PNG/#11tRNS
        if self.transparent is not None:
            if self.greyscale:
                write_chunk(outfile, 'tRNS',
                            struct.pack("!1H", *self.transparent))
            else:
                write_chunk(outfile, 'tRNS',
                            struct.pack("!3H", *self.transparent))

        # http://www.w3.org/TR/PNG/#11bKGD
        if self.background is not None:
            if self.greyscale:
                write_chunk(outfile, 'bKGD',
                            struct.pack("!1H", *self.background))
            else:
                write_chunk(outfile, 'bKGD',
                            struct.pack("!3H", *self.background))

        # http://www.w3.org/TR/PNG/#11IDAT
        if self.compression is not None:
            compressor = zlib.compressobj(self.compression)
        else:
            compressor = zlib.compressobj()

        # Choose an extend function based on the bitdepth.  The extend
        # function packs/decomposes the pixel values into bytes and
        # stuffs them onto the data array.
        data = array('B')
        if self.bitdepth == 8 or packed:
            extend = data.extend
        elif self.bitdepth == 16:
            # Decompose into bytes
            def extend(sl):
                fmt = '!%dH' % len(sl)
                data.extend(array('B', struct.pack(fmt, *sl)))
        else:
            # Pack into bytes
            assert self.bitdepth < 8
            # samples per byte
            spb = int(8 / self.bitdepth)

            def extend(sl):
                a = array('B', sl)
                # Adding padding bytes so we can group into a whole
                # number of spb-tuples.
                l = float(len(a))
                extra = math.ceil(l / float(spb)) * spb - l
                a.extend([0] * int(extra))
                # Pack into bytes
                l = group(a, spb)
                l = map(lambda e: reduce(lambda x, y:
                                           (x << self.bitdepth) + y, e), l)
                data.extend(l)
        if self.rescale:
            oldextend = extend
            factor = \
              float(2 ** self.rescale[1] - 1) / float(2 ** self.rescale[0] - 1)

            def extend(sl):
                oldextend(map(lambda x: int(round(factor * x)), sl))

        # Build the first row, testing mostly to see if we need to
        # changed the extend function to cope with NumPy integer types
        # (they cause our ordinary definition of extend to fail, so we
        # wrap it).  See
        # http://code.google.com/p/pypng/issues/detail?id=44
        enumrows = enumerate(rows)
        del rows

        # First row's filter type.
        data.append(0)
        # :todo: Certain exceptions in the call to ``.next()`` or the
        # following try would indicate no row data supplied.
        # Should catch.
        i, row = enumrows.next()
        try:
            # If this fails...
            extend(row)
        except:
            # ... try a version that converts the values to int first.
            # Not only does this work for the (slightly broken) NumPy
            # types, there are probably lots of other, unknown, "nearly"
            # int types it works for.
            def wrapmapint(f):
                return lambda sl: f(map(int, sl))
            extend = wrapmapint(extend)
            del wrapmapint
            extend(row)

        for i, row in enumrows:
            # Add "None" filter type.  Currently, it's essential that
            # this filter type be used for every scanline as we do not
            # mark the first row of a reduced pass image; that means we
            # could accidentally compute the wrong filtered scanline if
            # we used "up", "average", or "paeth" on such a line.
            data.append(0)
            extend(row)
            if len(data) > self.chunk_limit:
                compressed = compressor.compress(tostring(data))
                if len(compressed):
                    # print >> sys.stderr, len(data), len(compressed)
                    write_chunk(outfile, 'IDAT', compressed)
                # Because of our very witty definition of ``extend``,
                # above, we must re-use the same ``data`` object.  Hence
                # we use ``del`` to empty this one, rather than create a
                # fresh one (which would be my natural FP instinct).
                del data[:]
        if len(data):
            compressed = compressor.compress(tostring(data))
        else:
            compressed = ''
        flushed = compressor.flush()
        if len(compressed) or len(flushed):
            # print >> sys.stderr, len(data), len(compressed), len(flushed)
            write_chunk(outfile, 'IDAT', compressed + flushed)
        # http://www.w3.org/TR/PNG/#11IEND
        write_chunk(outfile, 'IEND')
        return i + 1

    def write_array(self, outfile, pixels):
        """
        Write an array in flat row flat pixel format as a PNG file on
        the output file.  See also :meth:`write` method.
        """

        if self.interlace:
            self.write_passes(outfile, self.array_scanlines_interlace(pixels))
        else:
            self.write_passes(outfile, self.array_scanlines(pixels))

    def write_packed(self, outfile, rows):
        """
        Write PNG file to `outfile`.  The pixel data comes from `rows`
        which should be in boxed row packed format.  Each row should be
        a sequence of packed bytes.

        Technically, this method does work for interlaced images but it
        is best avoided.  For interlaced images, the rows should be
        presented in the order that they appear in the file.

        This method should not be used when the source image bit depth
        is not one naturally supported by PNG; the bit depth should be
        1, 2, 4, 8, or 16.
        """

        if self.rescale:
            raise Error("write_packed method not suitable for bit depth %d" %
              self.rescale[0])
        return self.write_passes(outfile, rows, packed=True)

    def convert_pnm(self, infile, outfile):
        """
        Convert a PNM file containing raw pixel data into a PNG file
        with the parameters set in the writer object.  Works for
        (binary) PGM, PPM, and PAM formats.
        """

        if self.interlace:
            pixels = array('B')
            pixels.fromfile(infile,
                            (self.bitdepth / 8) * self.color_planes *
                            self.width * self.height)
            self.write_passes(outfile, self.array_scanlines_interlace(pixels))
        else:
            self.write_passes(outfile, self.file_scanlines(infile))

    def convert_ppm_and_pgm(self, ppmfile, pgmfile, outfile):
        """
        Convert a PPM and PGM file containing raw pixel data into a
        PNG outfile with the parameters set in the writer object.
        """
        pixels = array('B')
        pixels.fromfile(ppmfile,
                        (self.bitdepth / 8) * self.color_planes *
                        self.width * self.height)
        apixels = array('B')
        apixels.fromfile(pgmfile,
                         (self.bitdepth / 8) *
                         self.width * self.height)
        pixels = interleave_planes(pixels, apixels,
                                   (self.bitdepth / 8) * self.color_planes,
                                   (self.bitdepth / 8))
        if self.interlace:
            self.write_passes(outfile, self.array_scanlines_interlace(pixels))
        else:
            self.write_passes(outfile, self.array_scanlines(pixels))

    def file_scanlines(self, infile):
        """
        Generates boxed rows in flat pixel format, from the input file
        `infile`.  It assumes that the input file is in a "Netpbm-like"
        binary format, and is positioned at the beginning of the first
        pixel.  The number of pixels to read is taken from the image
        dimensions (`width`, `height`, `planes`) and the number of bytes
        per value is implied by the image `bitdepth`.
        """

        # Values per row
        vpr = self.width * self.planes
        row_bytes = vpr
        if self.bitdepth > 8:
            assert self.bitdepth == 16
            row_bytes *= 2
            fmt = '>%dH' % vpr

            def line():
                return array('H', struct.unpack(fmt, infile.read(row_bytes)))
        else:
            def line():
                scanline = array('B', infile.read(row_bytes))
                return scanline
        for y in range(self.height):
            yield line()

    def array_scanlines(self, pixels):
        """
        Generates boxed rows (flat pixels) from flat rows (flat pixels)
        in an array.
        """

        # Values per row
        vpr = self.width * self.planes
        stop = 0
        for y in range(self.height):
            start = stop
            stop = start + vpr
            yield pixels[start:stop]

    def array_scanlines_interlace(self, pixels):
        """
        Generator for interlaced scanlines from an array.  `pixels` is
        the full source image in flat row flat pixel format.  The
        generator yields each scanline of the reduced passes in turn, in
        boxed row flat pixel format.
        """

        # http://www.w3.org/TR/PNG/#8InterlaceMethods
        # Array type.
        fmt = 'BH'[self.bitdepth > 8]
        # Value per row
        vpr = self.width * self.planes
        for xstart, ystart, xstep, ystep in _adam7:
            if xstart >= self.width:
                continue
            # Pixels per row (of reduced image)
            ppr = int(math.ceil((self.width - xstart) / float(xstep)))
            # number of values in reduced image row.
            row_len = ppr * self.planes
            for y in range(ystart, self.height, ystep):
                if xstep == 1:
                    offset = y * vpr
                    yield pixels[offset:offset + vpr]
                else:
                    row = array(fmt)
                    # There's no easier way to set the length of an array
                    row.extend(pixels[0:row_len])
                    offset = y * vpr + xstart * self.planes
                    end_offset = (y + 1) * vpr
                    skip = self.planes * xstep
                    for i in range(self.planes):
                        row[i::self.planes] = \
                            pixels[offset + i:end_offset:skip]
                    yield row


def write_chunk(outfile, tag, data=''):
    """
    Write a PNG chunk to the output file, including length and
    checksum.
    """

    # http://www.w3.org/TR/PNG/#5Chunk-layout
    outfile.write(struct.pack("!I", len(data)))
    outfile.write(tag)
    outfile.write(data)
    checksum = zlib.crc32(tag)
    checksum = zlib.crc32(data, checksum)
    outfile.write(struct.pack("!i", checksum))


def write_chunks(out, chunks):
    """Create a PNG file by writing out the chunks."""

    out.write(_signature)
    for chunk in chunks:
        write_chunk(out, *chunk)


def filter_scanline(type, line, fo, prev=None):
    """Apply a scanline filter to a scanline.  `type` specifies the
    filter type (0 to 4); `line` specifies the current (unfiltered)
    scanline as a sequence of bytes; `prev` specifies the previous
    (unfiltered) scanline as a sequence of bytes. `fo` specifies the
    filter offset; normally this is size of a pixel in bytes (the number
    of bytes per sample times the number of channels), but when this is
    < 1 (for bit depths < 8) then the filter offset is 1.
    """

    assert 0 <= type < 5

    # The output array.  Which, pathetically, we extend one-byte at a
    # time (fortunately this is linear).
    out = array('B', [type])

    def sub():
        ai = -fo
        for x in line:
            if ai >= 0:
                x = (x - line[ai]) & 0xff
            out.append(x)
            ai += 1

    def up():
        for i, x in enumerate(line):
            x = (x - prev[i]) & 0xff
            out.append(x)

    def average():
        ai = -fo
        for i, x in enumerate(line):
            if ai >= 0:
                x = (x - ((line[ai] + prev[i]) >> 1)) & 0xff
            else:
                x = (x - (prev[i] >> 1)) & 0xff
            out.append(x)
            ai += 1

    def paeth():
        # http://www.w3.org/TR/PNG/#9Filter-type-4-Paeth
        ai = -fo  # also used for ci
        for i, x in enumerate(line):
            a = 0
            b = prev[i]
            c = 0

            if ai >= 0:
                a = line[ai]
                c = prev[ai]
            p = a + b - c
            pa = abs(p - a)
            pb = abs(p - b)
            pc = abs(p - c)
            if pa <= pb and pa <= pc:
                Pr = a
            elif pb <= pc:
                Pr = b
            else:
                Pr = c

            x = (x - Pr) & 0xff
            out.append(x)
            ai += 1

    if not prev:
        # We're on the first line.  Some of the filters can be reduced
        # to simpler cases which makes handling the line "off the top"
        # of the image simpler.  "up" becomes "none"; "paeth" becomes
        # "left" (non-trivial, but true). "average" needs to be handled
        # specially.
        if type == 2:  # "up"
            return line  # type = 0
        elif type == 3:
            prev = [0] * len(line)
        elif type == 4:  # "paeth"
            type = 1
    if type == 0:
        out.extend(line)
    elif type == 1:
        sub()
    elif type == 2:
        up()
    elif type == 3:
        average()
    else:  # type == 4
        paeth()
    return out


class _readable:
    """
    A simple file-like interface for strings and arrays.
    """

    def __init__(self, buf):
        self.buf = buf
        self.offset = 0

    def read(self, n):
        r = self.buf[self.offset:self.offset + n]
        if isarray(r):
            r = r.tostring()
        self.offset += n
        return r


class Reader:
    """
    PNG decoder in pure Python.
    """

    def __init__(self, _guess=None, **kw):
        """
        Create a PNG decoder object.

        The constructor expects exactly one keyword argument. If you
        supply a positional argument instead, it will guess the input
        type. You can choose among the following keyword arguments:

        filename
          Name of input file (a PNG file).
        file
          A file-like object (object with a read() method).
        bytes
          ``array`` or ``string`` with PNG data.

        """
        if ((_guess is not None and len(kw) != 0) or
            (_guess is None and len(kw) != 1)):
            raise TypeError("Reader() takes exactly 1 argument")

        # Will be the first 8 bytes, later on.  See validate_signature.
        self.signature = None
        self.transparent = None
        # A pair of (len,type) if a chunk has been read but its data and
        # checksum have not (in other words the file position is just
        # past the 4 bytes that specify the chunk type).  See preamble
        # method for how this is used.
        self.atchunk = None

        if _guess is not None:
            if isarray(_guess):
                kw["bytes"] = _guess
            elif isinstance(_guess, (str, unicode)):
                kw["filename"] = _guess
            elif hasattr(_guess, "read"):
                kw["file"] = _guess

        if "filename" in kw:
            self.file = file(kw["filename"], "rb")
        elif "file" in kw:
            self.file = kw["file"]
        elif "bytes" in kw:
            self.file = _readable(kw["bytes"])
        else:
            raise TypeError("expecting filename, file or bytes array")

    def chunk(self, seek=None):
        """
        Read the next PNG chunk from the input file; returns type (as a 4
        character string) and data.  If the optional `seek` argument is
        specified then it will keep reading chunks until it either runs
        out of file or finds the type specified by the argument.  Note
        that in general the order of chunks in PNGs is unspecified, so
        using `seek` can cause you to miss chunks.
        """

        self.validate_signature()

        while True:
            # http://www.w3.org/TR/PNG/#5Chunk-layout
            if not self.atchunk:
                self.atchunk = self.chunklentype()
            length, type = self.atchunk
            self.atchunk = None
            data = self.file.read(length)
            if len(data) != length:
                raise ChunkError('Chunk %s too short for required %i octets.'
                  % (type, length))
            checksum = self.file.read(4)
            if len(checksum) != 4:
                raise ValueError('Chunk %s too short for checksum.', type)
            if seek and type != seek:
                continue
            verify = zlib.crc32(type)
            verify = zlib.crc32(data, verify)
            # Whether the output from zlib.crc32 is signed or not varies
            # according to hideous implementation details, see
            # http://bugs.python.org/issue1202 .
            # We coerce it to be positive here (in a way which works on
            # Python 2.3 and older).
            verify &= 2 ** 32 - 1
            verify = struct.pack('!I', verify)
            if checksum != verify:
                # print repr(checksum)
                (a,) = struct.unpack('!I', checksum)
                (b,) = struct.unpack('!I', verify)
                raise ChunkError(
                  "Checksum error in %s chunk: 0x%08X != 0x%08X." %
                  (type, a, b))
            return type, data

    def chunks(self):
        """Return an iterator that will yield each chunk as a
        (*chunktype*, *content*) pair.
        """

        while True:
            t, v = self.chunk()
            yield t, v
            if t == 'IEND':
                break

    def undo_filter(self, filter_type, scanline, previous):
        """Undo the filter for a scanline.  `scanline` is a sequence of
        bytes that does not include the initial filter type byte.
        `previous` is decoded previous scanline (for straightlaced
        images this is the previous pixel row, but for interlaced
        images, it is the previous scanline in the reduced image, which
        in general is not the previous pixel row in the final image).
        When there is no previous scanline (the first row of a
        straightlaced image, or the first row in one of the passes in an
        interlaced image), then this argument should be ``None``.

        The scanline will have the effects of filtering removed, and the
        result will be returned as a fresh sequence of bytes.
        """

        # :todo: Would it be better to update scanline in place?

        # Create the result byte array.  It seems that the best way to
        # create the array to be the right size is to copy from an
        # existing sequence.  *sigh*
        # If we fill the result with scanline, then this allows a
        # micro-optimisation in the "null" and "sub" cases.
        result = array('B', scanline)

        if filter_type == 0:
            # And here, we _rely_ on filling the result with scanline,
            # above.
            return result

        if filter_type not in (1, 2, 3, 4):
            raise FormatError('Invalid PNG Filter Type.'
              '  See http://www.w3.org/TR/2003/REC-PNG-20031110/#9Filters .')

        # Filter unit.  The stride from one pixel to the corresponding
        # byte from the previous previous.  Normally this is the pixel
        # size in bytes, but when this is smaller than 1, the previous
        # byte is used instead.
        fu = max(1, self.psize)

        # For the first line of a pass, synthesize a dummy previous
        # line.  An alternative approach would be to observe that on the
        # first line 'up' is the same as 'null', 'paeth' is the same
        # as 'sub', with only 'average' requiring any special case.
        if not previous:
            previous = array('B', [0] * len(scanline))

        def sub():
            """Undo sub filter."""

            ai = 0
            # Loops starts at index fu.  Observe that the initial part
            # of the result is already filled in correctly with
            # scanline.
            for i in range(fu, len(result)):
                x = scanline[i]
                a = result[ai]
                result[i] = (x + a) & 0xff
                ai += 1

        def up():
            """Undo up filter."""

            for i in range(len(result)):
                x = scanline[i]
                b = previous[i]
                result[i] = (x + b) & 0xff

        def average():
            """Undo average filter."""

            ai = -fu
            for i in range(len(result)):
                x = scanline[i]
                if ai < 0:
                    a = 0
                else:
                    a = result[ai]
                b = previous[i]
                result[i] = (x + ((a + b) >> 1)) & 0xff
                ai += 1

        def paeth():
            """Undo Paeth filter."""

            # Also used for ci.
            ai = -fu
            for i in range(len(result)):
                x = scanline[i]
                if ai < 0:
                    a = c = 0
                else:
                    a = result[ai]
                    c = previous[ai]
                b = previous[i]
                p = a + b - c
                pa = abs(p - a)
                pb = abs(p - b)
                pc = abs(p - c)
                if pa <= pb and pa <= pc:
                    pr = a
                elif pb <= pc:
                    pr = b
                else:
                    pr = c
                result[i] = (x + pr) & 0xff
                ai += 1

        # Call appropriate filter algorithm.  Note that 0 has already
        # been dealt with.
        (None, sub, up, average, paeth)[filter_type]()
        return result

    def deinterlace(self, raw):
        """
        Read raw pixel data, undo filters, deinterlace, and flatten.
        Return in flat row flat pixel format.
        """

        # print >> sys.stderr, ("Reading interlaced, w=%s, r=%s, planes=%s," +
        #     " bpp=%s") % (self.width, self.height, self.planes, self.bps)
        # Values per row (of the target image)
        vpr = self.width * self.planes

        # Make a result array, and make it big enough.  Interleaving
        # writes to the output array randomly (well, not quite), so the
        # entire output array must be in memory.
        fmt = 'BH'[self.bitdepth > 8]
        a = array(fmt, [0] * vpr * self.height)
        source_offset = 0

        for xstart, ystart, xstep, ystep in _adam7:
            # print >> sys.stderr, "Adam7: start=%s,%s step=%s,%s" % (
            #     xstart, ystart, xstep, ystep)
            if xstart >= self.width:
                continue
            # The previous (reconstructed) scanline.  None at the
            # beginning of a pass to indicate that there is no previous
            # line.
            recon = None
            # Pixels per row (reduced pass image)
            ppr = int(math.ceil((self.width - xstart) / float(xstep)))
            # Row size in bytes for this pass.
            row_size = int(math.ceil(self.psize * ppr))
            for y in range(ystart, self.height, ystep):
                filter_type = raw[source_offset]
                source_offset += 1
                scanline = raw[source_offset:source_offset + row_size]
                source_offset += row_size
                recon = self.undo_filter(filter_type, scanline, recon)
                # Convert so that there is one element per pixel value
                flat = self.serialtoflat(recon, ppr)
                if xstep == 1:
                    assert xstart == 0
                    offset = y * vpr
                    a[offset:offset + vpr] = flat
                else:
                    offset = y * vpr + xstart * self.planes
                    end_offset = (y + 1) * vpr
                    skip = self.planes * xstep
                    for i in range(self.planes):
                        a[offset + i:end_offset:skip] = \
                            flat[i::self.planes]
        return a

    def iterboxed(self, rows):
        """Iterator that yields each scanline in boxed row flat pixel
        format.  `rows` should be an iterator that yields the bytes of
        each row in turn.
        """

        def asvalues(raw):
            """Convert a row of raw bytes into a flat row.  Result may
            or may not share with argument"""

            if self.bitdepth == 8:
                return raw
            if self.bitdepth == 16:
                raw = tostring(raw)
                return array('H', struct.unpack('!%dH' % (len(raw) // 2), raw))
            assert self.bitdepth < 8
            width = self.width
            # Samples per byte
            spb = 8 // self.bitdepth
            out = array('B')
            mask = 2 ** self.bitdepth - 1
            shifts = map(self.bitdepth.__mul__, reversed(range(spb)))
            for o in raw:
                out.extend(map(lambda i: mask & (o >> i), shifts))
            return out[:width]

        return itertools.imap(asvalues, rows)

    def serialtoflat(self, bytes, width=None):
        """Convert serial format (byte stream) pixel data to flat row
        flat pixel.
        """

        if self.bitdepth == 8:
            return bytes
        if self.bitdepth == 16:
            bytes = tostring(bytes)
            return array('H',
              struct.unpack('!%dH' % (len(bytes) // 2), bytes))
        assert self.bitdepth < 8
        if width is None:
            width = self.width
        # Samples per byte
        spb = 8 // self.bitdepth
        out = array('B')
        mask = 2 ** self.bitdepth - 1
        shifts = map(self.bitdepth.__mul__, reversed(range(spb)))
        l = width
        for o in bytes:
            out.extend(map(lambda i: mask & (o >> i), shifts)[:l])
            l -= spb
            if l <= 0:
                l = width
        return out

    def iterstraight(self, raw):
        """Iterator that undoes the effect of filtering, and yields each
        row in serialised format (as a sequence of bytes).  Assumes input
        is straightlaced.  `raw` should be an iterable that yields the
        raw bytes in chunks of arbitrary size."""

        # length of row, in bytes
        rb = self.row_bytes
        a = array('B')
        # The previous (reconstructed) scanline.  None indicates first
        # line of image.
        recon = None
        for some in raw:
            a.extend(some)
            while len(a) >= rb + 1:
                filter_type = a[0]
                scanline = a[1:rb + 1]
                del a[:rb + 1]
                recon = self.undo_filter(filter_type, scanline, recon)
                yield recon
        if len(a) != 0:
            # :file:format We get here with a file format error: when the
            # available bytes (after decompressing) do not pack into exact
            # rows.
            raise FormatError(
              'Wrong size for decompressed IDAT chunk.')
        assert len(a) == 0

    def validate_signature(self):
        """If signature (header) has not been read then read and
        validate it; otherwise do nothing.
        """

        if self.signature:
            return
        self.signature = self.file.read(8)
        if self.signature != _signature:
            raise FormatError("PNG file has invalid signature.")

    def preamble(self):
        """
        Extract the image metadata by reading the initial part of the PNG
        file up to the start of the ``IDAT`` chunk.  All the chunks that
        precede the ``IDAT`` chunk are read and either processed for
        metadata or discarded.
        """

        self.validate_signature()

        while True:
            if not self.atchunk:
                self.atchunk = self.chunklentype()
                if self.atchunk is None:
                    raise FormatError(
                      'This PNG file has no IDAT chunks.')
            if self.atchunk[1] == 'IDAT':
                return
            self.process_chunk()

    def chunklentype(self):
        """Reads just enough of the input to determine the next
        chunk's length and type, returned as a (*length*, *type*) pair
        where *type* is a string.  If there are no more chunks, ``None``
        is returned.
        """

        x = self.file.read(8)
        if not x:
            return None
        if len(x) != 8:
            raise FormatError(
              'End of file whilst reading chunk length and type.')
        length, type = struct.unpack('!I4s', x)
        if length > 2 ** 31 - 1:
            raise FormatError('Chunk %s is too large: %d.' % (type, length))
        return length, type

    def process_chunk(self):
        """Process the next chunk and its data.  This only processes the
        following chunk types, all others are ignored: ``IHDR``,
        ``PLTE``, ``bKGD``, ``tRNS``, ``gAMA``, ``sBIT``.
        """

        type, data = self.chunk()
        if type == 'IHDR':
            # http://www.w3.org/TR/PNG/#11IHDR
            if len(data) != 13:
                raise FormatError('IHDR chunk has incorrect length.')
            (self.width, self.height, self.bitdepth, self.color_type,
             self.compression, self.filter,
             self.interlace) = struct.unpack("!2I5B", data)

            # Check that the header specifies only valid combinations.
            if self.bitdepth not in (1, 2, 4, 8, 16):
                raise Error("invalid bit depth %d" % self.bitdepth)
            if self.color_type not in (0, 2, 3, 4, 6):
                raise Error("invalid colour type %d" % self.color_type)
            # Check indexed (palettized) images have 8 or fewer bits
            # per pixel; check only indexed or greyscale images have
            # fewer than 8 bits per pixel.
            if ((self.color_type & 1 and self.bitdepth > 8) or
                (self.bitdepth < 8 and self.color_type not in (0, 3))):
                raise FormatError("Illegal combination of bit depth (%d)"
                  " and colour type (%d)."
                  " See http://www.w3.org/TR/2003/REC-PNG-20031110/#table111 ."
                  % (self.bitdepth, self.color_type))
            if self.compression != 0:
                raise Error("unknown compression method %d" % self.compression)
            if self.filter != 0:
                raise FormatError("Unknown filter method %d,"
                  " see http://www.w3.org/TR/2003/REC-PNG-20031110/#9Filters ."
                  % self.filter)
            if self.interlace not in (0, 1):
                raise FormatError("Unknown interlace method %d,"
                  " see http://www.w3.org/TR/2003/REC-PNG-20031110/#8InterlaceMethods ."
                  % self.interlace)

            # Derived values
            # http://www.w3.org/TR/PNG/#6Colour-values
            colormap = bool(self.color_type & 1)
            greyscale = not (self.color_type & 2)
            alpha = bool(self.color_type & 4)
            color_planes = (3, 1)[greyscale or colormap]
            planes = color_planes + alpha

            self.colormap = colormap
            self.greyscale = greyscale
            self.alpha = alpha
            self.color_planes = color_planes
            self.planes = planes
            self.psize = float(self.bitdepth) / float(8) * planes
            if int(self.psize) == self.psize:
                self.psize = int(self.psize)
            self.row_bytes = int(math.ceil(self.width * self.psize))
            # Stores PLTE chunk if present, and is used to check
            # chunk ordering constraints.
            self.plte = None
            # Stores tRNS chunk if present, and is used to check chunk
            # ordering constraints.
            self.trns = None
            # Stores sbit chunk if present.
            self.sbit = None
        elif type == 'PLTE':
            # http://www.w3.org/TR/PNG/#11PLTE
            if self.plte:
                warnings.warn("Multiple PLTE chunks present.")
            self.plte = data
            if len(data) % 3 != 0:
                raise FormatError(
                  "PLTE chunk's length should be a multiple of 3.")
            if len(data) > (2 ** self.bitdepth) * 3:
                raise FormatError("PLTE chunk is too long.")
            if len(data) == 0:
                raise FormatError("Empty PLTE is not allowed.")
        elif type == 'bKGD':
            try:
                if self.colormap:
                    if not self.plte:
                        warnings.warn(
                          "PLTE chunk is required before bKGD chunk.")
                    self.background = struct.unpack('B', data)
                else:
                    self.background = struct.unpack("!%dH" % self.color_planes,
                      data)
            except struct.error:
                raise FormatError("bKGD chunk has incorrect length.")
        elif type == 'tRNS':
            # http://www.w3.org/TR/PNG/#11tRNS
            self.trns = data
            if self.colormap:
                if not self.plte:
                    warnings.warn("PLTE chunk is required before tRNS chunk.")
                else:
                    if len(data) > len(self.plte) / 3:
                        # Was warning, but promoted to Error as it
                        # would otherwise cause pain later on.
                        raise FormatError("tRNS chunk is too long.")
            else:
                if self.alpha:
                    raise FormatError(
                      "tRNS chunk is not valid with colour type %d." %
                      self.color_type)
                try:
                    self.transparent = \
                        struct.unpack("!%dH" % self.color_planes, data)
                except struct.error:
                    raise FormatError("tRNS chunk has incorrect length.")
        elif type == 'gAMA':
            try:
                self.gamma = struct.unpack("!L", data)[0] / 100000.0
            except struct.error:
                raise FormatError("gAMA chunk has incorrect length.")
        elif type == 'sBIT':
            self.sbit = data
            if (self.colormap and len(data) != 3 or
                not self.colormap and len(data) != self.planes):
                raise FormatError("sBIT chunk has incorrect length.")

    def read(self):
        """
        Read the PNG file and decode it.  Returns (`width`, `height`,
        `pixels`, `metadata`).

        May use excessive memory.

        `pixels` are returned in boxed row flat pixel format.
        """

        def iteridat():
            """Iterator that yields all the ``IDAT`` chunks as strings."""
            while True:
                try:
                    type, data = self.chunk()
                except ValueError, e:
                    raise ChunkError(e.args[0])
                if type == 'IEND':
                    # http://www.w3.org/TR/PNG/#11IEND
                    break
                if type != 'IDAT':
                    continue
                # type == 'IDAT'
                # http://www.w3.org/TR/PNG/#11IDAT
                if self.colormap and not self.plte:
                    warnings.warn("PLTE chunk is required before IDAT chunk")
                yield data

        def iterdecomp(idat):
            """Iterator that yields decompressed strings.  `idat` should
            be an iterator that yields the ``IDAT`` chunk data.
            """

            # Currently, with no max_length paramter to decompress, this
            # routine will do one yield per IDAT chunk.  So not very
            # incremental.
            d = zlib.decompressobj()
            # The decompression loop:
            # Decompress an IDAT chunk, then decompress any remaining
            # unused data until the unused data does not get any
            # smaller.  Add the unused data to the front of the input
            # and loop to process the next IDAT chunk.
            cdata = ''
            for data in idat:
                # :todo: add a max_length argument here to limit output
                # size.
                yield array('B', d.decompress(cdata + data))
            yield array('B', d.flush())

        self.preamble()
        raw = iterdecomp(iteridat())

        if self.interlace:
            raw = array('B', itertools.chain(*raw))
            arraycode = 'BH'[self.bitdepth > 8]
            # Like :meth:`group` but producing an array.array object for
            # each row.
            pixels = itertools.imap(lambda * row: array(arraycode, row),
                       *[iter(self.deinterlace(raw))] * self.width * self.planes)
        else:
            pixels = self.iterboxed(self.iterstraight(raw))
        meta = dict()
        for attr in 'greyscale alpha planes bitdepth interlace'.split():
            meta[attr] = getattr(self, attr)
        meta['size'] = (self.width, self.height)
        for attr in 'gamma transparent background'.split():
            a = getattr(self, attr, None)
            if a is not None:
                meta[attr] = a
        return self.width, self.height, pixels, meta

    def read_flat(self):
        """
        Read a PNG file and decode it into flat row flat pixel format.
        Returns (*width*, *height*, *pixels*, *metadata*).

        May use excessive memory.

        `pixels` are returned in flat row flat pixel format.

        See also the :meth:`read` method which returns pixels in the
        more stream-friendly boxed row flat pixel format.
        """

        x, y, pixel, meta = self.read()
        arraycode = 'BH'[meta['bitdepth'] > 8]
        pixel = array(arraycode, itertools.chain(*pixel))
        return x, y, pixel, meta

    def palette(self, alpha='natural'):
        """Returns a palette that is a sequence of 3-tuples or 4-tuples,
        synthesizing it from the ``PLTE`` and ``tRNS`` chunks.  These
        chunks should have already been processed (for example, by
        calling the :meth:`preamble` method).  All the tuples are the
        same size, 3-tuples if there is no ``tRNS`` chunk, 4-tuples when
        there is a ``tRNS`` chunk.  Assumes that the image is colour type
        3 and therefore a ``PLTE`` chunk is required.

        If the `alpha` argument is ``'force'`` then an alpha channel is
        always added, forcing the result to be a sequence of 4-tuples.
        """

        if not self.plte:
            raise FormatError(
                "Required PLTE chunk is missing in colour type 3 image.")
        plte = group(array('B', self.plte), 3)
        if self.trns or alpha == 'force':
            trns = array('B', self.trns or '')
            trns.extend([255] * (len(plte) - len(trns)))
            plte = map(operator.add, plte, group(trns, 1))
        return plte

    def asDirect(self):
        """Returns the image data as a direct representation of an
        ``x * y * planes`` array.  This method is intended to remove the
        need for callers to deal with palettes and transparency
        themselves.  Images with a palette (colour type 3)
        are converted to RGB or RGBA; images with transparency (a
        ``tRNS`` chunk) are converted to LA or RGBA as appropriate.
        When returned in this format the pixel values represent the
        colour value directly without needing to refer to palettes or
        transparency information.

        Like the :meth:`read` method this method returns a 4-tuple:

        (*width*, *height*, *pixels*, *meta*)

        This method normally returns pixel values with the bit depth
        they have in the source image, but when the source PNG has an
        ``sBIT`` chunk it is inspected and can reduce the bit depth of
        the result pixels; pixel values will be reduced according to
        the bit depth specified in the ``sBIT`` chunk (PNG nerds should
        note a single result bit depth is used for all channels; the
        maximum of the ones specified in the ``sBIT`` chunk.  An RGB565
        image will be rescaled to 6-bit RGB666).

        The *meta* dictionary that is returned reflects the `direct`
        format and not the original source image.  For example, an RGB
        source image with a ``tRNS`` chunk to represent a transparent
        colour, will have ``planes=3`` and ``alpha=False`` for the
        source image, but the *meta* dictionary returned by this method
        will have ``planes=4`` and ``alpha=True`` because an alpha
        channel is synthesized and added.

        *pixels* is the pixel data in boxed row flat pixel format (just
        like the :meth:`read` method).

        All the other aspects of the image data are not changed.
        """

        self.preamble()

        # Simple case, no conversion necessary.
        if not self.colormap and not self.trns and not self.sbit:
            return self.read()

        x, y, pixels, meta = self.read()

        if self.colormap:
            meta['colormap'] = False
            meta['alpha'] = bool(self.trns)
            meta['bitdepth'] = 8
            meta['planes'] = 3 + bool(self.trns)
            plte = self.palette()

            def iterpal(pixels):
                for row in pixels:
                    row = map(plte.__getitem__, row)
                    yield array('B', itertools.chain(*row))
            pixels = iterpal(pixels)
        elif self.trns:
            # It would be nice if there was some reasonable way of doing
            # this without generating a whole load of intermediate tuples.
            # But tuples does seem like the easiest way, with no other way
            # clearly much simpler or much faster.  (Actually, the L to LA
            # conversion could perhaps go faster (all those 1-tuples!), but
            # I still wonder whether the code proliferation is worth it)
            it = self.transparent
            maxval = 2 ** meta['bitdepth'] - 1
            planes = meta['planes']
            meta['alpha'] = True
            meta['planes'] += 1
            typecode = 'BH'[meta['bitdepth'] > 8]

            def itertrns(pixels):
                for row in pixels:
                    # For each row we group it into pixels, then form a
                    # characterisation vector that says whether each pixel
                    # is opaque or not.  Then we convert True/False to
                    # 0/maxval (by multiplication), and add it as the extra
                    # channel.
                    row = group(row, planes)
                    opa = map(it.__ne__, row)
                    opa = map(maxval.__mul__, opa)
                    opa = zip(opa)  # convert to 1-tuples
                    yield array(typecode,
                      itertools.chain(*map(operator.add, row, opa)))
            pixels = itertrns(pixels)
        targetbitdepth = None
        if self.sbit:
            sbit = struct.unpack('%dB' % len(self.sbit), self.sbit)
            targetbitdepth = max(sbit)
            if targetbitdepth > meta['bitdepth']:
                raise Error('sBIT chunk %r exceeds bitdepth %d' %
                    (sbit, self.bitdepth))
            if min(sbit) <= 0:
                raise Error('sBIT chunk %r has a 0-entry' % sbit)
            if targetbitdepth == meta['bitdepth']:
                targetbitdepth = None
        if targetbitdepth:
            shift = meta['bitdepth'] - targetbitdepth
            meta['bitdepth'] = targetbitdepth

            def itershift(pixels):
                for row in pixels:
                    yield map(shift.__rrshift__, row)
            pixels = itershift(pixels)
        return x, y, pixels, meta

    def asFloat(self, maxval=1.0):
        """Return image pixels as per :meth:`asDirect` method, but scale
        all pixel values to be floating point values between 0.0 and
        *maxval*.
        """

        x, y, pixels, info = self.asDirect()
        sourcemaxval = 2 ** info['bitdepth'] - 1
        del info['bitdepth']
        info['maxval'] = float(maxval)
        factor = float(maxval) / float(sourcemaxval)

        def iterfloat():
            for row in pixels:
                yield map(factor.__mul__, row)
        return x, y, iterfloat(), info

    def _as_rescale(self, get, targetbitdepth):
        """Helper used by :meth:`asRGB8` and :meth:`asRGBA8`."""

        width, height, pixels, meta = get()
        maxval = 2 ** meta['bitdepth'] - 1
        targetmaxval = 2 ** targetbitdepth - 1
        factor = float(targetmaxval) / float(maxval)
        meta['bitdepth'] = targetbitdepth

        def iterscale():
            for row in pixels:
                yield map(lambda x: int(round(x * factor)), row)
        return width, height, iterscale(), meta

    def asRGB8(self):
        """Return the image data as an RGB pixels with 8-bits per
    sample.  This is like the :meth:`asRGB` method except that
    this method additionally rescales the values so that they
    are all between 0 and 255 (8-bit).  In the case where the
    source image has a bit depth < 8 the transformation preserves
    all the information; where the source image has bit depth
    > 8, then rescaling to 8-bit values loses precision.  No
    dithering is performed.  Like :meth:`asRGB`, an alpha channel
    in the source image will raise an exception.

        This function returns a 4-tuple:
        (*width*, *height*, *pixels*, *metadata*).
        *width*, *height*, *metadata* are as per the :meth:`read` method.

        *pixels* is the pixel data in boxed row flat pixel format.
        """

        return self._as_rescale(self.asRGB, 8)

    def asRGBA8(self):
        """Return the image data as RGBA pixels with 8-bits per
        sample.  This method is similar to :meth:`asRGB8` and
        :meth:`asRGBA`:  The result pixels have an alpha channel, _and_
        values are rescale to the range 0 to 255.  The alpha channel is
        synthesized if necessary.
        """

        return self._as_rescale(self.asRGBA, 8)

    def asRGB(self):
        """Return image as RGB pixels.  Greyscales are expanded into RGB
        triplets.  An alpha channel in the source image will raise an
        exception.  The return values are as for the :meth:`read` method
        except that the *metadata* reflect the returned pixels, not the
        source image.  In particular, for this method
        ``metadata['greyscale']`` will be ``False``.
        """

        width, height, pixels, meta = self.asDirect()
        if meta['alpha']:
            raise Error("will not convert image with alpha channel to RGB")
        if not meta['greyscale']:
            return width, height, pixels, meta
        meta['greyscale'] = False
        typecode = 'BH'[meta['bitdepth'] > 8]

        def iterrgb():
            for row in pixels:
                a = array(typecode, [0]) * 3 * width
                for i in range(3):
                    a[i::3] = row
                yield a
        return width, height, iterrgb(), meta

    def asRGBA(self):
        """Return image as RGBA pixels.  Greyscales are expanded into
        RGB triplets; an alpha channel is synthesized if necessary.
        The return values are as for the :meth:`read` method
        except that the *metadata* reflect the returned pixels, not the
        source image.  In particular, for this method
        ``metadata['greyscale']`` will be ``False``, and
        ``metadata['alpha']`` will be ``True``.
        """

        width, height, pixels, meta = self.asDirect()
        if meta['alpha'] and not meta['greyscale']:
            return width, height, pixels, meta
        typecode = 'BH'[meta['bitdepth'] > 8]
        maxval = 2 ** meta['bitdepth'] - 1

        def newarray():
            return array(typecode, [0]) * 4 * width
        if meta['alpha'] and meta['greyscale']:
            # LA to RGBA
            def convert():
                for row in pixels:
                    # Create a fresh target row, then copy L channel
                    # into first three target channels, and A channel
                    # into fourth channel.
                    a = newarray()
                    for i in range(3):
                        a[i::4] = row[0::2]
                    a[3::4] = row[1::2]
                    yield a
        elif meta['greyscale']:
            # L to RGBA
            def convert():
                for row in pixels:
                    a = newarray()
                    for i in range(3):
                        a[i::4] = row
                    a[3::4] = array(typecode, maxval) * width
                    yield a
        else:
            assert not meta['alpha'] and not meta['greyscale']

            # RGB to RGBA
            def convert():
                for row in pixels:
                    a = newarray()
                    for i in range(3):
                        a[i::4] = row[i::3]
                    a[3::4] = array(typecode, [maxval]) * width
                    yield a
        meta['alpha'] = True
        meta['greyscale'] = False
        return width, height, convert(), meta


# === Legacy Version Support ===

# :pyver:old:  PyPNG works on Python versions 2.3 and 2.2, but not
# without some awkward problems.  Really PyPNG works on Python 2.4 (and
# above); it works on Pythons 2.3 and 2.2 by virtue of fixing up
# problems here.  It's a bit ugly (which is why it's hidden down here).
#
# Generally the strategy is one of pretending that we're running on
# Python 2.4 (or above), and patching up the library support on earlier
# versions so that it looks enough like Python 2.4.  When it comes to
# Python 2.2 there is one thing we cannot patch: extended slices
# http://www.python.org/doc/2.3/whatsnew/section-slices.html.
# Instead we simply declare that features that are implemented using
# extended slices will not work on Python 2.2.
#
# In order to work on Python 2.3 we fix up a recurring annoyance involving
# the array type.  In Python 2.3 an array cannot be initialised with an
# array, and it cannot be extended with a list (or other sequence).
# Both of those are repeated issues in the code.  Whilst I would not
# normally tolerate this sort of behaviour, here we "shim" a replacement
# for array into place (and hope no-ones notices).  You never read this.
#
# In an amusing case of warty hacks on top of warty hacks... the array
# shimming we try and do only works on Python 2.3 and above (you can't
# subclass array.array in Python 2.2).  So to get it working on Python
# 2.2 we go for something much simpler and (probably) way slower.
try:
    array('B').extend([])
    array('B', array('B'))
except:
    # Expect to get here on Python 2.3
    try:
        class _array_shim(array):
            true_array = array

            def __new__(cls, typecode, init=None):
                super_new = super(_array_shim, cls).__new__
                it = super_new(cls, typecode)
                if init is None:
                    return it
                it.extend(init)
                return it

            def extend(self, extension):
                super_extend = super(_array_shim, self).extend
                if isinstance(extension, self.true_array):
                    return super_extend(extension)
                if not isinstance(extension, (list, str)):
                    # Convert to list.  Allows iterators to work.
                    extension = list(extension)
                return super_extend(self.true_array(self.typecode, extension))
        array = _array_shim
    except:
        # Expect to get here on Python 2.2
        def array(typecode, init=()):
            if type(init) == str:
                return map(ord, init)
            return list(init)

# Further hacks to get it limping along on Python 2.2
try:
    enumerate
except:
    def enumerate(seq):
        i = 0
        for x in seq:
            yield i, x
            i += 1

try:
    reversed
except:
    def reversed(l):
        l = list(l)
        l.reverse()
        for x in l:
            yield x

try:
    itertools
except:
    class _dummy_itertools:
        pass
    itertools = _dummy_itertools()

    def _itertools_imap(f, seq):
        for x in seq:
            yield f(x)
    itertools.imap = _itertools_imap

    def _itertools_chain(*iterables):
        for it in iterables:
            for element in it:
                yield element
    itertools.chain = _itertools_chain

# === Internal Test Support ===

# This section comprises the tests that are internally validated (as
# opposed to tests which produce output files that are externally
# validated).  Primarily they are unittests.

# Note that it is difficult to internally validate the results of
# writing a PNG file.  The only thing we can do is read it back in
# again, which merely checks consistency, not that the PNG file we
# produce is valid.

# Run the tests from the command line:
# python -c 'import png;png.test()'

from cStringIO import StringIO
import tempfile
# http://www.python.org/doc/2.4.4/lib/module-unittest.html
import unittest


def test():
    unittest.main(__name__)


def topngbytes(name, rows, x, y, **k):
    """Convenience function for creating a PNG file "in memory" as a
    string.  Creates a :class:`Writer` instance using the keyword arguments,
    then passes `rows` to its :meth:`Writer.write` method.  The resulting
    PNG file is returned as a string.  `name` is used to identify the file for
    debugging.
    """

    import os

    print name
    f = StringIO()
    w = Writer(x, y, **k)
    w.write(f, rows)
    if os.environ.get('PYPNG_TEST_TMP'):
        w = open(name, 'wb')
        w.write(f.getvalue())
        w.close()
    return f.getvalue()


def testWithIO(inp, out, f):
    """Calls the function `f` with ``sys.stdin`` changed to `inp`
    and ``sys.stdout`` changed to `out`.  They are restored when `f`
    returns.  This function returns whatever `f` returns.
    """
    try:
        oldin, sys.stdin = sys.stdin, inp
        oldout, sys.stdout = sys.stdout, out
        x = f()
    finally:
        sys.stdin = oldin
        sys.stdout = oldout
    return x


class Test(unittest.TestCase):
    # This member is used by the superclass.  If we don't define a new
    # class here then when we use self.assertRaises() and the PyPNG code
    # raises an assertion then we get no proper traceback.  I can't work
    # out why, but defining a new class here means we get a proper
    # traceback.
    class failureException(Exception):
        pass

    def helperLN(self, n):
        mask = (1 << n) - 1
        # Use small chunk_limit so that multiple chunk writing is
        # tested.  Making it a test for Issue 20.
        w = Writer(15, 17, greyscale=True, bitdepth=n, chunk_limit=99)
        f = StringIO()
        w.write_array(f, array('B', map(mask.__and__, range(1, 256))))
        r = Reader(bytes=f.getvalue())
        x, y, pixels, meta = r.read()
        self.assertEqual(x, 15)
        self.assertEqual(y, 17)
        self.assertEqual(list(itertools.chain(*pixels)),
                         map(mask.__and__, range(1, 256)))

    def testL8(self):
        return self.helperLN(8)

    def testL4(self):
        return self.helperLN(4)

    def testL2(self):
        "Also tests asRGB8."
        w = Writer(1, 4, greyscale=True, bitdepth=2)
        f = StringIO()
        w.write_array(f, array('B', range(4)))
        r = Reader(bytes=f.getvalue())
        x, y, pixels, meta = r.asRGB8()
        self.assertEqual(x, 1)
        self.assertEqual(y, 4)
        for i, row in enumerate(pixels):
            self.assertEqual(len(row), 3)
            self.assertEqual(list(row), [0x55 * i] * 3)

    def testP2(self):
        "2-bit palette."
        a = (255, 255, 255)
        b = (200, 120, 120)
        c = (50, 99, 50)
        w = Writer(1, 4, bitdepth=2, palette=[a, b, c])
        f = StringIO()
        w.write_array(f, array('B', (0, 1, 1, 2)))
        r = Reader(bytes=f.getvalue())
        x, y, pixels, meta = r.asRGB8()
        self.assertEqual(x, 1)
        self.assertEqual(y, 4)
        self.assertEqual(list(pixels), map(list, [a, b, b, c]))

    def testPtrns(self):
        "Test colour type 3 and tRNS chunk (and 4-bit palette)."
        a = (50, 99, 50, 50)
        b = (200, 120, 120, 80)
        c = (255, 255, 255)
        d = (200, 120, 120)
        e = (50, 99, 50)
        w = Writer(3, 3, bitdepth=4, palette=[a, b, c, d, e])
        f = StringIO()
        w.write_array(f, array('B', (4, 3, 2, 3, 2, 0, 2, 0, 1)))
        r = Reader(bytes=f.getvalue())
        x, y, pixels, meta = r.asRGBA8()
        self.assertEquals(x, 3)
        self.assertEquals(y, 3)
        c = c + (255,)
        d = d + (255,)
        e = e + (255,)
        boxed = [(e, d, c), (d, c, a), (c, a, b)]
        flat = map(lambda row: itertools.chain(*row), boxed)
        self.assertEqual(map(list, pixels), map(list, flat))

    def testRGBtoRGBA(self):
        "asRGBA8() on colour type 2 source."""
        # Test for Issue 26
        r = Reader(bytes=_pngsuite['basn2c08'])
        x, y, pixels, meta = r.asRGBA8()
        # Test the pixels at row 9 columns 0 and 1.
        row9 = list(pixels)[9]
        self.assertEqual(row9[0:8],
                         [0xff, 0xdf, 0xff, 0xff, 0xff, 0xde, 0xff, 0xff])

    def testCtrns(self):
        "Test colour type 2 and tRNS chunk."
        # Test for Issue 25
        r = Reader(bytes=_pngsuite['tbrn2c08'])
        x, y, pixels, meta = r.asRGBA8()
        # I just happen to know that the first pixel is transparent.
        # In particular it should be #7f7f7f00
        row0 = list(pixels)[0]
        self.assertEqual(tuple(row0[0:4]), (0x7f, 0x7f, 0x7f, 0x00))

    def testAdam7read(self):
        """Adam7 interlace reading.
        Specifically, test that for images in the PngSuite that
        have both an interlaced and straightlaced pair that both
        images from the pair produce the same array of pixels."""
        for candidate in _pngsuite:
            if not candidate.startswith('basn'):
                continue
            candi = candidate.replace('n', 'i')
            if candi not in _pngsuite:
                continue
            print 'adam7 read', candidate
            straight = Reader(bytes=_pngsuite[candidate])
            adam7 = Reader(bytes=_pngsuite[candi])
            # Just compare the pixels.  Ignore x,y (because they're
            # likely to be correct?); metadata is ignored because the
            # "interlace" member differs.  Lame.
            straight = straight.read()[2]
            adam7 = adam7.read()[2]
            self.assertEqual(map(list, straight), map(list, adam7))

    def testAdam7write(self):
        """Adam7 interlace writing.
        For each test image in the PngSuite, write an interlaced
        and a straightlaced version.  Decode both, and compare results.
        """
        # Not such a great test, because the only way we can check what
        # we have written is to read it back again.

        for name, bytes in _pngsuite.items():
            # Only certain colour types supported for this test.
            if name[3:5] not in ['n0', 'n2', 'n4', 'n6']:
                continue
            it = Reader(bytes=bytes)
            x, y, pixels, meta = it.read()
            pngi = topngbytes('adam7wn' + name + '.png', pixels,
              x=x, y=y, bitdepth=it.bitdepth,
              greyscale=it.greyscale, alpha=it.alpha,
              transparent=it.transparent,
              interlace=False)
            x, y, ps, meta = Reader(bytes=pngi).read()
            it = Reader(bytes=bytes)
            x, y, pixels, meta = it.read()
            pngs = topngbytes('adam7wi' + name + '.png', pixels,
              x=x, y=y, bitdepth=it.bitdepth,
              greyscale=it.greyscale, alpha=it.alpha,
              transparent=it.transparent,
              interlace=True)
            x, y, pi, meta = Reader(bytes=pngs).read()
            self.assertEqual(map(list, ps), map(list, pi))

    def testPGMin(self):
        """Test that the command line tool can read PGM files."""
        def do():
            return _main(['testPGMin'])
        s = StringIO()
        s.write('P5 2 2 3\n')
        s.write('\x00\x01\x02\x03')
        s.flush()
        s.seek(0)
        o = StringIO()
        testWithIO(s, o, do)
        r = Reader(bytes=o.getvalue())
        x, y, pixels, meta = r.read()
        self.assert_(r.greyscale)
        self.assertEqual(r.bitdepth, 2)

    def testPAMin(self):
        """Test that the command line tool can read PAM file."""
        def do():
            return _main(['testPAMin'])
        s = StringIO()
        s.write('P7\nWIDTH 3\nHEIGHT 1\nDEPTH 4\nMAXVAL 255\n'
                'TUPLTYPE RGB_ALPHA\nENDHDR\n')
        # The pixels in flat row flat pixel format
        flat = [255, 0, 0, 255, 0, 255, 0, 120, 0, 0, 255, 30]
        s.write(''.join(map(chr, flat)))
        s.flush()
        s.seek(0)
        o = StringIO()
        testWithIO(s, o, do)
        r = Reader(bytes=o.getvalue())
        x, y, pixels, meta = r.read()
        self.assert_(r.alpha)
        self.assert_(not r.greyscale)
        self.assertEqual(list(itertools.chain(*pixels)), flat)

    def testLA4(self):
        """Create an LA image with bitdepth 4."""
        bytes = topngbytes('la4.png', [[5, 12]], 1, 1,
          greyscale=True, alpha=True, bitdepth=4)
        sbit = Reader(bytes=bytes).chunk('sBIT')[1]
        self.assertEqual(sbit, '\x04\x04')

    def testPNMsbit(self):
        """Test that PNM files can generates sBIT chunk."""
        def do():
            return _main(['testPNMsbit'])
        s = StringIO()
        s.write('P6 8 1 1\n')
        for pixel in range(8):
            s.write(struct.pack('<I', (0x4081 * pixel) & 0x10101)[:3])
        s.flush()
        s.seek(0)
        o = StringIO()
        testWithIO(s, o, do)
        r = Reader(bytes=o.getvalue())
        sbit = r.chunk('sBIT')[1]
        self.assertEqual(sbit, '\x01\x01\x01')

    def testLtrns0(self):
        """Create greyscale image with tRNS chunk."""
        return self.helperLtrns(0)

    def testLtrns1(self):
        """Using 1-tuple for transparent arg."""
        return self.helperLtrns((0,))

    def helperLtrns(self, transparent):
        """Helper used by :meth:`testLtrns*`."""
        pixels = zip(map(ord, '00384c545c403800'.decode('hex')))
        o = StringIO()
        w = Writer(8, 8, greyscale=True, bitdepth=1, transparent=transparent)
        w.write_packed(o, pixels)
        r = Reader(bytes=o.getvalue())
        x, y, pixels, meta = r.asDirect()
        self.assert_(meta['alpha'])
        self.assert_(meta['greyscale'])
        self.assertEqual(meta['bitdepth'], 1)

    def testWinfo(self):
        """Test the dictionary returned by a `read` method can be used
        as args for :meth:`Writer`.
        """
        r = Reader(bytes=_pngsuite['basn2c16'])
        info = r.read()[3]
        w = Writer(**info)

    def testPackedIter(self):
        """Test iterator for row when using write_packed.

        Indicative for Issue 47.
        """
        w = Writer(16, 2, greyscale=True, alpha=False, bitdepth=1)
        o = StringIO()
        w.write_packed(o, [itertools.chain([0x0a], [0xaa]),
                           itertools.chain([0x0f], [0xff])])
        r = Reader(bytes=o.getvalue())
        x, y, pixels, info = r.asDirect()
        pixels = list(pixels)
        self.assertEqual(len(pixels), 2)
        self.assertEqual(len(pixels[0]), 16)

    def testInterlacedArray(self):
        """Test that reading an interlaced PNG yields each row as an
        array."""
        r = Reader(bytes=_pngsuite['basi0g08'])
        list(r.read()[2])[0].tostring

    def testTrnsArray(self):
        """Test that reading a type 2 PNG with tRNS chunk yields each
        row as an array (using asDirect)."""
        r = Reader(bytes=_pngsuite['tbrn2c08'])
        list(r.asDirect()[2])[0].tostring

    # Invalid file format tests.  These construct various badly
    # formatted PNG files, then feed them into a Reader.  When
    # everything is working properly, we should get FormatError
    # exceptions raised.
    def testEmpty(self):
        """Test empty file."""

        r = Reader(bytes='')
        self.assertRaises(FormatError, r.asDirect)

    def testSigOnly(self):
        """Test file containing just signature bytes."""

        r = Reader(bytes=_signature)
        self.assertRaises(FormatError, r.asDirect)

    def testExtraPixels(self):
        """Test file that contains too many pixels."""

        def eachchunk(chunk):
            if chunk[0] != 'IDAT':
                return chunk
            data = chunk[1].decode('zip')
            data += '\x00garbage'
            data = data.encode('zip')
            chunk = (chunk[0], data)
            return chunk
        self.assertRaises(FormatError, self.helperFormat, eachchunk)

    def testNotEnoughPixels(self):
        def eachchunk(chunk):
            if chunk[0] != 'IDAT':
                return chunk
            # Remove last byte.
            data = chunk[1].decode('zip')
            data = data[:-1]
            data = data.encode('zip')
            return chunk[0], data
        self.assertRaises(FormatError, self.helperFormat, eachchunk)

    def helperFormat(self, f):
        r = Reader(bytes=_pngsuite['basn0g01'])
        o = StringIO()

        def newchunks():
            for chunk in r.chunks():
                yield f(chunk)
        write_chunks(o, newchunks())
        r = Reader(bytes=o.getvalue())
        return list(r.asDirect()[2])

    def testBadFilter(self):
        def eachchunk(chunk):
            if chunk[0] != 'IDAT':
                return chunk
            data = chunk[1].decode('zip')
            # Corrupt the first filter byte
            data = '\x99' + data[1:]
            data = data.encode('zip')
            return chunk[0], data
        self.assertRaises(FormatError, self.helperFormat, eachchunk)

    def testFlat(self):
        """Test read_flat."""
        import hashlib

        r = Reader(bytes=_pngsuite['basn0g02'])
        x, y, pixel, meta = r.read_flat()
        d = hashlib.md5(''.join(map(chr, pixel))).digest()
        self.assertEqual(d.encode('hex'), '255cd971ab8cd9e7275ff906e5041aa0')

    # numpy dependent tests.  These are skipped (with a message to
    # sys.stderr) if numpy cannot be imported.
    def testNumpyuint16(self):
        """numpy uint16."""

        try:
            import numpy
        except ImportError:
            print >> sys.stderr, "skipping numpy test"
            return

        rows = [map(numpy.uint16, range(0, 0x10000, 0x5555))]
        b = topngbytes('numpyuint16.png', rows, 4, 1,
            greyscale=True, alpha=False, bitdepth=16)

    def testNumpyuint8(self):
        """numpy uint8."""

        try:
            import numpy
        except ImportError:
            print >> sys.stderr, "skipping numpy test"
            return

        rows = [map(numpy.uint8, range(0, 0x100, 0x55))]
        b = topngbytes('numpyuint8.png', rows, 4, 1,
            greyscale=True, alpha=False, bitdepth=8)

    def testNumpybool(self):
        """numpy bool."""

        try:
            import numpy
        except ImportError:
            print >> sys.stderr, "skipping numpy test"
            return

        rows = [map(numpy.bool, [0, 1])]
        b = topngbytes('numpybool.png', rows, 2, 1,
            greyscale=True, alpha=False, bitdepth=1)


# === Command Line Support ===


def _dehex(s):
    """Liberally convert from hex string to binary string."""
    import re

    # Remove all non-hexadecimal digits
    s = re.sub(r'[^a-fA-F\d]', '', s)
    return s.decode('hex')

# Copies of PngSuite test files taken
# from http://www.schaik.com/pngsuite/pngsuite_bas_png.html
# on 2009-02-19 by drj and converted to hex.
# Some of these are not actually in PngSuite (but maybe they should
# be?), they use the same naming scheme, but start with a capital
# letter.
_pngsuite = {
  'basi0g01': _dehex("""
89504e470d0a1a0a0000000d49484452000000200000002001000000012c0677
cf0000000467414d41000186a031e8965f0000009049444154789c2d8d310ec2
300c45dfc682c415187a00a42e197ab81e83b127e00c5639001363a580d8582c
65c910357c4b78b0bfbfdf4f70168c19e7acb970a3f2d1ded9695ce5bf5963df
d92aaf4c9fd927ea449e6487df5b9c36e799b91bdf082b4d4bd4014fe4014b01
ab7a17aee694d28d328a2d63837a70451e1648702d9a9ff4a11d2f7a51aa21e5
a18c7ffd0094e3511d661822f20000000049454e44ae426082
"""),
  'basi0g02': _dehex("""
89504e470d0a1a0a0000000d49484452000000200000002002000000016ba60d
1f0000000467414d41000186a031e8965f0000005149444154789c635062e860
00e17286bb609c93c370ec189494960631366e4467b3ae675dcf10f521ea0303
90c1ca006444e11643482064114a4852c710baea3f18c31918020c30410403a6
0ac1a09239009c52804d85b6d97d0000000049454e44ae426082
"""),
  'basi0g04': _dehex("""
89504e470d0a1a0a0000000d4948445200000020000000200400000001e4e6f8
bf0000000467414d41000186a031e8965f000000ae49444154789c658e5111c2
301044171c141c141c041c843a287510ea20d441c041c141c141c04191102454
03994998cecd7edcecedbb9bdbc3b2c2b6457545fbc4bac1be437347f7c66a77
3c23d60db15e88f5c5627338a5416c2e691a9b475a89cd27eda12895ae8dfdab
43d61e590764f5c83a226b40d669bec307f93247701687723abf31ff83a2284b
a5b4ae6b63ac6520ad730ca4ed7b06d20e030369bd6720ed383290360406d24e
13811f2781eba9d34d07160000000049454e44ae426082
"""),
  'basi0g08': _dehex("""
89504e470d0a1a0a0000000d4948445200000020000000200800000001211615
be0000000467414d41000186a031e8965f000000b549444154789cb5905d0ac2
3010849dbac81c42c47bf843cf253e8878b0aa17110f214bdca6be240f5d21a5
94ced3e49bcd322c1624115515154998aa424822a82a5624a1aa8a8b24c58f99
999908130989a04a00d76c2c09e76cf21adcb209393a6553577da17140a2c59e
70ecbfa388dff1f03b82fb82bd07f05f7cb13f80bb07ad2fd60c011c3c588eef
f1f4e03bbec7ce832dca927aea005e431b625796345307b019c845e6bfc3bb98
769d84f9efb02ea6c00f9bb9ff45e81f9f280000000049454e44ae426082
"""),
  'basi0g16': _dehex("""
89504e470d0a1a0a0000000d49484452000000200000002010000000017186c9
fd0000000467414d41000186a031e8965f000000e249444154789cb5913b0ec2
301044c7490aa8f85d81c3e4301c8f53a4ca0da8902c8144b3920b4043111282
23bc4956681a6bf5fc3c5a3ba0448912d91a4de2c38dd8e380231eede4c4f7a1
4677700bec7bd9b1d344689315a3418d1a6efbe5b8305ba01f8ff4808c063e26
c60d5c81edcf6c58c535e252839e93801b15c0a70d810ae0d306b205dc32b187
272b64057e4720ff0502154034831520154034c3df81400510cdf0015c86e5cc
5c79c639fddba9dcb5456b51d7980eb52d8e7d7fa620a75120d6064641a05120
b606771a05626b401a05f1f589827cf0fe44c1f0bae0055698ee8914fffffe00
00000049454e44ae426082
"""),
  'basi2c08': _dehex("""
89504e470d0a1a0a0000000d49484452000000200000002008020000018b1fdd
350000000467414d41000186a031e8965f000000f249444154789cd59341aa04
210c44abc07b78133d59d37333bd89d76868b566d10cf4675af8596431a11662
7c5688919280e312257dd6a0a4cf1a01008ee312a5f3c69c37e6fcc3f47e6776
a07f8bdaf5b40feed2d33e025e2ff4fe2d4a63e1a16d91180b736d8bc45854c5
6d951863f4a7e0b66dcf09a900f3ffa2948d4091e53ca86c048a64390f662b50
4a999660ced906182b9a01a8be00a56404a6ede182b1223b4025e32c4de34304
63457680c93aada6c99b73865aab2fc094920d901a203f5ddfe1970d28456783
26cffbafeffcd30654f46d119be4793f827387fc0d189d5bc4d69a3c23d45a7f
db803146578337df4d0a3121fc3d330000000049454e44ae426082
"""),
  'basi2c16': _dehex("""
89504e470d0a1a0a0000000d4948445200000020000000201002000001db8f01
760000000467414d41000186a031e8965f0000020a49444154789cd5962173e3
3010853fcf1838cc61a1818185a53e56787fa13fa130852e3b5878b4b0b03081
b97f7030070b53e6b057a0a8912bbb9163b9f109ececbc59bd7dcf2b45492409
d66f00eb1dd83cb5497d65456aeb8e1040913b3b2c04504c936dd5a9c7e2c6eb
b1b8f17a58e8d043da56f06f0f9f62e5217b6ba3a1b76f6c9e99e8696a2a72e2
c4fb1e4d452e92ec9652b807486d12b6669be00db38d9114b0c1961e375461a5
5f76682a85c367ad6f682ff53a9c2a353191764b78bb07d8ddc3c97c1950f391
6745c7b9852c73c2f212605a466a502705c8338069c8b9e84efab941eb393a97
d4c9fd63148314209f1c1d3434e847ead6380de291d6f26a25c1ebb5047f5f24
d85c49f0f22cc1d34282c72709cab90477bf25b89d49f0f351822297e0ea9704
f34c82bc94002448ede51866e5656aef5d7c6a385cb4d80e6a538ceba04e6df2
480e9aa84ddedb413bb5c97b3838456df2d4fec2c7a706983e7474d085fae820
a841776a83073838973ac0413fea2f1dc4a06e71108fda73109bdae48954ad60
bf867aac3ce44c7c1589a711cf8a81df9b219679d96d1cec3d8bbbeaa2012626
df8c7802eda201b2d2e0239b409868171fc104ba8b76f10b4da09f6817ffc609
c413ede267fd1fbab46880c90f80eccf0013185eb48b47ba03df2bdaadef3181
cb8976f18e13188768170f98c0f844bb78cb04c62ddac59d09fc3fa25dfc1da4
14deb3df1344f70000000049454e44ae426082
"""),
  'basi3p08': _dehex("""
89504e470d0a1a0a0000000d494844520000002000000020080300000133a3ba
500000000467414d41000186a031e8965f00000300504c5445224400f5ffed77
ff77cbffff110a003a77002222ffff11ff110000222200ffac5566ff66ff6666
ff01ff221200dcffffccff994444ff005555220000cbcbff44440055ff55cbcb
00331a00ffecdcedffffe4ffcbffdcdc44ff446666ff330000442200ededff66
6600ffa444ffffaaeded0000cbcbfefffffdfffeffff0133ff33552a000101ff
8888ff00aaaa010100440000888800ffe4cbba5b0022ff22663200ffff99aaaa
ff550000aaaa00cb630011ff11d4ffaa773a00ff4444dc6b0066000001ff0188
4200ecffdc6bdc00ffdcba00333300ed00ed7300ffff88994a0011ffff770000
ff8301ffbabafe7b00fffeff00cb00ff999922ffff880000ffff77008888ffdc
ff1a33000000aa33ffff009900990000000001326600ffbaff44ffffffaaff00
770000fefeaa00004a9900ffff66ff22220000998bff1155ffffff0101ff88ff
005500001111fffffefffdfea4ff4466ffffff66ff003300ffff55ff77770000
88ff44ff00110077ffff006666ffffed000100fff5ed1111ffffff44ff22ffff
eded11110088ffff00007793ff2200dcdc3333fffe00febabaff99ffff333300
63cb00baba00acff55ffffdcffff337bfe00ed00ed5555ffaaffffdcdcff5555
00000066dcdc00dc00dc83ff017777fffefeffffffcbff5555777700fefe00cb
00cb0000fe010200010000122200ffff220044449bff33ffd4aa0000559999ff
999900ba00ba2a5500ffcbcbb4ff66ff9b33ffffbaaa00aa42880053aa00ffaa
aa0000ed00babaffff1100fe00000044009999990099ffcc99ba000088008800
dc00ff93220000dcfefffeaa5300770077020100cb0000000033ffedff00ba00
ff3333edffedffc488bcff7700aa00660066002222dc0000ffcbffdcffdcff8b
110000cb00010155005500880000002201ffffcbffcbed0000ff88884400445b
ba00ffbc77ff99ff006600baffba00777773ed00fe00003300330000baff77ff
004400aaffaafffefe000011220022c4ff8800eded99ff99ff55ff002200ffb4
661100110a1100ff1111dcffbabaffff88ff88010001ff33ffb98ed362000002
a249444154789c65d0695c0b001806f03711a9904a94d24dac63292949e5a810
d244588a14ca5161d1a1323973252242d62157d12ae498c8124d25ca3a11398a
16e55a3cdffab0ffe7f77d7fcff3528645349b584c3187824d9d19d4ec2e3523
9eb0ae975cf8de02f2486d502191841b42967a1ad49e5ddc4265f69a899e26b5
e9e468181baae3a71a41b95669da8df2ea3594c1b31046d7b17bfb86592e4cbe
d89b23e8db0af6304d756e60a8f4ad378bdc2552ae5948df1d35b52143141533
33bbbbababebeb3b3bc9c9c9c6c6c0c0d7b7b535323225a5aa8a02024a4bedec
0a0a2a2bcdcd7d7cf2f3a9a9c9cdcdd8b8adcdd5b5ababa828298982824a4ab2
b21212acadbdbc1414e2e24859b9a72730302f4f49292c4c57373c9c0a0b7372
8c8c1c1c3a3a92936d6dfdfd293e3e26262a4a4eaea2424b4b5fbfbc9c323278
3c0b0ba1303abaae8ecdeeed950d6669a9a7a7a141d4de9e9d5d5cdcd2229b94
c572716132f97cb1d8db9bc3110864a39795d9db6b6a26267a7a9a98d4d6a6a7
cb76090ef6f030354d4d75766e686030545464cb393a1a1ac6c68686eae8f8f9
a9aa4644c8b66d6e1689dcdd2512a994cb35330b0991ad9f9b6b659596a6addd
d8282fafae5e5323fb8f41d01f76c22fd8061be01bfc041a0323e1002c81cd30
0b9ec027a0c930014ec035580fc3e112bc069a0b53e11c0c8095f00176c163a0
e5301baec06a580677600ddc05ba0f13e120bc81a770133ec355a017300d4ec2
0c7800bbe1219c02fa08f3e13c1c85dbb00a2ec05ea0dff00a6ec15a98027360
070c047a06d7e1085c84f1b014f6c03fa0b33018b6c0211801ebe018fc00da0a
6f61113c877eb01d4ec317a085700f26c130f80efbe132bc039a0733e106fc81
f7f017f6c10aa0d1300a0ec374780943e1382c06fa0a9b60238c83473016cec0
02f80f73fefe1072afc1e50000000049454e44ae426082
"""),
  'basi6a08': _dehex("""
89504e470d0a1a0a0000000d4948445200000020000000200806000001047d4a
620000000467414d41000186a031e8965f0000012049444154789cc595414ec3
3010459fa541b8bbb26641b8069b861e8b4d12c1c112c1452a710a2a65d840d5
949041fc481ec98ae27c7f3f8d27e3e4648047600fec0d1f390fbbe2633a31e2
9389e4e4ea7bfdbf3d9a6b800ab89f1bd6b553cfcbb0679e960563d72e0a9293
b7337b9f988cc67f5f0e186d20e808042f1c97054e1309da40d02d7e27f92e03
6cbfc64df0fc3117a6210a1b6ad1a00df21c1abcf2a01944c7101b0cb568a001
909c9cf9e399cf3d8d9d4660a875405d9a60d000b05e2de55e25780b7a5268e0
622118e2399aab063a815808462f1ab86890fc2e03e48bb109ded7d26ce4bf59
0db91bac0050747fec5015ce80da0e5700281be533f0ce6d5900b59bcb00ea6d
200314cf801faab200ea752803a8d7a90c503a039f824a53f4694e7342000000
0049454e44ae426082
"""),
  'basn0g01': _dehex("""
89504e470d0a1a0a0000000d49484452000000200000002001000000005b0147
590000000467414d41000186a031e8965f0000005b49444154789c2dccb10903
300c05d1ebd204b24a200b7a346f90153c82c18d0a61450751f1e08a2faaead2
a4846ccea9255306e753345712e211b221bf4b263d1b427325255e8bdab29e6f
6aca30692e9d29616ee96f3065f0bf1f1087492fd02f14c90000000049454e44
ae426082
"""),
  'basn0g02': _dehex("""
89504e470d0a1a0a0000000d49484452000000200000002002000000001ca13d
890000000467414d41000186a031e8965f0000001f49444154789c6360085df5
1f8cf1308850c20053868f0133091f6390b90700bd497f818b0989a900000000
49454e44ae426082
"""),
  # A version of basn0g04 dithered down to 3 bits.
  'Basn0g03': _dehex("""
89504e470d0a1a0a0000000d494844520000002000000020040000000093e1c8
2900000001734249540371d88211000000fd49444154789c6d90d18906210c84
c356f22356b2889588604301b112112b11d94a96bb495cf7fe87f32d996f2689
44741cc658e39c0b118f883e1f63cc89dafbc04c0f619d7d898396c54b875517
83f3a2e7ac09a2074430e7f497f00f1138a5444f82839c5206b1f51053cca968
63258821e7f2b5438aac16fbecc052b646e709de45cf18996b29648508728612
952ca606a73566d44612b876845e9a347084ea4868d2907ff06be4436c4b41a3
a3e1774285614c5affb40dbd931a526619d9fa18e4c2be420858de1df0e69893
a0e3e5523461be448561001042b7d4a15309ce2c57aef2ba89d1c13794a109d7
b5880aa27744fc5c4aecb5e7bcef5fe528ec6293a930690000000049454e44ae
426082
"""),
  'basn0g04': _dehex("""
89504e470d0a1a0a0000000d494844520000002000000020040000000093e1c8
290000000467414d41000186a031e8965f0000004849444154789c6360601014
545232367671090d4d4b2b2f6720430095dbd1418e002a77e64c720450b9ab56
912380caddbd9b1c0154ee9933e408a072efde25470095fbee1d1902001f14ee
01eaff41fa0000000049454e44ae426082
"""),
  'basn0g08': _dehex("""
89504e470d0a1a0a0000000d4948445200000020000000200800000000561125
280000000467414d41000186a031e8965f0000004149444154789c6364602400
1408c8b30c05058c0f0829f8f71f3f6079301c1430ca11906764a2795c0c0605
8c8ff0cafeffcff887e67131181430cae0956564040050e5fe7135e2d8590000
000049454e44ae426082
"""),
  'basn0g16': _dehex("""
89504e470d0a1a0a0000000d49484452000000200000002010000000000681f9
6b0000000467414d41000186a031e8965f0000005e49444154789cd5d2310ac0
300c4351395bef7fc6dca093c0287b32d52a04a3d98f3f3880a7b857131363a0
3a82601d089900dd82f640ca04e816dc06422640b7a03d903201ba05b7819009
d02d680fa44c603f6f07ec4ff41938cf7f0016d84bd85fae2b9fd70000000049
454e44ae426082
"""),
  'basn2c08': _dehex("""
89504e470d0a1a0a0000000d4948445200000020000000200802000000fc18ed
a30000000467414d41000186a031e8965f0000004849444154789cedd5c10900
300c024085ec91fdb772133b442bf4a1f8cee12bb40d043b800a14f81ca0ede4
7d4c784081020f4a871fc284071428f0a0743823a94081bb7077a3c00182b1f9
5e0f40cf4b0000000049454e44ae426082
"""),
  'basn2c16': _dehex("""
89504e470d0a1a0a0000000d4948445200000020000000201002000000ac8831
e00000000467414d41000186a031e8965f000000e549444154789cd596c10a83
301044a7e0417fcb7eb7fdadf6961e06039286266693cc7a188645e43dd6a08f
1042003e2fe09aef6472737e183d27335fcee2f35a77b702ebce742870a23397
f3edf2705dd10160f3b2815fe8ecf2027974a6b0c03f74a6e4192843e75c6c03
35e8ec3202f5e84c0181bbe8cca967a00d9df3491bb040671f2e6087ce1c2860
8d1e05f8c7ee0f1d00b667e70df44467ef26d01fbd9bc028f42860f71d188bce
fb8d3630039dbd59601e7ab3c06cf428507f0634d039afdc80123a7bb1801e7a
b1802a7a14c89f016d74ce331bf080ce9e08f8414f04bca133bfe642fe5e07bb
c4ec0000000049454e44ae426082
"""),
  'basn6a08': _dehex("""
89504e470d0a1a0a0000000d4948445200000020000000200806000000737a7a
f40000000467414d41000186a031e8965f0000006f49444154789cedd6310a80
300c46e12764684fa1f73f55048f21c4ddc545781d52e85028fc1f4d28d98a01
305e7b7e9cffba33831d75054703ca06a8f90d58a0074e351e227d805c8254e3
1bb0420f5cdc2e0079208892ffe2a00136a07b4007943c1004d900195036407f
011bf00052201a9c160fb84c0000000049454e44ae426082
"""),
  'cs3n3p08': _dehex("""
89504e470d0a1a0a0000000d494844520000002000000020080300000044a48a
c60000000467414d41000186a031e8965f0000000373424954030303a392a042
00000054504c544592ff0000ff9200ffff00ff0000dbff00ff6dffb600006dff
b6ff00ff9200dbff000049ffff2400ff000024ff0049ff0000ffdb00ff4900ff
b6ffff0000ff2400b6ffffdb000092ffff6d000024ffff49006dff00df702b17
0000004b49444154789c85cac70182000000b1b3625754b0edbfa72324ef7486
184ed0177a437b680bcdd0031c0ed00ea21f74852ed00a1c9ed0086da0057487
6ed0121cd6d004bda0013a421ff803224033e177f4ae260000000049454e44ae
426082
"""),
  's09n3p02': _dehex("""
89504e470d0a1a0a0000000d49484452000000090000000902030000009dffee
830000000467414d41000186a031e8965f000000037342495404040477f8b5a3
0000000c504c544500ff000077ffff00ffff7700ff5600640000001f49444154
789c63600002fbff0c0c56ab19182ca381581a4283f82071200000696505c36a
437f230000000049454e44ae426082
"""),
  'tbgn3p08': _dehex("""
89504e470d0a1a0a0000000d494844520000002000000020080300000044a48a
c60000000467414d41000186a031e8965f00000207504c54457f7f7fafafafab
abab110000222200737300999999510d00444400959500959595e6e600919191
8d8d8d620d00898989666600b7b700911600000000730d007373736f6f6faaaa
006b6b6b676767c41a00cccc0000f30000ef00d51e0055555567670000dd0051
515100d1004d4d4de61e0038380000b700160d0d00ab00560d00090900009500
009100008d003333332f2f2f2f2b2f2b2b000077007c7c001a05002b27000073
002b2b2b006f00bb1600272727780d002323230055004d4d00cc1e00004d00cc
1a000d00003c09006f6f00002f003811271111110d0d0d55554d090909001100
4d0900050505000d00e2e200000900000500626200a6a6a6a2a2a29e9e9e8484
00fb00fbd5d500801100800d00ea00ea555500a6a600e600e6f7f700e200e233
0500888888d900d9848484c01a007777003c3c05c8c8008080804409007c7c7c
bb00bbaa00aaa600a61e09056262629e009e9a009af322005e5e5e05050000ee
005a5a5adddd00a616008d008d00e20016050027270088110078780000c40078
00787300736f006f44444400aa00c81e004040406600663c3c3c090000550055
1a1a00343434d91e000084004d004d007c004500453c3c00ea1e00222222113c
113300331e1e1efb22001a1a1a004400afaf00270027003c001616161e001e0d
160d2f2f00808000001e00d1d1001100110d000db7b7b7090009050005b3b3b3
6d34c4230000000174524e530040e6d86600000001624b474402660b7c640000
01f249444154789c6360c0048c8c58049100575f215ee92e6161ef109cd2a15e
4b9645ce5d2c8f433aa4c24f3cbd4c98833b2314ab74a186f094b9c2c27571d2
6a2a58e4253c5cda8559057a392363854db4d9d0641973660b0b0bb76bb16656
06970997256877a07a95c75a1804b2fbcd128c80b482a0b0300f8a824276a9a8
ec6e61612b3e57ee06fbf0009619d5fac846ac5c60ed20e754921625a2daadc6
1967e29e97d2239c8aec7e61fdeca9cecebef54eb36c848517164514af16169e
866444b2b0b7b55534c815cc2ec22d89cd1353800a8473100a4485852d924a6a
412adc74e7ad1016ceed043267238c901716f633a812022998a4072267c4af02
92127005c0f811b62830054935ce017b38bf0948cc5c09955f030a24617d9d46
63371fd940b0827931cbfdf4956076ac018b592f72d45594a9b1f307f3261b1a
084bc2ad50018b1900719ba6ba4ca325d0427d3f6161449486f981144cf3100e
2a5f2a1ce8683e4ddf1b64275240c8438d98af0c729bbe07982b8a1c94201dc2
b3174c9820bcc06201585ad81b25b64a2146384e3798290c05ad280a18c0a62e
e898260c07fca80a24c076cc864b777131a00190cdfa3069035eccbc038c30e1
3e88b46d16b6acc5380d6ac202511c392f4b789aa7b0b08718765990111606c2
9e854c38e5191878fbe471e749b0112bb18902008dc473b2b2e8e72700000000
49454e44ae426082
"""),
  'Tp2n3p08': _dehex("""
89504e470d0a1a0a0000000d494844520000002000000020080300000044a48a
c60000000467414d41000186a031e8965f00000300504c544502ffff80ff05ff
7f0703ff7f0180ff04ff00ffff06ff000880ff05ff7f07ffff06ff000804ff00
0180ff02ffff03ff7f02ffff80ff0503ff7f0180ffff0008ff7f0704ff00ffff
06ff000802ffffff7f0704ff0003ff7fffff0680ff050180ff04ff000180ffff
0008ffff0603ff7f80ff05ff7f0702ffffff000880ff05ffff0603ff7f02ffff
ff7f070180ff04ff00ffff06ff000880ff050180ffff7f0702ffff04ff0003ff
7fff7f0704ff0003ff7f0180ffffff06ff000880ff0502ffffffff0603ff7fff
7f0702ffff04ff000180ff80ff05ff0008ff7f07ffff0680ff0504ff00ff0008
0180ff03ff7f02ffff02ffffffff0604ff0003ff7f0180ffff000880ff05ff7f
0780ff05ff00080180ff02ffffff7f0703ff7fffff0604ff00ff7f07ff0008ff
ff0680ff0504ff0002ffff0180ff03ff7fff0008ffff0680ff0504ff000180ff
02ffff03ff7fff7f070180ff02ffff04ff00ffff06ff0008ff7f0780ff0503ff
7fffff06ff0008ff7f0780ff0502ffff03ff7f0180ff04ff0002ffffff7f07ff
ff0604ff0003ff7fff00080180ff80ff05ffff0603ff7f0180ffff000804ff00
80ff0502ffffff7f0780ff05ffff0604ff000180ffff000802ffffff7f0703ff
7fff0008ff7f070180ff03ff7f02ffff80ff05ffff0604ff00ff0008ffff0602
ffff0180ff04ff0003ff7f80ff05ff7f070180ff04ff00ff7f0780ff0502ffff
ff000803ff7fffff0602ffffff7f07ffff0680ff05ff000804ff0003ff7f0180
ff02ffff0180ffff7f0703ff7fff000804ff0080ff05ffff0602ffff04ff00ff
ff0603ff7fff7f070180ff80ff05ff000803ff7f0180ffff7f0702ffffff0008
04ff00ffff0680ff0503ff7f0180ff04ff0080ff05ffff06ff000802ffffff7f
0780ff05ff0008ff7f070180ff03ff7f04ff0002ffffffff0604ff00ff7f07ff
000880ff05ffff060180ff02ffff03ff7f80ff05ffff0602ffff0180ff03ff7f
04ff00ff7f07ff00080180ffff000880ff0502ffff04ff00ff7f0703ff7fffff
06ff0008ffff0604ff00ff7f0780ff0502ffff03ff7f0180ffdeb83387000000
f874524e53000000000000000008080808080808081010101010101010181818
1818181818202020202020202029292929292929293131313131313131393939
393939393941414141414141414a4a4a4a4a4a4a4a52525252525252525a5a5a
5a5a5a5a5a62626262626262626a6a6a6a6a6a6a6a73737373737373737b7b7b
7b7b7b7b7b83838383838383838b8b8b8b8b8b8b8b94949494949494949c9c9c
9c9c9c9c9ca4a4a4a4a4a4a4a4acacacacacacacacb4b4b4b4b4b4b4b4bdbdbd
bdbdbdbdbdc5c5c5c5c5c5c5c5cdcdcdcdcdcdcdcdd5d5d5d5d5d5d5d5dedede
dededededee6e6e6e6e6e6e6e6eeeeeeeeeeeeeeeef6f6f6f6f6f6f6f6b98ac5
ca0000012c49444154789c6360e7169150d230b475f7098d4ccc28a96ced9e32
63c1da2d7b8e9fb97af3d1fb8f3f18e8a0808953544a4dd7c4c2c9233c2621bf
b4aab17fdacce5ab36ee3a72eafaad87efbefea68702362e7159652d031b07cf
c0b8a4cce28aa68e89f316aedfb4ffd0b92bf79fbcfcfe931e0a183904e55435
8decdcbcc22292b3caaadb7b27cc5db67af3be63e72fdf78fce2d31f7a2860e5
119356d037b374f10e8a4fc92eaa6fee99347fc9caad7b0f9ebd74f7c1db2fbf
e8a180995f484645dbdccad12f38363dafbcb6a573faeca5ebb6ed3e7ce2c29d
e76fbefda38702063e0149751d537b67ff80e8d4dcc29a86bea97316add9b0e3
c0e96bf79ebdfafc971e0a587885e515f58cad5d7d43a2d2720aeadaba26cf5a
bc62fbcea3272fde7efafac37f3a28000087c0fe101bc2f85f0000000049454e
44ae426082
"""),
  'tbbn1g04': _dehex("""
89504e470d0a1a0a0000000d494844520000002000000020040000000093e1c8
290000000467414d41000186a031e8965f0000000274524e530007e8f7589b00
000002624b47440000aa8d23320000013e49444154789c55d1cd4b024118c7f1
efbe6419045b6a48a72d352808b435284f9187ae9b098627a1573a19945beba5
e8129e8222af11d81e3a4545742de8ef6af6d5762e0fbf0fc33c33f36085cb76
bc4204778771b867260683ee57e13f0c922df5c719c2b3b6c6c25b2382cea4b9
9f7d4f244370746ac71f4ca88e0f173a6496749af47de8e44ba8f3bf9bdfa98a
0faf857a7dd95c7dc8d7c67c782c99727997f41eb2e3c1e554152465bb00fe8e
b692d190b718d159f4c0a45c4435915a243c58a7a4312a7a57913f05747594c6
46169866c57101e4d4ce4d511423119c419183a3530cc63db88559ae28e7342a
1e9c8122b71139b8872d6e913153224bc1f35b60e4445bd4004e20ed6682c759
1d9873b3da0fbf50137dc5c9bde84fdb2ec8bde1189e0448b63584735993c209
7a601bd2710caceba6158797285b7f2084a2f82c57c01a0000000049454e44ae
426082
"""),
  'tbrn2c08': _dehex("""
89504e470d0a1a0a0000000d4948445200000020000000200802000000fc18ed
a30000000467414d41000186a031e8965f0000000674524e53007f007f007f8a
33334f00000006624b474400ff0000000033277cf3000004d649444154789cad
965f68537714c73fd912d640235e692f34d0406fa0c1663481045ab060065514
56660a295831607df0a1488715167060840a1614e6431e9cb34fd2c00a762c85
f6a10f816650c13b0cf40612e1822ddc4863bd628a8924d23d6464f9d3665dd9
f7e977ce3dbff3cd3939bfdfef6bb87dfb364782dbed065ebe7cd93acc78b4ec
a228debd7bb7bfbfbfbbbbfb7f261045311a8d261209405194274f9ea4d3e916
f15f1c3eb5dd6e4fa5fecce526239184a2b0b8486f6f617171b1f5ae4311381c
8e57af5e5dbd7a351088150a78bd389d44222c2f93cdfe66b7db8f4ee07038b6
b6b6bebf766d7e7e7e60a06432313b4ba984c3c1c4049a46b95c5a58583822c1
dbb76f27272733d1b9df853c3030c0f232562b9108cf9eb1b888d7cbf030abab
31abd5fa1f08dc6ef7e7cf9f1f3f7e1c8944745d4f1400c62c001313acad21cb
b8dd2c2c603271eb1640341aad4c6d331aa7e8c48913a150a861307ecc11e964
74899919bc5e14e56fffc404f1388502f178dceff7ef4bf0a5cfe7abb533998c
e5f9ea2f1dd88c180d64cb94412df3dd57e83a6b3b3c7a84c98420100c72fd3a
636348bae726379fe69e8e8d8dbd79f3a6558b0607079796965256479b918085
7b02db12712b6181950233023f3f647494ee6e2e5ea45864cce5b8a7fe3acffc
3aebb22c2bd5d20e22d0757d7b7bbbbdbd3d94a313bed1b0aa3cd069838b163a
8d4c59585f677292d0b84d9a995bd337def3fe6bbe5e6001989b9b6bfe27ea08
36373781542ab56573248b4c5bc843ac4048c7ab21aa24ca00534c25482828a3
8c9ee67475bbaaaab22cb722c8e57240a150301a8d219de94e44534d7d90e885
87acb0e2c4f9800731629b6c5ee14a35a6b9887d2a0032994cb9cf15dbe59650
ff7b46a04c9a749e7cc5112214266cc65c31354d5b5d5d3d90209bcd5616a552
a95c2e87f2a659bd9ee01c2cd73964e438f129a6aa9e582c363838b80f81d7eb
5555b56a2a8ad2d9d7affd0409f8015c208013fea00177b873831b0282c964f2
783c1e8fa7582cee5f81a669b5e6eeeeaee58e8559b0c233d8843c7c0b963a82
34e94b5cb2396d7d7d7db22c8ba258fb0afd43f0e2c58b919191ba9de9b4d425
118329b0c3323c8709d02041b52b4ea7f39de75d2a934a2693c0a953a76a93d4
5d157ebf7f6565a5542a553df97c5e10045dd731c130b86113cc300cbd489224
08422a952a140a95788fc763b1d41558d7a2d7af5f5fb870a1d6a3aaaacd6603
18802da84c59015bd2e6897b745d9765b99a1df0f97c0daf74e36deaf7fbcd66
73ad2797cb89a2c839880188a2e8743a8bc5a22ccbba5e376466b3b9bdbdbd21
6123413a9d0e0402b51e4dd3bababa788eb022b85caeb6b6364551b6b7b76942
43f7f727007a7a7a04a1ee8065b3595fde2768423299ac1ec6669c3973e65004
c0f8f878ad69341a33994ced2969c0d0d0502412f9f8f163f3a7fd654b474787
288ad53e74757535df6215b85cae60302849d2410aecc037f9f2e5cbd5b5c160
680eb0dbede170381c0e7ff8f0a185be3b906068684892a4ca7a6f6faff69328
8ad3d3d3f7efdfdfdbdbfb57e96868a14d0d0643381c96242997cbe5f3794010
84603078fcf8f1d6496bd14a3aba5c2ea7d369341a5555b5582c8140e0fcf9f3
1b1b1b87cf4eeb0a8063c78e45a3d19e9e1ebfdfdf5a831e844655d18093274f
9e3d7bf6d3a74f3b3b3b47c80efc05ff7af28fefb70d9b0000000049454e44ae
426082
"""),
  'basn6a16': _dehex("""
89504e470d0a1a0a0000000d494844520000002000000020100600000023eaa6
b70000000467414d41000186a031e8965f00000d2249444154789cdd995f6c1c
d775c67ff38fb34b724d2ee55a8e4b04a0ac87049100cab4dbd8c6528902cb4d
10881620592e52d4325ac0905bc98a94025e71fd622cb5065ac98a0c283050c0
728a00b6e542a1d126885cd3298928891d9a0444037e904434951d4b90b84b2f
c9dde1fcebc33977a95555348f411e16dfce9d3b77ee77eebde77ce78c95a669
0ad07c17009a13edd898b87dfb1fcb7d2b4d1bff217f33df80deb1e6267df0ff
c1e6e6dfafdf1f5a7fd30f9aef66b6d546dd355bf02c40662e3307f9725a96c6
744c3031f83782f171c148dbc3bf1774f5dad1e79d6f095a3f54d4fbec5234ef
d9a2f8d73afe4f14f57ef4f42def7b44f19060f06b45bddf1c5534d77fd922be
2973a15a82e648661c6e3240aa3612ead952b604bde57458894f29deaf133bac
13d2766f5227a4a3b8cf08da7adfd6fbd6bd8a4fe9dbb43d35e3dfa3f844fbf8
9119bf4f7144094fb56333abf8a86063ca106f94b3a3b512343765e60082097f
1bb86ba72439a653519b09f5cee1ce61c897d37eedf5553580ae60f4af8af33a
b14fd400b6a0f34535c0434afc0b3a9f07147527a5fa7ca218ff56c74d74dc3f
155cfd3325fc278acf2ae1cb4a539f5f9937c457263b0bd51234c732a300cdd1
cc1840f0aaff54db0e4874ed5a9b5d6d27d4bb36746d80de72baa877ff4b275a
d7895ed1897ea4139b5143fcbb1a62560da1ed9662aaed895ec78a91c18795b8
5e07ab4af8ba128e95e682e0728bf8f2e5ae815a091a53d902ac1920d8e05f06
589de8d8d66680789f4e454fb9d9ec66cd857af796ee2d902fa73fd5bba775a2
153580ae44705ed0d37647d15697cb8f14bfa3e3e8fdf8031d47af571503357c
f30d25acedcbbf135c9a35c49766ba07ab255859e8ec03684e66860182dff8f7
0304bff6ff1c20fc81b7afdd00a71475539a536e36bb5973a19e3b923b02bde5
e4efd4003ac170eb2d13fe274157afedbd82d6fb3a9a1e85e4551d47cf7078f8
9671fe4289ebf5f2bf08d63f37c4eb4773c55a0996efeefa0ca011671d8060ca
2f0004c7fcc300e166ef0240f825efe3361f106d57d423d0723f7acacd66376b
2ed47b7a7a7a205f4ef4ac4691e0aad9aa0d41cf13741c3580a506487574ddca
61a8c403c1863ebfbcac3475168b2de28b8b3d77544bb05ce92a02aceced3c0d
d0cc65ea371b201cf1c601c24dde1c4078cedbdeb60322f50126a019bf6edc9b
39e566b39b3517eaf97c3e0fbde5e4491d45bd74537145d155b476aa0176e868
c6abebf30dbd5e525c54ac8e18e2d56abeb756827a3d970358a97416019a6f64
f60004fdfe1580d5c98e618070cc1b05887eee7e0d209a70db7d8063029889b4
c620ead78d7b33a7dc6c76b3e6427ddddbebde867c393aa7845e5403e8ca794a
d0d6fb897af5f03525fe5782f5e7046bdaef468bf88d1debc6ab25583cd17310
6079b9ab0ba059c914018245bf076075b5a303200c3c1f209a733701444fbbaf
00c4134ebb016c5d0b23614c243701cdf875e3decce9349bddacb9505fbf7dfd
76e82d87736a00f5d2b5ffd4b7dce2719a4d25ae717ee153c1abef18e257cfad
7fa45682da48ef38c052b53b0fd06864b300c151ff08c0ea431de701a287dd5f
004497dc7b01a253ee3e80b8c7f91c20f967fb6fdb7c80ada7d8683723614c24
3701cdf875e3decc29379bddacb950ef3fd47f08f2e5a61ea4aa2a3eb757cd55
13345efcfa59c12b2f19e2578ef77fb75a82854ffbee01a83f977b11a031931d
040802df07082b5e11207cc17b1e209a770700e2df0a83e409fb7580f827c230
99b06fd901fb058d6835dacd481813c94d40337eddb83773cacd66376b2ed437
bebcf165e82d2f4e4beb7f3fa6e652c2d7ee10bc78c010bfb87fe3c95a09ae9f
bd732740bd2fb700d0f865f64180e059ff044018ca0ca28a5b04883f701e0088
bfec7c0c909cb71f0448c6ec518074b375012079d9dedf66004bcfbc51eb2dd1
aadacd481813c94d40337eddb83773cacd66376b2ed487868686205fbe7c49ef
5605a73f34c4a7a787eeab96e0da81bb4e022c15ba27019a5b339300e16bf286
a8eae601e25866907cdf3e0890acb36f00245fb57f05904e59c300e92561946e
b2e600d209ab7d07f04d458dfb46ad1bd16ab49b913026929b8066fcba716fe6
949bcd6ed65ca8ef7e7cf7e3d05b7e7c8f217ee6cdddbb6a25a856f37980e0c7
fe4e80a82623c48193014846ec7180f4acf518409aca0cd28a5504e03b32c374
de1a00608a0240faaa327a4b19fe946fb6f90054dbb5f2333d022db56eb4966a
3723614c243701cdf8f556bea8a7dc6c76b3e66bd46584ddbbcebc0990cf4b0f
ff4070520c282338a7e26700ec725202b01e4bcf0258963c6f1d4d8f0030cb20
805549c520930c03584fa522b676f11600ffc03fde3e1b3489a9c9054c9aa23b
c08856a3dd8c843191dc0434e3d78d7b33a75c36fb993761f7ae5a69f72ef97f
e6ad336fed7e1c60e8bee96980bbdebbb60da07b7069062033d9dc0ae03d296f
70ab511ec071640676252902d833c916007b3e1900b0a6d2028035968e025861
ea01581369fb11488c34d18cbc95989afccca42baad65ba2d5683723614c24d7
8066fcbab8b7e96918baaf5aaa56219f975fb50a43f7c9bde90fa73f1c1a02d8
78f2e27e803b77ca08b90519315b6fe400fc1392097a9eccc0ad444500e70199
a1331f0f00d8934901c07e5d526ceb87c2d07e2579badd005a2b31a5089391b7
1253358049535a6add8856dd0146c298482e01ede27ed878b256ba7600ee3a09
c18fc1df09fe01084ec25defc1b56db0f1a4f4bd78e0e2818d2f0334e7330300
7df7c888b917e50dd9c1c60c80efcb0cbc63e1f700bce7c31700dccbd1060027
8add9b0de06c8e2f00d84962b7d7030e2a61538331b98051f92631bd253f336a
dd8856a3dd44c25c390efddfad96ae9f853b77c25201ba27c533b8bdf28b6ad0
3d084b33d2e7fa59099e9901b8f2d29597fa0f01848f78e70082117f1ca07b76
6910209b9519f895a008d031bbba05c09d8f06005c5b18b8fba25300cea6780e
c03e911c6ccf06d507b48a4fa606634a114609de929f9934c5a87511ad57cfc1
fa476aa5854fa1ef1e3910b905686e85cc24c40138198915f133d2d6dc2a7dea
7df2ccc2a752faf2cec1d577aebeb37e3b4034eeee0008dff3be0e6b923773b4
7904c0ef9119767cb4fa1500ef1361e08e452500f71561e84cc4ed3e20fab6a2
c905f40cb76a3026bf3319b91ac2e46792a6dcd801ebc6aba5da08f48ecb81c8
bd088d5f42f6417191de93908c803d0e76199292b485af41b60e8d9c3c537f0e
8211f0c7211a077707dc18b931b2ee6d80a4d7ae024491ebc24d4a708ff70680
7f25e807e8785f1878e322d6ddaf453f0770ff2dfa769b01423dbbad72a391b6
5a7c3235985629423372494cab55c8f7d64a8b27a0e7202c55a13b0f8d19c80e
4ae9ca3f015115dc3ca467c17a4c7ee95970ab10e5a54ff0ac3cd39881ee5958
1a84f03df0be0e492fd855a8d6aa35d10b4962dbb0a604a3d3ee5e80a8eee600
a24977f8660378bf0bbf00e01d0a8fb7f980f04b8aa6ce6aca8d5a7533c52753
839152c4e222f4dc512dd5eb90cbc981e8ea12cf90cd8a8bf47d89159e2741d3
7124f65b96fcd254dae258fa84a13c13043246a32129574787e49eae2b49b86d
c3e2e78b9ff7f4002415bb08907c66df0d103b4e0c104db90500ff70700c203a
ee1e82dba4c3e16e256c0acca6ceaae9afd1f612d7eb472157ac95962bd05594
7dd1598466053245088e827f44628657942a825b84e4fb601f84b4025611aca3
901e01bb024911dc0a4445f08e41f83df02b10142173149ab71baf027611ea95
7a257704201d14cd9af4d90b00f194530088cb4e09c0df1c5c0088f7393f6833
c0aa3ac156655de3bca9b34ab9716906ba07aba5e5bba1eb3358d90b9da7c533
64f6888bf47b60f521e8380fe10be03d2feac17900927560df40f4e48f805960
50328d648bf4893f9067c217a0631656b7c898c122847bc07b03a2d3e0ee85e4
33b0ef867450c4fad2ecd26cf7168074c0ba0c904cdac300c9cfec4701924df6
1cdca61e10685c6f7d52d0caba1498972f43d740adb4b2009d7d7220b20e3473
90a943d00ffe959bb6eac3e0fe42ea49ee00c45f06e76329b1dabf127d690d80
5581b408f63c2403e0cc433c00ee658836803b0fd100747c04ab5f917704fd10
d5c1cd41ec801343d207f602a403605d86e5f9e5f9ae0d00e994556833806685
c931fb709b0f08b4e869bea5c827859549e82c544b8d29c816a0390999613920
7e610d5727a16318c2003c1fa24be0de2b32caf92224e7c17e5004b6350c4c01
05601218066b0ad28224e149019c086257ca315102de2712903bde97b8144d82
3b2c6ac52d403c054e019249b087f53d0558995a99ea946c70cc927458b3c1ff
550f30050df988d4284376b4566a8e416654cc921985e037e0df0fc131f00f4b
acf0c6211c036f14a239703741740adc7da227edd7e56b833d0ae92549b4d357
25dfb49ed2ff63908e6adf27d6d0dda7638d4154d2778daca17f58e61297c129
41f233b01f5dc3740cac51688c35c6b22580f48224fee9b83502569a66b629f1
09f3713473413e2666e7fe6f6c6efefdfafda1f56f6e06f93496d9d67cb7366a
9964b6f92e64b689196ec6c604646fd3fe4771ff1bf03f65d8ecc3addbb5f300
00000049454e44ae426082
"""),
}


def test_suite(options, args):
    """
    Create a PNG test image and write the file to stdout.
    """

    # Below is a big stack of test image generators.
    # They're all really tiny, so PEP 8 rules are suspended.

    def test_gradient_horizontal_lr(x, y):
        return x

    def test_gradient_horizontal_rl(x, y):
        return 1 - x

    def test_gradient_vertical_tb(x, y):
        return y

    def test_gradient_vertical_bt(x, y):
        return 1 - y

    def test_radial_tl(x, y):
        return max(1 - math.sqrt(x * x + y * y), 0.0)

    def test_radial_center(x, y):
        return test_radial_tl(x - 0.5, y - 0.5)

    def test_radial_tr(x, y):
        return test_radial_tl(1 - x, y)

    def test_radial_bl(x, y):
        return test_radial_tl(x, 1 - y)

    def test_radial_br(x, y):
        return test_radial_tl(1 - x, 1 - y)

    def test_stripe(x, n):
        return float(int(x * n) & 1)

    def test_stripe_h_2(x, y):
        return test_stripe(x, 2)

    def test_stripe_h_4(x, y):
        return test_stripe(x, 4)

    def test_stripe_h_10(x, y):
        return test_stripe(x, 10)

    def test_stripe_v_2(x, y):
        return test_stripe(y, 2)

    def test_stripe_v_4(x, y):
        return test_stripe(y, 4)

    def test_stripe_v_10(x, y):
        return test_stripe(y, 10)

    def test_stripe_lr_10(x, y):
        return test_stripe(x + y, 10)

    def test_stripe_rl_10(x, y):
        return test_stripe(1 + x - y, 10)

    def test_checker(x, y, n):
        return float((int(x * n) & 1) ^ (int(y * n) & 1))

    def test_checker_8(x, y):
        return test_checker(x, y, 8)

    def test_checker_15(x, y):
        return test_checker(x, y, 15)

    def test_zero(x, y):
        return 0

    def test_one(x, y):
        return 1

    test_patterns = {
        'GLR': test_gradient_horizontal_lr,
        'GRL': test_gradient_horizontal_rl,
        'GTB': test_gradient_vertical_tb,
        'GBT': test_gradient_vertical_bt,
        'RTL': test_radial_tl,
        'RTR': test_radial_tr,
        'RBL': test_radial_bl,
        'RBR': test_radial_br,
        'RCTR': test_radial_center,
        'HS2': test_stripe_h_2,
        'HS4': test_stripe_h_4,
        'HS10': test_stripe_h_10,
        'VS2': test_stripe_v_2,
        'VS4': test_stripe_v_4,
        'VS10': test_stripe_v_10,
        'LRS': test_stripe_lr_10,
        'RLS': test_stripe_rl_10,
        'CK8': test_checker_8,
        'CK15': test_checker_15,
        'ZERO': test_zero,
        'ONE': test_one,
        }

    def test_pattern(width, height, bitdepth, pattern):
        """Create a single plane (monochrome) test pattern.  Returns a
        flat row flat pixel array.
        """

        maxval = 2 ** bitdepth - 1
        if maxval > 255:
            a = array('H')
        else:
            a = array('B')
        fw = float(width)
        fh = float(height)
        pfun = test_patterns[pattern]
        for y in range(height):
            fy = float(y) / fh
            for x in range(width):
                a.append(int(round(pfun(float(x) / fw, fy) * maxval)))
        return a

    def test_rgba(size=256, bitdepth=8,
                    red="GTB", green="GLR", blue="RTL", alpha=None):
        """
        Create a test image.  Each channel is generated from the
        specified pattern; any channel apart from red can be set to
        None, which will cause it not to be in the image.  It
        is possible to create all PNG channel types (L, RGB, LA, RGBA),
        as well as non PNG channel types (RGA, and so on).
        """

        i = test_pattern(size, size, bitdepth, red)
        psize = 1
        for channel in (green, blue, alpha):
            if channel:
                c = test_pattern(size, size, bitdepth, channel)
                i = interleave_planes(i, c, psize, 1)
                psize += 1
        return i

    def pngsuite_image(name):
        """
        Create a test image by reading an internal copy of the files
        from the PngSuite.  Returned in flat row flat pixel format.
        """

        if name not in _pngsuite:
            raise NotImplementedError("cannot find PngSuite file %s (use -L for a list)" % name)
        r = Reader(bytes=_pngsuite[name])
        w, h, pixels, meta = r.asDirect()
        assert w == h
        # LAn for n < 8 is a special case for which we need to rescale
        # the data.
        if meta['greyscale'] and meta['alpha'] and meta['bitdepth'] < 8:
            factor = 255 // (2 ** meta['bitdepth'] - 1)

            def rescale(data):
                for row in data:
                    yield map(factor.__mul__, row)
            pixels = rescale(pixels)
            meta['bitdepth'] = 8
        arraycode = 'BH'[meta['bitdepth'] > 8]
        return w, array(arraycode, itertools.chain(*pixels)), meta

    # The body of test_suite()
    size = 256
    if options.test_size:
        size = options.test_size
    options.bitdepth = options.test_depth
    options.greyscale = bool(options.test_black)

    kwargs = {}
    if options.test_red:
        kwargs["red"] = options.test_red
    if options.test_green:
        kwargs["green"] = options.test_green
    if options.test_blue:
        kwargs["blue"] = options.test_blue
    if options.test_alpha:
        kwargs["alpha"] = options.test_alpha
    if options.greyscale:
        if options.test_red or options.test_green or options.test_blue:
            raise ValueError("cannot specify colours (R, G, B) when greyscale image (black channel, K) is specified")
        kwargs["red"] = options.test_black
        kwargs["green"] = None
        kwargs["blue"] = None
    options.alpha = bool(options.test_alpha)
    if not args:
        pixels = test_rgba(size, options.bitdepth, **kwargs)
    else:
        size, pixels, meta = pngsuite_image(args[0])
        for k in ['bitdepth', 'alpha', 'greyscale']:
            setattr(options, k, meta[k])

    writer = Writer(size, size,
                    bitdepth=options.bitdepth,
                    transparent=options.transparent,
                    background=options.background,
                    gamma=options.gamma,
                    greyscale=options.greyscale,
                    alpha=options.alpha,
                    compression=options.compression,
                    interlace=options.interlace)
    writer.write_array(sys.stdout, pixels)


def read_pam_header(infile):
    """
    Read (the rest of a) PAM header.  `infile` should be positioned
    immediately after the initial 'P7' line (at the beginning of the
    second line).  Returns are as for `read_pnm_header`.
    """

    # Unlike PBM, PGM, and PPM, we can read the header a line at a time.
    header = dict()
    while True:
        l = infile.readline().strip()
        if l == 'ENDHDR':
            break
        if l == '':
            raise EOFError('PAM ended prematurely')
        if l[0] == '#':
            continue
        l = l.split(None, 1)
        if l[0] not in header:
            header[l[0]] = l[1]
        else:
            header[l[0]] += ' ' + l[1]

    if ('WIDTH' not in header or
        'HEIGHT' not in header or
        'DEPTH' not in header or
        'MAXVAL' not in header):
        raise Error('PAM file must specify WIDTH, HEIGHT, DEPTH, and MAXVAL')
    width = int(header['WIDTH'])
    height = int(header['HEIGHT'])
    depth = int(header['DEPTH'])
    maxval = int(header['MAXVAL'])
    if (width <= 0 or
        height <= 0 or
        depth <= 0 or
        maxval <= 0):
        raise Error(
          'WIDTH, HEIGHT, DEPTH, MAXVAL must all be positive integers')
    return 'P7', width, height, depth, maxval


def read_pnm_header(infile, supported=('P5', 'P6')):
    """
    Read a PNM header, returning (format,width,height,depth,maxval).
    `width` and `height` are in pixels.  `depth` is the number of
    channels in the image; for PBM and PGM it is synthesized as 1, for
    PPM as 3; for PAM images it is read from the header.  `maxval` is
    synthesized (as 1) for PBM images.
    """

    # Generally, see http://netpbm.sourceforge.net/doc/ppm.html
    # and http://netpbm.sourceforge.net/doc/pam.html

    # Technically 'P7' must be followed by a newline, so by using
    # rstrip() we are being liberal in what we accept.  I think this
    # is acceptable.
    type = infile.read(3).rstrip()
    if type not in supported:
        raise NotImplementedError('file format %s not supported' % type)
    if type == 'P7':
        # PAM header parsing is completely different.
        return read_pam_header(infile)
    # Expected number of tokens in header (3 for P4, 4 for P6)
    expected = 4
    pbm = ('P1', 'P4')
    if type in pbm:
        expected = 3
    header = [type]

    # We have to read the rest of the header byte by byte because the
    # final whitespace character (immediately following the MAXVAL in
    # the case of P6) may not be a newline.  Of course all PNM files in
    # the wild use a newline at this point, so it's tempting to use
    # readline; but it would be wrong.
    def getc():
        c = infile.read(1)
        if c == '':
            raise Error('premature EOF reading PNM header')
        return c

    c = getc()
    while True:
        # Skip whitespace that precedes a token.
        while c.isspace():
            c = getc()
        # Skip comments.
        while c == '#':
            while c not in '\n\r':
                c = getc()
        if not c.isdigit():
            raise Error('unexpected character %s found in header' % c)
        # According to the specification it is legal to have comments
        # that appear in the middle of a token.
        # This is bonkers; I've never seen it; and it's a bit awkward to
        # code good lexers in Python (no goto).  So we break on such
        # cases.
        token = ''
        while c.isdigit():
            token += c
            c = getc()
        # Slight hack.  All "tokens" are decimal integers, so convert
        # them here.
        header.append(int(token))
        if len(header) == expected:
            break
    # Skip comments (again)
    while c == '#':
        while c not in '\n\r':
            c = getc()
    if not c.isspace():
        raise Error('expected header to end with whitespace, not %s' % c)

    if type in pbm:
        # synthesize a MAXVAL
        header.append(1)
    depth = (1, 3)[type == 'P6']
    return header[0], header[1], header[2], depth, header[3]


def write_pnm(file, width, height, pixels, meta):
    """Write a Netpbm PNM/PAM file."""

    bitdepth = meta['bitdepth']
    maxval = 2 ** bitdepth - 1
    # Rudely, the number of image planes can be used to determine
    # whether we are L (PGM), LA (PAM), RGB (PPM), or RGBA (PAM).
    planes = meta['planes']
    # Can be an assert as long as we assume that pixels and meta came
    # from a PNG file.
    assert planes in (1, 2, 3, 4)
    if planes in (1, 3):
        if 1 == planes:
            # PGM
            # Could generate PBM if maxval is 1, but we don't (for one
            # thing, we'd have to convert the data, not just blat it
            # out).
            fmt = 'P5'
        else:
            # PPM
            fmt = 'P6'
        file.write('%s %d %d %d\n' % (fmt, width, height, maxval))
    if planes in (2, 4):
        # PAM
        # See http://netpbm.sourceforge.net/doc/pam.html
        if 2 == planes:
            tupltype = 'GRAYSCALE_ALPHA'
        else:
            tupltype = 'RGB_ALPHA'
        file.write('P7\nWIDTH %d\nHEIGHT %d\nDEPTH %d\nMAXVAL %d\n'
                   'TUPLTYPE %s\nENDHDR\n' %
                   (width, height, planes, maxval, tupltype))
    # Values per row
    vpr = planes * width
    # struct format
    fmt = '>%d' % vpr
    if maxval > 0xff:
        fmt = fmt + 'H'
    else:
        fmt = fmt + 'B'
    for row in pixels:
        file.write(struct.pack(fmt, *row))
    file.flush()


def color_triple(color):
    """
    Convert a command line colour value to a RGB triple of integers.
    FIXME: Somewhere we need support for greyscale backgrounds etc.
    """
    if color.startswith('#') and len(color) == 4:
        return (int(color[1], 16),
                int(color[2], 16),
                int(color[3], 16))
    if color.startswith('#') and len(color) == 7:
        return (int(color[1:3], 16),
                int(color[3:5], 16),
                int(color[5:7], 16))
    elif color.startswith('#') and len(color) == 13:
        return (int(color[1:5], 16),
                int(color[5:9], 16),
                int(color[9:13], 16))


def _main(argv):
    """
    Run the PNG encoder with options from the command line.
    """

    # Parse command line arguments
    from optparse import OptionParser
    import re
    version = '%prog ' + re.sub(r'( ?\$|URL: |Rev:)', '', __version__)
    parser = OptionParser(version=version)
    parser.set_usage("%prog [options] [imagefile]")
    parser.add_option('-r', '--read-png', default=False,
                      action='store_true',
                      help='Read PNG, write PNM')
    parser.add_option("-i", "--interlace",
                      default=False, action="store_true",
                      help="create an interlaced PNG file (Adam7)")
    parser.add_option("-t", "--transparent",
                      action="store", type="string", metavar="color",
                      help="mark the specified colour (#RRGGBB) as transparent")
    parser.add_option("-b", "--background",
                      action="store", type="string", metavar="color",
                      help="save the specified background colour")
    parser.add_option("-a", "--alpha",
                      action="store", type="string", metavar="pgmfile",
                      help="alpha channel transparency (RGBA)")
    parser.add_option("-g", "--gamma",
                      action="store", type="float", metavar="value",
                      help="save the specified gamma value")
    parser.add_option("-c", "--compression",
                      action="store", type="int", metavar="level",
                      help="zlib compression level (0-9)")
    parser.add_option("-T", "--test",
                      default=False, action="store_true",
                      help="create a test image (a named PngSuite image if an argument is supplied)")
    parser.add_option('-L', '--list',
                      default=False, action='store_true',
                      help="print list of named test images")
    parser.add_option("-R", "--test-red",
                      action="store", type="string", metavar="pattern",
                      help="test pattern for the red image layer")
    parser.add_option("-G", "--test-green",
                      action="store", type="string", metavar="pattern",
                      help="test pattern for the green image layer")
    parser.add_option("-B", "--test-blue",
                      action="store", type="string", metavar="pattern",
                      help="test pattern for the blue image layer")
    parser.add_option("-A", "--test-alpha",
                      action="store", type="string", metavar="pattern",
                      help="test pattern for the alpha image layer")
    parser.add_option("-K", "--test-black",
                      action="store", type="string", metavar="pattern",
                      help="test pattern for greyscale image")
    parser.add_option("-d", "--test-depth",
                      default=8, action="store", type="int",
                      metavar='NBITS',
                      help="create test PNGs that are NBITS bits per channel")
    parser.add_option("-S", "--test-size",
                      action="store", type="int", metavar="size",
                      help="width and height of the test image")
    (options, args) = parser.parse_args(args=argv[1:])

    # Convert options
    if options.transparent is not None:
        options.transparent = color_triple(options.transparent)
    if options.background is not None:
        options.background = color_triple(options.background)

    if options.list:
        names = list(_pngsuite)
        names.sort()
        for name in names:
            print name
        return

    # Run regression tests
    if options.test:
        return test_suite(options, args)

    # Prepare input and output files
    if len(args) == 0:
        infilename = '-'
        infile = sys.stdin
    elif len(args) == 1:
        infilename = args[0]
        infile = open(infilename, 'rb')
    else:
        parser.error("more than one input file")
    outfile = sys.stdout

    if options.read_png:
        # Encode PNG to PPM
        png = Reader(file=infile)
        width, height, pixels, meta = png.asDirect()
        write_pnm(outfile, width, height, pixels, meta)
    else:
        # Encode PNM to PNG
        format, width, height, depth, maxval = \
          read_pnm_header(infile, ('P5', 'P6', 'P7'))
        # When it comes to the variety of input formats, we do something
        # rather rude.  Observe that L, LA, RGB, RGBA are the 4 colour
        # types supported by PNG and that they correspond to 1, 2, 3, 4
        # channels respectively.  So we use the number of channels in
        # the source image to determine which one we have.  We do not
        # care about TUPLTYPE.
        greyscale = depth <= 2
        pamalpha = depth in (2, 4)
        supported = map(lambda x: 2 ** x - 1, range(1, 17))
        try:
            mi = supported.index(maxval)
        except ValueError:
            raise NotImplementedError(
              'your maxval (%s) not in supported list %s' %
              (maxval, str(supported)))
        bitdepth = mi + 1
        writer = Writer(width, height,
                        greyscale=greyscale,
                        bitdepth=bitdepth,
                        interlace=options.interlace,
                        transparent=options.transparent,
                        background=options.background,
                        alpha=bool(pamalpha or options.alpha),
                        gamma=options.gamma,
                        compression=options.compression)
        if options.alpha:
            pgmfile = open(options.alpha, 'rb')
            format, awidth, aheight, adepth, amaxval = \
              read_pnm_header(pgmfile, 'P5')
            if amaxval != '255':
                raise NotImplementedError(
                  'maxval %s not supported for alpha channel' % amaxval)
            if (awidth, aheight) != (width, height):
                raise ValueError("alpha channel image size mismatch"
                                 " (%s has %sx%s but %s has %sx%s)"
                                 % (infilename, width, height,
                                    options.alpha, awidth, aheight))
            writer.convert_ppm_and_pgm(infile, pgmfile, outfile)
        else:
            writer.convert_pnm(infile, outfile)


if __name__ == '__main__':
    try:
        _main(sys.argv)
    except Error, e:
        print >> sys.stderr, e

########NEW FILE########
__FILENAME__ = release
import os.path
import subprocess
import directories

def get_version():
    """
    Loads the build version from the bundled version file, if available.
    """
    if not os.path.exists(os.path.join(directories.dataDir, 'RELEASE-VERSION')):
        try:
            return subprocess.check_output('git describe --tags --match=*.*.*'.split()).strip()
        except:
            return 'unknown'

    fin = open(os.path.join(directories.dataDir, 'RELEASE-VERSION'), 'rb')
    v = fin.read().strip()
    fin.close()

    return v

def get_commit():
    """
    Loads the git commit ID from the bundled version file, if available.
    """
    if not os.path.exists(os.path.join(directories.dataDir, 'GIT-COMMIT')):
        try:
            return subprocess.check_output('git rev-parse HEAD'.split()).strip()
        except:
            return 'unknown'

    fin = open(os.path.join(directories.dataDir, 'GIT-COMMIT'), 'rb')
    v = fin.read().strip()
    fin.close()

    return v

release = get_version()
commit = get_commit()

########NEW FILE########
__FILENAME__ = renderer
"""Copyright (c) 2010-2012 David Rio Vierra

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE."""


"""
renderer.py

What is going on in this file?

Here is an attempt to show the relationships between classes and
their responsibilities

MCRenderer:
    has "position", "origin", optionally "viewFrustum"
    Loads chunks near position+origin, draws chunks offset by origin
    Calls visible on viewFrustum to exclude chunks


    (+) ChunkRenderer
        Has "chunkPosition", "invalidLayers", "lists"
        One per chunk and detail level.
        Creates display lists from BlockRenderers

        (*) BlockRenderer
            Has "vertexArrays"
            One per block type, plus one for low detail and one for Entity

"""

from collections import defaultdict, deque
from datetime import datetime, timedelta
from depths import DepthOffset
from glutils import gl, Texture
import logging
import numpy
from OpenGL import GL
import pymclevel
import sys
#import time


def chunkMarkers(chunkSet):
    """ Returns a mapping { size: [position, ...] } for different powers of 2
    as size.
    """

    sizedChunks = defaultdict(list)
    size = 1

    def all4(cx, cz):
        cx &= ~size
        cz &= ~size
        return [(cx, cz), (cx + size, cz), (cx + size, cz + size), (cx, cz + size)]

    # lastsize = 6
    size = 1
    while True:
        nextsize = size << 1
        chunkSet = set(chunkSet)
        while len(chunkSet):
            cx, cz = chunkSet.pop()
            chunkSet.add((cx, cz))
            o = all4(cx, cz)
            others = set(o).intersection(chunkSet)
            if len(others) == 4:
                sizedChunks[nextsize].append(o[0])
                for c in others:
                    chunkSet.discard(c)
            else:
                for c in others:
                    sizedChunks[size].append(c)
                    chunkSet.discard(c)

        if len(sizedChunks[nextsize]):
            chunkSet = set(sizedChunks[nextsize])
            sizedChunks[nextsize] = []
            size <<= 1
        else:
            break
    return sizedChunks


class ChunkRenderer(object):
    maxlod = 2
    minlod = 0

    def __init__(self, renderer, chunkPosition):
        self.renderer = renderer
        self.blockRenderers = []
        self.detailLevel = 0
        self.invalidLayers = set(Layer.AllLayers)

        self.chunkPosition = chunkPosition
        self.bufferSize = 0
        self.renderstateLists = None

    @property
    def visibleLayers(self):
        return self.renderer.visibleLayers

    def forgetDisplayLists(self, states=None):
        if self.renderstateLists is not None:
            # print "Discarded {0}, gained {1} bytes".format(self.chunkPosition,self.bufferSize)

            for k in states or self.renderstateLists.iterkeys():
                a = self.renderstateLists.get(k, [])
                # print a
                for i in a:
                    gl.glDeleteLists(i, 1)

            if states:
                del self.renderstateLists[states]
            else:
                self.renderstateLists = None

            self.needsRedisplay = True
            self.renderer.discardMasterList()

    def debugDraw(self):
        for blockRenderer in self.blockRenderers:
            blockRenderer.drawArrays(self.chunkPosition, False)

    def makeDisplayLists(self):
        if not self.needsRedisplay:
            return
        self.forgetDisplayLists()
        if not self.blockRenderers:
            return

        lists = defaultdict(list)

        showRedraw = self.renderer.showRedraw

        if not (showRedraw and self.needsBlockRedraw):
            GL.glEnableClientState(GL.GL_COLOR_ARRAY)

        renderers = self.blockRenderers

        for blockRenderer in renderers:
            if self.detailLevel not in blockRenderer.detailLevels:
                continue
            if blockRenderer.layer not in self.visibleLayers:
                continue

            l = blockRenderer.makeArrayList(self.chunkPosition, self.needsBlockRedraw and showRedraw)
            lists[blockRenderer.renderstate].append(l)

        if not (showRedraw and self.needsBlockRedraw):
            GL.glDisableClientState(GL.GL_COLOR_ARRAY)

        self.needsRedisplay = False
        self.renderstateLists = lists

    @property
    def needsBlockRedraw(self):
        return Layer.Blocks in self.invalidLayers

    def invalidate(self, layers=None):
        if layers is None:
            layers = Layer.AllLayers

        if layers:
            layers = set(layers)
            self.invalidLayers.update(layers)
            blockRenderers = [br for br in self.blockRenderers
                              if br.layer is Layer.Blocks
                              or br.layer not in layers]
            if len(blockRenderers) < len(self.blockRenderers):
                self.forgetDisplayLists()
            self.blockRenderers = blockRenderers

            if self.renderer.showRedraw and Layer.Blocks in layers:
                self.needsRedisplay = True

    def calcFaces(self):
        minlod = self.renderer.detailLevelForChunk(self.chunkPosition)

        minlod = min(minlod, self.maxlod)
        if self.detailLevel != minlod:
            self.forgetDisplayLists()
            self.detailLevel = minlod
            self.invalidLayers.add(Layer.Blocks)

            # discard the standard detail renderers
            if minlod > 0:
                blockRenderers = []
                for br in self.blockRenderers:
                    if br.detailLevels != (0,):
                        blockRenderers.append(br)

                self.blockRenderers = blockRenderers

        if self.renderer.chunkCalculator:
            for i in self.renderer.chunkCalculator.calcFacesForChunkRenderer(self):
                yield

        else:
            raise StopIteration
            yield

    def vertexArraysDone(self):
        bufferSize = 0
        for br in self.blockRenderers:
            bufferSize += br.bufferSize()
            if self.renderer.alpha != 0xff:
                br.setAlpha(self.renderer.alpha)
        self.bufferSize = bufferSize
        self.invalidLayers = set()
        self.needsRedisplay = True
        self.renderer.invalidateMasterList()

    needsRedisplay = False

    @property
    def done(self):
        return len(self.invalidLayers) == 0

_XYZ = numpy.s_[..., 0:3]
_ST = numpy.s_[..., 3:5]
_XYZST = numpy.s_[..., :5]
_RGBA = numpy.s_[..., 20:24]
_RGB = numpy.s_[..., 20:23]
_A = numpy.s_[..., 23]


def makeVertexTemplates(xmin=0, ymin=0, zmin=0, xmax=1, ymax=1, zmax=1):
        return numpy.array([

             # FaceXIncreasing:
                              [[xmax, ymin, zmax, (zmin * 16), 16 - (ymin * 16), 0x0b],
                               [xmax, ymin, zmin, (zmax * 16), 16 - (ymin * 16), 0x0b],
                               [xmax, ymax, zmin, (zmax * 16), 16 - (ymax * 16), 0x0b],
                               [xmax, ymax, zmax, (zmin * 16), 16 - (ymax * 16), 0x0b],
                               ],

             # FaceXDecreasing:
                              [[xmin, ymin, zmin, (zmin * 16), 16 - (ymin * 16), 0x0b],
                               [xmin, ymin, zmax, (zmax * 16), 16 - (ymin * 16), 0x0b],
                               [xmin, ymax, zmax, (zmax * 16), 16 - (ymax * 16), 0x0b],
                               [xmin, ymax, zmin, (zmin * 16), 16 - (ymax * 16), 0x0b]],


             # FaceYIncreasing:
                              [[xmin, ymax, zmin, xmin * 16, 16 - (zmax * 16), 0x11],  # ne
                               [xmin, ymax, zmax, xmin * 16, 16 - (zmin * 16), 0x11],  # nw
                               [xmax, ymax, zmax, xmax * 16, 16 - (zmin * 16), 0x11],  # sw
                               [xmax, ymax, zmin, xmax * 16, 16 - (zmax * 16), 0x11]],  # se

             # FaceYDecreasing:
                              [[xmin, ymin, zmin, xmin * 16, 16 - (zmax * 16), 0x08],
                               [xmax, ymin, zmin, xmax * 16, 16 - (zmax * 16), 0x08],
                               [xmax, ymin, zmax, xmax * 16, 16 - (zmin * 16), 0x08],
                               [xmin, ymin, zmax, xmin * 16, 16 - (zmin * 16), 0x08]],

             # FaceZIncreasing:
                              [[xmin, ymin, zmax, xmin * 16, 16 - (ymin * 16), 0x0d],
                               [xmax, ymin, zmax, xmax * 16, 16 - (ymin * 16), 0x0d],
                               [xmax, ymax, zmax, xmax * 16, 16 - (ymax * 16), 0x0d],
                               [xmin, ymax, zmax, xmin * 16, 16 - (ymax * 16), 0x0d]],

             # FaceZDecreasing:
                              [[xmax, ymin, zmin, xmin * 16, 16 - (ymin * 16), 0x0d],
                               [xmin, ymin, zmin, xmax * 16, 16 - (ymin * 16), 0x0d],
                               [xmin, ymax, zmin, xmax * 16, 16 - (ymax * 16), 0x0d],
                               [xmax, ymax, zmin, xmin * 16, 16 - (ymax * 16), 0x0d],
                              ],

        ])

elementByteLength = 24


def createPrecomputedVertices():
    height = 16
    precomputedVertices = [numpy.zeros(shape=(16, 16, height, 4, 6),  # x,y,z,s,t,rg, ba
                                  dtype='float32') for d in faceVertexTemplates]

    xArray = numpy.arange(16)[:, numpy.newaxis, numpy.newaxis, numpy.newaxis]
    zArray = numpy.arange(16)[numpy.newaxis, :, numpy.newaxis, numpy.newaxis]
    yArray = numpy.arange(height)[numpy.newaxis, numpy.newaxis, :, numpy.newaxis]

    for dir in range(len(faceVertexTemplates)):
        precomputedVertices[dir][_XYZ][..., 0] = xArray
        precomputedVertices[dir][_XYZ][..., 1] = yArray
        precomputedVertices[dir][_XYZ][..., 2] = zArray
        precomputedVertices[dir][_XYZ] += faceVertexTemplates[dir][..., 0:3]  # xyz

        precomputedVertices[dir][_ST] = faceVertexTemplates[dir][..., 3:5]  # s
        precomputedVertices[dir].view('uint8')[_RGB] = faceVertexTemplates[dir][..., 5, numpy.newaxis]
        precomputedVertices[dir].view('uint8')[_A] = 0xff

    return precomputedVertices

faceVertexTemplates = makeVertexTemplates()


class ChunkCalculator (object):
    cachedTemplate = None
    cachedTemplateHeight = 0

    whiteLight = numpy.array([[[15] * 16] * 16] * 16, numpy.uint8)
    precomputedVertices = createPrecomputedVertices()

    def __init__(self, level):
        self.makeRenderstates(level.materials)

            # del xArray, zArray, yArray
        self.nullVertices = numpy.zeros((0,) * len(self.precomputedVertices[0].shape), dtype=self.precomputedVertices[0].dtype)
        from leveleditor import Settings

        Settings.fastLeaves.addObserver(self)
        Settings.roughGraphics.addObserver(self)

    class renderstatePlain(object):
        @classmethod
        def bind(self):
            pass

        @classmethod
        def release(self):
            pass

    class renderstateVines(object):
        @classmethod
        def bind(self):
            GL.glDisable(GL.GL_CULL_FACE)
            GL.glEnable(GL.GL_ALPHA_TEST)

        @classmethod
        def release(self):
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_ALPHA_TEST)

    class renderstateLowDetail(object):
        @classmethod
        def bind(self):
            GL.glDisable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_TEXTURE_2D)

        @classmethod
        def release(self):
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glEnable(GL.GL_TEXTURE_2D)

    class renderstateAlphaTest(object):
        @classmethod
        def bind(self):
            GL.glEnable(GL.GL_ALPHA_TEST)

        @classmethod
        def release(self):
            GL.glDisable(GL.GL_ALPHA_TEST)

    class _renderstateAlphaBlend(object):
        @classmethod
        def bind(self):
            GL.glEnable(GL.GL_BLEND)

        @classmethod
        def release(self):
            GL.glDisable(GL.GL_BLEND)

    class renderstateWater(_renderstateAlphaBlend):
        pass

    class renderstateIce(_renderstateAlphaBlend):
        pass

    class renderstateEntity(object):
        @classmethod
        def bind(self):
            GL.glDisable(GL.GL_DEPTH_TEST)
            # GL.glDisable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_TEXTURE_2D)
            GL.glEnable(GL.GL_BLEND)

        @classmethod
        def release(self):
            GL.glEnable(GL.GL_DEPTH_TEST)
            # GL.glEnable(GL.GL_CULL_FACE)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glDisable(GL.GL_BLEND)

    renderstates = (
        renderstatePlain,
        renderstateVines,
        renderstateLowDetail,
        renderstateAlphaTest,
        renderstateIce,
        renderstateWater,
        renderstateEntity,
    )

    def makeRenderstates(self, materials):
        self.blockRendererClasses = [
            GenericBlockRenderer,
            LeafBlockRenderer,
            PlantBlockRenderer,
            TorchBlockRenderer,
            WaterBlockRenderer,
            SlabBlockRenderer,
        ]
        if materials.name in ("Alpha", "Pocket"):
            self.blockRendererClasses += [
                RailBlockRenderer,
                LadderBlockRenderer,
                SnowBlockRenderer,
                RedstoneBlockRenderer,
                IceBlockRenderer,
                FeatureBlockRenderer,
                StairBlockRenderer,
                VineBlockRenderer,
            # button, floor plate, door -> 1-cube features
            # lever, sign, wall sign, stairs -> 2-cube features

            # repeater
            # fence

            # bed
            # cake
            # portal
            ]

        self.materialMap = materialMap = numpy.zeros((pymclevel.materials.id_limit,), 'uint8')
        materialMap[1:] = 1  # generic blocks

        materialCount = 2

        for br in self.blockRendererClasses[1:]:  # skip generic blocks
            materialMap[br.getBlocktypes(materials)] = materialCount
            br.materialIndex = materialCount
            materialCount += 1

        self.exposedMaterialMap = numpy.array(materialMap)
        self.addTransparentMaterials(self.exposedMaterialMap, materialCount)

    def addTransparentMaterials(self, mats, materialCount):
        transparentMaterials = [
            pymclevel.materials.alphaMaterials.Glass,
            pymclevel.materials.alphaMaterials.GlassPane,
            pymclevel.materials.alphaMaterials.IronBars,
            pymclevel.materials.alphaMaterials.MonsterSpawner,
            pymclevel.materials.alphaMaterials.Vines,
            pymclevel.materials.alphaMaterials.Fire,
            pymclevel.materials.alphaMaterials.Trapdoor,
            pymclevel.materials.alphaMaterials.Lever,
            pymclevel.materials.alphaMaterials.BrewingStand,

        ]
        for b in transparentMaterials:
            mats[b.ID] = materialCount
            materialCount += 1

    hiddenOreMaterials = numpy.arange(pymclevel.materials.id_limit, dtype='uint8')
    hiddenOreMaterials[2] = 1  # don't show boundaries between dirt,grass,sand,gravel,stone
    hiddenOreMaterials[3] = 1
    hiddenOreMaterials[12] = 1
    hiddenOreMaterials[13] = 1

    roughMaterials = numpy.ones((pymclevel.materials.id_limit,), dtype='uint8')
    roughMaterials[0] = 0
    addTransparentMaterials(None, roughMaterials, 2)

    def calcFacesForChunkRenderer(self, cr):
        if 0 == len(cr.invalidLayers):
#            layers = set(br.layer for br in cr.blockRenderers)
#            assert set() == cr.visibleLayers.difference(layers)

            return

        lod = cr.detailLevel
        cx, cz = cr.chunkPosition
        level = cr.renderer.level
        try:
            chunk = level.getChunk(cx, cz)
        except Exception, e:
            logging.warn(u"Error reading chunk: %s", e)
            yield
            return

        yield
        brs = []
        classes = [
            TileEntityRenderer,
            MonsterRenderer,
            ItemRenderer,
            TileTicksRenderer,
            TerrainPopulatedRenderer,
            LowDetailBlockRenderer,
            OverheadBlockRenderer,
        ]
        existingBlockRenderers = dict(((type(b), b) for b in cr.blockRenderers))

        for blockRendererClass in classes:
            if cr.detailLevel not in blockRendererClass.detailLevels:
                continue
            if blockRendererClass.layer not in cr.visibleLayers:
                continue
            if blockRendererClass.layer not in cr.invalidLayers:
                if blockRendererClass in existingBlockRenderers:
                    brs.append(existingBlockRenderers[blockRendererClass])

                continue

            br = blockRendererClass(self)
            br.detailLevel = cr.detailLevel

            for _ in br.makeChunkVertices(chunk):
                yield
            brs.append(br)

        blockRenderers = []

        # Recalculate high detail blocks if needed, otherwise retain the high detail renderers
        if lod == 0 and Layer.Blocks in cr.invalidLayers:
            for _ in self.calcHighDetailFaces(cr, blockRenderers):
                yield
        else:
            blockRenderers.extend(br for br in cr.blockRenderers if type(br) not in classes)

        # Add the layer renderers
        blockRenderers.extend(brs)
        cr.blockRenderers = blockRenderers

        cr.vertexArraysDone()
        raise StopIteration

    def getNeighboringChunks(self, chunk):
        cx, cz = chunk.chunkPosition
        level = chunk.world

        neighboringChunks = {}
        for dir, dx, dz in ((pymclevel.faces.FaceXDecreasing, -1, 0),
                           (pymclevel.faces.FaceXIncreasing, 1, 0),
                           (pymclevel.faces.FaceZDecreasing, 0, -1),
                           (pymclevel.faces.FaceZIncreasing, 0, 1)):
            if not level.containsChunk(cx + dx, cz + dz):
                neighboringChunks[dir] = pymclevel.infiniteworld.ZeroChunk(level.Height)
            else:
                # if not level.chunkIsLoaded(cx+dx,cz+dz):
                #    raise StopIteration
                try:
                    neighboringChunks[dir] = level.getChunk(cx + dx, cz + dz)
                except (EnvironmentError, pymclevel.mclevelbase.ChunkNotPresent, pymclevel.mclevelbase.ChunkMalformed):
                    neighboringChunks[dir] = pymclevel.infiniteworld.ZeroChunk(level.Height)
        return neighboringChunks

    def getAreaBlocks(self, chunk, neighboringChunks):
        chunkWidth, chunkLength, chunkHeight = chunk.Blocks.shape

        areaBlocks = numpy.zeros((chunkWidth + 2, chunkLength + 2, chunkHeight + 2), numpy.uint16)
        areaBlocks[1:-1, 1:-1, 1:-1] = chunk.Blocks
        areaBlocks[:1, 1:-1, 1:-1] = neighboringChunks[pymclevel.faces.FaceXDecreasing].Blocks[-1:, :chunkLength, :chunkHeight]
        areaBlocks[-1:, 1:-1, 1:-1] = neighboringChunks[pymclevel.faces.FaceXIncreasing].Blocks[:1, :chunkLength, :chunkHeight]
        areaBlocks[1:-1, :1, 1:-1] = neighboringChunks[pymclevel.faces.FaceZDecreasing].Blocks[:chunkWidth, -1:, :chunkHeight]
        areaBlocks[1:-1, -1:, 1:-1] = neighboringChunks[pymclevel.faces.FaceZIncreasing].Blocks[:chunkWidth, :1, :chunkHeight]
        return areaBlocks

    def getFacingBlockIndices(self, areaBlocks, areaBlockMats):
        facingBlockIndices = [None] * 6

        exposedFacesX = (areaBlockMats[:-1, 1:-1, 1:-1] != areaBlockMats[1:, 1:-1, 1:-1])

        facingBlockIndices[pymclevel.faces.FaceXDecreasing] = exposedFacesX[:-1]
        facingBlockIndices[pymclevel.faces.FaceXIncreasing] = exposedFacesX[1:]

        exposedFacesZ = (areaBlockMats[1:-1, :-1, 1:-1] != areaBlockMats[1:-1, 1:, 1:-1])

        facingBlockIndices[pymclevel.faces.FaceZDecreasing] = exposedFacesZ[:, :-1]
        facingBlockIndices[pymclevel.faces.FaceZIncreasing] = exposedFacesZ[:, 1:]

        exposedFacesY = (areaBlockMats[1:-1, 1:-1, :-1] != areaBlockMats[1:-1, 1:-1, 1:])

        facingBlockIndices[pymclevel.faces.FaceYDecreasing] = exposedFacesY[:, :, :-1]
        facingBlockIndices[pymclevel.faces.FaceYIncreasing] = exposedFacesY[:, :, 1:]
        return facingBlockIndices

    def getAreaBlockLights(self, chunk, neighboringChunks):
        chunkWidth, chunkLength, chunkHeight = chunk.Blocks.shape
        lights = chunk.BlockLight
        skyLight = chunk.SkyLight
        finalLight = self.whiteLight

        if lights != None:
            finalLight = lights
        if skyLight != None:
            finalLight = numpy.maximum(skyLight, lights)

        areaBlockLights = numpy.ones((chunkWidth + 2, chunkLength + 2, chunkHeight + 2), numpy.uint8)
        areaBlockLights[:] = 15

        areaBlockLights[1:-1, 1:-1, 1:-1] = finalLight

        nc = neighboringChunks[pymclevel.faces.FaceXDecreasing]
        numpy.maximum(nc.SkyLight[-1:, :chunkLength, :chunkHeight],
                nc.BlockLight[-1:, :chunkLength, :chunkHeight],
                areaBlockLights[0:1, 1:-1, 1:-1])

        nc = neighboringChunks[pymclevel.faces.FaceXIncreasing]
        numpy.maximum(nc.SkyLight[:1, :chunkLength, :chunkHeight],
                nc.BlockLight[:1, :chunkLength, :chunkHeight],
                areaBlockLights[-1:, 1:-1, 1:-1])

        nc = neighboringChunks[pymclevel.faces.FaceZDecreasing]
        numpy.maximum(nc.SkyLight[:chunkWidth, -1:, :chunkHeight],
                nc.BlockLight[:chunkWidth, -1:, :chunkHeight],
                areaBlockLights[1:-1, 0:1, 1:-1])

        nc = neighboringChunks[pymclevel.faces.FaceZIncreasing]
        numpy.maximum(nc.SkyLight[:chunkWidth, :1, :chunkHeight],
                nc.BlockLight[:chunkWidth, :1, :chunkHeight],
                areaBlockLights[1:-1, -1:, 1:-1])

        minimumLight = 4
        # areaBlockLights[areaBlockLights<minimumLight]=minimumLight
        numpy.clip(areaBlockLights, minimumLight, 16, areaBlockLights)

        return areaBlockLights

    def calcHighDetailFaces(self, cr, blockRenderers):  # ForChunk(self, chunkPosition = (0,0), level = None, alpha = 1.0):
        """ calculate the geometry for a chunk renderer from its blockMats, data,
        and lighting array. fills in the cr's blockRenderers with verts
        for each block facing and material"""

        # chunkBlocks and chunkLights shall be indexed [x,z,y] to follow infdev's convention
        cx, cz = cr.chunkPosition
        level = cr.renderer.level

        chunk = level.getChunk(cx, cz)
        neighboringChunks = self.getNeighboringChunks(chunk)

        areaBlocks = self.getAreaBlocks(chunk, neighboringChunks)
        yield

        areaBlockLights = self.getAreaBlockLights(chunk, neighboringChunks)
        yield

        slabs = areaBlocks == pymclevel.materials.alphaMaterials.StoneSlab.ID
        if slabs.any():
            areaBlockLights[slabs] = areaBlockLights[:, :, 1:][slabs[:, :, :-1]]
        yield

        showHiddenOres = cr.renderer.showHiddenOres
        if showHiddenOres:
            facingMats = self.hiddenOreMaterials[areaBlocks]
        else:
            facingMats = self.exposedMaterialMap[areaBlocks]

        yield

        if self.roughGraphics:
            areaBlockMats = self.roughMaterials[areaBlocks]
        else:
            areaBlockMats = self.materialMap[areaBlocks]

        facingBlockIndices = self.getFacingBlockIndices(areaBlocks, facingMats)
        yield

        for i in self.computeGeometry(chunk, areaBlockMats, facingBlockIndices, areaBlockLights, cr, blockRenderers):
            yield

    def computeGeometry(self, chunk, areaBlockMats, facingBlockIndices, areaBlockLights, chunkRenderer, blockRenderers):
        blocks, blockData = chunk.Blocks, chunk.Data
        blockData = blockData & 0xf
        blockMaterials = areaBlockMats[1:-1, 1:-1, 1:-1]
        if self.roughGraphics:
            blockMaterials.clip(0, 1, blockMaterials)

        sx = sz = slice(0, 16)
        asx = asz = slice(0, 18)

        for y in range(0, chunk.world.Height, 16):
            sy = slice(y, y + 16)
            asy = slice(y, y + 18)

            for _i in self.computeCubeGeometry(
                    y,
                    blockRenderers,
                    blocks[sx, sz, sy],
                    blockData[sx, sz, sy],
                    chunk.materials,
                    blockMaterials[sx, sz, sy],
                    [f[sx, sz, sy] for f in facingBlockIndices],
                    areaBlockLights[asx, asz, asy],
                    chunkRenderer):
                yield

    def computeCubeGeometry(self, y, blockRenderers, blocks, blockData, materials, blockMaterials, facingBlockIndices, areaBlockLights, chunkRenderer):
        materialCounts = numpy.bincount(blockMaterials.ravel())

        def texMap(blocks, blockData=0, direction=slice(None)):
            return materials.blockTextures[blocks, blockData, direction]  # xxx slow

        for blockRendererClass in self.blockRendererClasses:
            mi = blockRendererClass.materialIndex
            if mi >= len(materialCounts) or materialCounts[mi] == 0:
                continue

            blockRenderer = blockRendererClass(self)
            blockRenderer.y = y
            blockRenderer.materials = materials
            for _ in blockRenderer.makeVertices(facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
                yield
            blockRenderers.append(blockRenderer)

            yield

    def makeTemplate(self, direction, blockIndices):
        return self.precomputedVertices[direction][blockIndices]


class Layer:
    Blocks = "Blocks"
    Entities = "Entities"
    Monsters = "Monsters"
    Items = "Items"
    TileEntities = "TileEntities"
    TileTicks = "TileTicks"
    TerrainPopulated = "TerrainPopulated"
    AllLayers = (Blocks, Entities, Monsters, Items, TileEntities, TileTicks, TerrainPopulated)


class BlockRenderer(object):
    # vertexArrays = None
    detailLevels = (0,)
    layer = Layer.Blocks
    directionOffsets = {
        pymclevel.faces.FaceXDecreasing: numpy.s_[:-2, 1:-1, 1:-1],
        pymclevel.faces.FaceXIncreasing: numpy.s_[2:, 1:-1, 1:-1],
        pymclevel.faces.FaceYDecreasing: numpy.s_[1:-1, 1:-1, :-2],
        pymclevel.faces.FaceYIncreasing: numpy.s_[1:-1, 1:-1, 2:],
        pymclevel.faces.FaceZDecreasing: numpy.s_[1:-1, :-2, 1:-1],
        pymclevel.faces.FaceZIncreasing: numpy.s_[1:-1, 2:, 1:-1],
    }
    renderstate = ChunkCalculator.renderstateAlphaTest

    def __init__(self, cc):
        self.makeTemplate = cc.makeTemplate
        self.chunkCalculator = cc
        self.vertexArrays = []

        pass

    @classmethod
    def getBlocktypes(cls, mats):
        return cls.blocktypes

    def setAlpha(self, alpha):
        "alpha is an unsigned byte value"
        for a in self.vertexArrays:
            a.view('uint8')[_RGBA][..., 3] = alpha

    def bufferSize(self):
        return sum(a.size for a in self.vertexArrays) * 4

    def getMaterialIndices(self, blockMaterials):
        return blockMaterials == self.materialIndex

    def makeVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        arrays = []
        materialIndices = self.getMaterialIndices(blockMaterials)
        yield

        blockLight = areaBlockLights[1:-1, 1:-1, 1:-1]

        for (direction, exposedFaceIndices) in enumerate(facingBlockIndices):
            facingBlockLight = areaBlockLights[self.directionOffsets[direction]]
            vertexArray = self.makeFaceVertices(direction, materialIndices, exposedFaceIndices, blocks, blockData, blockLight, facingBlockLight, texMap)
            yield
            if len(vertexArray):
                arrays.append(vertexArray)
        self.vertexArrays = arrays

    def makeArrayList(self, chunkPosition, showRedraw):
        l = gl.glGenLists(1)
        GL.glNewList(l, GL.GL_COMPILE)
        self.drawArrays(chunkPosition, showRedraw)
        GL.glEndList()
        return l

    def drawArrays(self, chunkPosition, showRedraw):
        cx, cz = chunkPosition
        y = 0
        if hasattr(self, 'y'):
            y = self.y
        with gl.glPushMatrix(GL.GL_MODELVIEW):
            GL.glTranslate(cx << 4, y, cz << 4)

            if showRedraw:
                GL.glColor(1.0, 0.25, 0.25, 1.0)

            self.drawVertices()

    def drawVertices(self):
        if self.vertexArrays:
            for buf in self.vertexArrays:
                self.drawFaceVertices(buf)

    def drawFaceVertices(self, buf):
        if 0 == len(buf):
            return
        stride = elementByteLength

        GL.glVertexPointer(3, GL.GL_FLOAT, stride, (buf.ravel()))
        GL.glTexCoordPointer(2, GL.GL_FLOAT, stride, (buf.ravel()[3:]))
        GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, stride, (buf.view(dtype=numpy.uint8).ravel()[20:]))

        GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)


class EntityRendererGeneric(BlockRenderer):
    renderstate = ChunkCalculator.renderstateEntity
    detailLevels = (0, 1, 2)

    def drawFaceVertices(self, buf):
        if 0 == len(buf):
            return
        stride = elementByteLength

        GL.glVertexPointer(3, GL.GL_FLOAT, stride, (buf.ravel()))
        GL.glTexCoordPointer(2, GL.GL_FLOAT, stride, (buf.ravel()[3:]))
        GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, stride, (buf.view(dtype=numpy.uint8).ravel()[20:]))

        GL.glDepthMask(False)

        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)

        GL.glLineWidth(2.0)
        GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)

        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

        GL.glPolygonOffset(DepthOffset.TerrainWire, DepthOffset.TerrainWire)
        with gl.glEnable(GL.GL_POLYGON_OFFSET_FILL, GL.GL_DEPTH_TEST):
            GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
        GL.glDepthMask(True)

    def _computeVertices(self, positions, colors, offset=False, chunkPosition=(0, 0)):
        cx, cz = chunkPosition
        x = cx << 4
        z = cz << 4

        vertexArray = numpy.zeros(shape=(len(positions), 6, 4, 6), dtype='float32')
        if len(positions):
            positions = numpy.array(positions)
            positions[:, (0, 2)] -= (x, z)
            if offset:
                positions -= 0.5

            vertexArray.view('uint8')[_RGBA] = colors
            vertexArray[_XYZ] = positions[:, numpy.newaxis, numpy.newaxis, :]
            vertexArray[_XYZ] += faceVertexTemplates[_XYZ]
            vertexArray.shape = (len(positions) * 6, 4, 6)
        return vertexArray


class TileEntityRenderer(EntityRendererGeneric):
    layer = Layer.TileEntities

    def makeChunkVertices(self, chunk):
        tilePositions = []
        for i, ent in enumerate(chunk.TileEntities):
            if i % 10 == 0:
                yield
            if not 'x' in ent:
                continue
            tilePositions.append(pymclevel.TileEntity.pos(ent))
        tiles = self._computeVertices(tilePositions, (0xff, 0xff, 0x33, 0x44), chunkPosition=chunk.chunkPosition)
        yield
        self.vertexArrays = [tiles]


class BaseEntityRenderer(EntityRendererGeneric):
    pass


class MonsterRenderer(BaseEntityRenderer):
    layer = Layer.Entities  # xxx Monsters
    notMonsters = set(["Item", "XPOrb", "Painting"])

    def makeChunkVertices(self, chunk):
        monsterPositions = []
        for i, ent in enumerate(chunk.Entities):
            if i % 10 == 0:
                yield
            id = ent["id"].value
            if id in self.notMonsters:
                continue

            monsterPositions.append(pymclevel.Entity.pos(ent))

        monsters = self._computeVertices(monsterPositions,
                                         (0xff, 0x22, 0x22, 0x44),
                                         offset=True,
                                         chunkPosition=chunk.chunkPosition)
        yield
        self.vertexArrays = [monsters]


class EntityRenderer(BaseEntityRenderer):
    def makeChunkVertices(self, chunk):
        yield
#        entityPositions = []
#        for i, ent in enumerate(chunk.Entities):
#            if i % 10 == 0:
#                yield
#            entityPositions.append(pymclevel.Entity.pos(ent))
#
#        entities = self._computeVertices(entityPositions, (0x88, 0x00, 0x00, 0x66), offset=True, chunkPosition=chunk.chunkPosition)
#        yield
#        self.vertexArrays = [entities]


class ItemRenderer(BaseEntityRenderer):
    layer = Layer.Items

    def makeChunkVertices(self, chunk):
        entityPositions = []
        entityColors = []
        colorMap = {
            "Item": (0x22, 0xff, 0x22, 0x5f),
            "XPOrb": (0x88, 0xff, 0x88, 0x5f),
            "Painting": (134, 96, 67, 0x5f),
        }
        for i, ent in enumerate(chunk.Entities):
            if i % 10 == 0:
                yield
            color = colorMap.get(ent["id"].value)
            if color is None:
                continue

            entityPositions.append(pymclevel.Entity.pos(ent))
            entityColors.append(color)

        entities = self._computeVertices(entityPositions, numpy.array(entityColors, dtype='uint8')[:, numpy.newaxis, numpy.newaxis], offset=True, chunkPosition=chunk.chunkPosition)
        yield
        self.vertexArrays = [entities]


class TileTicksRenderer(EntityRendererGeneric):
    layer = Layer.TileTicks

    def makeChunkVertices(self, chunk):
        if chunk.root_tag and "Level" in chunk.root_tag and "TileTicks" in chunk.root_tag["Level"]:
            ticks = chunk.root_tag["Level"]["TileTicks"]
            if len(ticks):
                self.vertexArrays.append(self._computeVertices([[t[i].value for i in "xyz"] for t in ticks],
                                                               (0xff, 0xff, 0xff, 0x44),
                                                               chunkPosition=chunk.chunkPosition))

        yield


class TerrainPopulatedRenderer(EntityRendererGeneric):
    layer = Layer.TerrainPopulated
    vertexTemplate = numpy.zeros((6, 4, 6), 'float32')
    vertexTemplate[_XYZ] = faceVertexTemplates[_XYZ]
    vertexTemplate[_XYZ] *= (16, 128, 16)
    color = (255, 200, 155)
    vertexTemplate.view('uint8')[_RGBA] = color + (72,)

    def drawFaceVertices(self, buf):
        if 0 == len(buf):
            return
        stride = elementByteLength

        GL.glVertexPointer(3, GL.GL_FLOAT, stride, (buf.ravel()))
        GL.glTexCoordPointer(2, GL.GL_FLOAT, stride, (buf.ravel()[3:]))
        GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, stride, (buf.view(dtype=numpy.uint8).ravel()[20:]))

        GL.glDepthMask(False)

        # GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
        GL.glDisable(GL.GL_CULL_FACE)

        with gl.glEnable(GL.GL_DEPTH_TEST):
            GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)

        GL.glEnable(GL.GL_CULL_FACE)

        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)

        GL.glLineWidth(1.0)
        GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
        GL.glLineWidth(2.0)
        with gl.glEnable(GL.GL_DEPTH_TEST):
            GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
        GL.glLineWidth(1.0)

        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
        GL.glDepthMask(True)

#        GL.glPolygonOffset(DepthOffset.TerrainWire, DepthOffset.TerrainWire)
#        with gl.glEnable(GL.GL_POLYGON_OFFSET_FILL, GL.GL_DEPTH_TEST):
#            GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
#

    def makeChunkVertices(self, chunk):
        neighbors = self.chunkCalculator.getNeighboringChunks(chunk)

        def getpop(ch):
            return getattr(ch, "TerrainPopulated", True)

        pop = getpop(chunk)
        yield
        if pop:
            return

        visibleFaces = [
            getpop(neighbors[pymclevel.faces.FaceXIncreasing]),
            getpop(neighbors[pymclevel.faces.FaceXDecreasing]),
            True,
            True,
            getpop(neighbors[pymclevel.faces.FaceZIncreasing]),
            getpop(neighbors[pymclevel.faces.FaceZDecreasing]),
        ]
        visibleFaces = numpy.array(visibleFaces, dtype='bool')
        verts = self.vertexTemplate[visibleFaces]
        self.vertexArrays.append(verts)

        yield


class LowDetailBlockRenderer(BlockRenderer):
    renderstate = ChunkCalculator.renderstateLowDetail
    detailLevels = (1,)

    def drawFaceVertices(self, buf):
        if not len(buf):
            return
        stride = 16

        GL.glVertexPointer(3, GL.GL_FLOAT, stride, numpy.ravel(buf.ravel()))
        GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, stride, (buf.view(dtype='uint8').ravel()[12:]))

        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDrawArrays(GL.GL_QUADS, 0, len(buf) * 4)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

    def setAlpha(self, alpha):
        for va in self.vertexArrays:
            va.view('uint8')[..., -1] = alpha

    def makeChunkVertices(self, ch):
        step = 1

        level = ch.world
        vertexArrays = []
        blocks = ch.Blocks
        heightMap = ch.HeightMap

        heightMap = heightMap[::step, ::step]
        blocks = blocks[::step, ::step]

        if 0 in blocks.shape:
            return

        chunkWidth, chunkLength, chunkHeight = blocks.shape
        blockIndices = numpy.zeros((chunkWidth, chunkLength, chunkHeight), bool)

        gridaxes = list(numpy.indices((chunkWidth, chunkLength)))
        h = numpy.swapaxes(heightMap - 1, 0, 1)[:chunkWidth, :chunkLength]
        numpy.clip(h, 0, chunkHeight - 1, out=h)

        gridaxes = [gridaxes[0], gridaxes[1], h]

        depths = numpy.zeros((chunkWidth, chunkLength), dtype='uint16')
        depths[1:-1, 1:-1] = reduce(numpy.minimum, (h[1:-1, :-2], h[1:-1, 2:], h[:-2, 1:-1]), h[2:, 1:-1])
        yield

        try:
            topBlocks = blocks[gridaxes]
            nonAirBlocks = (topBlocks != 0)
            blockIndices[gridaxes] = nonAirBlocks
            h += 1
            numpy.clip(h, 0, chunkHeight - 1, out=h)
            overblocks = blocks[gridaxes][nonAirBlocks].ravel()

        except ValueError, e:
            raise ValueError(str(e.args) + "Chunk shape: {0}".format(blockIndices.shape), sys.exc_info()[-1])

        if nonAirBlocks.any():
            blockTypes = blocks[blockIndices]

            flatcolors = level.materials.flatColors[blockTypes, ch.Data[blockIndices] & 0xf][:, numpy.newaxis, :]
            # flatcolors[:,:,:3] *= (0.6 + (h * (0.4 / float(chunkHeight-1)))) [topBlocks != 0][:, numpy.newaxis, numpy.newaxis]
            x, z, y = blockIndices.nonzero()

            yield
            vertexArray = numpy.zeros((len(x), 4, 4), dtype='float32')
            vertexArray[_XYZ][..., 0] = x[:, numpy.newaxis]
            vertexArray[_XYZ][..., 1] = y[:, numpy.newaxis]
            vertexArray[_XYZ][..., 2] = z[:, numpy.newaxis]

            va0 = numpy.array(vertexArray)

            va0[..., :3] += faceVertexTemplates[pymclevel.faces.FaceYIncreasing, ..., :3]

            overmask = overblocks > 0
            flatcolors[overmask] = level.materials.flatColors[:, 0][overblocks[overmask]][:, numpy.newaxis]

            if self.detailLevel == 2:
                heightfactor = (y / float(2.0 * ch.world.Height)) + 0.5
                flatcolors[..., :3] *= heightfactor[:, numpy.newaxis, numpy.newaxis]

            _RGBA = numpy.s_[..., 12:16]
            va0.view('uint8')[_RGBA] = flatcolors

            va0[_XYZ][:, :, 0] *= step
            va0[_XYZ][:, :, 2] *= step

            yield
            if self.detailLevel == 2:
                self.vertexArrays = [va0]
                return

            va1 = numpy.array(vertexArray)
            va1[..., :3] += faceVertexTemplates[pymclevel.faces.FaceXIncreasing, ..., :3]

            va1[_XYZ][:, (0, 1), 1] = depths[nonAirBlocks].ravel()[:, numpy.newaxis]  # stretch to floor
            va1[_XYZ][:, (1, 2), 0] -= 1.0  # turn diagonally
            va1[_XYZ][:, (2, 3), 1] -= 0.5  # drop down to prevent intersection pixels

            va1[_XYZ][:, :, 0] *= step
            va1[_XYZ][:, :, 2] *= step

            flatcolors *= 0.8

            va1.view('uint8')[_RGBA] = flatcolors
            grassmask = topBlocks[nonAirBlocks] == 2
            # color grass sides with dirt's color
            va1.view('uint8')[_RGBA][grassmask] = level.materials.flatColors[:, 0][[3]][:, numpy.newaxis]

            va2 = numpy.array(va1)
            va2[_XYZ][:, (1, 2), 0] += step
            va2[_XYZ][:, (0, 3), 0] -= step

            vertexArrays = [va1, va2, va0]

        self.vertexArrays = vertexArrays


class OverheadBlockRenderer(LowDetailBlockRenderer):
    detailLevels = (2,)


class GenericBlockRenderer(BlockRenderer):
    renderstate = ChunkCalculator.renderstateAlphaTest

    materialIndex = 1

    def makeGenericVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        vertexArrays = []
        materialIndices = self.getMaterialIndices(blockMaterials)
        yield

        for (direction, exposedFaceIndices) in enumerate(facingBlockIndices):
            facingBlockLight = areaBlockLights[self.directionOffsets[direction]]
            blockIndices = materialIndices & exposedFaceIndices

            theseBlocks = blocks[blockIndices]
            bdata = blockData[blockIndices]

            vertexArray = self.makeTemplate(direction, blockIndices)
            if not len(vertexArray):
                continue

            def setTexture():
                vertexArray[_ST] += texMap(theseBlocks, bdata, direction)[:, numpy.newaxis, 0:2]
            setTexture()

            def setGrassColors():
                grass = theseBlocks == pymclevel.materials.alphaMaterials.Grass.ID
                vertexArray.view('uint8')[_RGB][grass] *= self.grassColor

            def getBlockLight():
                return facingBlockLight[blockIndices]

            def setColors():
                vertexArray.view('uint8')[_RGB] *= getBlockLight()[..., numpy.newaxis, numpy.newaxis]
                if self.materials.name in ("Alpha", "Pocket"):
                    if direction == pymclevel.faces.FaceYIncreasing:
                        setGrassColors()
                # leaves = theseBlocks == pymclevel.materials.alphaMaterials.Leaves.ID
                # vertexArray.view('uint8')[_RGBA][leaves] *= [0.15, 0.88, 0.15, 1.0]
#                snow = theseBlocks == pymclevel.materials.alphaMaterials.SnowLayer.ID
#                if direction == pymclevel.faces.FaceYIncreasing:
#                    vertexArray[_XYZ][snow, ...,1] -= 0.875
#
#                if direction != pymclevel.faces.FaceYIncreasing and direction != pymclevel.faces.FaceYDecreasing:
#                    vertexArray[_XYZ][snow, ...,2:4,1] -= 0.875
#                    vertexArray[_ST][snow, ...,2:4,1] += 14
#
            setColors()
            yield

            vertexArrays.append(vertexArray)

        self.vertexArrays = vertexArrays

    grassColor = grassColorDefault = [0.39, 0.77, 0.23]  # 62C743

    makeVertices = makeGenericVertices


class LeafBlockRenderer(BlockRenderer):
    blocktypes = [18]

    @property
    def renderstate(self):
        if self.chunkCalculator.fastLeaves:
            return ChunkCalculator.renderstatePlain
        else:
            return ChunkCalculator.renderstateAlphaTest

    def makeLeafVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        arrays = []
        materialIndices = self.getMaterialIndices(blockMaterials)
        yield

        if self.materials.name in ("Alpha", "Pocket"):
            if not self.chunkCalculator.fastLeaves:
                blockIndices = materialIndices
                data = blockData[blockIndices]
                data &= 0x3  # ignore decay states
                leaves = (data == 0) | (data == 3)
                pines = (data == pymclevel.materials.alphaMaterials.PineLeaves.blockData)
                birches = (data == pymclevel.materials.alphaMaterials.BirchLeaves.blockData)
                texes = texMap(18, data, 0)
        else:
            blockIndices = materialIndices
            texes = texMap(18, [0], 0)

        for (direction, exposedFaceIndices) in enumerate(facingBlockIndices):
            if self.materials.name in ("Alpha", "Pocket"):
                if self.chunkCalculator.fastLeaves:
                    blockIndices = materialIndices & exposedFaceIndices
                    data = blockData[blockIndices]
                    data &= 0x3  # ignore decay states
                    leaves = (data == 0)
                    pines = (data == pymclevel.materials.alphaMaterials.PineLeaves.blockData)
                    birches = (data == pymclevel.materials.alphaMaterials.BirchLeaves.blockData)
                    type3 = (data == 3)
                    leaves |= type3

                    texes = texMap(18, data, 0)

            facingBlockLight = areaBlockLights[self.directionOffsets[direction]]
            vertexArray = self.makeTemplate(direction, blockIndices)
            if not len(vertexArray):
                continue

            vertexArray[_ST] += texes[:, numpy.newaxis]

            if not self.chunkCalculator.fastLeaves:
                vertexArray[_ST] -= (0x10, 0x0)

            vertexArray.view('uint8')[_RGB] *= facingBlockLight[blockIndices][..., numpy.newaxis, numpy.newaxis]
            if self.materials.name in ("Alpha", "Pocket"):
                vertexArray.view('uint8')[_RGB][leaves] *= self.leafColor
                vertexArray.view('uint8')[_RGB][pines] *= self.pineLeafColor
                vertexArray.view('uint8')[_RGB][birches] *= self.birchLeafColor

            yield
            arrays.append(vertexArray)

        self.vertexArrays = arrays

    leafColor = leafColorDefault = [0x48 / 255., 0xb5 / 255., 0x18 / 255.]  # 48b518
    pineLeafColor = pineLeafColorDefault = [0x61 / 255., 0x99 / 255., 0x61 / 255.]  # 0x619961
    birchLeafColor = birchLeafColorDefault = [0x80 / 255., 0xa7 / 255., 0x55 / 255.]  # 0x80a755

    makeVertices = makeLeafVertices


class PlantBlockRenderer(BlockRenderer):
    @classmethod
    def getBlocktypes(cls, mats):
        # blocktypes = [6, 37, 38, 39, 40, 59, 83]
        # if mats.name != "Classic": blocktypes += [31, 32]  # shrubs, tall grass
        # if mats.name == "Alpha": blocktypes += [115]  # nether wart
        blocktypes = [b.ID for b in mats if b.type in ("DECORATION_CROSS", "NETHER_WART", "CROPS", "STEM")]

        return blocktypes

    renderstate = ChunkCalculator.renderstateAlphaTest

    def makePlantVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        arrays = []
        blockIndices = self.getMaterialIndices(blockMaterials)
        yield

        theseBlocks = blocks[blockIndices]

        bdata = blockData[blockIndices]
        bdata[theseBlocks == 6] &= 0x3  # xxx saplings only
        texes = texMap(blocks[blockIndices], bdata, 0)

        blockLight = areaBlockLights[1:-1, 1:-1, 1:-1]
        lights = blockLight[blockIndices][..., numpy.newaxis, numpy.newaxis]

        colorize = None
        if self.materials.name == "Alpha":
            colorize = (theseBlocks == pymclevel.materials.alphaMaterials.TallGrass.ID) & (bdata != 0)

        for direction in (pymclevel.faces.FaceXIncreasing, pymclevel.faces.FaceXDecreasing, pymclevel.faces.FaceZIncreasing, pymclevel.faces.FaceZDecreasing):
            vertexArray = self.makeTemplate(direction, blockIndices)
            if not len(vertexArray):
                return

            if direction == pymclevel.faces.FaceXIncreasing:
                vertexArray[_XYZ][..., 1:3, 0] -= 1
            if direction == pymclevel.faces.FaceXDecreasing:
                vertexArray[_XYZ][..., 1:3, 0] += 1
            if direction == pymclevel.faces.FaceZIncreasing:
                vertexArray[_XYZ][..., 1:3, 2] -= 1
            if direction == pymclevel.faces.FaceZDecreasing:
                vertexArray[_XYZ][..., 1:3, 2] += 1

            vertexArray[_ST] += texes[:, numpy.newaxis, 0:2]

            vertexArray.view('uint8')[_RGB] = 0xf  # ignore precomputed directional light
            vertexArray.view('uint8')[_RGB] *= lights
            if colorize is not None:
                vertexArray.view('uint8')[_RGB][colorize] *= LeafBlockRenderer.leafColor

            arrays.append(vertexArray)
            yield

        self.vertexArrays = arrays

    makeVertices = makePlantVertices


class TorchBlockRenderer(BlockRenderer):
    blocktypes = [50, 75, 76]
    renderstate = ChunkCalculator.renderstateAlphaTest
    torchOffsetsStraight = [
        [  # FaceXIncreasing
            (-7 / 16., 0, 0),
            (-7 / 16., 0, 0),
            (-7 / 16., 0, 0),
            (-7 / 16., 0, 0),
        ],
        [  # FaceXDecreasing
            (7 / 16., 0, 0),
            (7 / 16., 0, 0),
            (7 / 16., 0, 0),
            (7 / 16., 0, 0),
        ],
        [  # FaceYIncreasing
            (7 / 16., -6 / 16., 7 / 16.),
            (7 / 16., -6 / 16., -7 / 16.),
            (-7 / 16., -6 / 16., -7 / 16.),
            (-7 / 16., -6 / 16., 7 / 16.),
        ],
        [  # FaceYDecreasing
            (7 / 16., 0., 7 / 16.),
            (-7 / 16., 0., 7 / 16.),
            (-7 / 16., 0., -7 / 16.),
            (7 / 16., 0., -7 / 16.),
        ],

        [  # FaceZIncreasing
            (0, 0, -7 / 16.),
            (0, 0, -7 / 16.),
            (0, 0, -7 / 16.),
            (0, 0, -7 / 16.)
        ],
        [  # FaceZDecreasing
            (0, 0, 7 / 16.),
            (0, 0, 7 / 16.),
            (0, 0, 7 / 16.),
            (0, 0, 7 / 16.)
        ],

    ]

    torchOffsetsSouth = [
        [  # FaceXIncreasing
            (-7 / 16., 3 / 16., 0),
            (-7 / 16., 3 / 16., 0),
            (-7 / 16., 3 / 16., 0),
            (-7 / 16., 3 / 16., 0),
        ],
        [  # FaceXDecreasing
            (7 / 16., 3 / 16., 0),
            (7 / 16., 3 / 16., 0),
            (7 / 16., 3 / 16., 0),
            (7 / 16., 3 / 16., 0),
        ],
        [  # FaceYIncreasing
            (7 / 16., -3 / 16., 7 / 16.),
            (7 / 16., -3 / 16., -7 / 16.),
            (-7 / 16., -3 / 16., -7 / 16.),
            (-7 / 16., -3 / 16., 7 / 16.),
        ],
        [  # FaceYDecreasing
            (7 / 16., 3 / 16., 7 / 16.),
            (-7 / 16., 3 / 16., 7 / 16.),
            (-7 / 16., 3 / 16., -7 / 16.),
            (7 / 16., 3 / 16., -7 / 16.),
        ],

        [  # FaceZIncreasing
            (0, 3 / 16., -7 / 16.),
            (0, 3 / 16., -7 / 16.),
            (0, 3 / 16., -7 / 16.),
            (0, 3 / 16., -7 / 16.)
        ],
        [  # FaceZDecreasing
            (0, 3 / 16., 7 / 16.),
            (0, 3 / 16., 7 / 16.),
            (0, 3 / 16., 7 / 16.),
            (0, 3 / 16., 7 / 16.),
        ],

    ]
    torchOffsetsNorth = torchOffsetsWest = torchOffsetsEast = torchOffsetsSouth

    torchOffsets = [
        torchOffsetsStraight,
        torchOffsetsSouth,
        torchOffsetsNorth,
        torchOffsetsWest,
        torchOffsetsEast,
        torchOffsetsStraight,
    ] + [torchOffsetsStraight] * 10

    torchOffsets = numpy.array(torchOffsets, dtype='float32')

    torchOffsets[1][..., 3, :, 0] -= 0.5

    torchOffsets[1][..., 0:2, 0:2, 0] -= 0.5
    torchOffsets[1][..., 4:6, 0:2, 0] -= 0.5
    torchOffsets[1][..., 0:2, 2:4, 0] -= 0.1
    torchOffsets[1][..., 4:6, 2:4, 0] -= 0.1

    torchOffsets[1][..., 2, :, 0] -= 0.25

    torchOffsets[2][..., 3, :, 0] += 0.5
    torchOffsets[2][..., 0:2, 0:2, 0] += 0.5
    torchOffsets[2][..., 4:6, 0:2, 0] += 0.5
    torchOffsets[2][..., 0:2, 2:4, 0] += 0.1
    torchOffsets[2][..., 4:6, 2:4, 0] += 0.1
    torchOffsets[2][..., 2, :, 0] += 0.25

    torchOffsets[3][..., 3, :, 2] -= 0.5
    torchOffsets[3][..., 0:2, 0:2, 2] -= 0.5
    torchOffsets[3][..., 4:6, 0:2, 2] -= 0.5
    torchOffsets[3][..., 0:2, 2:4, 2] -= 0.1
    torchOffsets[3][..., 4:6, 2:4, 2] -= 0.1
    torchOffsets[3][..., 2, :, 2] -= 0.25

    torchOffsets[4][..., 3, :, 2] += 0.5
    torchOffsets[4][..., 0:2, 0:2, 2] += 0.5
    torchOffsets[4][..., 4:6, 0:2, 2] += 0.5
    torchOffsets[4][..., 0:2, 2:4, 2] += 0.1
    torchOffsets[4][..., 4:6, 2:4, 2] += 0.1
    torchOffsets[4][..., 2, :, 2] += 0.25

    upCoords = ((7, 6), (7, 8), (9, 8), (9, 6))
    downCoords = ((7, 14), (7, 16), (9, 16), (9, 14))

    def makeTorchVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        blockIndices = self.getMaterialIndices(blockMaterials)
        torchOffsets = self.torchOffsets[blockData[blockIndices]]
        texes = texMap(blocks[blockIndices], blockData[blockIndices])
        yield
        arrays = []
        for direction in range(6):
            vertexArray = self.makeTemplate(direction, blockIndices)
            if not len(vertexArray):
                return

            vertexArray.view('uint8')[_RGBA] = 0xff
            vertexArray[_XYZ] += torchOffsets[:, direction]
            if direction == pymclevel.faces.FaceYIncreasing:
                vertexArray[_ST] = self.upCoords
            if direction == pymclevel.faces.FaceYDecreasing:
                vertexArray[_ST] = self.downCoords
            vertexArray[_ST] += texes[:, numpy.newaxis, direction]
            arrays.append(vertexArray)
            yield
        self.vertexArrays = arrays

    makeVertices = makeTorchVertices


class RailBlockRenderer(BlockRenderer):
    blocktypes = [pymclevel.materials.alphaMaterials.Rail.ID, pymclevel.materials.alphaMaterials.PoweredRail.ID, pymclevel.materials.alphaMaterials.DetectorRail.ID]
    renderstate = ChunkCalculator.renderstateAlphaTest

    railTextures = numpy.array([
        [(0, 128), (0, 144), (16, 144), (16, 128)],  # east-west
        [(0, 128), (16, 128), (16, 144), (0, 144)],  # north-south
        [(0, 128), (16, 128), (16, 144), (0, 144)],  # south-ascending
        [(0, 128), (16, 128), (16, 144), (0, 144)],  # north-ascending
        [(0, 128), (0, 144), (16, 144), (16, 128)],  # east-ascending
        [(0, 128), (0, 144), (16, 144), (16, 128)],  # west-ascending

        [(0, 112), (0, 128), (16, 128), (16, 112)],  # northeast corner
        [(0, 128), (16, 128), (16, 112), (0, 112)],  # southeast corner
        [(16, 128), (16, 112), (0, 112), (0, 128)],  # southwest corner
        [(16, 112), (0, 112), (0, 128), (16, 128)],  # northwest corner

        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown

    ], dtype='float32')
    railTextures -= pymclevel.materials.alphaMaterials.blockTextures[pymclevel.materials.alphaMaterials.Rail.ID, 0, 0]

    railOffsets = numpy.array([
        [0, 0, 0, 0],
        [0, 0, 0, 0],

        [0, 0, 1, 1],  # south-ascending
        [1, 1, 0, 0],  # north-ascending
        [1, 0, 0, 1],  # east-ascending
        [0, 1, 1, 0],  # west-ascending

        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],

        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],

    ], dtype='float32')

    def makeRailVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        direction = pymclevel.faces.FaceYIncreasing
        blockIndices = self.getMaterialIndices(blockMaterials)
        yield

        bdata = blockData[blockIndices]
        railBlocks = blocks[blockIndices]
        tex = texMap(railBlocks, bdata, pymclevel.faces.FaceYIncreasing)[:, numpy.newaxis, :]

        # disable 'powered' or 'pressed' bit for powered and detector rails
        bdata[railBlocks != pymclevel.materials.alphaMaterials.Rail.ID] &= ~0x8

        vertexArray = self.makeTemplate(direction, blockIndices)
        if not len(vertexArray):
            return

        vertexArray[_ST] = self.railTextures[bdata]
        vertexArray[_ST] += tex

        vertexArray[_XYZ][..., 1] -= 0.9
        vertexArray[_XYZ][..., 1] += self.railOffsets[bdata]

        blockLight = areaBlockLights[1:-1, 1:-1, 1:-1]

        vertexArray.view('uint8')[_RGB] *= blockLight[blockIndices][..., numpy.newaxis, numpy.newaxis]
        yield
        self.vertexArrays = [vertexArray]

    makeVertices = makeRailVertices


class LadderBlockRenderer(BlockRenderer):
    blocktypes = [pymclevel.materials.alphaMaterials.Ladder.ID]

    ladderOffsets = numpy.array([
        [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)],
        [(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)],

        [(0, -1, 0.9), (0, 0, -0.1), (0, 0, -0.1), (0, -1, 0.9)],  # facing east
        [(0, 0, 0.1), (0, -1, -.9), (0, -1, -.9), (0, 0, 0.1)],  # facing west
        [(.9, -1, 0), (.9, -1, 0), (-.1, 0, 0), (-.1, 0, 0)],  # north
        [(0.1, 0, 0), (0.1, 0, 0), (-.9, -1, 0), (-.9, -1, 0)],  # south

    ] + [[(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)]] * 10, dtype='float32')

    ladderTextures = numpy.array([
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown
        [(0, 192), (0, 208), (16, 208), (16, 192)],  # unknown

        [(64, 96), (64, 80), (48, 80), (48, 96), ],  # e
        [(48, 80), (48, 96), (64, 96), (64, 80), ],  # w
        [(48, 96), (64, 96), (64, 80), (48, 80), ],  # n
        [(64, 80), (48, 80), (48, 96), (64, 96), ],  # s

        ] + [[(0, 192), (0, 208), (16, 208), (16, 192)]] * 10, dtype='float32')

    def ladderVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        blockIndices = self.getMaterialIndices(blockMaterials)
        blockLight = areaBlockLights[1:-1, 1:-1, 1:-1]
        yield
        bdata = blockData[blockIndices]

        vertexArray = self.makeTemplate(pymclevel.faces.FaceYIncreasing, blockIndices)
        if not len(vertexArray):
            return

        vertexArray[_ST] = self.ladderTextures[bdata]
        vertexArray[_XYZ] += self.ladderOffsets[bdata]
        vertexArray.view('uint8')[_RGB] *= blockLight[blockIndices][..., numpy.newaxis, numpy.newaxis]

        yield
        self.vertexArrays = [vertexArray]

    makeVertices = ladderVertices


class SnowBlockRenderer(BlockRenderer):
    snowID = 78

    blocktypes = [snowID]

    def makeSnowVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        snowIndices = self.getMaterialIndices(blockMaterials)
        arrays = []
        yield
        for direction, exposedFaceIndices in enumerate(facingBlockIndices):
    # def makeFaceVertices(self, direction, blockIndices, exposedFaceIndices, blocks, blockData, blockLight, facingBlockLight, texMap):
        # return []

            if direction != pymclevel.faces.FaceYIncreasing:
                blockIndices = snowIndices & exposedFaceIndices
            else:
                blockIndices = snowIndices

            facingBlockLight = areaBlockLights[self.directionOffsets[direction]]
            lights = facingBlockLight[blockIndices][..., numpy.newaxis, numpy.newaxis]

            vertexArray = self.makeTemplate(direction, blockIndices)
            if not len(vertexArray):
                continue

            vertexArray[_ST] += texMap([self.snowID], 0, 0)[:, numpy.newaxis, 0:2]
            vertexArray.view('uint8')[_RGB] *= lights

            if direction == pymclevel.faces.FaceYIncreasing:
                vertexArray[_XYZ][..., 1] -= 0.875

            if direction != pymclevel.faces.FaceYIncreasing and direction != pymclevel.faces.FaceYDecreasing:
                vertexArray[_XYZ][..., 2:4, 1] -= 0.875
                vertexArray[_ST][..., 2:4, 1] += 14

            arrays.append(vertexArray)
            yield
        self.vertexArrays = arrays

    makeVertices = makeSnowVertices


class RedstoneBlockRenderer(BlockRenderer):
    blocktypes = [55]

    def redstoneVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        blockIndices = self.getMaterialIndices(blockMaterials)
        yield
        vertexArray = self.makeTemplate(pymclevel.faces.FaceYIncreasing, blockIndices)
        if not len(vertexArray):
            return

        vertexArray[_ST] += pymclevel.materials.alphaMaterials.blockTextures[55, 0, 0]
        vertexArray[_XYZ][..., 1] -= 0.9

        bdata = blockData[blockIndices]

        bdata <<= 3
        # bdata &= 0xe0
        bdata[bdata > 0] |= 0x80

        vertexArray.view('uint8')[_RGBA][..., 0] = bdata[..., numpy.newaxis]
        vertexArray.view('uint8')[_RGBA][..., 0:3] *= [1, 0, 0]

        yield
        self.vertexArrays = [vertexArray]

    makeVertices = redstoneVertices

# button, floor plate, door -> 1-cube features


class FeatureBlockRenderer(BlockRenderer):
#    blocktypes = [pymclevel.materials.alphaMaterials.Button.ID,
#                  pymclevel.materials.alphaMaterials.StoneFloorPlate.ID,
#                  pymclevel.materials.alphaMaterials.WoodFloorPlate.ID,
#                  pymclevel.materials.alphaMaterials.WoodenDoor.ID,
#                  pymclevel.materials.alphaMaterials.IronDoor.ID,
#                  ]
#
    blocktypes = [pymclevel.materials.alphaMaterials.Fence.ID]

    buttonOffsets = [
        [[-14 / 16., 6 / 16., -5 / 16.],
         [-14 / 16., 6 / 16., 5 / 16.],
         [-14 / 16., -7 / 16., 5 / 16.],
         [-14 / 16., -7 / 16., -5 / 16.],
        ],
        [[0 / 16., 6 / 16., 5 / 16.],
         [0 / 16., 6 / 16., -5 / 16.],
         [0 / 16., -7 / 16., -5 / 16.],
         [0 / 16., -7 / 16., 5 / 16.],
        ],

        [[0 / 16., -7 / 16., 5 / 16.],
         [0 / 16., -7 / 16., -5 / 16.],
         [-14 / 16., -7 / 16., -5 / 16.],
         [-14 / 16., -7 / 16., 5 / 16.],
        ],
        [[0 / 16., 6 / 16., 5 / 16.],
         [-14 / 16., 6 / 16., 5 / 16.],
         [-14 / 16., 6 / 16., -5 / 16.],
         [0 / 16., 6 / 16., -5 / 16.],
        ],

        [[0 / 16., 6 / 16., -5 / 16.],
         [-14 / 16., 6 / 16., -5 / 16.],
         [-14 / 16., -7 / 16., -5 / 16.],
         [0 / 16., -7 / 16., -5 / 16.],
        ],
        [[-14 / 16., 6 / 16., 5 / 16.],
         [0 / 16., 6 / 16., 5 / 16.],
         [0 / 16., -7 / 16., 5 / 16.],
         [-14 / 16., -7 / 16., 5 / 16.],
        ],
    ]
    buttonOffsets = numpy.array(buttonOffsets)
    buttonOffsets[buttonOffsets < 0] += 1.0

    dirIndexes = ((3, 2), (-3, 2), (1, 3), (1, 3), (-1, 2), (1, 2))

    def buttonVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        blockIndices = blocks == pymclevel.materials.alphaMaterials.Button.ID
        axes = blockIndices.nonzero()

        vertexArray = numpy.zeros((len(axes[0]), 6, 4, 6), dtype=numpy.float32)
        vertexArray[_XYZ][..., 0] = axes[0][..., numpy.newaxis, numpy.newaxis]
        vertexArray[_XYZ][..., 1] = axes[2][..., numpy.newaxis, numpy.newaxis]
        vertexArray[_XYZ][..., 2] = axes[1][..., numpy.newaxis, numpy.newaxis]

        vertexArray[_XYZ] += self.buttonOffsets
        vertexArray[_ST] = [[0, 0], [0, 16], [16, 16], [16, 0]]
        vertexArray[_ST] += texMap(pymclevel.materials.alphaMaterials.Stone.ID, 0)[numpy.newaxis, :, numpy.newaxis]

        # if direction == 0:
#        for i, j in enumerate(self.dirIndexes[direction]):
#                if j < 0:
#                    j = -j
#                    j -= 1
#                    offs = self.buttonOffsets[direction, ..., j] * 16
#                    offs = 16 - offs
#
#                else:
#                    j -= 1
#                    offs =self.buttonOffsets[direction, ..., j] * 16
#
#                # if i == 1:
#                #
#                #    vertexArray[_ST][...,i] -= offs
#                # else:
#                vertexArray[_ST][...,i] -= offs
#
        vertexArray.view('uint8')[_RGB] = 255
        vertexArray.shape = (len(axes[0]) * 6, 4, 6)

        self.vertexArrays = [vertexArray]

    fenceTemplates = makeVertexTemplates(3 / 8., 0, 3 / 8., 5 / 8., 1, 5 / 8.)

    def fenceVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        fenceMask = blocks == pymclevel.materials.alphaMaterials.Fence.ID
        fenceIndices = fenceMask.nonzero()
        yield

        vertexArray = numpy.zeros((len(fenceIndices[0]), 6, 4, 6), dtype='float32')
        for i in range(3):
            j = (0, 2, 1)[i]

            vertexArray[..., i] = fenceIndices[j][:, numpy.newaxis, numpy.newaxis]  # xxx swap z with y using ^

        vertexArray[..., 0:5] += self.fenceTemplates[..., 0:5]
        vertexArray[_ST] += pymclevel.materials.alphaMaterials.blockTextures[pymclevel.materials.alphaMaterials.WoodPlanks.ID, 0, 0]

        vertexArray.view('uint8')[_RGB] = self.fenceTemplates[..., 5][..., numpy.newaxis]
        vertexArray.view('uint8')[_A] = 0xFF
        vertexArray.view('uint8')[_RGB] *= areaBlockLights[1:-1, 1:-1, 1:-1][fenceIndices][..., numpy.newaxis, numpy.newaxis, numpy.newaxis]
        vertexArray.shape = (vertexArray.shape[0] * 6, 4, 6)
        yield
        self.vertexArrays = [vertexArray]

    makeVertices = fenceVertices


class StairBlockRenderer(BlockRenderer):
    @classmethod
    def getBlocktypes(cls, mats):
        return [a.ID for a in mats.AllStairs]

    # South - FaceXIncreasing
    # North - FaceXDecreasing
    # West - FaceZIncreasing
    # East - FaceZDecreasing
    stairTemplates = numpy.array([makeVertexTemplates(**kw) for kw in [
        # South - FaceXIncreasing
        {"xmin":0.5},
        # North - FaceXDecreasing
        {"xmax":0.5},
        # West - FaceZIncreasing
        {"zmin":0.5},
        # East - FaceZDecreasing
        {"zmax":0.5},
        # Slabtype
        {"ymax":0.5},
        ]
    ])

    def stairVertices(self, facingBlockIndices, blocks, blockMaterials, blockData, areaBlockLights, texMap):
        arrays = []
        materialIndices = self.getMaterialIndices(blockMaterials)
        yield
        stairBlocks = blocks[materialIndices]
        stairData = blockData[materialIndices]
        stairTop = (stairData >> 2).astype(bool)
        stairData &= 3

        blockLight = areaBlockLights[1:-1, 1:-1, 1:-1]
        x, z, y = materialIndices.nonzero()

        for _ in ("slab", "step"):
            vertexArray = numpy.zeros((len(x), 6, 4, 6), dtype='float32')
            for i in range(3):
                vertexArray[_XYZ][..., i] = (x, y, z)[i][:, numpy.newaxis, numpy.newaxis]

            if _ == "step":
                vertexArray[_XYZST] += self.stairTemplates[4][..., :5]
                vertexArray[_XYZ][..., 1][stairTop] += 0.5
            else:
                vertexArray[_XYZST] += self.stairTemplates[stairData][..., :5]

            vertexArray[_ST] += texMap(stairBlocks, 0)[..., numpy.newaxis, :]

            vertexArray.view('uint8')[_RGB] = self.stairTemplates[4][numpy.newaxis, ..., 5, numpy.newaxis]
            vertexArray.view('uint8')[_RGB] *= 0xf
            vertexArray.view('uint8')[_A] = 0xff

            vertexArray.shape = (len(x) * 6, 4, 6)
            yield
            arrays.append(vertexArray)
        self.vertexArrays = arrays

    makeVertices = stairVertices

class VineBlockRenderer(BlockRenderer):
    blocktypes = [106]

    SouthBit = 1 #FaceZIncreasing
    WestBit = 2 #FaceXDecreasing
    NorthBit = 4 #FaceZDecreasing
    EastBit = 8 #FaceXIncreasing

    renderstate = ChunkCalculator.renderstateVines

    def vineFaceVertices(self, direction, blockIndices, exposedFaceIndices, blocks, blockData, blockLight, facingBlockLight, texMap):

        bdata = blockData[blockIndices]
        blockIndices = numpy.array(blockIndices)
        if direction == pymclevel.faces.FaceZIncreasing:
            blockIndices[blockIndices] = (bdata & 1).astype(bool)
        elif direction == pymclevel.faces.FaceXDecreasing:
            blockIndices[blockIndices] = (bdata & 2).astype(bool)
        elif direction == pymclevel.faces.FaceZDecreasing:
            blockIndices[blockIndices] = (bdata & 4).astype(bool)
        elif direction == pymclevel.faces.FaceXIncreasing:
            blockIndices[blockIndices] = (bdata & 8).astype(bool)
        else:
            return []
        vertexArray = self.makeTemplate(direction, blockIndices)
        if not len(vertexArray):
            return vertexArray

        vertexArray[_ST] += texMap(self.blocktypes[0], [0], direction)[:, numpy.newaxis, 0:2]

        lights = blockLight[blockIndices][..., numpy.newaxis, numpy.newaxis]
        vertexArray.view('uint8')[_RGB] *= lights

        vertexArray.view('uint8')[_RGB] *= LeafBlockRenderer.leafColor

        if direction == pymclevel.faces.FaceZIncreasing:
            vertexArray[_XYZ][..., 2] -= 0.0625
        if direction == pymclevel.faces.FaceXDecreasing:
            vertexArray[_XYZ][..., 0] += 0.0625
        if direction == pymclevel.faces.FaceZDecreasing:
            vertexArray[_XYZ][..., 2] += 0.0625
        if direction == pymclevel.faces.FaceXIncreasing:
            vertexArray[_XYZ][..., 0] -= 0.0625

        return vertexArray

    makeFaceVertices = vineFaceVertices


class SlabBlockRenderer(BlockRenderer):
    blocktypes = [44, 126]

    def slabFaceVertices(self, direction, blockIndices, exposedFaceIndices, blocks, blockData, blockLight, facingBlockLight, texMap):
        if direction != pymclevel.faces.FaceYIncreasing:
            blockIndices = blockIndices & exposedFaceIndices

        lights = facingBlockLight[blockIndices][..., numpy.newaxis, numpy.newaxis]
        bdata = blockData[blockIndices]
        top = (bdata >> 3).astype(bool)
        bdata &= 7

        vertexArray = self.makeTemplate(direction, blockIndices)
        if not len(vertexArray):
            return vertexArray

        vertexArray[_ST] += texMap(blocks[blockIndices], bdata, direction)[:, numpy.newaxis, 0:2]
        vertexArray.view('uint8')[_RGB] *= lights

        if direction == pymclevel.faces.FaceYIncreasing:
            vertexArray[_XYZ][..., 1] -= 0.5

        if direction != pymclevel.faces.FaceYIncreasing and direction != pymclevel.faces.FaceYDecreasing:
            vertexArray[_XYZ][..., 2:4, 1] -= 0.5
            vertexArray[_ST][..., 2:4, 1] += 8

        vertexArray[_XYZ][..., 1][top] += 0.5

        return vertexArray

    makeFaceVertices = slabFaceVertices


class WaterBlockRenderer(BlockRenderer):
    waterID = 9
    blocktypes = [8, waterID]
    renderstate = ChunkCalculator.renderstateWater

    def waterFaceVertices(self, direction, blockIndices, exposedFaceIndices, blocks, blockData, blockLight, facingBlockLight, texMap):
        blockIndices = blockIndices & exposedFaceIndices
        vertexArray = self.makeTemplate(direction, blockIndices)
        vertexArray[_ST] += texMap(self.waterID, 0, 0)[numpy.newaxis, numpy.newaxis]
        vertexArray.view('uint8')[_RGB] *= facingBlockLight[blockIndices][..., numpy.newaxis, numpy.newaxis]
        return vertexArray

    makeFaceVertices = waterFaceVertices


class IceBlockRenderer(BlockRenderer):
    iceID = 79
    blocktypes = [iceID]
    renderstate = ChunkCalculator.renderstateIce

    def iceFaceVertices(self, direction, blockIndices, exposedFaceIndices, blocks, blockData, blockLight, facingBlockLight, texMap):
        blockIndices = blockIndices & exposedFaceIndices
        vertexArray = self.makeTemplate(direction, blockIndices)
        vertexArray[_ST] += texMap(self.iceID, 0, 0)[numpy.newaxis, numpy.newaxis]
        vertexArray.view('uint8')[_RGB] *= facingBlockLight[blockIndices][..., numpy.newaxis, numpy.newaxis]
        return vertexArray

    makeFaceVertices = iceFaceVertices

from glutils import DisplayList


class MCRenderer(object):
    isPreviewer = False

    def __init__(self, level=None, alpha=1.0):
        self.render = True
        self.origin = (0, 0, 0)
        self.rotation = 0

        self.bufferUsage = 0

        self.invalidChunkQueue = deque()
        self._chunkWorker = None
        self.chunkRenderers = {}
        self.loadableChunkMarkers = DisplayList()
        self.visibleLayers = set(Layer.AllLayers)

        self.masterLists = None

        alpha = alpha * 255
        self.alpha = (int(alpha) & 0xff)

        self.chunkStartTime = datetime.now()
        self.oldChunkStartTime = self.chunkStartTime

        self.oldPosition = None

        self.chunkSamples = [timedelta(0, 0, 0)] * 15

        self.chunkIterator = None

        import leveleditor
        Settings = leveleditor.Settings

        Settings.fastLeaves.addObserver(self)

        Settings.roughGraphics.addObserver(self)
        Settings.showHiddenOres.addObserver(self)
        Settings.vertexBufferLimit.addObserver(self)

        Settings.drawEntities.addObserver(self)
        Settings.drawTileEntities.addObserver(self)
        Settings.drawTileTicks.addObserver(self)
        Settings.drawUnpopulatedChunks.addObserver(self, "drawTerrainPopulated")
        Settings.drawMonsters.addObserver(self)
        Settings.drawItems.addObserver(self)

        Settings.showChunkRedraw.addObserver(self, "showRedraw")
        Settings.spaceHeight.addObserver(self)
        Settings.targetFPS.addObserver(self, "targetFPS")

        self.level = level

    chunkClass = ChunkRenderer
    calculatorClass = ChunkCalculator

    minViewDistance = 2
    maxViewDistance = 24

    _viewDistance = 8

    needsRedraw = True

    def toggleLayer(self, val, layer):
        if val:
            self.visibleLayers.add(layer)
        else:
            self.visibleLayers.discard(layer)
        for cr in self.chunkRenderers.itervalues():
            cr.invalidLayers.add(layer)

        self.loadNearbyChunks()

    def layerProperty(layer, default=True):  # @NoSelf
        attr = intern("_draw" + layer)

        def _get(self):
            return getattr(self, attr, default)

        def _set(self, val):
            if val != _get(self):
                setattr(self, attr, val)
                self.toggleLayer(val, layer)

        return property(_get, _set)

    drawEntities = layerProperty(Layer.Entities)
    drawTileEntities = layerProperty(Layer.TileEntities)
    drawTileTicks = layerProperty(Layer.TileTicks)
    drawMonsters = layerProperty(Layer.Monsters)
    drawItems = layerProperty(Layer.Items)
    drawTerrainPopulated = layerProperty(Layer.TerrainPopulated)

    def inSpace(self):
        if self.level is None:
            return True
        h = self.position[1]
        return ((h > self.level.Height + self.spaceHeight) or
                (h <= -self.spaceHeight))

    def chunkDistance(self, cpos):
        camx, camy, camz = self.position

        # if the renderer is offset into the world somewhere, adjust for that
        ox, oy, oz = self.origin
        camx -= ox
        camz -= oz

        camcx = int(numpy.floor(camx)) >> 4
        camcz = int(numpy.floor(camz)) >> 4

        cx, cz = cpos

        return max(abs(cx - camcx), abs(cz - camcz))

    overheadMode = False

    def detailLevelForChunk(self, cpos):
        if self.overheadMode:
            return 2
        if self.isPreviewer:
            w, l, h = self.level.bounds.size
            if w + l < 256:
                return 0

        distance = self.chunkDistance(cpos) - self.viewDistance
        if distance > 0 or self.inSpace():
            return 1
        return 0

    def getViewDistance(self):
        return self._viewDistance

    def setViewDistance(self, vd):
        vd = int(vd) & 0xfffe
        vd = min(max(vd, self.minViewDistance), self.maxViewDistance)
        if vd != self._viewDistance:
            self._viewDistance = vd
            self.viewDistanceChanged()
            # self.invalidateChunkMarkers()

    viewDistance = property(getViewDistance, setViewDistance, None, "View Distance")

    @property
    def effectiveViewDistance(self):
        if self.inSpace():
            return self.viewDistance * 4
        else:
            return self.viewDistance * 2

    def viewDistanceChanged(self):
        self.oldPosition = None  # xxx
        self.discardMasterList()
        self.loadNearbyChunks()
        self.discardChunksOutsideViewDistance()

    maxWorkFactor = 64
    minWorkFactor = 1
    workFactor = 2

    chunkCalculator = None

    _level = None

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level):
        """ this probably warrants creating a new renderer """
        self.stopWork()

        self._level = level
        self.oldPosition = None
        self.position = (0, 0, 0)
        self.chunkCalculator = None

        self.invalidChunkQueue = deque()

        self.discardAllChunks()

        self.loadableChunkMarkers.invalidate()

        if level:
            self.chunkCalculator = self.calculatorClass(self.level)

            self.oldPosition = None
            level.allChunks

        self.loadNearbyChunks()

    position = (0, 0, 0)

    def loadChunksStartingFrom(self, wx, wz, distance=None):  # world position
        if None is self.level:
            return

        cx = wx >> 4
        cz = wz >> 4

        if distance is None:
            d = self.effectiveViewDistance
        else:
            d = distance

        self.chunkIterator = self.iterateChunks(wx, wz, d * 2)

    def iterateChunks(self, x, z, d):
        cx = x >> 4
        cz = z >> 4

        yield (cx, cz)

        step = dir = 1

        while True:
            for i in range(step):
                cx += dir
                yield (cx, cz)

            for i in range(step):
                cz += dir
                yield (cx, cz)

            step += 1
            if step > d and not self.overheadMode:
                raise StopIteration

            dir = -dir

    chunkIterator = None

    @property
    def chunkWorker(self):
        if self._chunkWorker is None:
            self._chunkWorker = self.makeWorkIterator()
        return self._chunkWorker

    def stopWork(self):
        self._chunkWorker = None

    def discardAllChunks(self):
        self.bufferUsage = 0
        self.forgetAllDisplayLists()
        self.chunkRenderers = {}
        self.oldPosition = None  # xxx force reload

    def discardChunksInBox(self, box):
        self.discardChunks(box.chunkPositions)

    def discardChunksOutsideViewDistance(self):
        if self.overheadMode:
            return

        # print "discardChunksOutsideViewDistance"
        d = self.effectiveViewDistance
        cx = (self.position[0] - self.origin[0]) / 16
        cz = (self.position[2] - self.origin[2]) / 16

        origin = (cx - d, cz - d)
        size = d * 2

        if not len(self.chunkRenderers):
            return
        (ox, oz) = origin
        bytes = 0
        # chunks = numpy.fromiter(self.chunkRenderers.iterkeys(), dtype='int32', count=len(self.chunkRenderers))
        chunks = numpy.fromiter(self.chunkRenderers.iterkeys(), dtype='i,i', count=len(self.chunkRenderers))
        chunks.dtype = 'int32'
        chunks.shape = len(self.chunkRenderers), 2

        if size:
            outsideChunks = chunks[:, 0] < ox - 1
            outsideChunks |= chunks[:, 0] > ox + size
            outsideChunks |= chunks[:, 1] < oz - 1
            outsideChunks |= chunks[:, 1] > oz + size
            chunks = chunks[outsideChunks]

        self.discardChunks(chunks)

    def discardChunks(self, chunks):
        for cx, cz in chunks:
            self.discardChunk(cx, cz)
        self.oldPosition = None  # xxx force reload

    def discardChunk(self, cx, cz):
        " discards the chunk renderer for this chunk and compresses the chunk "
        if (cx, cz) in self.chunkRenderers:
            self.bufferUsage -= self.chunkRenderers[cx, cz].bufferSize
            self.chunkRenderers[cx, cz].forgetDisplayLists()
            del self.chunkRenderers[cx, cz]

    _fastLeaves = False

    @property
    def fastLeaves(self):
        return self._fastLeaves

    @fastLeaves.setter
    def fastLeaves(self, val):
        if self._fastLeaves != bool(val):
            self.discardAllChunks()

        self._fastLeaves = bool(val)

    _roughGraphics = False

    @property
    def roughGraphics(self):
        return self._roughGraphics

    @roughGraphics.setter
    def roughGraphics(self, val):
        if self._roughGraphics != bool(val):
            self.discardAllChunks()

        self._roughGraphics = bool(val)

    _showHiddenOres = False

    @property
    def showHiddenOres(self):
        return self._showHiddenOres

    @showHiddenOres.setter
    def showHiddenOres(self, val):
        if self._showHiddenOres != bool(val):
            self.discardAllChunks()

        self._showHiddenOres = bool(val)

    def invalidateChunk(self, cx, cz, layers=None):
        " marks the chunk for regenerating vertex data and display lists "
        if (cx, cz) in self.chunkRenderers:
            # self.chunkRenderers[(cx,cz)].invalidate()
            # self.bufferUsage -= self.chunkRenderers[(cx, cz)].bufferSize

            self.chunkRenderers[(cx, cz)].invalidate(layers)
            # self.bufferUsage += self.chunkRenderers[(cx, cz)].bufferSize

            self.invalidChunkQueue.append((cx, cz))  # xxx encapsulate

    def invalidateChunksInBox(self, box, layers=None):
        # If the box is at the edge of any chunks, expanding by 1 makes sure the neighboring chunk gets redrawn.
        box = box.expand(1)

        self.invalidateChunks(box.chunkPositions, layers)

    def invalidateEntitiesInBox(self, box):
        self.invalidateChunks(box.chunkPositions, [Layer.Entities])

    def invalidateChunks(self, chunks, layers=None):
        for c in chunks:
            cx, cz = c
            self.invalidateChunk(cx, cz, layers)

        self.stopWork()
        self.discardMasterList()
        self.loadNearbyChunks()

    def invalidateAllChunks(self, layers=None):
        self.invalidateChunks(self.chunkRenderers.iterkeys(), layers)

    def forgetAllDisplayLists(self):
        for cr in self.chunkRenderers.itervalues():
            cr.forgetDisplayLists()

    def invalidateMasterList(self):
        self.discardMasterList()

    shouldRecreateMasterList = True

    def discardMasterList(self):
        self.shouldRecreateMasterList = True

    @property
    def shouldDrawAll(self):
        box = self.level.bounds
        return self.isPreviewer and box.width + box.length < 256

    distanceToChunkReload = 32.0

    def cameraMovedFarEnough(self):
        if self.shouldDrawAll:
            return False
        if self.oldPosition is None:
            return True

        cPos = self.position
        oldPos = self.oldPosition

        cameraDelta = self.distanceToChunkReload

        return any([abs(x - y) > cameraDelta for x, y in zip(cPos, oldPos)])

    def loadVisibleChunks(self):
        """ loads nearby chunks if the camera has moved beyond a certain distance """

        # print "loadVisibleChunks"
        if self.cameraMovedFarEnough():
            if datetime.now() - self.lastVisibleLoad > timedelta(0, 0.5):
                self.discardChunksOutsideViewDistance()
                self.loadNearbyChunks()

                self.oldPosition = self.position
                self.lastVisibleLoad = datetime.now()

    lastVisibleLoad = datetime.now()

    def loadNearbyChunks(self):
        if None is self.level:
            return
        # print "loadNearbyChunks"
        cameraPos = self.position

        if self.shouldDrawAll:
            self.loadAllChunks()
        else:
            # subtract self.origin to load nearby chunks correctly for preview renderers
            self.loadChunksStartingFrom(int(cameraPos[0]) - self.origin[0], int(cameraPos[2]) - self.origin[2])

    def loadAllChunks(self):
        box = self.level.bounds

        self.loadChunksStartingFrom(box.origin[0] + box.width / 2, box.origin[2] + box.length / 2, max(box.width, box.length))

    _floorTexture = None

    @property
    def floorTexture(self):
        if self._floorTexture is None:
            self._floorTexture = Texture(self.makeFloorTex)
        return self._floorTexture

    def makeFloorTex(self):
        color0 = (0xff, 0xff, 0xff, 0x22)
        color1 = (0xff, 0xff, 0xff, 0x44)

        img = numpy.array([color0, color1, color1, color0], dtype='uint8')

        GL.glTexParameter(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        GL.glTexParameter(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)

        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, 2, 2, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, img)

    def invalidateChunkMarkers(self):
        self.loadableChunkMarkers.invalidate()

    def _drawLoadableChunkMarkers(self):
        if self.level.chunkCount:
            chunkSet = set(self.level.allChunks)

            sizedChunks = chunkMarkers(chunkSet)

            GL.glPushAttrib(GL.GL_FOG_BIT)
            GL.glDisable(GL.GL_FOG)

            GL.glEnable(GL.GL_BLEND)
            GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
            GL.glPolygonOffset(DepthOffset.ChunkMarkers, DepthOffset.ChunkMarkers)
            GL.glEnable(GL.GL_DEPTH_TEST)

            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glColor(1.0, 1.0, 1.0, 1.0)

            self.floorTexture.bind()
            # chunkColor = numpy.zeros(shape=(chunks.shape[0], 4, 4), dtype='float32')
#            chunkColor[:]= (1, 1, 1, 0.15)
#
#            cc = numpy.array(chunks[:,0] + chunks[:,1], dtype='int32')
#            cc &= 1
#            coloredChunks = cc > 0
#            chunkColor[coloredChunks] = (1, 1, 1, 0.28)
#            chunkColor *= 255
#            chunkColor = numpy.array(chunkColor, dtype='uint8')
#
            # GL.glColorPointer(4, GL.GL_UNSIGNED_BYTE, 0, chunkColor)
            for size, chunks in sizedChunks.iteritems():
                if not len(chunks):
                    continue
                chunks = numpy.array(chunks, dtype='float32')

                chunkPosition = numpy.zeros(shape=(chunks.shape[0], 4, 3), dtype='float32')
                chunkPosition[:, :, (0, 2)] = numpy.array(((0, 0), (0, 1), (1, 1), (1, 0)), dtype='float32')
                chunkPosition[:, :, (0, 2)] *= size
                chunkPosition[:, :, (0, 2)] += chunks[:, numpy.newaxis, :]
                chunkPosition *= 16
                GL.glVertexPointer(3, GL.GL_FLOAT, 0, chunkPosition.ravel())
                # chunkPosition *= 8
                GL.glTexCoordPointer(2, GL.GL_FLOAT, 0, (chunkPosition[..., (0, 2)] * 8).ravel())
                GL.glDrawArrays(GL.GL_QUADS, 0, len(chunkPosition) * 4)

            GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
            GL.glDisable(GL.GL_TEXTURE_2D)
            GL.glDisable(GL.GL_BLEND)
            GL.glDisable(GL.GL_DEPTH_TEST)
            GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
            GL.glPopAttrib()

    def drawLoadableChunkMarkers(self):
        if not self.isPreviewer or isinstance(self.level, pymclevel.MCInfdevOldLevel):
            self.loadableChunkMarkers.call(self._drawLoadableChunkMarkers)

        # self.drawCompressedChunkMarkers()

    needsImmediateRedraw = False
    viewingFrustum = None
    if "-debuglists" in sys.argv:
        def createMasterLists(self):
            pass

        def callMasterLists(self):
            for cr in self.chunkRenderers.itervalues():
                cr.debugDraw()
    else:
        def createMasterLists(self):
            if self.shouldRecreateMasterList:
                lists = {}
                chunkLists = defaultdict(list)
                chunksPerFrame = 80
                shouldRecreateAgain = False

                for ch in self.chunkRenderers.itervalues():
                    if chunksPerFrame:
                        if ch.needsRedisplay:
                            chunksPerFrame -= 1
                        ch.makeDisplayLists()
                    else:
                        shouldRecreateAgain = True

                    if ch.renderstateLists:
                        for rs in ch.renderstateLists:
                            chunkLists[rs] += ch.renderstateLists[rs]

                for rs in chunkLists:
                    if len(chunkLists[rs]):
                        lists[rs] = numpy.array(chunkLists[rs], dtype='uint32').ravel()

                # lists = lists[lists.nonzero()]
                self.masterLists = lists
                self.shouldRecreateMasterList = shouldRecreateAgain
                self.needsImmediateRedraw = shouldRecreateAgain

        def callMasterLists(self):
            for renderstate in self.chunkCalculator.renderstates:
                if renderstate not in self.masterLists:
                    continue

                if self.alpha != 0xff and renderstate is not ChunkCalculator.renderstateLowDetail:
                    GL.glEnable(GL.GL_BLEND)
                renderstate.bind()

                GL.glCallLists(self.masterLists[renderstate])

                renderstate.release()
                if self.alpha != 0xff and renderstate is not ChunkCalculator.renderstateLowDetail:
                    GL.glDisable(GL.GL_BLEND)

    errorLimit = 10

    def draw(self):
        self.needsRedraw = False
        if not self.level:
            return
        if not self.chunkCalculator:
            return
        if not self.render:
            return

        chunksDrawn = 0
        if self.level.materials.name in ("Pocket", "Alpha"):
            GL.glMatrixMode(GL.GL_TEXTURE)
            GL.glScalef(1/2., 1/2., 1/2.)

        with gl.glPushMatrix(GL.GL_MODELVIEW):
            dx, dy, dz = self.origin
            GL.glTranslate(dx, dy, dz)

            GL.glEnable(GL.GL_CULL_FACE)
            GL.glEnable(GL.GL_DEPTH_TEST)

            self.level.materials.terrainTexture.bind()
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)

            offset = DepthOffset.PreviewRenderer if self.isPreviewer else DepthOffset.Renderer
            GL.glPolygonOffset(offset, offset)
            GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)

            self.createMasterLists()
            try:
                self.callMasterLists()

            except GL.GLError, e:
                if self.errorLimit:
                    self.errorLimit -= 1
                    traceback.print_exc()
                    print e

            GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)

            GL.glDisable(GL.GL_CULL_FACE)
            GL.glDisable(GL.GL_DEPTH_TEST)

            GL.glDisable(GL.GL_TEXTURE_2D)
            GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
                # if self.drawLighting:
            self.drawLoadableChunkMarkers()

        if self.level.materials.name in ("Pocket", "Alpha"):
            GL.glMatrixMode(GL.GL_TEXTURE)
            GL.glScalef(2., 2., 2.)

    renderErrorHandled = False

    def addDebugInfo(self, addDebugString):
        addDebugString("BU: {0} MB, ".format(
            self.bufferUsage / 1000000,
             ))

        addDebugString("WQ: {0}, ".format(len(self.invalidChunkQueue)))
        if self.chunkIterator:
            addDebugString("[LR], ")

        addDebugString("CR: {0}, ".format(len(self.chunkRenderers),))

    def next(self):
        self.chunkWorker.next()

    def makeWorkIterator(self):
        ''' does chunk face and vertex calculation work. returns a generator that can be
        iterated over for smaller work units.'''

        try:
            while True:
                if self.level is None:
                    raise StopIteration

                if len(self.invalidChunkQueue) > 1024:
                    self.invalidChunkQueue.clear()

                if len(self.invalidChunkQueue):
                    c = self.invalidChunkQueue[0]
                    for i in self.workOnChunk(c):
                        yield
                    self.invalidChunkQueue.popleft()

                elif self.chunkIterator is None:
                    raise StopIteration

                else:
                    c = self.chunkIterator.next()
                    if self.vertexBufferLimit:
                        while self.bufferUsage > (0.9 * (self.vertexBufferLimit << 20)):
                            deadChunk = None
                            deadDistance = self.chunkDistance(c)
                            for cr in self.chunkRenderers.itervalues():
                                dist = self.chunkDistance(cr.chunkPosition)
                                if dist > deadDistance:
                                    deadChunk = cr
                                    deadDistance = dist

                            if deadChunk is not None:
                                self.discardChunk(*deadChunk.chunkPosition)

                            else:
                                break

                        else:
                            for i in self.workOnChunk(c):
                                yield

                    else:
                        for i in self.workOnChunk(c):
                            yield

                yield

        finally:
            self._chunkWorker = None
            if self.chunkIterator:
                self.chunkIterator = None

    vertexBufferLimit = 384

    def getChunkRenderer(self, c):
        if not (c in self.chunkRenderers):
            cr = self.chunkClass(self, c)
        else:
            cr = self.chunkRenderers[c]

        return cr

    def calcFacesForChunkRenderer(self, cr):
        self.bufferUsage -= cr.bufferSize

        calc = cr.calcFaces()
        work = 0
        for i in calc:
            yield
            work += 1

        self.chunkDone(cr, work)

    def workOnChunk(self, c):
        work = 0

        if self.level.containsChunk(*c):
            cr = self.getChunkRenderer(c)
            if self.viewingFrustum:
                # if not self.viewingFrustum.visible(numpy.array([[c[0] * 16 + 8, 64, c[1] * 16 + 8, 1.0]]), 64).any():
                if not self.viewingFrustum.visible1([c[0] * 16 + 8, self.level.Height / 2, c[1] * 16 + 8, 1.0], self.level.Height / 2):
                    raise StopIteration
                    yield

            faceInfoCalculator = self.calcFacesForChunkRenderer(cr)
            try:
                for result in faceInfoCalculator:
                    work += 1
                    if (work % MCRenderer.workFactor) == 0:
                        yield

                self.invalidateMasterList()

            except Exception, e:
                traceback.print_exc()
                fn = c

                logging.info(u"Skipped chunk {f}: {e}".format(e=e, f=fn))

    redrawChunks = 0

    def chunkDone(self, chunkRenderer, work):
        self.chunkRenderers[chunkRenderer.chunkPosition] = chunkRenderer
        self.bufferUsage += chunkRenderer.bufferSize
        # print "Chunk {0} used {1} work units".format(chunkRenderer.chunkPosition, work)
        if not self.needsRedraw:
            if self.redrawChunks:
                self.redrawChunks -= 1
                if not self.redrawChunks:
                    self.needsRedraw = True

            else:
                self.redrawChunks = 2

        if work > 0:
            self.oldChunkStartTime = self.chunkStartTime
            self.chunkStartTime = datetime.now()
            self.chunkSamples.pop(0)
            self.chunkSamples.append(self.chunkStartTime - self.oldChunkStartTime)

            cx, cz = chunkRenderer.chunkPosition



class PreviewRenderer(MCRenderer):
    isPreviewer = True


def rendermain():
    renderer = MCRenderer()

    renderer.level = pymclevel.mclevel.loadWorld("World1")
    renderer.viewDistance = 6
    renderer.detailLevelForChunk = lambda * x: 0
    start = datetime.now()

    renderer.loadVisibleChunks()

    try:
        while True:
        # for i in range(100):
            renderer.next()
    except StopIteration:
        pass
    except Exception, e:
        traceback.print_exc()
        print repr(e)

    duration = datetime.now() - start
    perchunk = duration / len(renderer.chunkRenderers)
    print "Duration: {0} ({1} chunks per second, {2} per chunk, {3} chunks)".format(duration, 1000000.0 / perchunk.microseconds, perchunk, len(renderer.chunkRenderers))

    # display.init( (640, 480), OPENGL | DOUBLEBUF )
    from mcedit import GLDisplayContext
    from OpenGL import GLU
    cxt = GLDisplayContext()
    import pygame

    # distance = 4000
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(35, 640.0 / 480.0, 0.5, 4000.0)
    h = 366

    pos = (0, h, 0)

    look = (0.0001, h - 1, 0.0001)
    up = (0, 1, 0)
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()

    GLU.gluLookAt(pos[0], pos[1], pos[2],
                   look[0], look[1], look[2],
                   up[0], up[1], up[2])

    GL.glClearColor(0.0, 0.0, 0.0, 1.0)

    framestart = datetime.now()
    frames = 200
    for i in range(frames):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        renderer.draw()
        pygame.display.flip()

    delta = datetime.now() - framestart
    seconds = delta.seconds + delta.microseconds / 1000000.0
    print "{0} frames in {1} ({2} per frame, {3} FPS)".format(frames, delta, delta / frames, frames / seconds)

    while True:
        evt = pygame.event.poll()
        if evt.type == pygame.MOUSEBUTTONDOWN:
            break
    # time.sleep(3.0)


import traceback
import cProfile

if __name__ == "__main__":
    cProfile.run("rendermain()", "mcedit.profile")

########NEW FILE########