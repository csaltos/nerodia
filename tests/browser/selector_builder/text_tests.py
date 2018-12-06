from re import compile

import pytest

from nerodia.elements.html_elements import HTMLElement
from nerodia.exception import LocatorException
from nerodia.locators.element.xpath_support import XpathSupport
from nerodia.locators.text_field.selector_builder import SelectorBuilder

pytestmark = pytest.mark.page('forms_with_input_elements.html')

ATTRIBUTES = HTMLElement.ATTRIBUTES
NEGATIVE_TYPES = ' and '.join([
    "translate(@type,'{}','{}')!='file'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE),
    "translate(@type,'{}','{}')!='radio'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE),
    "translate(@type,'{}','{}')!='checkbox'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE),
    "translate(@type,'{}','{}')!='submit'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE),
    "translate(@type,'{}','{}')!='reset'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE),
    "translate(@type,'{}','{}')!='image'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE),
    "translate(@type,'{}','{}')!='button'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE),
    "translate(@type,'{}','{}')!='hidden'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE),
    "translate(@type,'{}','{}')!='range'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE),
    "translate(@type,'{}','{}')!='color'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE),
    "translate(@type,'{}','{}')!='date'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE),
    "translate(@type,'{}','{}')!='datetime-local'".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE)
])


def verify_build(browser, selector, wd, data=None, remaining=None, scope=None):
    builder = SelectorBuilder(ATTRIBUTES)
    query_scope = scope or browser
    built = builder.build(selector)
    assert built == [wd, remaining or {}]

    located = query_scope.wd.find_element(*list(wd.items())[0])

    if data:
        assert located.get_attribute('data-locator') == data


