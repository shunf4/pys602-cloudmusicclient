# uncompyle6 version 2.11.3
# Python bytecode 2.5 (62131)
# Decompiled from: Python 2.7.13 (v2.7.13:a06454b1afa1, Dec 17 2016, 20:53:40) [MSC v.1500 64 bit (AMD64)]
# Embedded file name: D:/appuifw2_132843\appuifw2.py
# Compiled at: 2012-09-16 13:07:55
import e32
from appuifw import *
if e32.s60_version_info >= (3, 0):
    import imp
    _appuifw2 = imp.load_dynamic('_appuifw2', 'kf__appuifw2_fd8f9a7f.pyd')
    del imp
else:
    import _appuifw2
version = '1.00.0'
version_info = tuple(version.split('.'))

def schedule(target, *args, **kwargs):
    e32.ao_sleep(0, lambda : target(*args, **kwargs))


class Item(object):

    def __init__(self, title, **kwargs):
        kwargs['title'] = title
        self.__dict__.update(kwargs)
        self.__observers = []

    def add_observer(self, observer):
        from weakref import ref
        if ref(observer) not in self.__observers:
            self.__observers.append(ref(observer, self.__del_observer))

    def remove_observer(self, observer):
        from weakref import ref
        self.__del_observer(ref(observer))

    def __del_observer(self, ref):
        try:
            self.__observers.remove(ref)
        except ValueError:
            pass

    def __getattribute__(self, name):
        if not name.startswith('_'):
            for obref in self.__observers:
                ob = obref()
                if hasattr(ob, 'handle_item_getattr'):
                    ob.handle_item_getattr(self, name)

        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if not name.startswith('_'):
            for obref in self.__observers:
                ob = obref()
                if hasattr(ob, 'handle_item_setattr'):
                    ob.handle_item_setattr(self, name)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self.title))


