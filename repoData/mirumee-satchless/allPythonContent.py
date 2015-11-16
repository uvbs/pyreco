__FILENAME__ = conf
# -*- coding: utf-8 -*-
#
# satchless documentation build configuration file, created by
# sphinx-quickstart on Mon Nov  8 12:30:14 2010.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#sys.path.append(os.path.abspath('.'))

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'satchless'
copyright = u'2010-2013, Mirumee Software'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '1.0'
# The full version, including alpha/beta/rc tags.
release = '1.0.4'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
#unused_docs = []

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['_build']

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = 'default'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = []

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_use_modindex = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'satchlessdoc'


# -- Options for LaTeX output --------------------------------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
    ('index', 'satchless.tex', u'satchless Documentation',
     u'Mirumee Software', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_use_modindex = True

########NEW FILE########
__FILENAME__ = tests
from prices import Price
from unittest import TestCase

from . import Cart, CartLine
from ..item import InsufficientStock, Item, StockedItem


class Swallow(Item):

    def __init__(self, kind):
        super(Swallow, self).__init__()
        self.kind = kind

    def get_price_per_item(self):
        if self.kind == 'african':
            return Price(10, currency='BTC')
        elif self.kind == 'european':
            return Price(10, currency='GBP')
        return NotImplemented


class LimitedShrubbery(StockedItem):

    def get_stock(self):
        return 1


class CartLineTest(TestCase):

    def test_getstate(self):
        'CartLine.__getstate__() returns a tuple of all values'
        cart_line = CartLine('shrubbery', 0)
        state = cart_line.__getstate__()
        self.assertEqual(state, ('shrubbery', 0, None))

    def test_setstate(self):
        'CartLine.__setstate__() properly restores all fields'
        cart_line = CartLine('apple', 2, 'jonagold')
        cart_line.__setstate__(('shrubbery', 1, 'trimmed'))
        self.assertEqual(cart_line.product, 'shrubbery')
        self.assertEqual(cart_line.quantity, 1)
        self.assertEqual(cart_line.data, 'trimmed')

    def test_equality(self):
        'Cart lines are only equal to cart lines with equal attributes'
        apple = CartLine('apple', 1, None)
        self.assertEqual(apple, CartLine('apple', 1, None))
        orange = CartLine('orange', 1, None)
        self.assertNotEqual(apple, orange)
        self.assertNotEqual(apple, 5)

    def test_repr(self):
        'CartLine.__repr__() returns valid code'
        shrubbery = CartLine('shrubbery', 1, None)
        self.assertEqual(
            repr(shrubbery),
            "CartLine(product='shrubbery', quantity=1, data=None)")

    def test_get_total(self):
        'CartLine.get_total() works and correctly passes **kwargs'
        swallows_a = CartLine(Swallow(kind='african'), 2, None)
        self.assertEqual(swallows_a.get_total(), Price(20, currency='BTC'))
        swallows_e = CartLine(Swallow(kind='european'), 2, None)
        self.assertEqual(swallows_e.get_total(), Price(20, currency='GBP'))


class CartTest(TestCase):

    def test_add_zero_does_nothing(self):
        'Zero quantity is not stored in the cart'
        cart = Cart()
        cart.add('shrubbery', 0)
        self.assertEqual(cart.count(), 0)
        self.assertEqual(list(cart), [])

    def test_add_increases_count(self):
        'Cart.add() increases previous quantity'
        cart = Cart()
        cart.add('shrubbery')
        self.assertEqual(cart.count(), 1)
        cart.add('shrubbery', 2)
        self.assertEqual(cart.count(), 3)

    def test_negative_add_allowed(self):
        'Negative values are allowed as long as the result is not negative'
        cart = Cart()
        cart.add('swallow', 3)
        cart.add('swallow', -1)
        self.assertEqual(cart.count(), 2)

    def test_negative_shalt_thou_not_count(self):
        'No operation can result in negative quantity'
        cart = Cart()
        self.assertRaises(ValueError,
                          lambda: cart.add('holy hand grenade', -1, None))

    def test_bad_values_do_not_break_state(self):
        'Invalid operations do not alter the cart state'
        cart = Cart()
        cart.add('seconds', 3)
        self.assertRaises(TypeError, lambda: cart.add('seconds', 'five'))
        self.assertEqual(cart[0], CartLine('seconds', 3))

    def test_replace(self):
        'Cart.add(replace=True) replaces existing quantity'
        cart = Cart()
        cart.add('shrubbery')
        self.assertEqual(cart.count(), 1)
        cart.add('shrubbery', 10, replace=True)
        self.assertEqual(cart.count(), 10)

    def test_replace_by_zero(self):
        'Replacing by zero quantity removes the item from cart'
        cart = Cart()
        cart.add('shrubbery')
        self.assertEqual(cart.count(), 1)
        cart.add('shrubbery', 0, replace=True)
        self.assertEqual(cart.count(), 0)

    def test_data_is_stored(self):
        'Data is stored in cart lines'
        cart = Cart()
        cart.add('shrubbery', 10, data='trimmed')
        self.assertEqual(list(cart), [CartLine('shrubbery', 10, 'trimmed')])

    def test_data_uniqueness(self):
        'Unique data results in a separate cart line'
        cart = Cart()
        cart.add('shrubbery', 10)
        cart.add('shrubbery', 10, data='trimmed', replace=True)
        self.assertEqual(cart.count(), 20)

    def test_getstate(self):
        'Cart.__getstate__() returns a list of cart lines'
        cart = Cart()
        state = cart.__getstate__()
        self.assertEqual(state, ([],))
        cart.add('shrubbery', 2)
        state = cart.__getstate__()
        self.assertEqual(state, ([CartLine('shrubbery', 2, None)],))

    def test_getstate_is_true(self):
        'Cart.__getstate__() returns a truthy value'
        cart = Cart()
        state = cart.__getstate__()
        self.assertTrue(state)

    def test_setstate(self):
        'Cart.__setstate__() properly restores state'
        cart = Cart()
        cart.__setstate__(([CartLine('shrubbery', 2, None)],))
        self.assertEqual(cart._state, [CartLine('shrubbery', 2, None)])

    def test_setstate_resets_modified(self):
        'Cart.__setstate__() sets modified to False'
        cart = Cart()
        cart.modified = True
        cart.__setstate__(([],))
        self.assertFalse(cart.modified)

    def test_init_with_items(self):
        'Passing lines to Cart.__init__() works'
        carrier = CartLine('swallow', 2, 'african')
        payload = CartLine('coconut', 1, None)
        cart = Cart([carrier, payload])
        self.assertEqual(cart.count(), 3)

    def test_repr(self):
        'Cart.__repr__() returns valid code'
        cart = Cart()
        cart.add('rabbit')
        self.assertEqual(
            repr(cart),
            "Cart([CartLine(product='rabbit', quantity=1, data=None)])")

    def test_truthiness(self):
        'bool(cart) is only true if cart contains items'
        cart = Cart()
        self.assertFalse(cart)
        cart.add('book of armaments')
        self.assertTrue(cart)

    def test_sufficient_quantity(self):
        'Cart.add() should allow product to be added if enough is in stock'
        cart = Cart()
        cart.add(LimitedShrubbery(), 1)

    def test_insufficient_quantity(self):
        'Cart.add() should disallow product to be added if stock is exceeded'
        cart = Cart()
        self.assertRaises(InsufficientStock,
                          lambda: cart.add(LimitedShrubbery(), 2))

    def test_insufficient_quantity_without_checks(self):
        'Cart.add() should allow product to exceeded stock with checks off'
        cart = Cart()
        cart.add(LimitedShrubbery(), 2, check_quantity=False)
        self.assertEqual(cart[0].quantity, 2)

    def test_clear(self):
        'Cart.clear() clears the cart and marks it as modified'
        cart = Cart()
        cart.add('rabbit')
        cart.modified = False
        cart.clear()
        self.assertEqual(len(cart), 0)
        self.assertEqual(cart.modified, True)


########NEW FILE########
__FILENAME__ = tests
from prices import Price, PriceRange
from unittest import TestCase

from . import (ClassifyingPartitioner, InsufficientStock, Item, ItemLine,
               ItemList, ItemRange, Partitioner, StockedItem, partition)


class Swallow(Item):

    def get_price_per_item(self, sale=False):
        if sale:
            return Price(1, currency='USD')
        return Price(5, currency='USD')


class SpanishInquisition(Item):

    def get_price_per_item(self):
        return Price(15, currency='BTC')


class FetchezLaVache(Item):

    def get_price_per_item(self):
        return Price(5, currency='BTC')


class EmptyRange(ItemRange):

    def __iter__(self):
        return iter([])


class ThingsNobodyExpects(ItemRange):

    def __iter__(self):
        yield SpanishInquisition()
        yield FetchezLaVache()


class SwallowLine(ItemLine):

    def get_quantity(self):
        return 2

    def get_price_per_item(self):
        return Price(5, currency='EUR')


class CoconutLine(ItemLine):

    def get_price_per_item(self):
        return Price(15, currency='EUR')


class LimitedShrubbery(StockedItem):

    def get_stock(self):
        return 1


class SwallowPartitioner(ClassifyingPartitioner):

    def classify(self, item):
        if isinstance(item, Swallow):
            return 'swallow'
        return 'unknown'


class ItemTest(TestCase):

    def test_get_price(self):
        'Item.get_price() works'
        swallow = Swallow()
        self.assertEqual(swallow.get_price(), Price(5, currency='USD'))
        self.assertEqual(swallow.get_price(sale=True),
                         Price(1, currency='USD'))


class ItemRangeTest(TestCase):

    def test_get_price_range(self):
        'ItemRange.get_price_range() works and calls its items'
        unexpected = ThingsNobodyExpects()
        self.assertEqual(unexpected.get_price_range(),
                         PriceRange(Price(5, currency='BTC'),
                                    Price(15, currency='BTC')))

    def test_get_price_range_on_empty(self):
        'ItemRange.get_price_range() raises an exception on an empty range'
        empty = EmptyRange()
        self.assertRaises(AttributeError, empty.get_price_range)


class ItemListTest(TestCase):

    def test_repr(self):
        'ItemList.__repr__() returns valid code'
        item_list = ItemList([1])
        self.assertEqual(item_list.__repr__(), 'ItemList([1])')

    def test_get_total(self):
        'ItemSet.get_total() works and calls its lines'
        coconut_delivery = ItemList([SwallowLine(), CoconutLine()])
        self.assertEqual(coconut_delivery.get_total(),
                         Price(25, currency='EUR'))

    def test_get_total_on_empty(self):
        'ItemSet.get_total() raises an exception on an empty cart'
        empty = ItemList()
        self.assertRaises(AttributeError, empty.get_total)


class PartitionerTest(TestCase):

    def test_default_is_all_items(self):
        'Default implementation returns a single group with all items'
        fake_cart = ['one', 'two', 'five']
        partitioner = Partitioner(fake_cart)
        self.assertEqual(list(partitioner), [ItemList(fake_cart)])

    def test_total_works(self):
        'Partitioner returns the same price the cart does'
        item_set = ItemList([SwallowLine()])
        partitioner = Partitioner(item_set)
        self.assertEqual(partitioner.get_total(), Price(10, currency='EUR'))

    def test_truthiness(self):
        'bool(partitioner) is only true if the set contains items'
        item_set = ItemList()
        partitioner = Partitioner(item_set)
        self.assertFalse(partitioner)
        item_set = ItemList([SwallowLine()])
        partitioner = Partitioner(item_set)
        self.assertTrue(partitioner)

    def test_repr(self):
        'Partitioner.__repr__() returns valid code'
        partitioner = Partitioner([1])
        self.assertEqual(partitioner.__repr__(), 'Partitioner([1])')


class ClassifyingPartitionerTest(TestCase):

    def test_classification(self):
        'Partitions should be split according to the classifying key'
        swallow = Swallow()
        inquisition = SpanishInquisition()
        cow = FetchezLaVache()
        fake_cart = [inquisition, swallow, cow]
        partitioner = SwallowPartitioner(fake_cart)
        self.assertEqual(list(partitioner),
                         [ItemList([swallow]),
                          ItemList([inquisition, cow])])


class PartitionTest(TestCase):

    def test_basic_classification(self):
        def keyfunc(item):
            if item > 5:
                return 'more'
            return 'less'
        partitioner = partition([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], keyfunc)
        self.assertEqual(list(partitioner),
                         [ItemList([1, 2, 3, 4, 5]),
                          ItemList([6, 7, 8, 9, 10])])

    def test_custom_class(self):
        def keyfunc(item):
            if item > 5:
                return 'more'
            return 'less'
        partitioner = partition([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], keyfunc,
                                partition_class=list)
        self.assertEqual(list(partitioner),
                         [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]])