class TestBuild(object):
    def test_without_any_elements(self, browser):
        items = {
            'selector': {},
            'wd': {'xpath': ".//*[local-name()='input'][not(@type) or "
                            "({})]".format(NEGATIVE_TYPES)},
            'data': 'input name'
        }
        verify_build(browser, **items)

    # with type

    def test_specified_text_field_type_that_is_text(self, browser):
        items = {
            'selector': {'type': 'text'},
            'wd': {'xpath': ".//*[local-name()='input'][translate(@type,'{}','{}')='text'"
                            "]".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE)},
            'data': 'first text'
        }
        verify_build(browser, **items)

    def test_specified_text_field_type_that_is_not_text(self, browser):
        items = {
            'selector': {'type': 'number'},
            'wd': {'xpath': ".//*[local-name()='input'][translate(@type,'{}','{}')='number'"
                            "]".format(XpathSupport.UPPERCASE, XpathSupport.LOWERCASE)},
            'data': '42'
        }
        verify_build(browser, **items)

    def test_true_locates_text_field_with_a_type_specified(self, browser):
        items = {
            'selector': {'type': True},
            'wd': {'xpath': ".//*[local-name()='input'][{}]".format(NEGATIVE_TYPES)},
            'data': 'input name'
        }
        verify_build(browser, **items)

    def test_false_locates_text_field_without_type_specified(self, browser):
        items = {
            'selector': {'type': False},
            'wd': {'xpath': ".//*[local-name()='input'][not(@type)]"},
            'data': 'input name'
        }
        verify_build(browser, **items)

    def test_raises_exception_when_a_non_text_field_type_input_is_specified(self):
        match = 'TextField Elements can not be located by type: checkbox'
        with pytest.raises(LocatorException, match=match):
            SelectorBuilder(ATTRIBUTES).build({'type': 'checkbox'})

    # with text

    def test_string_for_value(self, browser):
        items = {
            'selector': {'text': 'Developer'},
            'wd': {'xpath': ".//*[local-name()='input'][not(@type) or "
                            "({})]".format(NEGATIVE_TYPES)},
            'remaining': {'text': 'Developer'}
        }
        verify_build(browser, **items)

    def test_simple_regexp_for_value(self, browser):
        items = {
            'selector': {'text': compile(r'Dev')},
            'wd': {'xpath': ".//*[local-name()='input'][not(@type) or "
                            "({})]".format(NEGATIVE_TYPES)},
            'remaining': {'text': compile(r'Dev')}
        }
        verify_build(browser, **items)

    def test_returns_complicated_regexp_to_the_locator_as_a_value(self, browser):
        items = {
            'selector': {'text': compile(r'^foo$')},
            'wd': {'xpath': ".//*[local-name()='input'][not(@type) or "
                            "({})]".format(NEGATIVE_TYPES)},
            'remaining': {'text': compile(r'^foo$')}
        }
        verify_build(browser, **items)

    # with label

    def test_using_string(self, browser):
        items = {
            'selector': {'label': 'First name'},
            'wd': {'xpath': ".//*[local-name()='input'][not(@type) or ({})]"
                            "[@id=//label[normalize-space()='First name']/@for or parent::"
                            "label[normalize-space()='First name']]".format(NEGATIVE_TYPES)},
            'data': 'input name'
        }
        verify_build(browser, **items)

    def test_using_string_with_hidden_text(self, browser):
        items = {
            'selector': {'label': 'With hidden text'},
            'wd': {'xpath': ".//*[local-name()='input'][not(@type) or ({})][@id=//label"
                            "[normalize-space()='With hidden text']/@for or parent::"
                            "label[normalize-space()='With hidden text']]".format(NEGATIVE_TYPES)},
            'data': 'hidden'
        }
        verify_build(browser, **items)

    # def test_using_simple_regex(self, browser):
    #     items = {
    #         'selector': {'label': compile(r'First')},
    #         'wd': {'xpath': ".//*[local-name()='input'][not(@type) or ({})][@id=//label"
    #                         "[contains(text(), 'First')]/@for or parent::"
    #                         "label[contains(text(), 'First')]]".format(NEGATIVE_TYPES)},
    #         'data': 'input name'
    #     }
    #     verify_build(browser, **items)
    #
    # def test_using_complex_regex(self, browser):
    #     items = {
    #         'selector': {'label': compile(r'([qa])st? name')},
    #         'wd': {'xpath': ".//*[local-name()='input'][not(@type) or ({})]"
    #                         "[@id=//label[contains(text(), 's') and contains(text(), ' name')]"
    #                         "/@for or parent::label[contains(text(), 's') and "
    #                         "contains(text(), ' name')]]".format(NEGATIVE_TYPES)},
    #         'remaining': {'label_element': compile(r'([qa])st? name')}
    #     }
    #     verify_build(browser, **items)

    # with index

    def test_index_positive(self, browser):
        items = {
            'selector': {'index': 4},
            'wd': {'xpath': "(.//*[local-name()='input'][not(@type) or "
                            "({})])[5]".format(NEGATIVE_TYPES)},
            'data': 'dev'
        }
        verify_build(browser, **items)

    def test_index_negative(self, browser):
        items = {
            'selector': {'index': -3},
            'wd': {'xpath': "(.//*[local-name()='input'][not(@type) or "
                            "({})])[last()-2]".format(NEGATIVE_TYPES)},
            'data': '42'
        }
        verify_build(browser, **items)

    def test_index_last(self, browser):
        items = {
            'selector': {'index': -1},
            'wd': {'xpath': "(.//*[local-name()='input'][not(@type) or "
                            "({})])[last()]".format(NEGATIVE_TYPES)},
            'data': 'last text'
        }
        verify_build(browser, **items)

    def test_index_does_not_return_index_if_zero(self, browser):
        items = {
            'selector': {'index': 0},
            'wd': {'xpath': ".//*[local-name()='input'][not(@type) or "
                            "({})]".format(NEGATIVE_TYPES)},
            'data': 'input name'
        }
        verify_build(browser, **items)

    def test_raises_exception_when_index_is_not_an_integer(self, browser):
        msg = "expected one of {!r}, got 'foo':{}".format([int], str)
        with pytest.raises(TypeError) as e:
            SelectorBuilder(ATTRIBUTES).build({'index': 'foo'})
        assert e.value.args[0] == msg

    # with multiple locators

    def test_locates_using_tag_name_class_attributes_text(self, browser):
        items = {
            'selector': {'text': 'Developer', 'class_name': compile(r'c'), 'id': True},
            'wd': {'xpath': ".//*[local-name()='input'][contains(@class, 'c')][not(@type) or "
                            "({})][@id]".format(NEGATIVE_TYPES)},
            'remaining': {'text': 'Developer'}
        }
        verify_build(browser, **items)

    def test_delegates_adjacent_to_element_selector_builder(self, browser):
        items = {
            'scope': browser.element(id='new_user_email').locate(),
            'selector': {'adjacent': 'ancestor', 'index': 1},
            'wd': {'xpath': './ancestor::*[2]'},
            'data': 'form'
        }
        verify_build(browser, **items)