class Listbox2(list):

    def __init__(self, items=[], select_callback=None, double=False, icons=False, markable=False):
        if double:
            if icons:
                mode = 3
            else:
                mode = 1
        else:
            if icons:
                mode = 2
            else:
                mode = 0
            if markable:
                flags = 16385
            else:
                flags = 0
            self.__double = double
            self.__icons = icons
            self.__markable = markable
            list.__init__(self, items)
            self._uicontrolapi = _appuifw2.Listbox2_create(mode, flags, select_callback)
            for item in self:
                self.__item_check(item)
                self.__ui_insert(-1, item)
                item.add_observer(self)

        self.__update_level = 0
        self.__update_mode = 0

    def __ui_insert(self, pos, item):
        if self.__double:
            s = u'%s\t%s' % (item.title, getattr(item, 'subtitle', u''))
        else:
            s = item.title
        if self.__icons:
            try:
                i = item.icon
            except AttributeError:
                raise TypeError('this listbox requires icons')

        else:
            i = None
        api = self._uicontrolapi
        self.begin_update()
        try:
            self.__update_init(1)
            pos = _appuifw2.Listbox2_insert(api, pos, s, i)
            if self.__markable:
                for i in xrange(len(self) - 1, pos, -1):
                    _appuifw2.Listbox2_select(api, i, _appuifw2.Listbox2_select(api, i - 1))

                _appuifw2.Listbox2_select(api, pos, getattr(item, 'marked', False))
        finally:
            self.end_update()

        return

    def __ui_delete(self, pos, count=1):
        api = self._uicontrolapi
        self.begin_update()
        try:
            self.__update_init(2)
            if self.__markable:
                for i in xrange(pos + count, len(self)):
                    _appuifw2.Listbox2_select(api, i, _appuifw2.Listbox2_select(api, i + count))

            _appuifw2.Listbox2_delete(api, pos, count)
        finally:
            self.end_update()

    def __item_check(self, item):
        if not isinstance(item, Item):
            raise TypeError('items must be Item class instances')

    def handle_item_getattr(self, item, name):
        try:
            pos = self.index(item)
        except ValueError:
            return

        if name == 'current':
            item.__dict__[name] = self.current() == pos
        elif name == 'marked':
            item.__dict__[name] = _appuifw2.Listbox2_select(self._uicontrolapi, pos)

    def handle_item_setattr(self, item, name):
        try:
            pos = self.index(item)
        except ValueError:
            return

        if name == 'current':
            if item.__dict__[name]:
                self.set_current(pos)
            else:
                item.__dict__[name] = self.current() == pos
        elif name == 'marked':
            self.begin_update()
            try:
                _appuifw2.Listbox2_select(self._uicontrolapi, pos, item.__dict__[name])
            finally:
                self.end_update()

        elif name in ('title', 'subtitle', 'icon'):
            self.__setitem__(pos, item)

    def begin_update(self):
        self.__update_level += 1

    def end_update(self):
        if self.__update_level == 0:
            return
        self.__update_level -= 1
        if self.__update_level == 0:
            self.__update_process()
            self.__update_mode = 0
            app.refresh()

    def __update_init(self, mode):
        if mode != self.__update_mode:
            self.__update_process()
            self.__update_mode = mode

    def __update_process(self):
        if self.__update_mode == 1:
            _appuifw2.Listbox2_finish_insert(self._uicontrolapi)
        elif self.__update_mode == 2:
            _appuifw2.Listbox2_finish_delete(self._uicontrolapi)

    def clear(self):
        del self[:]

    def append(self, item):
        self.__item_check(item)
        self.__ui_insert(-1, item)
        item.add_observer(self)
        list.append(self, item)

    def extend(self, lst):
        self.begin_update()
        try:
            for item in lst:
                self.__item_check(item)
                self.__ui_insert(-1, item)
                item.add_observer(self)

            list.extend(self, lst)
        finally:
            self.end_update()

    def insert(self, pos, item):
        self.__item_check(item)
        list.insert(self, pos, item)
        if pos < 0:
            pos = 0
        elif pos > len(self):
            pos = -1
        self.__ui_insert(pos, item)
        item.add_observer(self)

    def remove(self, item):
        pos = list.index(self, item)
        list.remove(self, item)
        self.__ui_delete(pos)
        item.remove_observer(self)

    def pop(self, pos=-1):
        item = list.pop(self, pos)
        if pos < 0:
            pos = len(self) + pos + 1
        elif pos >= len(self):
            pos = -1
        self.__ui_delete(pos)
        item.remove_observer(self)
        return item

    def __defcmpfunc(item1, item2):
        s1 = (u'%s%s' % (item1.title, getattr(item1, 'text', u''))).lower()
        s2 = (u'%s%s' % (item2.title, getattr(item2, 'text', u''))).lower()
        return -(s1 < s2)

    def sort(self, cmpfunc=__defcmpfunc):
        list.sort(self, cmpfunc)
        self.begin_update()
        try:
            self.__ui_delete(0, len(self))
            for item in self:
                self.__ui_insert(-1, item)

        finally:
            self.end_update()

    def reverse(self):
        list.reverse(self)
        self.begin_update()
        try:
            self.__ui.delete(0, len(self))
            for item in self:
                self.__ui_insert(-1, item)

        finally:
            self.end_update()

    def current(self):
        pos = _appuifw2.Listbox2_current(self._uicontrolapi)
        if pos is None:
            raise IndexError('no item selected')
        return pos

    def set_current(self, pos):
        if pos < 0:
            pos += len(self)
        self.begin_update()
        try:
            _appuifw2.Listbox2_current(self._uicontrolapi, pos)
        finally:
            self.end_update()

    def current_item(self):
        return self[self.current()]

    def top(self):
        if not len(self):
            raise IndexError('list is empty')
        return _appuifw2.Listbox2_top(self._uicontrolapi)

    def set_top(self, pos):
        if pos < 0:
            pos += len(self)
        if not 0 <= pos < len(self):
            raise IndexError('index out of range')
        self.begin_update()
        try:
            _appuifw2.Listbox2_top(self._uicontrolapi, pos)
        finally:
            self.end_update()

    def top_item(self):
        return self[self.top()]

    def bottom(self):
        if not len(self):
            raise IndexError('list is empty')
        return _appuifw2.Listbox2_bottom(self._uicontrolapi)

    def bottom_item(self):
        return self[self.bottom()]

    def make_visible(self, pos):
        if pos < 0:
            pos += len(self)
        if not 0 <= pos < len(self):
            raise IndexError('index out of range')
        self.begin_update()
        try:
            _appuifw2.Listbox2_make_visible(self._uicontrolapi, pos)
        finally:
            self.end_update()

    def bind(self, event_code, callback):
        _appuifw2.bind(self._uicontrolapi, event_code, callback)

    def marked(self):
        return _appuifw2.Listbox2_selection(self._uicontrolapi)

    def marked_items(self):
        return [ self[x] for x in self.selected() ]

    def clear_marked(self):
        _appuifw2.Listbox2_clear_selection(self._uicontrolapi)

    def empty_list_text(self):
        return _appuifw2.Listbox2_empty_text(self._uicontrolapi)

    def set_empty_list_text(self, text):
        self.begin_update()
        try:
            _appuifw2.Listbox2_empty_text(self._uicontrolapi, text)
        finally:
            self.end_update()

    if e32.s60_version_info >= (3, 0):

        def highlight_rect(self):
            return _appuifw2.Listbox2_highlight_rect(self._uicontrolapi)

    def __setitem__(self, pos, item):
        olditem = self[pos]
        self.__item_check(item)
        list.__setitem__(self, pos, item)
        olditem.remove_observer(self)
        if pos < 0:
            pos = len(self) + pos
        self.begin_update()
        try:
            self.__ui_delete(pos)
            self.__ui_insert(pos, item)
        finally:
            self.end_update()

        item.add_observer(self)

    def __delitem__(self, pos):
        item = self[pos]
        list.__delitem__(self, pos)
        item.remove_observer(self)
        if pos < 0:
            pos = len(self) + pos
        self.__ui_delete(pos)

    def __setslice__(self, i, j, items):
        olditems = self[i:j]
        list.__setslice__(self, i, j, items)
        for item in olditems:
            item.remove_observer(self)

        ln = len(self)
        i = min(ln, max(0, i))
        j = min(ln, max(i, j))
        self.begin_update()
        try:
            self.__ui_delete(i, j - i)
            for pos in xrange(i, i + len(items)):
                self.__ui_insert(pos, self[pos])

        finally:
            self.end_update()

    def __delslice__(self, i, j):
        items = self[i:j]
        size = len(self)
        list.__delslice__(self, i, j)
        for item in items:
            item.remove_observer(self)

        i = min(size, max(0, i))
        j = min(size, max(i, j))
        self.__ui_delete(i, j - i)

    def __repr__(self):
        return '<%s instance at 0x%08X; %d items>' % (self.__class__.__name__, id(self), len(self))