class StockedItemTest(TestCase):

    def test_check_valid_quantity(self):
        'StockedItem.get_quantity() allows smaller quantities to be used'
        item = LimitedShrubbery()
        item.check_quantity(0)
        item.check_quantity(1)

    def test_check_negative_quantity(self):
        'StockedItem.get_quantity() disallows negative quantities'
        item = LimitedShrubbery()
        self.assertRaises(ValueError, lambda: item.check_quantity(-1))

    def test_check_excessive_quantity(self):
        'StockedItem.get_quantity() disallows excessive quantities'
        item = LimitedShrubbery()
        self.assertRaises(InsufficientStock, lambda: item.check_quantity(2))

########NEW FILE########
__FILENAME__ = tests
from unittest import TestCase

from . import ProcessManager, Step, InvalidData


class AddSwallows(Step):

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return 'swallows-needed'

    def validate(self):
        if self.data.swallows < 2:
            raise InvalidData('Not enough swallows')


class AddCoconuts(Step):

    def __init__(self, data):
        self.data = data

    def __str__(self):
        return 'coconuts-needed'

    def validate(self):
        if self.data.coconuts < 1:
            raise InvalidData('Need a coconut')


class CoconutDelivery(ProcessManager):

    def __init__(self):
        self.swallows = 0
        self.coconuts = 0

    def __iter__(self):
        yield AddSwallows(self)
        yield AddCoconuts(self)


