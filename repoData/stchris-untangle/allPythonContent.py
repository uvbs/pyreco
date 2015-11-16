__FILENAME__ = conf
# -*- coding: utf-8 -*-
#
# untangle documentation build configuration file, created by
# sphinx-quickstart on Fri Apr  6 16:05:20 2012.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys, os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))
import untangle

# -- General configuration -----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sphinx.ext.autodoc']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8-sig'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'untangle'
copyright = u'2012, Christian Stefanescu'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = untangle.__version__
# The full version, including alpha/beta/rc tags.
release = untangle.__version__

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ['_build']

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

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
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
html_static_path = ['_static']

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
#html_domain_indices = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = 'untangledoc'


# -- Options for LaTeX output --------------------------------------------------

latex_elements = {
# The paper size ('letterpaper' or 'a4paper').
#'papersize': 'letterpaper',

# The font size ('10pt', '11pt' or '12pt').
#'pointsize': '10pt',

# Additional stuff for the LaTeX preamble.
#'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('index', 'untangle.tex', u'untangle Documentation',
   u'Christian Stefanescu', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# If true, show page references after internal links.
#latex_show_pagerefs = False

# If true, show URL addresses after external links.
#latex_show_urls = False

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_domain_indices = True


# -- Options for manual page output --------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    ('index', 'untangle', u'untangle Documentation',
     [u'Christian Stefanescu'], 1)
]

# If true, show URL addresses after external links.
#man_show_urls = False


# -- Options for Texinfo output ------------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
  ('index', 'untangle', u'untangle Documentation',
   u'Christian Stefanescu', 'untangle', 'One line description of project.',
   'Miscellaneous'),
]

# Documents to append as an appendix to all manuals.
#texinfo_appendices = []

# If false, no module index is generated.
#texinfo_domain_indices = True

# How to display URL addresses: 'footnote', 'no', or 'inline'.
#texinfo_show_urls = 'footnote'

########NEW FILE########
__FILENAME__ = examples
#!/usr/bin/env python

import untangle


def access():
    o = untangle.parse('<node id="5"><subnode value="abc"/></node>')
    return ("Node id = %s, subnode value = %s" %
            (o.node['id'], o.node.subnode['value']))


def siblings_list():
    o = untangle.parse('''
        <root>
            <child name="child1"/>
            <child name="child2"/>
            <child name="child3"/>
        </root>
        ''')
    return ','.join([child['name'] for child in o.root.child])


examples = [
    ('Access children with parent.children and'
     ' attributes with element["attribute"]', access),
    ('Access siblings as list', siblings_list),
]

if __name__ == '__main__':
    for description, func in examples:
        print '=' * 70
        print description
        print '=' * 70
        print
        print func()
        print

# vim: set expandtab ts=4 sw=4:

########NEW FILE########
__FILENAME__ = tests
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import untangle
import xml


class FromStringTestCase(unittest.TestCase):
    """ Basic parsing tests with input as string """
    def test_basic(self):
        o = untangle.parse("<a><b/><c/></a>")
        self.assert_(o is not None)
        self.assert_(o.a is not None)
        self.assert_(o.a.b is not None)
        self.assert_(o.a.c is not None)

    def test_basic_with_decl(self):
        o = untangle.parse("<?xml version='1.0'?><a><b/><c/></a>")
        self.assert_(o is not None)
        self.assert_(o.a is not None)
        self.assert_(o.a.b is not None)
        self.assert_(o.a.c is not None)

    def test_with_attributes(self):
        o = untangle.parse('''
                    <Soup name="Tomato soup" version="1">
                     <Ingredients>
                        <Water qty="1l" />
                        <Tomatoes qty="1kg" />
                        <Salt qty="1tsp" />
                     </Ingredients>
                     <Instructions>
                        <boil-water/>
                        <add-ingredients/>
                        <done/>
                     </Instructions>
                    </Soup>
                     ''')
        self.assertEquals('Tomato soup', o.Soup['name'])
        self.assertEquals(1, int(o.Soup['version']))
        self.assertEquals('1l', o.Soup.Ingredients.Water['qty'])
        self.assert_(o.Soup.Instructions.add_ingredients is not None)

    def test_grouping(self):
        o = untangle.parse('''
                    <root>
                     <child name="child1">
                        <subchild name="sub1"/>
                     </child>
                     <child name="child2"/>
                     <child name="child3">
                        <subchild name="sub2"/>
                        <subchild name="sub3"/>
                     </child>
                    </root>
                     ''')
        self.assert_(o.root)

        children = o.root.child
        self.assertEquals(3, len(children))
        self.assertEquals('child1', children[0]['name'])
        self.assertEquals('sub1', children[0].subchild['name'])
        self.assertEquals(2, len(children[2].subchild))
        self.assertEquals('sub2', children[2].subchild[0]['name'])

    def test_single_root(self):
        self.assert_(untangle.parse('<single_root_node/>'))