class Listbox(object):

    def __init__(self, items, select_callback=None):
        self.__set_items(items, just_check=True)
        self._uicontrolapi = _appuifw2.Listbox2_create(self.__mode, 0, select_callback)
        self.__set_items(items)

    def __set_items(self, items, just_check=False):
        if not isinstance(items, list):
            raise TypeError('argument 1 must be a list')
        if not items:
            raise ValueError('non-empty list expected')
        item = items[0]
        mode = 0
        if isinstance(item, tuple):
            if len(item) == 2:
                if isinstance(item[1], unicode):
                    mode = 1
                else:
                    mode = 2
            elif len(item) == 3:
                mode = 3
            else:
                raise ValueError('tuple must include 2 or 3 elements')
        if just_check:
            self.__mode = mode
        else:
            if mode != self.__mode:
                raise ValueError('changing of listbox type not permitted')
            api = self._uicontrolapi
            _appuifw2.Listbox2_delete(api)
            if mode == 0:
                for item in items:
                    _appuifw2.Listbox2_insert(api, -1, item)

            elif mode == 1:
                for item in items:
                    _appuifw2.Listbox2_insert(api, -1, u'%s\t%s' % (item[0], item[1]))

            elif mode == 2:
                for item in items:
                    _appuifw2.Listbox2_insert(api, -1, item[0], item[1])

            else:
                for item in items:
                    _appuifw2.Listbox2_insert(api, -1, u'%s\t%s' % (item[0], item[1]), item[2])

            _appuifw2.Listbox2_finish_insert(api)
            app.refresh()

    def bind(self, event_code, callback):
        _appuifw2.bind(self._uicontrolapi, event_code, callback)

    def current(self):
        return _appuifw2.Listbox2_current(self._uicontrolapi)

    def set_list(self, items, current=0):
        app.begin_refresh()
        try:
            self.__set_items(items)
            current = min(len(items) - 1, max(0, current))
            _appuifw2.Listbox2_current(self._uicontrolapi, current)
        finally:
            app.end_refresh()

    if e32.s60_version_info >= (3, 0):

        def __get_size(self):
            return _appuifw2.Listbox2_highlight_rect(self._uicontrolapi)[2:]

        size = property(__get_size)

        def __get_position(self):
            return _appuifw2.Listbox2_highlight_rect(self._uicontrolapi)[:2]

        position = property(__get_position)