class ProcessManagerTest(TestCase):

    def test_iter(self):
        'ProcessManager.__iter__() returns the steps'
        process = CoconutDelivery()
        steps = map(str, list(process))
        self.assertEqual(steps, ['swallows-needed', 'coconuts-needed'])

    def test_get_next_step(self):
        'ProcessManager.get_next_step() returns the first step with invalid data'
        process = CoconutDelivery()
        process.coconuts = 1
        self.assertEqual(str(process.get_next_step()), 'swallows-needed')
        process.swallows = 2
        self.assertEqual(process.get_next_step(), None)
        process.coconuts = 0
        self.assertEqual(str(process.get_next_step()), 'coconuts-needed')

    def test_is_complete(self):
        'ProcessManager.is_complete() returns true if all steps are satisfied'
        process = CoconutDelivery()
        self.assertFalse(process.is_complete())
        process.coconuts = 1
        process.swallows = 2
        self.assertTrue(process.is_complete())

    def test_item_access(self):
        'You can index a ProcessManager using step names'
        process = CoconutDelivery()
        self.assertTrue(isinstance(process['coconuts-needed'], AddCoconuts))

        def invalid():
            return process['spam-needed']

        self.assertRaises(KeyError, invalid)

    def test_errors(self):
        'ProcessManager.get_errors() returns a dict of all invalid steps'
        process = CoconutDelivery()
        process.swallows = 2
        errors = process.get_errors()
        self.assertFalse('swallows-needed' in errors)
        self.assertTrue('coconuts-needed' in errors)

########NEW FILE########
__FILENAME__ = tests
from unittest import TestSuite, TestLoader

TEST_MODULES = [
    'satchless.cart.tests',
    'satchless.item.tests',
    'satchless.process.tests']

suite = TestSuite()
loader = TestLoader()
for module in TEST_MODULES:
    suite.addTests(loader.loadTestsFromName(module))

########NEW FILE########