class InvalidTestCase(unittest.TestCase):
    """ Test corner cases """
    def test_invalid_xml(self):
        self.assertRaises(
            xml.sax.SAXParseException,
            untangle.parse,
            '<unclosed>'
        )

    def test_empty_xml(self):
        self.assertRaises(ValueError, untangle.parse, '')

    def test_none_xml(self):
        self.assertRaises(ValueError, untangle.parse, None)


class PomXmlTestCase(unittest.TestCase):
    """ Tests parsing a Maven pom.xml """
    def setUp(self):
        self.o = untangle.parse('tests/res/pom.xml')

    def test_parent(self):
        project = self.o.project
        self.assert_(project)

        parent = project.parent
        self.assert_(parent)
        self.assertEquals(
            'com.atlassian.confluence.plugin.base',
            parent.groupId
        )
        self.assertEquals('confluence-plugin-base', parent.artifactId)
        self.assertEquals('17', parent.version)

        self.assertEquals('4.0.0', project.modelVersion)
        self.assertEquals('com.this.that.groupId', project.groupId)

        self.assertEquals('', project.name)
        self.assertEquals(
            '${pom.groupId}.${pom.artifactId}',
            project.properties.atlassian_plugin_key
        )
        self.assertEquals(
            '1.4.1',
            project.properties.atlassian_product_test_lib_version
        )
        self.assertEquals(
            '2.9',
            project.properties.atlassian_product_data_version
        )

    def test_lengths(self):
        self.assertEquals(1, len(self.o))
        self.assertEquals(8, len(self.o.project))
        self.assertEquals(3, len(self.o.project.parent))
        self.assertEquals(4, len(self.o.project.properties))


class NamespaceTestCase(unittest.TestCase):
    """ Tests for XMLs with namespaces """
    def setUp(self):
        self.o = untangle.parse('tests/res/some.xslt')

    def test_namespace(self):
        self.assert_(self.o)

        stylesheet = self.o.xsl_stylesheet
        self.assert_(stylesheet)
        self.assertEquals('1.0', stylesheet['version'])

        template = stylesheet.xsl_template[0]
        self.assert_(template)
        self.assertEquals('math', template['match'])
        self.assertEquals('compact', template.table['class'])
        self.assertEquals(
            'compact vam',
            template.table.tr.xsl_for_each.td['class']
        )
        self.assert_(
            template.table.tr.xsl_for_each.td.xsl_apply_templates
        )

        last_template = stylesheet.xsl_template[-1]
        self.assert_(last_template)
        self.assertEquals('m_var', last_template['match'])
        self.assertEquals(
            'compact tac formula italic',
            last_template.p['class']
        )
        self.assert_(last_template.p.xsl_apply_templates)