class Text(object):

    def __init__(self, text=u'', move_callback=None, edit_callback=None, skinned=False, scrollbar=False, word_wrap=True, t9=True, indicator=True, fixed_case=False, flags=37128, editor_flags=0):
        if not word_wrap:
            flags |= 32
        self._uicontrolapi = _appuifw2.Text2_create(flags, scrollbar, skinned, move_callback, edit_callback)
        if text:
            self.set(text)
            self.set_pos(0)
        if not t9:
            editor_flags |= 2
        if not indicator:
            editor_flags |= 4
        if fixed_case:
            editor_flags |= 1
        if editor_flags:
            _appuifw2.Text2_set_editor_flags(self._uicontrolapi, editor_flags)

    def add(self, text):
        _appuifw2.Text2_add_text(self._uicontrolapi, text)

    def insert(self, pos, text):
        _appuifw2.Text2_insert_text(self._uicontrolapi, pos, text)

    def bind(self, event_code, callback):
        _appuifw2.bind(self._uicontrolapi, event_code, callback)

    def clear(self):
        _appuifw2.Text2_clear_text(self._uicontrolapi)

    def delete(self, pos=0, length=-1):
        _appuifw2.Text2_delete_text(self._uicontrolapi, pos, length)

    def apply(self, pos=0, length=-1):
        _appuifw2.Text2_apply(self._uicontrolapi, pos, length)

    def get_pos(self):
        return _appuifw2.Text2_get_pos(self._uicontrolapi)

    def set_pos(self, cursor_pos, select=False):
        _appuifw2.Text2_set_pos(self._uicontrolapi, cursor_pos, select)

    def len(self):
        return _appuifw2.Text2_text_length(self._uicontrolapi)

    def get(self, pos=0, length=-1):
        return _appuifw2.Text2_get_text(self._uicontrolapi, pos, length)

    def set(self, text):
        _appuifw2.Text2_set_text(self._uicontrolapi, text)

    def __len__(self):
        return _appuifw2.Text2_text_length(self._uicontrolapi)

    def __getitem__(self, i):
        return _appuifw2.Text2_get_text(self._uicontrolapi, i, 1)

    def __setitem__(self, i, value):
        _appuifw2.Text2_delete_text(self._uicontrolapi, i, len(value))
        _appuifw2.Text2_insert_text(self._uicontrolapi, i, value)

    def __delitem__(self, i):
        _appuifw2.Text2_delete_text(self._uicontrolapi, i, 1)

    def __getslice__(self, i, j):
        ln = len(self)
        i = min(ln, max(0, i))
        j = min(ln, max(i, j))
        return _appuifw2.Text2_get_text(self._uicontrolapi, i, j - i)

    def __setslice__(self, i, j, value):
        ln = len(self)
        i = min(ln, max(0, i))
        j = min(ln, max(i, j))
        _appuifw2.Text2_delete_text(self._uicontrolapi, i, j - i)
        _appuifw2.Text2_insert_text(self._uicontrolapi, i, value)

    def __delslice__(self, i, j):
        ln = len(self)
        i = min(ln, max(0, i))
        j = min(ln, max(i, j))
        return _appuifw2.Text2_delete_text(self._uicontrolapi, i, j - i)

    def get_selection(self):
        pos, anchor = _appuifw2.Text2_get_selection(self._uicontrolapi)
        i = min(pos, anchor)
        j = max(pos, anchor)
        return (
         pos, anchor, _appuifw2.Text2_get_text(self._uicontrolapi, i, j - i))

    def set_selection(self, pos, anchor):
        _appuifw2.Text2_set_selection(self._uicontrolapi, pos, anchor)

    def set_word_wrap(self, word_wrap):
        _appuifw2.Text2_set_word_wrap(self._uicontrolapi, word_wrap)

    def set_limit(self, limit):
        _appuifw2.Text2_set_limit(self._uicontrolapi, limit)

    def get_word_info(self, pos=-1):
        return _appuifw2.Text2_get_word_info(self._uicontrolapi, pos)

    def set_case(self, case):
        _appuifw2.Text2_set_case(self._uicontrolapi, case)

    def set_allowed_cases(self, cases):
        _appuifw2.Text2_set_allowed_cases(self._uicontrolapi, cases)

    def set_input_mode(self, mode):
        _appuifw2.Text2_set_input_mode(self._uicontrolapi, mode)

    def set_allowed_input_modes(self, modes):
        _appuifw2.Text2_set_allowed_input_modes(self._uicontrolapi, modes)

    def set_undo_buffer(self, pos=0, length=-1):
        return _appuifw2.Text2_set_undo_buffer(self._uicontrolapi, pos, length)

    def move(self, direction, select=False):
        _appuifw2.Text2_move(self._uicontrolapi, direction, select)

    def move_display(self, direction):
        _appuifw2.Text2_move_display(self._uicontrolapi, direction)

    def xy2pos(self, coords):
        return _appuifw2.Text2_xy2pos(self._uicontrolapi, coords)

    def pos2xy(self, pos):
        return _appuifw2.Text2_pos2xy(self._uicontrolapi, pos)

    for name in ('color', 'focus', 'font', 'highlight_color', 'style', 'read_only',
                 'has_changed', 'allow_undo', 'indicator_text'):
        exec '%s = property(lambda self: _appuifw2.Text2_get_%s(self._uicontrolapi),lambda self, value: _appuifw2.Text2_set_%s(self._uicontrolapi, value))' % (
         name, name, name)

    for name in ('clear', 'select_all', 'clear_selection', 'undo', 'clear_undo', 'can_undo',
                 'can_cut', 'cut', 'can_copy', 'copy', 'can_paste', 'paste'):
        exec '%s = lambda self: _appuifw2.Text2_%s(self._uicontrolapi)' % (
         name, name)

    del name


