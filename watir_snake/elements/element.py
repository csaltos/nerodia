from importlib import import_module

from re import search, sub
from selenium.common.exceptions import InvalidElementStateException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from warnings import warn

import watir_snake
from ..atoms import Atoms
from ..exception import Error, ObjectDisabledException, ObjectReadOnlyException, \
    UnknownFrameException, UnknownObjectException
from ..locators.element.selector_builder import SelectorBuilder
from ..wait.timer import Timer
from ..wait.wait import TimeoutError, Wait, Waitable


# class Element(Container, EventuallyPresent, Waitable, Adjacent):
class Element(Atoms, Waitable):
    ATTRIBUTES = []
    _attr_id = (str, 'id')
    _attr_class_name = (str, 'className')

    def __init__(self, query_scope, selector):
        self.query_scope = query_scope
        if not isinstance(selector, dict):
            raise TypeError('invalid argument: {!r}'.format(selector))
        self.element = selector.pop('element', None)
        self.selector = selector
        self.keyword = None

    @property
    def exists(self):
        """
        Returns True if element exists, False otherwise
        :rtype: bool
        """
        try:
            self.assert_exists()
            return True
        except (UnknownObjectException, UnknownFrameException):
            return False

    exist = exists

    @property
    def attribute_list(self):
        return self.ATTRIBUTES

    def __repr__(self):
        string = '#<#{}: '.format(self.__class__.__name__)
        if self.keyword:
            string += 'keyword: {} '.format(self.keyword)
        string += 'located: {}; '.format(self.element is not None)
        if not self.selector:
            string += '{element: (selenium element)}'
        else:
            string += self.selector_string
        string += '>'
        return string

    def __eq__(self, other):
        """
        Returns True if two elements are equal
        :param other: other element to compare
        :rtype: bool
        """
        return self.wd if isinstance(other, self.__class__) else other.wd

    eql = __eq__

    def __hash__(self):
        return self.element.__hash__() if self.element else super(Element, self).__hash__()

    @property
    def text(self):
        """
        Returns the text of the element
        :rtype: str
        """
        return self._element_call(self.element.text)

    def tag_name(self):
        """
        Returns the tag name of the element
        :rtype: str
        """
        return self._element_call(self.element.tag_name.lower)

    def click(self, *modifiers):
        """
        Clicks the element, optionally while pressing the given modifier keys.
        Note that support for holding a modifier key is currently experimental, and may not work
        at all.

        :param modifiers: modifier keys to press while clicking
        :Example: Click an element

        browser.element(name='new_user_button').click()

        :Example: Click an element with shift key pressed
        from selenium.webdriver.common.keys import Keys
        browser.element(name='new_user_button').click(Keys.SHIFT)

        :Example: Click an element with several modifier keys pressed
        from selenium.webdriver.common.keys import Keys
        browser.element(name='new_user_button').click(Keys.SHIFT, Keys.CONTROL)
        """

        def method():
            if modifiers:
                action = ActionChains(self.driver)
                for mod in modifiers:
                    action.key_down(mod)
                action.click(self.element)
                for mod in modifiers:
                    action.key_up(mod)
                action.perform()
            else:
                self.element.click()

        self._element_call(method, self.wait_for_enabled)
        self.browser.after_hooks.run()

    def double_click(self):
        """
        Double clicks the element.
        Note that browser support may vary.

        :Example: Double-click an element

        browser.element(name='new_user_button').double_click()
        """
        self._element_call(lambda: ActionChains(self.driver).double_click(self.element)
                           .perform(), self.wait_for_present)
        self.browser.after_hooks.run()

    def right_click(self):
        """
        Right clicks the element
        Note that browser support may vary

        :Example: Right click an element

        browser.element(name='new_user_button').right_click()
        """
        self._element_call(lambda: ActionChains(self.driver).context_click(self.element)
                           .perform(), self.wait_for_present)
        self.browser.after_hooks.run()

    def hover(self):
        """
        Moves the mouse to the middle of this element
        Note that browser support may vary

        :Example: Hover over an element

        browser.element(name='new_user_button').hover()
        """
        self._element_call(lambda: ActionChains(self.driver).move_to_element(self.element)
                           .perform(), self.wait_for_present)
        self.browser.after_hooks.run()

    def drag_and_drop_on(self, other):
        """
        Drag and drop this element on to another element instance
        Note that browser support may vary

        :param other: element to drop on

        :Example: Drag an element onto another

        a = browser.div(id='draggable')
        b = browser.div(id='droppable')
        a.drag_and_drop_on(b)
        """
        self._assert_is_element(other)

        self._element_call(lambda: ActionChains(self.driver).drag_and_drop(self.element, other.wd)
                           .perform(), self.wait_for_present)

    def drag_and_drop_by(self, xoffset, yoffset):
        """
        Drag and drop this element by the given offsets.
        Note that browser support may vary.

        :param xoffset: amount to move horizontally
        :param yoffset: amount to move vertically

        :Example: Drag an element onto another

        browser.div(id='draggable').drag_and_drop_by(100, -200)
        """
        self._element_call(lambda: ActionChains(self.driver).
                           drag_and_drop_by_offset(self.element, xoffset, yoffset).perform(),
                           self.wait_for_present)

    def flash(self):
        """
        Flashes (change background color for a moment) element

        :Example:

        browser.text_field(name='new_user_first_name').flash()
        """
        background_color = self.style('backgroundColor')
        element_color = self.driver.execute_script('arguments[0].style.backgroundColor',
                                                   self.element)

        for n in range(10):
            color = 'red' if n % 2 == 0 else background_color
            self.driver.execute_script("arguments[0].style.backgroundColor = "
                                       "'{}'".format(color), self.element)

        self.driver.execute_script('arguments[0].style.backgroundColor = arguments[1]',
                                   self.element, element_color)

        return self

    @property
    def value(self):
        """
        Returns value of the element
        :rtype: str
        """
        try:
            return self.attribute_value('value') or ''
        except InvalidElementStateException:
            return ''

    def attribute_value(self, attribute_name):
        """
        Returns given attribute value of the element

        :param attribute_name: attribute to retrieve
        :type attribute_name: str
        :rtype: str

        :Example:

        browser.a(id='link_2').attribute_value('title')  #=> 'link_title_2'
        """
        return self._element_call(lambda: self.element.get_attribute(attribute_name))

    @property
    def outer_html(self):
        """
        Returns outer (inner + element itself) HTML code of element

        :rtype: str

        :Example:

        browser.div(id='foo').outer_html  #=> "<div id=\"foo\"><a href=\"#\">hello</a></div>"
        """
        return self._element_call(lambda: self._execute_atom('getOuterHtml',
                                                             self.element)).strip()

    html = outer_html

    @property
    def inner_html(self):
        """
        Returns inner HTML code of element

        :rtype: str

        :Example:

        browser.div(id='foo').inner_html  #=> "<div id=\"foo\"><a href=\"#\">hello</a></div>"
        """
        return self._element_call(lambda: self._execute_atom('getInnerHtml',
                                                             self.element)).strip()

    def send_keys(self, *args):
        """
        Sends sequence of keystrokes to the element
        :param args: keystrokes to send

        :Example:

        browser.text_field(name='new_user_first_name').send_keys('watir_snake')
        """
        return self._element_call(lambda: self.element.send_keys(*args), self.wait_for_writable)

    def focus(self):
        """
        Focuses the element
        Note that Firefox queues focus events until the window actually has focus
        """
        self._element_call(lambda: self.driver.execute_script('return arguments[0].focus()',
                                                              self.element))

    @property
    def focused(self):
        """
        Returns True if the element is focused
        :rtype: bool
        """
        return self._element_call(lambda: self.element == self.driver.switch_to.active_element)

    def fire_event(self, event_name):
        """
        Simulates JavaScript events on element
        Note that you may omit 'on' from event name

        :param event_name: event to fire

        :Example:

        browser.button(name='new_user_button').fire_event('click')
        browser.button(name='new_user_button').fire_event('mousemove')
        browser.button(name='new_user_button').fire_event('onmouseover')
        """
        event_name = sub(r'^on', '', str(event_name)).lower()

        self._element_call(lambda: self._execute_atom('fireEvent', self.element, event_name))

    @property
    def driver(self):
        return self.query_scope.driver

    @property
    def wd(self):
        self.assert_exists()
        return self.element

    @property
    def visible(self):
        """
        Returns true if this element is visible on the page
        Raises exception if element does not exist

        :rtype: bool
        """
        return self._element_call(lambda: self.element.displayed, self.assert_exists)

    @property
    def enabled(self):
        """
        Returns True if the element is present and enabled on the page

        :rtype: bool
        """
        return self._element_call(lambda: self.element.enabled, self.assert_exists)

    @property
    def present(self):
        """
        Returns True if the element exists and is visible on the page
        Returns False if the element does not exist or exists but is not visible

        :rtype: bool
        """
        try:
            return self.visible
        except UnknownObjectException:
            return False

    def style(self, prop=None):
        """
        Returns given style property of this element

        :param prop: property to get
        :type prop: str
        :rtype: str

        :Example:

        browser.button(value='Delete').style           #=> "border: 4px solid red;"
        browser.button(value='Delete').style('border') #=> "4px solid rgb(255, 0, 0)"
        """
        if prop:
            return self._element_call(lambda: self.element.style(prop))
        else:
            return str(self.attribute_value('style')).strip()

    def to_subtype(self):
        """
        Cast this Element instance to a more specific subtype
        :Example:

        browser.element(xpath="//input[@type='submit']").to_subtype()  #=> #<Button>
        """
        elem = self.wd
        tag_name = elem.tag_name.lower()

        if tag_name == 'input':
            elem_type = elem.attribute('type')
            if elem_type in watir_snake.elements.Button.VALID_TYPES:
                klass = watir_snake.elements.Button
            elif elem_type == 'checkbox':
                klass = watir_snake.elements.CheckBox
            elif elem_type == 'radio':
                klass = watir_snake.elements.Radio
            elif elem_type == 'file':
                klass = watir_snake.elements.FileField
            else:
                klass = watir_snake.elements.TextField
        else:
            klass = watir_snake.element_class_for(tag_name)

        return klass(self.query_scope, element=elem)

    @property
    def browser(self):
        """
        Returns browser
        :rtype: watir_snake.browser.Browser
        """
        return self.query_scope.browser

    @property
    def stale(self):
        """
        Returns True if a previously located element is no longer attached to the DOM
        :rtype: bool
        """
        try:
            if self.element is None:
                raise Error('Can not check staleness of unused element')
            self.element.enabled  # any wire call will check for staleness
            return False
        except StaleElementReferenceException:
            return True

    def reset(self):
        self.element = None

    def wait_for_exists(self):
        if not watir_snake.relaxed_locate:
            return self.assert_exists()
        if self.exists:  # Performance shortcut
            return None
        try:
            self.query_scope.wait_for_exists()
            self.wait_until(self.exists)
        except TimeoutError:
            if watir_snake.default_timeout != 0:
                warn('This code has slept for the duration of the default timeout waiting for an '
                     'Element to exist. If the test is still passing, consider using '
                     'Element#exists instead of catching UnknownObjectException')
            raise UnknownObjectException('timed out after {} seconds, waiting for {} to be '
                                         'located'.format(watir_snake.default_timeout, self))

    def wait_for_present(self):
        if not watir_snake.relaxed_locate:
            return self.assert_exists()

        try:
            self.query_scope.wait_for_present()
            self.wait_until(self.exists)
        except TimeoutError:
            if watir_snake.default_timeout != 0:
                warn('This code has slept for the duration of the default timeout waiting for an '
                     'Element to exist. If the test is still passing, consider using '
                     'Element#present instead of catching UnknownObjectException')
            raise UnknownObjectException('timed out after {} seconds, waiting for {} to be '
                                         'located'.format(watir_snake.default_timeout, self))

    def wait_for_enabled(self):
        if not watir_snake.relaxed_locate:
            return self._assert_enabled()
        self.wait_for_present()

        try:
            self.wait_until(self.enabled)
        except TimeoutError:
            raise ObjectDisabledException('element present, but timed out after {} seconds, '
                                          'waiting for {} to be '
                                          'enabled'.format(watir_snake.default_timeout, self))

    def wait_for_writable(self):
        if not watir_snake.relaxed_locate:
            return self._assert_writable()
        self.wait_for_enabled()

        try:
            self.wait_until(lambda: not getattr(self, 'readonly', None) or not self.readonly)
        except TimeoutError:
            raise ObjectReadOnlyException('element present and enabled, but timed out after {} '
                                          'seconds, waiting for {} to not be '
                                          'readonly'.format(watir_snake.default_timeout, self))

    def assert_exists(self):
        """
        Ensure that the element exists, making sure that it is not stale and located if necessary
        """
        if self.element and not self.selector:
            self._ensure_context()
            if self.stale:
                self.reset()
        elif self.element and not self.stale:
            return
        else:
            self.element = self.locate()

        self.assert_element_found()

    def assert_element_found(self):
        if self.element is None:
            raise UnknownObjectException('unable to locate element: {}'.format(self))

    def locate(self):
        self._ensure_context()

        element_validator = self._element_validator_class()
        selector_builder = self._selector_builder_class(self.query_scope, self.selector,
                                                        self.attribute_list)
        locator = self._locator_class(self.query_scope, self.selector, selector_builder,
                                      element_validator)

        return locator.locate()

    @property
    def selector_string(self):
        if isinstance(self.query_scope, watir_snake.browser.Browser):
            return '{}'.format(self.selector)
        else:
            return '{} --> {}'.format(self.query_scope.selector_string, self.selector)

    # Private

    @property
    def _unknown_exception(self):
        return UnknownObjectException

    @property
    def _locator_class(self):
        return self._import_module.Locator

    @property
    def _element_validator_class(self):
        return self._import_module.Validator

    @property
    def _selector_builder_class(self):
        return self._import_module.SelectorBuilder

    @property
    def _import_module(self):
        modules = [watir_snake.locator_namespace.__name__, self._element_class_name.lower()]
        try:
            return import_module('watir_snake.{}.{}.locator'.format(*modules))
        except ImportError:
            return import_module('watir_snake.{}.element.locator'.format(*modules[:1]))

    @property
    def _element_class_name(self):
        return self.__class__.__name__

    # Ensure the driver is in the desired browser context
    def _ensure_context(self):
        if isinstance(self.query_scope, watir_snake.elements.IFrame):
            self.query_scope.switch_to()
        else:
            self.query_scope.assert_exists()

    def _is_attribute(self, attribute_name):
        return self.attribute_value(attribute_name) is not None

    def _assert_enabled(self):
        if not self._element_call(lambda: self.element.enabled):
            raise ObjectDisabledException('object is disabled {}'.format(self))

    def _assert_writable(self):
        self._assert_enabled()

        if getattr(self, 'readonly', None) and self.readonly:
            raise ObjectReadOnlyException('object is read only {}'.format(self))

    @classmethod
    def _assert_is_element(cls, obj):
        if not isinstance(obj, Element):
            raise TypeError('execpted watir_snake.Element, '
                            'got {}:{}'.format(obj, obj.__class__.__name__))

    def _element_call(self, method, exist_check=None):
        exist_check = exist_check or self.wait_for_exists
        if Wait.timer.locked is None:
            Wait.timer = Timer(timeout=watir_snake.default_timeout)
        try:
            exist_check()
            return method()
        except StaleElementReferenceException:
            exist_check()
            return method()
        finally:
            if Wait.timer.locked is None:
                Wait.timer.reset()

    def __getattr__(self, item):
        if search(SelectorBuilder.WILDCARD_ATTRIBUTE, item):
            return self.attribute_value(item.replace('_', '-'))
        raise AttributeError('{!r} is not a valid attribute for '
                             '{}!'.format(item, self.__class__.__name__))
