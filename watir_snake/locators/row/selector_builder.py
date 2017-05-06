import logging

import re

from ..element.selector_builder import SelectorBuilder as ElementSelectorBuilder
from ...exception import Error


class SelectorBuilder(ElementSelectorBuilder):
    def _build_wd_selector(self, selectors):
        if any(isinstance(selector, re._pattern_type) for selector in selectors):
            return None

        if not selectors.pop('tag_name', None):
            raise Error('internal error: no tag_name?!')

        expressions = ['./tr']

        if self.query_scope.tag_name.lower() not in ['tbody', 'tfoot', 'thead']:
            expressions += ['./body/tr', './thead/tr', './tfoot/tr']

        attr_expr = self.xpath_builder.attribute_expression(None, selectors)

        if attr_expr:
            expressions = ['{}[{}]'.format(e, attr_expr) for e in expressions]

        xpath = " | ".join(expressions)

        logging.debug({'build_wd_selector': xpath})

        return ['xpath', xpath]