class Text_display(Text):

    def __init__(self, text=u'', skinned=False, scrollbar=False, scroll_by_line=False):
        Text.__init__(self, text, skinned=skinned, scrollbar=scrollbar, indicator=False, flags=67156232, editor_flags=8)
        from key_codes import EKeyUpArrow, EKeyDownArrow
        if scroll_by_line:
            self.bind(EKeyUpArrow, lambda : self.move_display(EFLineUp))
            self.bind(EKeyDownArrow, lambda : self.move_display(EFLineDown))
        else:
            self.bind(EKeyUpArrow, lambda : self.move_display(EFPageUp))
            self.bind(EKeyDownArrow, lambda : self.move_display(EFPageDown))


EUpperCase = 1
ELowerCase = 2
ETextCase = 4
EAllCases = EUpperCase | ELowerCase | ETextCase
ENullInputMode = 0
ETextInputMode = 1
ENumericInputMode = 2
ESecretAlphaInputMode = 4
EKatakanaInputMode = 8
EFullWidthTextInputMode = 16
EFullWidthNumericInputMode = 32
EFullWidthKatakanaInputMode = 64
EHiraganaKanjiInputMode = 128
EHiraganaInputMode = 256
EHalfWidthTextInputMode = 512
EAllInputModes = ETextInputMode | ENumericInputMode | ESecretAlphaInputMode | EKatakanaInputMode | EFullWidthTextInputMode | EFullWidthNumericInputMode | EFullWidthKatakanaInputMode | EHiraganaKanjiInputMode | EHalfWidthTextInputMode
EFNoMovement = 0
EFLeft = 1
EFRight = 2
EFLineUp = 3
EFLineDown = 4
EFPageUp = 5
EFPageDown = 6
EFLineBeg = 7
EFLineEnd = 8

class Menu(list):

    def __init__(self, title=u'', items=[]):
        if title:
            self.title = title
        else:
            self.title = u''
        list.__init__(self, items)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self.title))

    def __defcompare(a, b):
        return -(a.title.lower() < b.title.lower())

    def sort(self, compare=__defcompare):
        list.sort(self, compare)

    def find(self, **kwargs):
        items = []
        for item in self:
            for name, val in kwargs.items():
                if not hasattr(item, name) or getattr(item, name) != val:
                    break
            else:
                items.append(item)

        return tuple(items)

    def popup(self, full_screen=False, search_field=False):
        menu = self
        while True:
            items = [ x for x in menu if not getattr(x, 'hidden', False) ]
            titles = [ x.title for x in items ]
            if full_screen:
                if menu.title:
                    title = app.title
                    app.title = menu.title
                i = selection_list(titles, search_field)
                if menu.title:
                    app.title = title
            else:
                if menu:
                    i = popup_menu(titles, menu.title)
                else:
                    i = None
                if i is None or i < 0:
                    item = None
                    break
            item = items[i]
            try:
                menu = item.submenu
            except AttributeError:
                break

        return item

    def multi_selection(self, style='checkbox', search_field=False):
        items = [ x for x in self if not getattr(x, 'hidden', False) ]
        titles = [ x.title for x in items ]
        if menu.title:
            title = app.title
            app.title = menu.title
        r = multi_selection_list(titles, style, search_field)
        if menu.title:
            app.title = title
        return [ items[x] for x in r ]

    def as_fw_menu(self):
        menu = []
        for item in self:
            if getattr(item, 'hidden', False):
                continue
            try:
                second = item.submenu.as_fw_menu()
            except AttributeError:
                second = getattr(item, 'callback', lambda : None)

            flags = getattr(item, 'flags', 0)
            if getattr(item, 'dimmed', False):
                flags |= 1
            if getattr(item, 'checked', False):
                flags |= 136
            if flags:
                menu.append((item.title, second, flags))
            else:
                menu.append((item.title, second))

        return menu

    def copy(self):
        items = []
        for item in self:
            item = Item(item.__dict__)
            try:
                item.submenu = item.submenu.copy()
            except AttributeError:
                pass

            items.append(item)

        return Menu(self.title, items)