class IterationTestCase(unittest.TestCase):
    """ Tests various cases of iteration over child nodes. """
    def test_multiple_children(self):
        """ Regular case of iteration. """
        o = untangle.parse("<a><b/><b/></a>")
        cnt = 0
        for i in o.a.b:
            cnt += 1
        self.assertEquals(2, cnt)

    def test_single_child(self):
        """ Special case when there is only a single child element.
            Does not work without an __iter__ implemented.
        """
        o = untangle.parse("<a><b/></a>")
        cnt = 0
        for i in o.a.b:
            cnt += 1
        self.assertEquals(1, cnt)


class TwimlTestCase(unittest.TestCase):
    """ Github Issue #5: can't dir the parsed object """
    def test_twiml_dir(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather action="http://example.com/calls/1/twiml?event=start"
  numDigits="1" timeout="0">
    <Play>http://example.com/barcall_message_url.wav</Play>
  </Gather>
  <Redirect>http://example.com/calls/1/twiml?event=start</Redirect>
</Response>
        """
        o = untangle.parse(xml)
        self.assertEquals([u'Response'], dir(o))
        resp = o.Response
        self.assertEquals([u'Gather', u'Redirect'], dir(resp))
        gather = resp.Gather
        redir = resp.Redirect
        self.assertEquals([u'Play'], dir(gather))
        self.assertEquals([], dir(redir))
        self.assertEquals(
            u'http://example.com/calls/1/twiml?event=start',
            o.Response.Redirect.cdata
        )


class UnicodeTestCase(unittest.TestCase):
    """ Github issue #8: UnicodeEncodeError """
    def test_unicode_file(self):
        o = untangle.parse('tests/res/unicode.xml')
        self.assertEquals(u'ðÒÉ×ÅÔ ÍÉÒ', o.page.menu.name)

    def test_lengths(self):
        o = untangle.parse('tests/res/unicode.xml')
        self.assertEquals(1, len(o))
        self.assertEquals(1, len(o.page))
        self.assertEquals(2, len(o.page.menu))
        self.assertEquals(2, len(o.page.menu.items))
        self.assertEquals(2, len(o.page.menu.items.item))
        self.assertEquals(0, len(o.page.menu.items.item[0].name))
        self.assertEquals(0, len(o.page.menu.items.item[1].name))


class FileObjects(unittest.TestCase):
    """ Test reading from file-like objects """
    def test_file_object(self):
        with open('tests/res/pom.xml') as pom_file:
            o = untangle.parse(pom_file)
            project = o.project
            self.assert_(project)

            parent = project.parent
            self.assert_(parent)
            self.assertEquals(
                'com.atlassian.confluence.plugin.base',
                parent.groupId
            )
            self.assertEquals('confluence-plugin-base', parent.artifactId)
            self.assertEquals('17', parent.version)


class Foo(object):
    """ Used in UntangleInObjectsTestCase """
    def __init__(self):
        self.doc = untangle.parse('<a><b x="1">foo</b></a>')


class UntangleInObjectsTestCase(unittest.TestCase):
    """ tests usage of untangle in classes """
    def test_object(self):
        foo = Foo()
        self.assertEquals('1', foo.doc.a.b['x'])
        self.assertEquals('foo', foo.doc.a.b.cdata)

class UrlStringTestCase(unittest.TestCase):
    """ tests is_url() function """
    def test_is_url(self):
        self.assertFalse(untangle.is_url('foo'))
        self.assertFalse(untangle.is_url('httpfoo'))
        self.assertFalse(untangle.is_url(7))

class TestSaxHandler(unittest.TestCase):
    """ Tests the SAX ContentHandler """

    def test_empty_handler(self):
        h = untangle.Handler()
        self.assertRaises(IndexError, h.endElement, 'foo')
        self.assertRaises(IndexError, h.characters, 'bar')

    def test_handler(self):
        h = untangle.Handler()
        h.startElement('foo', {})
        h.endElement('foo')
        self.assertEquals('foo', h.root.children[0]._name)

    def test_cdata(self):
        h = untangle.Handler()
        h.startElement('foo', {})
        h.characters('baz')
        self.assertEquals('baz', h.root.children[0].cdata)


if __name__ == '__main__':
    unittest.main()

# vim: set expandtab ts=4 sw=4:

########NEW FILE########
__FILENAME__ = untangle
#!/usr/bin/env python

"""
 untangle

 Converts xml to python objects.

 The only method you need to call is parse()

 Partially inspired by xml2obj
 (http://code.activestate.com/recipes/149368-xml2obj/)

 Author: Christian Stefanescu (http://0chris.com)
 License: MIT License - http://www.opensource.org/licenses/mit-license.php
"""

import os
from xml.sax import make_parser, handler
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
try:
    from types import StringTypes
    is_string = lambda x: isinstance(x, StringTypes)
except ImportError:
    is_string = lambda x: isinstance(x, str)

__version__ = '1.1.0'


class Element(object):
    """
    Representation of an XML element.
    """
    def __init__(self, name, attributes):
        self._name = name
        self._attributes = attributes
        self.children = []
        self.is_root = False
        self.cdata = ''

    def add_child(self, element):
        self.children.append(element)

    def add_cdata(self, cdata):
        self.cdata = self.cdata + cdata

    def get_attribute(self, key):
        return self._attributes.get(key)

    def get_elements(self, name=None):
        if name:
            return [e for e in self.children if e._name == name]
        else:
            return self.children

    def __getitem__(self, key):
        return self.get_attribute(key)

    def __getattr__(self, key):
        matching_children = [x for x in self.children if x._name == key]
        if matching_children:
            if len(matching_children) == 1:
                self.__dict__[key] = matching_children[0]
                return matching_children[0]
            else:
                self.__dict__[key] = matching_children
                return matching_children
        else:
            raise IndexError('Unknown key <%s>' % key)

    def __iter__(self):
        yield self

    def __str__(self):
        return (
            "Element <%s> with attributes %s, children %s and cdata %s" %
            (self._name, self._attributes, self.children, self.cdata)
        )

    def __repr__(self):
        return (
            "Element(name = %s, attributes = %s, cdata = %s)" %
            (self._name, self._attributes, self.cdata)
        )

    def __nonzero__(self):
        return self.is_root or self._name is not None

    def __eq__(self, val):
        return self.cdata == val

    def __dir__(self):
        children_names = [x._name for x in self.children]
        return children_names

    def __len__(self):
        return len(self.children)


class Handler(handler.ContentHandler):
    """
    SAX handler which creates the Python object structure out of ``Element``s
    """
    def __init__(self):
        self.root = Element(None, None)
        self.root.is_root = True
        self.elements = []

    def startElement(self, name, attributes):
        name = name.replace('-', '_')
        name = name.replace('.', '_')
        name = name.replace(':', '_')
        attrs = dict()
        for k, v in attributes.items():
            attrs[k] = v
        element = Element(name, attrs)
        if len(self.elements) > 0:
            self.elements[-1].add_child(element)
        else:
            self.root.add_child(element)
        self.elements.append(element)

    def endElement(self, name):
        self.elements.pop()

    def characters(self, cdata):
        self.elements[-1].add_cdata(cdata)


def parse(filename):
    """
    Interprets the given string as a filename, URL or XML data string,
    parses it and returns a Python object which represents the given
    document.

    Raises ``ValueError`` if the argument is None / empty string.

    Raises ``xml.sax.SAXParseException`` if something goes wrong
    during parsing.s
    """
    if (
        filename is None
        or (is_string(filename) and filename.strip()) == ''
    ):
        raise ValueError('parse() takes a filename, URL or XML string')
    parser = make_parser()
    sax_handler = Handler()
    parser.setContentHandler(sax_handler)
    if is_string(filename) and (os.path.exists(filename) or is_url(filename)):
        parser.parse(filename)
    else:
        if hasattr(filename, 'read'):
            parser.parse(filename)
        else:
            parser.parse(StringIO(filename))

    return sax_handler.root


def is_url(string):
    try:
        return string.startswith('http://') or string.startswith('https://')
    except:
        return False

# vim: set expandtab ts=4 sw=4:

########NEW FILE########