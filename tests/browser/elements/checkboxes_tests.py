import pytest

pytestmark = pytest.mark.page('forms_with_input_elements.html')


def test_returns_the_matching_elements(browser):
    assert list(browser.checkboxes(value='books')) == [browser.checkbox(value='books')]


def test_returns_the_number_of_checkboxes(browser):
    assert len(browser.checkboxes()) == 11


def test_returns_the_button_at_the_given_index(browser):
    assert browser.checkboxes()[0].id == 'new_user_interests_books'


def test_iterates_through_buttons_correctly(browser):
    from nerodia.elements.check_box import CheckBox
    count = 0
    for index, c in enumerate(browser.checkboxes()):
        checkbox = browser.checkbox(index=index)
        assert isinstance(checkbox, CheckBox)
        assert c.name == checkbox.name
        assert c.id == checkbox.id
        assert c.value == checkbox.value
        count += 1
    assert count > 0