class View(object):
    all_attributes = ('body', 'exit_key_handler', 'menu', 'screen', 'title', 'init_menu_handler',
                      'menu_key_handler', 'menu_key_text', 'exit_key_text', 'navi_text',
                      'left_navi_arrow', 'right_navi_arrow')

    def __init__(self):
        self.__body = None
        self.__exit_key_handler = self.close
        self.__menu = None
        self.__screen = 'normal'
        self.__title = unicode(self.__class__.__name__)
        self.__init_menu_handler = self.init_menu
        self.__menu_key_handler = self.handle_menu_key
        if app.view is not None:
            self.__menu_key_text = app._Application__views[0].menu_key_text
            self.__exit_key_text = app._Application__views[0].exit_key_text
        else:
            self.__menu_key_text = app.menu_key_text
            self.__exit_key_text = app.exit_key_text
        self.__navi_text = u''
        self.__left_navi_arrow = False
        self.__right_navi_arrow = False
        self.__tabs = ([], None)
        self.__tab_index = 0
        self.__lock = None
        return

    def shown(self):
        pass

    def hidden(self):
        pass

    def close(self):
        app._Application__pop_view(self)
        if self.__lock is not None:
            self.__lock.signal()
        return

    def wait_for_close(self):
        if self not in app._Application__views:
            raise AssertionError('View not opened')
        self.__lock = e32.Ao_lock()
        self.__lock.wait()
        self.__lock = None
        return

    def init_menu(self):
        pass

    def handle_menu_key(self):
        pass

    def set_tabs(self, tab_texts, callback):
        if app.view is self:
            app.set_tabs(tab_texts, callback)
        self.__tabs = (
         tab_texts, callback)
        self.__tab_index = 0

    def activate_tab(self, index):
        if app.view is self:
            app.activate_tab(index)
        self.__tab_index = index

    for name in all_attributes:
        exec 'def __get_%s(self):\n  return self._View__%s\n' % (name, name)
        exec 'def __set_%s(self, value):\n  self._View__%s = value\n  if app.view is self:\n    app.%s = value\n' % (
         name, name, name)
        exec '%s = property(__get_%s, __set_%s)' % (name, name, name)

    del name


class Application(object):
    from appuifw import app as __app
    for name in dir(__app):
        exec '%s = _Application__app.%s' % (name, name)

    del name

    def __init__(self):
        if isinstance(app, self.__class__):
            raise TypeError('%s already instantiated' % self.__class__.__name__)
        self.__tabs = ([], None)
        self.__tab_index = 0
        self.__menu = None
        self.__menu_id = 0
        self.__menu_key_handler = None
        self.__init_menu_handler = None
        self.__navi_text = u''
        self.__left_navi_arrow = False
        self.__right_navi_arrow = False
        self.__navi = None
        self.__menu_dyn_init_callback = _appuifw2.patch_menu_dyn_init_callback(self.__dyn_init_menu)
        self.__refresh_level = 0
        self.__refresh_pending = False
        self.__views = []
        return

    def begin_refresh(self):
        self.__refresh_level += 1

    def end_refresh(self):
        self.__refresh_level -= 1
        if self.__refresh_level <= 0:
            self.__refresh_level = 0
            if self.__refresh_pending:
                _appuifw2.refresh()
                self.__refresh_pending = False

    def refresh(self):
        if self.__refresh_level == 0:
            _appuifw2.refresh()
        else:
            self.__refresh_pending = True

    def set_tabs(self, tab_texts, callback):
        self.__app.set_tabs(tab_texts, callback)
        self.__tabs = (tab_texts, callback)
        self.__tab_index = 0

    def activate_tab(self, index):
        self.__app.activate_tab(index)
        self.__tab_index = index

    def __get_body(self):
        return self.__app.body

    def __set_body(self, value):
        self.__app.body = value

    def __get_exit_key_handler(self):
        return self.__app.exit_key_handler

    def __set_exit_key_handler(self, value):
        self.__app.exit_key_handler = value

    def __get_menu(self):
        if id(self.__app.menu) != self.__menu_id:
            return self.__app.menu
        return self.__menu

    def __set_menu(self, value):
        self.__menu = value
        self.__update_menu()

    def __dyn_init_menu(self):
        if self.__menu_key_handler is not None:
            schedule(self.__menu_key_handler)
        if self.__init_menu_handler is not None:
            self.__init_menu_handler()
        if id(self.__app.menu) == self.__menu_id:
            self.__update_menu()
        return

    def __update_menu(self):
        if hasattr(self.__menu, 'as_fw_menu'):
            self.__app.menu = self.__menu.as_fw_menu()
        elif self.__menu is None:
            self.__app.menu = []
        else:
            self.__app.menu = self.__menu
        self.__menu_id = id(self.__app.menu)
        return

    def __get_screen(self):
        return self.__app.screen

    def __set_screen(self, value):
        self.__app.screen = value

    def __get_title(self):
        return self.__app.title

    def __set_title(self, value):
        self.__app.title = value

    def __get_focus(self):
        return self.__app.focus

    def __set_focus(self, value):
        self.__app.focus = value

    if e32.s60_version_info >= (3, 0):

        def __get_orientation(self):
            return self.__app.orientation

        def __set_orientation(self, value):
            self.__app.orientation = value

    def __get_init_menu_handler(self):
        return self.__init_menu_handler

    def __set_init_menu_handler(self, value):
        self.__init_menu_handler = value

    def __get_menu_key_handler(self):
        return self.__menu_key_handler

    def __set_menu_key_handler(self, value):
        self.__menu_key_handler = value

    def __get_menu_key_text(self):
        return _appuifw2.command_text(3000)

    def __set_menu_key_text(self, value):
        _appuifw2.command_text(3000, value)

    def __get_exit_key_text(self):
        return _appuifw2.command_text(3009)

    def __set_exit_key_text(self, value):
        _appuifw2.command_text(3009, value)

    def __get_navi_text(self):
        return self.__navi_text

    def __set_navi_text(self, value):
        self.__navi_text = value
        self.__set_navi()

    def __get_left_navi_arrow(self):
        return self.__left_navi_arrow

    def __set_left_navi_arrow(self, value):
        self.__left_navi_arrow = bool(value)
        self.__set_navi()

    def __get_right_navi_arrow(self):
        return self.__right_navi_arrow

    def __set_right_navi_arrow(self, value):
        self.__right_navi_arrow = bool(value)
        self.__set_navi()

    def __set_navi(self):
        if self.__navi_text or self.__left_navi_arrow or self.__right_navi_arrow:
            self.__navi = _appuifw2.set_navi(self.__navi_text, self.__left_navi_arrow, self.__right_navi_arrow)
        else:
            self.__navi = None
        return

    def __get_view(self):
        try:
            return self.__views[-1]
        except IndexError:
            return None

        return None

    def __set_view(self, value):
        if not isinstance(value, View):
            raise TypeError('expected a View object')
        if not self.__views:
            appview = View()
            for name in View.all_attributes:
                setattr(appview, name, getattr(self, name))

            appview.set_tabs(*self.__tabs)
            appview.activate_tab(self.__tab_index)
            try:
                self.__views.append(appview)
                appview.shown()
            except:
                del self.__views[0]
                raise

        try:
            self.__views.append(value)
            self.__sync_view()
            self.__views[-2].hidden()
            value.shown()
        except:
            del self.__views[-1]
            if len(self.__views) == 1:
                del self.__views[0]
            raise

    def __pop_view(self, view=None):
        if view is None:
            i = -1
        else:
            try:
                i = self.__views.index(view)
            except ValueError:
                return

        curr = self.view
        try:
            self.__views.pop(i)
        except IndexError:
            return

        try:
            if self.view != curr:
                self.view.shown()
                self.__sync_view()
                curr.hidden()
        finally:
            if len(self.__views) == 1:
                del self.__views[0]

        return

    def __sync_view(self):
        try:
            view = self.__views[-1]
        except IndexError:
            return

        for name in View.all_attributes:
            setattr(self, name, getattr(view, name))

        self.set_tabs(*view._View__tabs)
        self.activate_tab(view._View__tab_index)

    body = property(__get_body, __set_body)
    exit_key_handler = property(__get_exit_key_handler, __set_exit_key_handler)
    menu = property(__get_menu, __set_menu)
    screen = property(__get_screen, __set_screen)
    title = property(__get_title, __set_title)
    focus = property(__get_focus, __set_focus)
    if e32.s60_version_info >= (3, 0):
        orientation = property(__get_orientation, __set_orientation)
    init_menu_handler = property(__get_init_menu_handler, __set_init_menu_handler)
    menu_key_handler = property(__get_menu_key_handler, __set_menu_key_handler)
    menu_key_text = property(__get_menu_key_text, __set_menu_key_text)
    exit_key_text = property(__get_exit_key_text, __set_exit_key_text)
    navi_text = property(__get_navi_text, __set_navi_text)
    left_navi_arrow = property(__get_left_navi_arrow, __set_left_navi_arrow)
    right_navi_arrow = property(__get_right_navi_arrow, __set_right_navi_arrow)
    view = property(__get_view, __set_view)


app = Application()

def get_skin_color(color_id):
    return _appuifw2.get_skin_color(*color_id)


EMainAreaTextColor = (
 268458534, 13056, 5)
get_language = _appuifw2.get_language
ELangTest = 0
ELangEnglish = 1
ELangFrench = 2
ELangGerman = 3
ELangSpanish = 4
ELangItalian = 5
ELangSwedish = 6
ELangDanish = 7
ELangNorwegian = 8
ELangFinnish = 9
ELangAmerican = 10
ELangSwissFrench = 11
ELangSwissGerman = 12
ELangPortuguese = 13
ELangTurkish = 14
ELangIcelandic = 15
ELangRussian = 16
ELangHungarian = 17
ELangDutch = 18
ELangBelgianFlemish = 19
ELangAustralian = 20
ELangBelgianFrench = 21
ELangAustrian = 22
ELangNewZealand = 23
ELangInternationalFrench = 24
ELangCzech = 25
ELangSlovak = 26
ELangPolish = 27
ELangSlovenian = 28
ELangTaiwanChinese = 29
ELangHongKongChinese = 30
ELangPrcChinese = 31
ELangJapanese = 32
ELangThai = 33
ELangAfrikaans = 34
ELangAlbanian = 35
ELangAmharic = 36
ELangArabic = 37
ELangArmenian = 38
ELangTagalog = 39
ELangBelarussian = 40
ELangBengali = 41
ELangBulgarian = 42
ELangBurmese = 43
ELangCatalan = 44
ELangCroatian = 45
ELangCanadianEnglish = 46
ELangInternationalEnglish = 47
ELangSouthAfricanEnglish = 48
ELangEstonian = 49
ELangFarsi = 50
ELangCanadianFrench = 51
ELangScotsGaelic = 52
ELangGeorgian = 53
ELangGreek = 54
ELangCyprusGreek = 55
ELangGujarati = 56
ELangHebrew = 57
ELangHindi = 58
ELangIndonesian = 59
ELangIrish = 60
ELangSwissItalian = 61
ELangKannada = 62
ELangKazakh = 63
ELangKhmer = 64
ELangKorean = 65
ELangLao = 66
ELangLatvian = 67
ELangLithuanian = 68
ELangMacedonian = 69
ELangMalay = 70
ELangMalayalam = 71
ELangMarathi = 72
ELangMoldavian = 73
ELangMongolian = 74
ELangNorwegianNynorsk = 75
ELangBrazilianPortuguese = 76
ELangPunjabi = 77
ELangRomanian = 78
ELangSerbian = 79
ELangSinhalese = 80
ELangSomali = 81
ELangInternationalSpanish = 82
ELangLatinAmericanSpanish = 83
ELangSwahili = 84
ELangFinlandSwedish = 85
ELangReserved1 = 86
ELangTamil = 87
ELangTelugu = 88
ELangTibetan = 89
ELangTigrinya = 90
ELangCyprusTurkish = 91
ELangTurkmen = 92
ELangUkrainian = 93
ELangUrdu = 94
ELangReserved2 = 95
ELangVietnamese = 96
ELangWelsh = 97
ELangZulu = 98
ELangOther = 99
ELangNone = 65535
ELangMaximum = ELangNone

def query(label, type, initial_value=None, ok=None, cancel=None):
    if ok is not None or cancel is not None:

        def set_ok_cancel(ok, cancel):
            if not abort:
                if ok is not None:
                    try:
                        _appuifw2.command_text(-2, ok)
                    except SymbianError:
                        pass

                if cancel is not None:
                    try:
                        _appuifw2.command_text(-1, cancel)
                    except SymbianError:
                        pass

            return

        abort = False
        schedule(set_ok_cancel, ok, cancel)
    from appuifw import query
    try:
        return query(label, type, initial_value)
    finally:
        abort = True

    return
# okay decompiling appuifw2.pyc
