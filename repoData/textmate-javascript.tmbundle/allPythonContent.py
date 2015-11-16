__FILENAME__ = testindentation
import re
import unittest
import jsbeautifier

class TestJSBeautifierIndentation(unittest.TestCase):
    def test_tabs(self):
        test_fragment = self.decodesto

        self.options.indent_with_tabs = 1;
        test_fragment('{tabs()}', "{\n\ttabs()\n}");

    def test_function_indent(self):
        test_fragment = self.decodesto

        self.options.indent_with_tabs = 1;
        self.options.keep_function_indentation = 1;
        test_fragment('var foo = function(){ bar() }();', "var foo = function() {\n\tbar()\n}();");

        self.options.tabs = 1;
        self.options.keep_function_indentation = 0;
        test_fragment('var foo = function(){ baz() }();', "var foo = function() {\n\tbaz()\n}();");

    def decodesto(self, input, expectation=None):
        self.assertEqual(
            jsbeautifier.beautify(input, self.options), expectation or input)

    @classmethod
    def setUpClass(cls):
        options = jsbeautifier.default_options()
        options.indent_size = 4
        options.indent_char = ' '
        options.preserve_newlines = True
        options.jslint_happy = False
        options.keep_array_indentation = False
        options.brace_style = 'collapse'
        options.indent_level = 0

        cls.options = options
        cls.wrapregex = re.compile('^(.+)$', re.MULTILINE)


if __name__ == '__main__':
    unittest.main()

########NEW FILE########
__FILENAME__ = testjsbeautifier
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import unittest
import jsbeautifier

class TestJSBeautifier(unittest.TestCase):
    def test_unescape(self):
        # Test cases contributed by <chrisjshull on GitHub.com>
        test_fragment = self.decodesto
        bt = self.bt

        bt('"\\\\s"'); # == "\\s" in the js source
        bt("'\\\\s'"); # == '\\s' in the js source
        bt("'\\\\\\s'"); # == '\\\s' in the js source
        bt("'\\s'"); # == '\s' in the js source
        bt('"•"');
        bt('"—"');
        bt('"\\x41\\x42\\x43\\x01"', '"\\x41\\x42\\x43\\x01"');
        bt('"\\u2022"', '"\\u2022"');
        bt('a = /\s+/')
        #bt('a = /\\x41/','a = /A/')
        bt('"\\u2022";a = /\s+/;"\\x41\\x42\\x43\\x01".match(/\\x41/);','"\\u2022";\na = /\s+/;\n"\\x41\\x42\\x43\\x01".match(/\\x41/);')
        bt('"\\x22\\x27",\'\\x22\\x27\',"\\x5c",\'\\x5c\',"\\xff and \\xzz","unicode \\u0000 \\u0022 \\u0027 \\u005c \\uffff \\uzzzz"', '"\\x22\\x27", \'\\x22\\x27\', "\\x5c", \'\\x5c\', "\\xff and \\xzz", "unicode \\u0000 \\u0022 \\u0027 \\u005c \\uffff \\uzzzz"');

        self.options.unescape_strings = True

        bt('"\\x41\\x42\\x43\\x01"', '"ABC\\x01"');
        bt('"\\u2022"', '"\\u2022"');
        bt('a = /\s+/')
        bt('"\\u2022";a = /\s+/;"\\x41\\x42\\x43\\x01".match(/\\x41/);','"\\u2022";\na = /\s+/;\n"ABC\\x01".match(/\\x41/);')
        bt('"\\x22\\x27",\'\\x22\\x27\',"\\x5c",\'\\x5c\',"\\xff and \\xzz","unicode \\u0000 \\u0022 \\u0027 \\u005c \\uffff \\uzzzz"', '"\\"\'", \'"\\\'\', "\\\\", \'\\\\\', "\\xff and \\xzz", "unicode \\u0000 \\" \' \\\\ \\uffff \\uzzzz"');

        self.options.unescape_strings = False

    def test_beautifier(self):
        test_fragment = self.decodesto
        bt = self.bt

        bt('');
        bt('return .5');
        test_fragment('    return .5');
        bt('a        =          1', 'a = 1');
        bt('a=1', 'a = 1');
        bt("a();\n\nb();", "a();\n\nb();");
        bt('var a = 1 var b = 2', "var a = 1\nvar b = 2");
        bt('var a=1, b=c[d], e=6;', 'var a = 1,\n    b = c[d],\n    e = 6;');
        bt('a = " 12345 "');
        bt("a = ' 12345 '");
        bt('if (a == 1) b = 2;', "if (a == 1) b = 2;");
        bt('if(1){2}else{3}', "if (1) {\n    2\n} else {\n    3\n}");
        bt('if(1||2);', 'if (1 || 2);');
        bt('(a==1)||(b==2)', '(a == 1) || (b == 2)');
        bt('var a = 1 if (2) 3;', "var a = 1\nif (2) 3;");
        bt('a = a + 1');
        bt('a = a == 1');
        bt('/12345[^678]*9+/.match(a)');
        bt('a /= 5');
        bt('a = 0.5 * 3');
        bt('a *= 10.55');
        bt('a < .5');
        bt('a <= .5');
        bt('a<.5', 'a < .5');
        bt('a<=.5', 'a <= .5');
        bt('a = 0xff;');
        bt('a=0xff+4', 'a = 0xff + 4');
        bt('a = [1, 2, 3, 4]');
        bt('F*(g/=f)*g+b', 'F * (g /= f) * g + b');
        bt('a.b({c:d})', "a.b({\n    c: d\n})");
        bt('a.b\n(\n{\nc:\nd\n}\n)', "a.b({\n    c: d\n})");
        bt('a=!b', 'a = !b');
        bt('a?b:c', 'a ? b : c');
        bt('a?1:2', 'a ? 1 : 2');
        bt('a?(b):c', 'a ? (b) : c');
        bt('x={a:1,b:w=="foo"?x:y,c:z}', 'x = {\n    a: 1,\n    b: w == "foo" ? x : y,\n    c: z\n}');
        bt('x=a?b?c?d:e:f:g;', 'x = a ? b ? c ? d : e : f : g;');
        bt('x=a?b?c?d:{e1:1,e2:2}:f:g;', 'x = a ? b ? c ? d : {\n    e1: 1,\n    e2: 2\n} : f : g;');
        bt('function void(void) {}');
        bt('if(!a)foo();', 'if (!a) foo();');
        bt('a=~a', 'a = ~a');
        bt('a;/*comment*/b;', "a; /*comment*/\nb;");
        bt('a;/* comment */b;', "a; /* comment */\nb;");
        test_fragment('a;/*\ncomment\n*/b;', "a;\n/*\ncomment\n*/\nb;"); # simple comments don't get touched at all
        bt('a;/**\n* javadoc\n*/b;', "a;\n/**\n * javadoc\n */\nb;");
        test_fragment('a;/**\n\nno javadoc\n*/b;', "a;\n/**\n\nno javadoc\n*/\nb;");
        bt('a;/*\n* javadoc\n*/b;', "a;\n/*\n * javadoc\n */\nb;"); # comment blocks detected and reindented even w/o javadoc starter

        bt('if(a)break;', "if (a) break;");
        bt('if(a){break}', "if (a) {\n    break\n}");
        bt('if((a))foo();', 'if ((a)) foo();');
        bt('for(var i=0;;) a', 'for (var i = 0;;) a');
        bt('for(var i=0;;)\na', 'for (var i = 0;;)\n    a');
        bt('a++;', 'a++;');
        bt('for(;;i++)a()', 'for (;; i++) a()');
        bt('for(;;i++)\na()', 'for (;; i++)\n    a()');
        bt('for(;;++i)a', 'for (;; ++i) a');
        bt('return(1)', 'return (1)');
        bt('try{a();}catch(b){c();}finally{d();}', "try {\n    a();\n} catch (b) {\n    c();\n} finally {\n    d();\n}");
        bt('(xx)()'); # magic function call
        bt('a[1]()'); # another magic function call
        bt('if(a){b();}else if(c) foo();', "if (a) {\n    b();\n} else if (c) foo();");
        bt('switch(x) {case 0: case 1: a(); break; default: break}', "switch (x) {\n    case 0:\n    case 1:\n        a();\n        break;\n    default:\n        break\n}");
        bt('switch(x){case -1:break;case !y:break;}', 'switch (x) {\n    case -1:\n        break;\n    case !y:\n        break;\n}');
        bt('a !== b');
        bt('if (a) b(); else c();', "if (a) b();\nelse c();");
        bt("// comment\n(function something() {})"); # typical greasemonkey start
        bt("{\n\n    x();\n\n}"); # was: duplicating newlines
        bt('if (a in b) foo();');
        bt('var a, b;');
        # bt('var a, b');
        bt('{a:1, b:2}', "{\n    a: 1,\n    b: 2\n}");
        bt('a={1:[-1],2:[+1]}', 'a = {\n    1: [-1],\n    2: [+1]\n}');
        bt('var l = {\'a\':\'1\', \'b\':\'2\'}', "var l = {\n    'a': '1',\n    'b': '2'\n}");
        bt('if (template.user[n] in bk) foo();');
        bt('{{}/z/}', "{\n    {}\n    /z/\n}");
        bt('return 45', "return 45");
        bt('If[1]', "If[1]");
        bt('Then[1]', "Then[1]");
        bt('a = 1e10', "a = 1e10");
        bt('a = 1.3e10', "a = 1.3e10");
        bt('a = 1.3e-10', "a = 1.3e-10");
        bt('a = -1.3e-10', "a = -1.3e-10");
        bt('a = 1e-10', "a = 1e-10");
        bt('a = e - 10', "a = e - 10");
        bt('a = 11-10', "a = 11 - 10");
        bt("a = 1;// comment", "a = 1; // comment");
        bt("a = 1; // comment", "a = 1; // comment");
        bt("a = 1;\n // comment", "a = 1;\n// comment");
        bt('a = [-1, -1, -1]');

        # The exact formatting these should have is open for discussion, but they are at least reasonable
        bt('a = [ // comment\n    -1, -1, -1\n]');
        bt('var a = [ // comment\n    -1, -1, -1\n]');
        bt('a = [ // comment\n    -1, // comment\n    -1, -1\n]');
        bt('var a = [ // comment\n    -1, // comment\n    -1, -1\n]');

        bt('o = [{a:b},{c:d}]', 'o = [{\n    a: b\n}, {\n    c: d\n}]');

        bt("if (a) {\n    do();\n}"); # was: extra space appended

        bt("if (a) {\n// comment\n}else{\n// comment\n}", "if (a) {\n    // comment\n} else {\n    // comment\n}"); # if/else statement with empty body
        bt("if (a) {\n// comment\n// comment\n}", "if (a) {\n    // comment\n    // comment\n}"); # multiple comments indentation
        bt("if (a) b() else c();", "if (a) b()\nelse c();");
        bt("if (a) b() else if c() d();", "if (a) b()\nelse if c() d();");

        bt("{}");
        bt("{\n\n}");
        bt("do { a(); } while ( 1 );", "do {\n    a();\n} while (1);");
        bt("do {} while (1);");
        bt("do {\n} while (1);", "do {} while (1);");
        bt("do {\n\n} while (1);");
        bt("var a = x(a, b, c)");
        bt("delete x if (a) b();", "delete x\nif (a) b();");
        bt("delete x[x] if (a) b();", "delete x[x]\nif (a) b();");
        bt("for(var a=1,b=2)d", "for (var a = 1, b = 2) d");
        bt("for(var a=1,b=2,c=3) d", "for (var a = 1, b = 2, c = 3) d");
        bt("for(var a=1,b=2,c=3;d<3;d++)\ne", "for (var a = 1, b = 2, c = 3; d < 3; d++)\n    e");
        bt("function x(){(a||b).c()}", "function x() {\n    (a || b).c()\n}");
        bt("function x(){return - 1}", "function x() {\n    return -1\n}");
        bt("function x(){return ! a}", "function x() {\n    return !a\n}");

        # a common snippet in jQuery plugins
        bt("settings = $.extend({},defaults,settings);", "settings = $.extend({}, defaults, settings);");

        bt('{xxx;}()', '{\n    xxx;\n}()');

        bt("a = 'a'\nb = 'b'");
        bt("a = /reg/exp");
        bt("a = /reg/");
        bt('/abc/.test()');
        bt('/abc/i.test()');
        bt("{/abc/i.test()}", "{\n    /abc/i.test()\n}");
        bt('var x=(a)/a;', 'var x = (a) / a;');

        bt('x != -1', 'x != -1');

        bt('for (; s-->0;)t', 'for (; s-- > 0;) t');
        bt('for (; s++>0;)u', 'for (; s++ > 0;) u');
        bt('a = s++>s--;', 'a = s++ > s--;');
        bt('a = s++>--s;', 'a = s++ > --s;');

        bt('{x=#1=[]}', '{\n    x = #1=[]\n}');
        bt('{a:#1={}}', '{\n    a: #1={}\n}');
        bt('{a:#1#}', '{\n    a: #1#\n}');

        test_fragment('"incomplete-string');
        test_fragment("'incomplete-string");
        test_fragment('/incomplete-regex');

        test_fragment('{a:1},{a:2}', '{\n    a: 1\n}, {\n    a: 2\n}');
        test_fragment('var ary=[{a:1}, {a:2}];', 'var ary = [{\n    a: 1\n}, {\n    a: 2\n}];');

        test_fragment('{a:#1', '{\n    a: #1'); # incomplete
        test_fragment('{a:#', '{\n    a: #'); # incomplete

        test_fragment('}}}', '}\n}\n}'); # incomplete

        test_fragment('<!--\nvoid();\n// -->', '<!--\nvoid();\n// -->');

        test_fragment('a=/regexp', 'a = /regexp'); # incomplete regexp

        bt('{a:#1=[],b:#1#,c:#999999#}', '{\n    a: #1=[],\n    b: #1#,\n    c: #999999#\n}');

        bt("a = 1e+2");
        bt("a = 1e-2");
        bt("do{x()}while(a>1)", "do {\n    x()\n} while (a > 1)");

        bt("x(); /reg/exp.match(something)", "x();\n/reg/exp.match(something)");

        test_fragment("something();(", "something();\n(");
        test_fragment("#!she/bangs, she bangs\nf=1", "#!she/bangs, she bangs\n\nf = 1");
        test_fragment("#!she/bangs, she bangs\n\nf=1", "#!she/bangs, she bangs\n\nf = 1");
        test_fragment("#!she/bangs, she bangs\n\n/* comment */", "#!she/bangs, she bangs\n\n/* comment */");
        test_fragment("#!she/bangs, she bangs\n\n\n/* comment */", "#!she/bangs, she bangs\n\n\n/* comment */");
        test_fragment("#", "#");
        test_fragment("#!", "#!");

        bt("function namespace::something()");

        test_fragment("<!--\nsomething();\n-->", "<!--\nsomething();\n-->");
        test_fragment("<!--\nif(i<0){bla();}\n-->", "<!--\nif (i < 0) {\n    bla();\n}\n-->");

        bt('{foo();--bar;}', '{\n    foo();\n    --bar;\n}');
        bt('{foo();++bar;}', '{\n    foo();\n    ++bar;\n}');
        bt('{--bar;}', '{\n    --bar;\n}');
        bt('{++bar;}', '{\n    ++bar;\n}');

        # Handling of newlines around unary ++ and -- operators
        bt('{foo\n++bar;}', '{\n    foo\n    ++bar;\n}');
        bt('{foo++\nbar;}', '{\n    foo++\n    bar;\n}');

        # This is invalid, but harder to guard against. Issue #203.
        bt('{foo\n++\nbar;}', '{\n    foo\n    ++\n    bar;\n}');


        # regexps
        bt('a(/abc\\/\\/def/);b()', "a(/abc\\/\\/def/);\nb()");
        bt('a(/a[b\\[\\]c]d/);b()', "a(/a[b\\[\\]c]d/);\nb()");
        test_fragment('a(/a[b\\[', "a(/a[b\\["); # incomplete char class
        # allow unescaped / in char classes
        bt('a(/[a/b]/);b()', "a(/[a/b]/);\nb()");

        bt('a=[[1,2],[4,5],[7,8]]', "a = [\n    [1, 2],\n    [4, 5],\n    [7, 8]\n]");
        bt('a=[[1,2],[4,5],function(){},[7,8]]',
            "a = [\n    [1, 2],\n    [4, 5],\n    function() {},\n    [7, 8]\n]");
        bt('a=[[1,2],[4,5],function(){},function(){},[7,8]]',
            "a = [\n    [1, 2],\n    [4, 5],\n    function() {},\n    function() {},\n    [7, 8]\n]");
        bt('a=[[1,2],[4,5],function(){},[7,8]]',
            "a = [\n    [1, 2],\n    [4, 5],\n    function() {},\n    [7, 8]\n]");
        bt('a=[b,c,function(){},function(){},d]',
            "a = [b, c,\n    function() {},\n    function() {},\n    d\n]");
        bt('a=[a[1],b[4],c[d[7]]]', "a = [a[1], b[4], c[d[7]]]");
        bt('[1,2,[3,4,[5,6],7],8]', "[1, 2, [3, 4, [5, 6], 7], 8]");

        bt('[[["1","2"],["3","4"]],[["5","6","7"],["8","9","0"]],[["1","2","3"],["4","5","6","7"],["8","9","0"]]]',
            '[\n    [\n        ["1", "2"],\n        ["3", "4"]\n    ],\n    [\n        ["5", "6", "7"],\n        ["8", "9", "0"]\n    ],\n    [\n        ["1", "2", "3"],\n        ["4", "5", "6", "7"],\n        ["8", "9", "0"]\n    ]\n]');

        bt('{[x()[0]];indent;}', '{\n    [x()[0]];\n    indent;\n}');

        bt('return ++i', 'return ++i');
        bt('return !!x', 'return !!x');
        bt('return !x', 'return !x');
        bt('return [1,2]', 'return [1, 2]');
        bt('return;', 'return;');
        bt('return\nfunc', 'return\nfunc');
        bt('catch(e)', 'catch (e)');

        bt('var a=1,b={foo:2,bar:3},{baz:4,wham:5},c=4;',
           'var a = 1,\n    b = {\n        foo: 2,\n        bar: 3\n    }, {\n        baz: 4,\n        wham: 5\n    }, c = 4;');
        bt('var a=1,b={foo:2,bar:3},{baz:4,wham:5},\nc=4;',
           'var a = 1,\n    b = {\n        foo: 2,\n        bar: 3\n    }, {\n        baz: 4,\n        wham: 5\n    },\n    c = 4;');

        # inline comment
        bt('function x(/*int*/ start, /*string*/ foo)', 'function x( /*int*/ start, /*string*/ foo)');

        # javadoc comment
        bt('/**\n* foo\n*/', '/**\n * foo\n */');
        bt('{\n/**\n* foo\n*/\n}', '{\n    /**\n     * foo\n     */\n}');

        bt('var a,b,c=1,d,e,f=2;', 'var a, b, c = 1,\n    d, e, f = 2;');
        bt('var a,b,c=[],d,e,f=2;', 'var a, b, c = [],\n    d, e, f = 2;');
        bt('function() {\n    var a, b, c, d, e = [],\n        f;\n}');

        bt('do/regexp/;\nwhile(1);', 'do /regexp/;\nwhile (1);'); # hmmm

        bt('var a = a,\na;\nb = {\nb\n}', 'var a = a,\n    a;\nb = {\n    b\n}');

        bt('var a = a,\n    /* c */\n    b;');
        bt('var a = a,\n    // c\n    b;');

        bt('foo.("bar");'); # weird element referencing


        bt('if (a) a()\nelse b()\nnewline()');
        bt('if (a) a()\nnewline()');
        bt('a=typeof(x)', 'a = typeof(x)');

        bt('var a = function() {\n    return null;\n},\n    b = false;');

        bt('var a = function() {\n    func1()\n}');
        bt('var a = function() {\n    func1()\n}\nvar b = function() {\n    func2()\n}');




        self.options.jslint_happy = True

        bt('x();\n\nfunction(){}', 'x();\n\nfunction () {}');
        bt('function () {\n    var a, b, c, d, e = [],\n        f;\n}');
        bt('switch(x) {case 0: case 1: a(); break; default: break}',
            "switch (x) {\ncase 0:\ncase 1:\n    a();\n    break;\ndefault:\n    break\n}");
        bt('switch(x){case -1:break;case !y:break;}',
            'switch (x) {\ncase -1:\n    break;\ncase !y:\n    break;\n}');
        test_fragment("// comment 1\n(function()", "// comment 1\n(function ()"); # typical greasemonkey start
        bt('var o1=$.extend(a);function(){alert(x);}', 'var o1 = $.extend(a);\n\nfunction () {\n    alert(x);\n}');
        bt('a=typeof(x)', 'a = typeof (x)');

        self.options.jslint_happy = False

        bt('switch(x) {case 0: case 1: a(); break; default: break}',
            "switch (x) {\n    case 0:\n    case 1:\n        a();\n        break;\n    default:\n        break\n}");
        bt('switch(x){case -1:break;case !y:break;}',
            'switch (x) {\n    case -1:\n        break;\n    case !y:\n        break;\n}');
        test_fragment("// comment 2\n(function()", "// comment 2\n(function()"); # typical greasemonkey start
        bt("var a2, b2, c2, d2 = 0, c = function() {}, d = '';", "var a2, b2, c2, d2 = 0,\n    c = function() {}, d = '';");
        bt("var a2, b2, c2, d2 = 0, c = function() {},\nd = '';", "var a2, b2, c2, d2 = 0,\n    c = function() {},\n    d = '';");
        bt('var o2=$.extend(a);function(){alert(x);}', 'var o2 = $.extend(a);\n\nfunction() {\n    alert(x);\n}');

        bt('{"x":[{"a":1,"b":3},7,8,8,8,8,{"b":99},{"a":11}]}', '{\n    "x": [{\n            "a": 1,\n            "b": 3\n        },\n        7, 8, 8, 8, 8, {\n            "b": 99\n        }, {\n            "a": 11\n        }\n    ]\n}');

        bt('{"1":{"1a":"1b"},"2"}', '{\n    "1": {\n        "1a": "1b"\n    },\n    "2"\n}');
        bt('{a:{a:b},c}', '{\n    a: {\n        a: b\n    },\n    c\n}');

        bt('{[y[a]];keep_indent;}', '{\n    [y[a]];\n    keep_indent;\n}');

        bt('if (x) {y} else { if (x) {y}}', 'if (x) {\n    y\n} else {\n    if (x) {\n        y\n    }\n}');

        bt('if (foo) one()\ntwo()\nthree()');
        bt('if (1 + foo() && bar(baz()) / 2) one()\ntwo()\nthree()');
        bt('if (1 + foo() && bar(baz()) / 2) one();\ntwo();\nthree();');

        self.options.indent_size = 1;
        self.options.indent_char = ' ';
        bt('{ one_char() }', "{\n one_char()\n}");

        bt('var a,b=1,c=2', 'var a, b = 1,\n c = 2');

        self.options.indent_size = 4;
        self.options.indent_char = ' ';
        bt('{ one_char() }', "{\n    one_char()\n}");

        self.options.indent_size = 1;
        self.options.indent_char = "\t";
        bt('{ one_char() }', "{\n\tone_char()\n}");
        bt('x = a ? b : c; x;', 'x = a ? b : c;\nx;');

        self.options.indent_size = 4;
        self.options.indent_char = ' ';

        self.options.preserve_newlines = False;
        bt('var\na=dont_preserve_newlines;', 'var a = dont_preserve_newlines;');

        # make sure the blank line between function definitions stays
        # even when preserve_newlines = False
        bt('function foo() {\n    return 1;\n}\n\nfunction foo() {\n    return 1;\n}');
        bt('function foo() {\n    return 1;\n}\nfunction foo() {\n    return 1;\n}',
        'function foo() {\n    return 1;\n}\n\nfunction foo() {\n    return 1;\n}'
        );
        bt('function foo() {\n    return 1;\n}\n\n\nfunction foo() {\n    return 1;\n}',
        'function foo() {\n    return 1;\n}\n\nfunction foo() {\n    return 1;\n}'
        );


        self.options.preserve_newlines = True;
        bt('var\na=do_preserve_newlines;', 'var\na = do_preserve_newlines;')
        bt('// a\n// b\n\n// c\n// d')
        bt('if (foo) //  comment\n{\n    bar();\n}')


        self.options.keep_array_indentation = False;
        bt("a = ['a', 'b', 'c',\n    'd', 'e', 'f']",
            "a = ['a', 'b', 'c',\n    'd', 'e', 'f'\n]");
        bt("a = ['a', 'b', 'c',\n    'd', 'e', 'f',\n        'g', 'h', 'i']",
            "a = ['a', 'b', 'c',\n    'd', 'e', 'f',\n    'g', 'h', 'i'\n]");
        bt("a = ['a', 'b', 'c',\n        'd', 'e', 'f',\n            'g', 'h', 'i']",
            "a = ['a', 'b', 'c',\n    'd', 'e', 'f',\n    'g', 'h', 'i'\n]");
        bt('var x = [{}\n]', 'var x = [{}]');
        bt('var x = [{foo:bar}\n]', 'var x = [{\n    foo: bar\n}]');
        bt("a = ['something',\n    'completely',\n    'different'];\nif (x);",
            "a = ['something',\n    'completely',\n    'different'\n];\nif (x);");
        bt("a = ['a','b','c']", "a = ['a', 'b', 'c']");
        bt("a = ['a',   'b','c']", "a = ['a', 'b', 'c']");
        bt("x = [{'a':0}]",
            "x = [{\n    'a': 0\n}]");
        bt('{a([[a1]], {b;});}',
            '{\n    a([\n        [a1]\n    ], {\n        b;\n    });\n}');
        bt("a();\n   [\n   ['sdfsdfsd'],\n        ['sdfsdfsdf']\n   ].toString();",
            "a();\n[\n    ['sdfsdfsd'],\n    ['sdfsdfsdf']\n].toString();");
        bt("function() {\n    Foo([\n        ['sdfsdfsd'],\n        ['sdfsdfsdf']\n    ]);\n}",
            "function() {\n    Foo([\n        ['sdfsdfsd'],\n        ['sdfsdfsdf']\n    ]);\n}");

        self.options.keep_array_indentation = True;
        bt("a = ['a', 'b', 'c',\n    'd', 'e', 'f']");
        bt("a = ['a', 'b', 'c',\n    'd', 'e', 'f',\n        'g', 'h', 'i']");
        bt("a = ['a', 'b', 'c',\n        'd', 'e', 'f',\n            'g', 'h', 'i']");
        bt('var x = [{}\n]', 'var x = [{}\n]');
        bt('var x = [{foo:bar}\n]', 'var x = [{\n        foo: bar\n    }\n]');
        bt("a = ['something',\n    'completely',\n    'different'];\nif (x);");
        bt("a = ['a','b','c']", "a = ['a', 'b', 'c']");
        bt("a = ['a',   'b','c']", "a = ['a', 'b', 'c']");
        bt("x = [{'a':0}]",
            "x = [{\n    'a': 0\n}]");
        bt('{a([[a1]], {b;});}',
            '{\n    a([[a1]], {\n        b;\n    });\n}');
        bt("a();\n   [\n   ['sdfsdfsd'],\n        ['sdfsdfsdf']\n   ].toString();",
            "a();\n   [\n   ['sdfsdfsd'],\n        ['sdfsdfsdf']\n   ].toString();");
        bt("function() {\n    Foo([\n        ['sdfsdfsd'],\n        ['sdfsdfsdf']\n    ]);\n}",
            "function() {\n    Foo([\n        ['sdfsdfsd'],\n        ['sdfsdfsdf']\n    ]);\n}");
        self.options.keep_array_indentation = False;

        bt('a = //comment\n/regex/;');

        test_fragment('/*\n * X\n */');
        test_fragment('/*\r\n * X\r\n */', '/*\n * X\n */');

        bt('if (a)\n{\nb;\n}\nelse\n{\nc;\n}', 'if (a) {\n    b;\n} else {\n    c;\n}');

        bt('var a = new function();');
        test_fragment('new function');

        self.options.brace_style = 'expand';

        bt('//case 1\nif (a == 1)\n{}\n//case 2\nelse if (a == 2)\n{}');
        bt('if(1){2}else{3}', "if (1)\n{\n    2\n}\nelse\n{\n    3\n}");
        bt('try{a();}catch(b){c();}catch(d){}finally{e();}',
            "try\n{\n    a();\n}\ncatch (b)\n{\n    c();\n}\ncatch (d)\n{}\nfinally\n{\n    e();\n}");
        bt('if(a){b();}else if(c) foo();',
            "if (a)\n{\n    b();\n}\nelse if (c) foo();");
        bt("if (a) {\n// comment\n}else{\n// comment\n}",
            "if (a)\n{\n    // comment\n}\nelse\n{\n    // comment\n}"); # if/else statement with empty body
        bt('if (x) {y} else { if (x) {y}}',
            'if (x)\n{\n    y\n}\nelse\n{\n    if (x)\n    {\n        y\n    }\n}');
        bt('if (a)\n{\nb;\n}\nelse\n{\nc;\n}',
            'if (a)\n{\n    b;\n}\nelse\n{\n    c;\n}');
        test_fragment('    /*\n* xx\n*/\n// xx\nif (foo) {\n    bar();\n}',
                      '    /*\n     * xx\n     */\n    // xx\n    if (foo)\n    {\n        bar();\n    }');
        bt('if (foo)\n{}\nelse /regex/.test();');
        bt('if (foo) /regex/.test();');
        bt('if (a)\n{\nb;\n}\nelse\n{\nc;\n}', 'if (a)\n{\n    b;\n}\nelse\n{\n    c;\n}');
        test_fragment('if (foo) {', 'if (foo)\n{');
        test_fragment('foo {', 'foo\n{');
        test_fragment('return {', 'return {'); # return needs the brace.
        test_fragment('return /* inline */ {', 'return /* inline */ {');
        # test_fragment('return\n{', 'return\n{'); # can't support this?, but that's an improbable and extreme case anyway.
        test_fragment('return;\n{', 'return;\n{');
        bt("throw {}");
        bt("throw {\n    foo;\n}");
        bt('var foo = {}');
        bt('if (foo) bar();\nelse break');
        bt('function x() {\n    foo();\n}zzz', 'function x()\n{\n    foo();\n}\nzzz');
        bt('a: do {} while (); xxx', 'a: do {} while ();\nxxx');
        bt('var a = new function();');
        bt('var a = new function() {};');
        bt('var a = new function a()\n    {};');
        test_fragment('new function');
        bt("foo({\n    'a': 1\n},\n10);",
            "foo(\n    {\n        'a': 1\n    },\n    10);");
        bt('(["foo","bar"]).each(function(i) {return i;});',
            '(["foo", "bar"]).each(function(i)\n{\n    return i;\n});');
        bt('(function(i) {return i;})();',
            '(function(i)\n{\n    return i;\n})();');
        bt( "test( /*Argument 1*/ {\n" +
            "    'Value1': '1'\n" +
            "}, /*Argument 2\n" +
            " */ {\n" +
            "    'Value2': '2'\n" +
            "});",
            # expected
            "test( /*Argument 1*/\n" +
            "    {\n" +
            "        'Value1': '1'\n" +
            "    },\n" +
            "    /*Argument 2\n" +
            "     */\n" +
            "    {\n" +
            "        'Value2': '2'\n" +
            "    });");
        bt( "test(\n" +
            "/*Argument 1*/ {\n" +
            "    'Value1': '1'\n" +
            "},\n" +
            "/*Argument 2\n" +
            " */ {\n" +
            "    'Value2': '2'\n" +
            "});",
            # expected
            "test(\n" +
            "    /*Argument 1*/\n" +
            "    {\n" +
            "        'Value1': '1'\n" +
            "    },\n" +
            "    /*Argument 2\n" +
            "     */\n" +
            "    {\n" +
            "        'Value2': '2'\n" +
            "    });");
        bt( "test( /*Argument 1*/\n" +
            "{\n" +
            "    'Value1': '1'\n" +
            "}, /*Argument 2\n" +
            " */\n" +
            "{\n" +
            "    'Value2': '2'\n" +
            "});",
            # expected
            "test( /*Argument 1*/\n" +
            "    {\n" +
            "        'Value1': '1'\n" +
            "    },\n" +
            "    /*Argument 2\n" +
            "     */\n" +
            "    {\n" +
            "        'Value2': '2'\n" +
            "    });");

        self.options.brace_style = 'collapse';

        bt('//case 1\nif (a == 1) {}\n//case 2\nelse if (a == 2) {}');
        bt('if(1){2}else{3}', "if (1) {\n    2\n} else {\n    3\n}");
        bt('try{a();}catch(b){c();}catch(d){}finally{e();}',
             "try {\n    a();\n} catch (b) {\n    c();\n} catch (d) {} finally {\n    e();\n}");
        bt('if(a){b();}else if(c) foo();',
            "if (a) {\n    b();\n} else if (c) foo();");
        bt("if (a) {\n// comment\n}else{\n// comment\n}",
            "if (a) {\n    // comment\n} else {\n    // comment\n}"); # if/else statement with empty body
        bt('if (x) {y} else { if (x) {y}}',
            'if (x) {\n    y\n} else {\n    if (x) {\n        y\n    }\n}');
        bt('if (a)\n{\nb;\n}\nelse\n{\nc;\n}',
            'if (a) {\n    b;\n} else {\n    c;\n}');
        test_fragment('    /*\n* xx\n*/\n// xx\nif (foo) {\n    bar();\n}',
                      '    /*\n     * xx\n     */\n    // xx\n    if (foo) {\n        bar();\n    }');
        bt('if (foo) {} else /regex/.test();');
        bt('if (foo) /regex/.test();');
        bt('if (a)\n{\nb;\n}\nelse\n{\nc;\n}', 'if (a) {\n    b;\n} else {\n    c;\n}');
        test_fragment('if (foo) {', 'if (foo) {');
        test_fragment('foo {', 'foo {');
        test_fragment('return {', 'return {'); # return needs the brace.
        test_fragment('return /* inline */ {', 'return /* inline */ {');
        # test_fragment('return\n{', 'return\n{'); # can't support this?, but that's an improbable and extreme case anyway.
        test_fragment('return;\n{', 'return; {');
        bt("throw {}");
        bt("throw {\n    foo;\n}");
        bt('var foo = {}');
        bt('if (foo) bar();\nelse break');
        bt('function x() {\n    foo();\n}zzz', 'function x() {\n    foo();\n}\nzzz');
        bt('a: do {} while (); xxx', 'a: do {} while ();\nxxx');
        bt('var a = new function();');
        bt('var a = new function() {};');
        bt('var a = new function a() {};');
        test_fragment('new function');
        bt("foo({\n    'a': 1\n},\n10);",
            "foo({\n        'a': 1\n    },\n    10);");
        bt('(["foo","bar"]).each(function(i) {return i;});',
            '(["foo", "bar"]).each(function(i) {\n    return i;\n});');
        bt('(function(i) {return i;})();',
            '(function(i) {\n    return i;\n})();');
        bt( "test( /*Argument 1*/ {\n" +
            "    'Value1': '1'\n" +
            "}, /*Argument 2\n" +
            " */ {\n" +
            "    'Value2': '2'\n" +
            "});",
            # expected
            "test( /*Argument 1*/ {\n" +
            "        'Value1': '1'\n" +
            "    },\n" +
            "    /*Argument 2\n" +
            "     */\n" +
            "    {\n" +
            "        'Value2': '2'\n" +
            "    });");
        bt( "test(\n" +
            "/*Argument 1*/ {\n" +
            "    'Value1': '1'\n" +
            "},\n" +
            "/*Argument 2\n" +
            " */ {\n" +
            "    'Value2': '2'\n" +
            "});",
            # expected
            "test(\n" +
            "    /*Argument 1*/\n" +
            "    {\n" +
            "        'Value1': '1'\n" +
            "    },\n" +
            "    /*Argument 2\n" +
            "     */\n" +
            "    {\n" +
            "        'Value2': '2'\n" +
            "    });");
        bt( "test( /*Argument 1*/\n" +
            "{\n" +
            "    'Value1': '1'\n" +
            "}, /*Argument 2\n" +
            " */\n" +
            "{\n" +
            "    'Value2': '2'\n" +
            "});",
            # expected
            "test( /*Argument 1*/ {\n" +
            "        'Value1': '1'\n" +
            "    },\n" +
            "    /*Argument 2\n" +
            "     */\n" +
            "    {\n" +
            "        'Value2': '2'\n" +
            "    });");

        self.options.brace_style = "end-expand";

        bt('//case 1\nif (a == 1) {}\n//case 2\nelse if (a == 2) {}');
        bt('if(1){2}else{3}', "if (1) {\n    2\n}\nelse {\n    3\n}");
        bt('try{a();}catch(b){c();}catch(d){}finally{e();}',
            "try {\n    a();\n}\ncatch (b) {\n    c();\n}\ncatch (d) {}\nfinally {\n    e();\n}");
        bt('if(a){b();}else if(c) foo();',
            "if (a) {\n    b();\n}\nelse if (c) foo();");
        bt("if (a) {\n// comment\n}else{\n// comment\n}",
            "if (a) {\n    // comment\n}\nelse {\n    // comment\n}"); # if/else statement with empty body
        bt('if (x) {y} else { if (x) {y}}',
            'if (x) {\n    y\n}\nelse {\n    if (x) {\n        y\n    }\n}');
        bt('if (a)\n{\nb;\n}\nelse\n{\nc;\n}',
            'if (a) {\n    b;\n}\nelse {\n    c;\n}');
        test_fragment('    /*\n* xx\n*/\n// xx\nif (foo) {\n    bar();\n}',
                      '    /*\n     * xx\n     */\n    // xx\n    if (foo) {\n        bar();\n    }');
        bt('if (foo) {}\nelse /regex/.test();');
        bt('if (foo) /regex/.test();');
        bt('if (a)\n{\nb;\n}\nelse\n{\nc;\n}', 'if (a) {\n    b;\n}\nelse {\n    c;\n}');
        test_fragment('if (foo) {', 'if (foo) {');
        test_fragment('foo {', 'foo {');
        test_fragment('return {', 'return {'); # return needs the brace.
        test_fragment('return /* inline */ {', 'return /* inline */ {');
        # test_fragment('return\n{', 'return\n{'); # can't support this?, but that's an improbable and extreme case anyway.
        test_fragment('return;\n{', 'return; {');
        bt("throw {}");
        bt("throw {\n    foo;\n}");
        bt('var foo = {}');
        bt('if (foo) bar();\nelse break');
        bt('function x() {\n    foo();\n}zzz', 'function x() {\n    foo();\n}\nzzz');
        bt('a: do {} while (); xxx', 'a: do {} while ();\nxxx');
        bt('var a = new function();');
        bt('var a = new function() {};');
        bt('var a = new function a() {};');
        test_fragment('new function');
        bt("foo({\n    'a': 1\n},\n10);",
            "foo({\n        'a': 1\n    },\n    10);");
        bt('(["foo","bar"]).each(function(i) {return i;});',
            '(["foo", "bar"]).each(function(i) {\n    return i;\n});');
        bt('(function(i) {return i;})();',
            '(function(i) {\n    return i;\n})();');
        bt( "test( /*Argument 1*/ {\n" +
            "    'Value1': '1'\n" +
            "}, /*Argument 2\n" +
            " */ {\n" +
            "    'Value2': '2'\n" +
            "});",
            # expected
            "test( /*Argument 1*/ {\n" +
            "        'Value1': '1'\n" +
            "    },\n" +
            "    /*Argument 2\n" +
            "     */\n" +
            "    {\n" +
            "        'Value2': '2'\n" +
            "    });");
        bt( "test(\n" +
            "/*Argument 1*/ {\n" +
            "    'Value1': '1'\n" +
            "},\n" +
            "/*Argument 2\n" +
            " */ {\n" +
            "    'Value2': '2'\n" +
            "});",
            # expected
            "test(\n" +
            "    /*Argument 1*/\n" +
            "    {\n" +
            "        'Value1': '1'\n" +
            "    },\n" +
            "    /*Argument 2\n" +
            "     */\n" +
            "    {\n" +
            "        'Value2': '2'\n" +
            "    });");
        bt( "test( /*Argument 1*/\n" +
            "{\n" +
            "    'Value1': '1'\n" +
            "}, /*Argument 2\n" +
            " */\n" +
            "{\n" +
            "    'Value2': '2'\n" +
            "});",
            # expected
            "test( /*Argument 1*/ {\n" +
            "        'Value1': '1'\n" +
            "    },\n" +
            "    /*Argument 2\n" +
            "     */\n" +
            "    {\n" +
            "        'Value2': '2'\n" +
            "    });");

        self.options.brace_style = 'collapse';

        bt('a = <?= external() ?> ;'); # not the most perfect thing in the world, but you're the weirdo beaufifying php mix-ins with javascript beautifier
        bt('a = <%= external() %> ;');

        test_fragment('roo = {\n    /*\n    ****\n      FOO\n    ****\n    */\n    BAR: 0\n};');
        test_fragment("if (zz) {\n    // ....\n}\n(function");

        self.options.preserve_newlines = True;
        bt('var a = 42; // foo\n\nvar b;')
        bt('var a = 42; // foo\n\n\nvar b;')
        bt("var a = 'foo' +\n    'bar';");
        bt("var a = \"foo\" +\n    \"bar\";");

        bt('"foo""bar""baz"', '"foo"\n"bar"\n"baz"')
        bt("'foo''bar''baz'", "'foo'\n'bar'\n'baz'")
        bt("{\n    get foo() {}\n}")
        bt("{\n    var a = get\n    foo();\n}")
        bt("{\n    set foo() {}\n}")
        bt("{\n    var a = set\n    foo();\n}")
        bt("var x = {\n    get function()\n}")
        bt("var x = {\n    set function()\n}")
        bt("var x = set\n\nfunction() {}", "var x = set\n\n    function() {}")

        bt('<!-- foo\nbar();\n-->')
        bt('<!-- dont crash')
        bt('for () /abc/.test()')
        bt('if (k) /aaa/m.test(v) && l();')
        bt('switch (true) {\n    case /swf/i.test(foo):\n        bar();\n}')
        bt('createdAt = {\n    type: Date,\n    default: Date.now\n}')
        bt('switch (createdAt) {\n    case a:\n        Date,\n    default:\n        Date.now\n}')

        bt('return function();')
        bt('var a = function();')
        bt('var a = 5 + function();')

        bt('{\n    foo // something\n    ,\n    bar // something\n    baz\n}')
        bt('function a(a) {} function b(b) {} function c(c) {}', 'function a(a) {}\n\nfunction b(b) {}\n\nfunction c(c) {}')


        bt('3.*7;', '3. * 7;')
        bt('import foo.*;', 'import foo.*;') # actionscript's import
        test_fragment('function f(a: a, b: b)') # actionscript
        bt('foo(a, function() {})');
        bt('foo(a, /regex/)');

        bt('/* foo */\n"x"');

        self.options.break_chained_methods = False
        self.options.preserve_newlines = False
        bt('foo\n.bar()\n.baz().cucumber(fat)', 'foo.bar().baz().cucumber(fat)');
        bt('foo\n.bar()\n.baz().cucumber(fat); foo.bar().baz().cucumber(fat)', 'foo.bar().baz().cucumber(fat);\nfoo.bar().baz().cucumber(fat)');
        bt('foo\n.bar()\n.baz().cucumber(fat)\n foo.bar().baz().cucumber(fat)', 'foo.bar().baz().cucumber(fat)\nfoo.bar().baz().cucumber(fat)');
        bt('this\n.something = foo.bar()\n.baz().cucumber(fat)', 'this.something = foo.bar().baz().cucumber(fat)');
        bt('this.something.xxx = foo.moo.bar()');
        bt('this\n.something\n.xxx = foo.moo\n.bar()', 'this.something.xxx = foo.moo.bar()');

        self.options.break_chained_methods = False
        self.options.preserve_newlines = True
        bt('foo\n.bar()\n.baz().cucumber(fat)', 'foo\n    .bar()\n    .baz().cucumber(fat)');
        bt('foo\n.bar()\n.baz().cucumber(fat); foo.bar().baz().cucumber(fat)', 'foo\n    .bar()\n    .baz().cucumber(fat);\nfoo.bar().baz().cucumber(fat)');
        bt('foo\n.bar()\n.baz().cucumber(fat)\n foo.bar().baz().cucumber(fat)', 'foo\n    .bar()\n    .baz().cucumber(fat)\nfoo.bar().baz().cucumber(fat)');
        bt('this\n.something = foo.bar()\n.baz().cucumber(fat)', 'this\n    .something = foo.bar()\n    .baz().cucumber(fat)');
        bt('this.something.xxx = foo.moo.bar()');
        bt('this\n.something\n.xxx = foo.moo\n.bar()', 'this\n    .something\n    .xxx = foo.moo\n    .bar()');

        self.options.break_chained_methods = True
        self.options.preserve_newlines = False
        bt('foo\n.bar()\n.baz().cucumber(fat)', 'foo.bar()\n    .baz()\n    .cucumber(fat)');
        bt('foo\n.bar()\n.baz().cucumber(fat); foo.bar().baz().cucumber(fat)', 'foo.bar()\n    .baz()\n    .cucumber(fat);\nfoo.bar()\n    .baz()\n    .cucumber(fat)');
        bt('foo\n.bar()\n.baz().cucumber(fat)\n foo.bar().baz().cucumber(fat)', 'foo.bar()\n    .baz()\n    .cucumber(fat)\nfoo.bar()\n    .baz()\n    .cucumber(fat)');
        bt('this\n.something = foo.bar()\n.baz().cucumber(fat)', 'this.something = foo.bar()\n    .baz()\n    .cucumber(fat)');
        bt('this.something.xxx = foo.moo.bar()');
        bt('this\n.something\n.xxx = foo.moo\n.bar()', 'this.something.xxx = foo.moo.bar()');

        self.options.break_chained_methods = True
        self.options.preserve_newlines = True
        bt('foo\n.bar()\n.baz().cucumber(fat)', 'foo\n    .bar()\n    .baz()\n    .cucumber(fat)');
        bt('foo\n.bar()\n.baz().cucumber(fat); foo.bar().baz().cucumber(fat)', 'foo\n    .bar()\n    .baz()\n    .cucumber(fat);\nfoo.bar()\n    .baz()\n    .cucumber(fat)');
        bt('foo\n.bar()\n.baz().cucumber(fat)\n foo.bar().baz().cucumber(fat)', 'foo\n    .bar()\n    .baz()\n    .cucumber(fat)\nfoo.bar()\n    .baz()\n    .cucumber(fat)');
        bt('this\n.something = foo.bar()\n.baz().cucumber(fat)', 'this\n    .something = foo.bar()\n    .baz()\n    .cucumber(fat)');
        bt('this.something.xxx = foo.moo.bar()');
        bt('this\n.something\n.xxx = foo.moo\n.bar()', 'this\n    .something\n    .xxx = foo.moo\n    .bar()');
        self.options.break_chained_methods = False
        self.options.preserve_newlines = False

        self.options.preserve_newlines = False
        self.options.wrap_line_length = 0
        #..............---------1---------2---------3---------4---------5---------6---------7
        #..............1234567890123456789012345678901234567890123456789012345678901234567890
        test_fragment('foo.bar().baz().cucumber((fat && "sassy") || (leans\n&& mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n.but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_\n.okay();',
                      # expected #
                      'foo.bar().baz().cucumber((fat && "sassy") || (leans && mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap.but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_.okay();')

        self.options.wrap_line_length = 70
        #..............---------1---------2---------3---------4---------5---------6---------7
        #..............1234567890123456789012345678901234567890123456789012345678901234567890
        test_fragment('foo.bar().baz().cucumber((fat && "sassy") || (leans\n&& mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n.but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_\n.okay();',
                      # expected #
                      'foo.bar().baz().cucumber((fat && "sassy") || (leans && mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap.but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_.okay();');

        self.options.wrap_line_length = 40
        #..............---------1---------2---------3---------4---------5---------6---------7
        #..............1234567890123456789012345678901234567890123456789012345678901234567890
        test_fragment('foo.bar().baz().cucumber((fat && "sassy") || (leans\n&& mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n.but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_\n.okay();',
                      # expected #
                      'foo.bar().baz().cucumber((fat &&\n' +
                      '    "sassy") || (leans && mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n' +
                      '    .but_this_can\n' +
                      'if (wraps_can_occur &&\n' +
                      '    inside_an_if_block) that_is_.okay();');

        self.options.wrap_line_length = 41
        # NOTE: wrap is only best effort - line continues until next wrap point is found.
        #..............---------1---------2---------3---------4---------5---------6---------7
        #..............1234567890123456789012345678901234567890123456789012345678901234567890
        test_fragment('foo.bar().baz().cucumber((fat && "sassy") || (leans\n&& mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n.but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_\n.okay();',
                      # expected #
                      'foo.bar().baz().cucumber((fat && "sassy") ||\n' +
                      '    (leans && mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n' +
                      '    .but_this_can\n' +
                      'if (wraps_can_occur &&\n' +
                      '    inside_an_if_block) that_is_.okay();');

        self.options.wrap_line_length = 45
        # NOTE: wrap is only best effort - line continues until next wrap point is found.
        #..............---------1---------2---------3---------4---------5---------6---------7
        #..............1234567890123456789012345678901234567890123456789012345678901234567890
        test_fragment('{\n' +
                      '    foo.bar().baz().cucumber((fat && "sassy") || (leans\n&& mean));\n' +
                      '    Test_very_long_variable_name_this_should_never_wrap\n.but_this_can\n' +
                      '    if (wraps_can_occur && inside_an_if_block) that_is_\n.okay();\n' +
                      '}',
                      # expected #
                      '{\n' +
                      '    foo.bar().baz().cucumber((fat && "sassy") ||\n' +
                      '        (leans && mean));\n' +
                      '    Test_very_long_variable_name_this_should_never_wrap\n' +
                      '        .but_this_can\n' +
                      '    if (wraps_can_occur &&\n' +
                      '        inside_an_if_block) that_is_.okay();\n' +
                      '}');

        self.options.preserve_newlines = True
        self.options.wrap_line_length = 0
        #..............---------1---------2---------3---------4---------5---------6---------7
        #..............1234567890123456789012345678901234567890123456789012345678901234567890
        test_fragment('foo.bar().baz().cucumber((fat && "sassy") || (leans\n&& mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n.but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_\n.okay();',
                      # expected #
                      'foo.bar().baz().cucumber((fat && "sassy") || (leans && mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n' +
                      '    .but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_\n' +
                      '    .okay();');

        self.options.wrap_line_length = 70
        #..............---------1---------2---------3---------4---------5---------6---------7
        #..............1234567890123456789012345678901234567890123456789012345678901234567890
        test_fragment('foo.bar().baz().cucumber((fat && "sassy") || (leans\n&& mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n.but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_\n.okay();',
                      # expected #
                      'foo.bar().baz().cucumber((fat && "sassy") || (leans && mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n' +
                      '    .but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_\n' +
                      '    .okay();');


        self.options.wrap_line_length = 40
        #..............---------1---------2---------3---------4---------5---------6---------7
        #..............1234567890123456789012345678901234567890123456789012345678901234567890
        test_fragment('foo.bar().baz().cucumber((fat && "sassy") || (leans\n&& mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n.but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_\n.okay();',
                      # expected #
                      'foo.bar().baz().cucumber((fat &&\n' +
                      '    "sassy") || (leans && mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n' +
                      '    .but_this_can\n' +
                      'if (wraps_can_occur &&\n' +
                      '    inside_an_if_block) that_is_\n' +
                      '    .okay();');

        self.options.wrap_line_length = 41
        # NOTE: wrap is only best effort - line continues until next wrap point is found.
        #..............---------1---------2---------3---------4---------5---------6---------7
        #..............1234567890123456789012345678901234567890123456789012345678901234567890
        test_fragment('foo.bar().baz().cucumber((fat && "sassy") || (leans\n&& mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n.but_this_can\n' +
                      'if (wraps_can_occur && inside_an_if_block) that_is_\n.okay();',
                      # expected #
                      'foo.bar().baz().cucumber((fat && "sassy") ||\n' +
                      '    (leans && mean));\n' +
                      'Test_very_long_variable_name_this_should_never_wrap\n' +
                      '    .but_this_can\n' +
                      'if (wraps_can_occur &&\n' +
                      '    inside_an_if_block) that_is_\n' +
                      '    .okay();');

        self.options.wrap_line_length = 45
        # NOTE: wrap is only best effort - line continues until next wrap point is found.
        #..............---------1---------2---------3---------4---------5---------6---------7
        #..............1234567890123456789012345678901234567890123456789012345678901234567890
        test_fragment('{\n' +
                      '    foo.bar().baz().cucumber((fat && "sassy") || (leans\n&& mean));\n' +
                      '    Test_very_long_variable_name_this_should_never_wrap\n.but_this_can\n' +
                      '    if (wraps_can_occur && inside_an_if_block) that_is_\n.okay();\n' +
                      '}',
                      # expected #
                      '{\n' +
                      '    foo.bar().baz().cucumber((fat && "sassy") ||\n' +
                      '        (leans && mean));\n' +
                      '    Test_very_long_variable_name_this_should_never_wrap\n' +
                      '        .but_this_can\n' +
                      '    if (wraps_can_occur &&\n' +
                      '        inside_an_if_block) that_is_\n' +
                      '        .okay();\n' +
                      '}');

        self.options.wrap_line_length = 0

        self.options.preserve_newlines = False
        bt('if (foo) // comment\n    bar();');
        bt('if (foo) // comment\n    (bar());');
        bt('if (foo) // comment\n    (bar());');
        bt('if (foo) // comment\n    /asdf/;');
        bt('this.oa = new OAuth(\n' +
           '    _requestToken,\n' +
           '    _accessToken,\n' +
           '    consumer_key\n' +
           ');',
           'this.oa = new OAuth(_requestToken, _accessToken, consumer_key);');
        bt('foo = {\n    x: y, // #44\n    w: z // #44\n}');
        bt('switch (x) {\n    case "a":\n        // comment on newline\n        break;\n    case "b": // comment on same line\n        break;\n}');

        # these aren't ready yet.
        #bt('if (foo) // comment\n    bar() /*i*/ + baz() /*j\n*/ + asdf();');
        bt('if\n(foo)\nif\n(bar)\nif\n(baz)\nwhee();\na();',
            'if (foo)\n    if (bar)\n        if (baz) whee();\na();');
        bt('if\n(foo)\nif\n(bar)\nif\n(baz)\nwhee();\nelse\na();',
            'if (foo)\n    if (bar)\n        if (baz) whee();\n        else a();');
        bt('if (foo)\nbar();\nelse\ncar();',
            'if (foo) bar();\nelse car();');

        bt('if (foo) if (bar) if (baz);\na();',
            'if (foo)\n    if (bar)\n        if (baz);\na();');
        bt('if (foo) if (bar) if (baz) whee();\na();',
            'if (foo)\n    if (bar)\n        if (baz) whee();\na();');
        bt('if (foo) a()\nif (bar) if (baz) whee();\na();',
            'if (foo) a()\nif (bar)\n    if (baz) whee();\na();');
        bt('if (foo);\nif (bar) if (baz) whee();\na();',
            'if (foo);\nif (bar)\n    if (baz) whee();\na();');
        bt('if (options)\n' +
           '    for (var p in options)\n' +
           '        this[p] = options[p];',
           'if (options)\n'+
           '    for (var p in options) this[p] = options[p];');
        bt('if (options) for (var p in options) this[p] = options[p];',
           'if (options)\n    for (var p in options) this[p] = options[p];');

        bt('if (options) do q(); while (b());',
           'if (options)\n    do q(); while (b());');
        bt('if (options) while (b()) q();',
           'if (options)\n    while (b()) q();');
        bt('if (options) do while (b()) q(); while (a());',
           'if (options)\n    do\n        while (b()) q(); while (a());');

        bt('function f(a, b, c,\nd, e) {}',
            'function f(a, b, c, d, e) {}');

        bt('function f(a,b) {if(a) b()}function g(a,b) {if(!a) b()}',
            'function f(a, b) {\n    if (a) b()\n}\n\nfunction g(a, b) {\n    if (!a) b()\n}');
        bt('function f(a,b) {if(a) b()}\n\n\n\nfunction g(a,b) {if(!a) b()}',
            'function f(a, b) {\n    if (a) b()\n}\n\nfunction g(a, b) {\n    if (!a) b()\n}');
        # This is not valid syntax, but still want to behave reasonably and not side-effect
        bt('(if(a) b())(if(a) b())',
            '(\n    if (a) b())(\n    if (a) b())');
        bt('(if(a) b())\n\n\n(if(a) b())',
            '(\n    if (a) b())\n(\n    if (a) b())');

        bt("if\n(a)\nb();", "if (a) b();");
        bt('var a =\nfoo', 'var a = foo');
        bt('var a = {\n"a":1,\n"b":2}', "var a = {\n    \"a\": 1,\n    \"b\": 2\n}");
        bt("var a = {\n'a':1,\n'b':2}", "var a = {\n    'a': 1,\n    'b': 2\n}");
        bt('var a = /*i*/ "b";');
        bt('var a = /*i*/\n"b";', 'var a = /*i*/ "b";');
        bt('var a = /*i*/\nb;', 'var a = /*i*/ b;');
        bt('{\n\n\n"x"\n}', '{\n    "x"\n}');
        bt('if(a &&\nb\n||\nc\n||d\n&&\ne) e = f', 'if (a && b || c || d && e) e = f');
        bt('if(a &&\n(b\n||\nc\n||d)\n&&\ne) e = f', 'if (a && (b || c || d) && e) e = f');
        test_fragment('\n\n"x"', '"x"');
        bt('a = 1;\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nb = 2;',
            'a = 1;\nb = 2;');


        self.options.preserve_newlines = True
        bt('if (foo) // comment\n    bar();');
        bt('if (foo) // comment\n    (bar());');
        bt('if (foo) // comment\n    (bar());');
        bt('if (foo) // comment\n    /asdf/;');
        bt('this.oa = new OAuth(\n' +
           '    _requestToken,\n' +
           '    _accessToken,\n' +
           '    consumer_key\n' +
           ');');
        bt('foo = {\n    x: y, // #44\n    w: z // #44\n}');
        bt('switch (x) {\n    case "a":\n        // comment on newline\n        break;\n    case "b": // comment on same line\n        break;\n}');

        # these aren't ready yet.
        # bt('if (foo) // comment\n    bar() /*i*/ + baz() /*j\n*/ + asdf();');
        bt('if\n(foo)\nif\n(bar)\nif\n(baz)\nwhee();\na();',
            'if (foo)\n    if (bar)\n        if (baz)\n            whee();\na();');
        bt('if\n(foo)\nif\n(bar)\nif\n(baz)\nwhee();\nelse\na();',
            'if (foo)\n    if (bar)\n        if (baz)\n            whee();\n        else\n            a();');
        bt('if (foo) bar();\nelse\ncar();',
            'if (foo) bar();\nelse\n    car();');

        bt('if (foo) if (bar) if (baz);\na();',
            'if (foo)\n    if (bar)\n        if (baz);\na();');
        bt('if (foo) if (bar) if (baz) whee();\na();',
            'if (foo)\n    if (bar)\n        if (baz) whee();\na();');
        bt('if (foo) a()\nif (bar) if (baz) whee();\na();',
            'if (foo) a()\nif (bar)\n    if (baz) whee();\na();');
        bt('if (foo);\nif (bar) if (baz) whee();\na();',
            'if (foo);\nif (bar)\n    if (baz) whee();\na();');
        bt('if (options)\n' +
           '    for (var p in options)\n' +
           '        this[p] = options[p];');
        bt('if (options) for (var p in options) this[p] = options[p];',
           'if (options)\n    for (var p in options) this[p] = options[p];');

        bt('if (options) do q(); while (b());',
           'if (options)\n    do q(); while (b());');
        bt('if (options) do; while (b());',
           'if (options)\n    do; while (b());');
        bt('if (options) while (b()) q();',
           'if (options)\n    while (b()) q();');
        bt('if (options) do while (b()) q(); while (a());',
           'if (options)\n    do\n        while (b()) q(); while (a());');

        bt('function f(a, b, c,\nd, e) {}',
            'function f(a, b, c,\n    d, e) {}');

        bt('function f(a,b) {if(a) b()}function g(a,b) {if(!a) b()}',
            'function f(a, b) {\n    if (a) b()\n}\n\nfunction g(a, b) {\n    if (!a) b()\n}');
        bt('function f(a,b) {if(a) b()}\n\n\n\nfunction g(a,b) {if(!a) b()}',
            'function f(a, b) {\n    if (a) b()\n}\n\n\n\nfunction g(a, b) {\n    if (!a) b()\n}');
        # This is not valid syntax, but still want to behave reasonably and not side-effect
        bt('(if(a) b())(if(a) b())',
            '(\n    if (a) b())(\n    if (a) b())');
        bt('(if(a) b())\n\n\n(if(a) b())',
            '(\n    if (a) b())\n\n\n(\n    if (a) b())');


        bt("if\n(a)\nb();", "if (a)\n    b();");
        bt('var a =\nfoo', 'var a =\n    foo');
        bt('var a = {\n"a":1,\n"b":2}', "var a = {\n    \"a\": 1,\n    \"b\": 2\n}");
        bt("var a = {\n'a':1,\n'b':2}", "var a = {\n    'a': 1,\n    'b': 2\n}");
        bt('var a = /*i*/ "b";');
        bt('var a = /*i*/\n"b";', 'var a = /*i*/\n    "b";');
        bt('var a = /*i*/\nb;', 'var a = /*i*/\n    b;');
        bt('{\n\n\n"x"\n}', '{\n\n\n    "x"\n}');
        bt('if(a &&\nb\n||\nc\n||d\n&&\ne) e = f', 'if (a &&\n    b ||\n    c || d &&\n    e) e = f');
        bt('if(a &&\n(b\n||\nc\n||d)\n&&\ne) e = f', 'if (a &&\n    (b ||\n        c || d) &&\n    e) e = f');
        test_fragment('\n\n"x"', '"x"');
        # this beavior differs between js and python, defaults to unlimited in js, 10 in python
        bt('a = 1;\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nb = 2;',
            'a = 1;\n\n\n\n\n\n\n\n\n\nb = 2;');
        self.options.max_preserve_newlines = 8;
        bt('a = 1;\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nb = 2;',
            'a = 1;\n\n\n\n\n\n\n\nb = 2;');

        # Test the option to have spaces within parens
        self.options.space_in_paren = False
        bt('if(p) foo(a,b)', 'if (p) foo(a, b)');
        bt('try{while(true){willThrow()}}catch(result)switch(result){case 1:++result }',
           'try {\n    while (true) {\n        willThrow()\n    }\n} catch (result) switch (result) {\n    case 1:\n        ++result\n}');
        bt('((e/((a+(b)*c)-d))^2)*5;', '((e / ((a + (b) * c) - d)) ^ 2) * 5;');
        bt('function f(a,b) {if(a) b()}function g(a,b) {if(!a) b()}',
            'function f(a, b) {\n    if (a) b()\n}\n\nfunction g(a, b) {\n    if (!a) b()\n}');
        bt('a=[];',
            'a = [];');
        bt('a=[b,c,d];',
            'a = [b, c, d];');
        bt('a= f[b];',
            'a = f[b];');
        self.options.space_in_paren = True
        bt('if(p) foo(a,b)', 'if ( p ) foo( a, b )');
        bt('try{while(true){willThrow()}}catch(result)switch(result){case 1:++result }',
           'try {\n    while ( true ) {\n        willThrow( )\n    }\n} catch ( result ) switch ( result ) {\n    case 1:\n        ++result\n}');
        bt('((e/((a+(b)*c)-d))^2)*5;', '( ( e / ( ( a + ( b ) * c ) - d ) ) ^ 2 ) * 5;');
        bt('function f(a,b) {if(a) b()}function g(a,b) {if(!a) b()}',
            'function f( a, b ) {\n    if ( a ) b( )\n}\n\nfunction g( a, b ) {\n    if ( !a ) b( )\n}');
        bt('a=[ ];',
            'a = [ ];');
        bt('a=[b,c,d];',
            'a = [ b, c, d ];');
        bt('a= f[b];',
            'a = f[ b ];');
        self.options.space_in_paren = False


        # Test that e4x literals passed through when e4x-option is enabled
        bt('xml=<a b="c"><d/><e>\n foo</e>x</a>;', 'xml = < a b = "c" > < d / > < e >\n    foo < /e>x</a > ;');
        self.options.e4x = True
        bt('xml=<a b="c"><d/><e>\n foo</e>x</a>;', 'xml = <a b="c"><d/><e>\n foo</e>x</a>;');
        bt('<a b=\'This is a quoted "c".\'/>', '<a b=\'This is a quoted "c".\'/>');
        bt('<a b="This is a quoted \'c\'."/>', '<a b="This is a quoted \'c\'."/>');
        bt('<a b="A quote \' inside string."/>', '<a b="A quote \' inside string."/>');
        bt('<a b=\'A quote " inside string.\'/>', '<a b=\'A quote " inside string.\'/>');
        bt('<a b=\'Some """ quotes ""  inside string.\'/>', '<a b=\'Some """ quotes ""  inside string.\'/>');
        # Handles inline expressions
        bt('xml=<{a} b="c"><d/><e v={z}>\n foo</e>x</{a}>;', 'xml = <{a} b="c"><d/><e v={z}>\n foo</e>x</{a}>;');
        # xml literals with special characters in elem names
        bt('xml = <_:.valid.xml- _:.valid.xml-="123"/>;', 'xml = <_:.valid.xml- _:.valid.xml-="123"/>;');
        # Handles CDATA
        bt('xml=<a b="c"><![CDATA[d/>\n</a></{}]]></a>;', 'xml = <a b="c"><![CDATA[d/>\n</a></{}]]></a>;');
        bt('xml=<![CDATA[]]>;', 'xml = <![CDATA[]]>;');
        bt('xml=<![CDATA[ b="c"><d/><e v={z}>\n foo</e>x/]]>;', 'xml = <![CDATA[ b="c"><d/><e v={z}>\n foo</e>x/]]>;');
        # Handles messed up tags, as long as it isn't the same name
        # as the root tag. Also handles tags of same name as root tag
        # as long as nesting matches.
        bt('xml=<a x="jn"><c></b></f><a><d jnj="jnn"><f></a ></nj></a>;',
         'xml = <a x="jn"><c></b></f><a><d jnj="jnn"><f></a ></nj></a>;');
        # If xml is not terminated, the remainder of the file is treated
        # as part of the xml-literal (passed through unaltered)
        test_fragment('xml=<a></b>\nc<b;', 'xml = <a></b>\nc<b;');
        self.options.e4x = False

        # START tests for issue 241
        bt('obj\n' +
           '    .last({\n' +
           '        foo: 1,\n' +
           '        bar: 2\n' +
           '    });\n' +
           'var test = 1;');

        bt('obj\n' +
           '    .last(a, function() {\n' +
           '        var test;\n' +
           '    });\n' +
           'var test = 1;');

        bt('obj.first()\n' +
           '    .second()\n' +
           '    .last(function(err, response) {\n' +
           '        console.log(err);\n' +
           '    });');

        # END tests for issue 241


        # START tests for issue 268 and 275
        bt('obj.last(a, function() {\n' +
           '    var test;\n' +
           '});\n' +
           'var test = 1;');

        bt('obj.last(a,\n' +
           '    function() {\n' +
           '        var test;\n' +
           '    });\n' +
           'var test = 1;');

        bt('(function() {if (!window.FOO) window.FOO || (window.FOO = function() {var b = {bar: "zort"};});})();',
           '(function() {\n' +
           '    if (!window.FOO) window.FOO || (window.FOO = function() {\n' +
           '        var b = {\n' +
           '            bar: "zort"\n' +
           '        };\n' +
           '    });\n' +
           '})();');
        # END tests for issue 268 and 275

        # START tests for issue 281
        bt('define(["dojo/_base/declare", "my/Employee", "dijit/form/Button",\n' +
           '    "dojo/_base/lang", "dojo/Deferred"\n' +
           '], function(declare, Employee, Button, lang, Deferred) {\n' +
           '    return declare(Employee, {\n' +
           '        constructor: function() {\n' +
           '            new Button({\n' +
           '                onClick: lang.hitch(this, function() {\n' +
           '                    new Deferred().then(lang.hitch(this, function() {\n' +
           '                        this.salary * 0.25;\n' +
           '                    }));\n' +
           '                })\n' +
           '            });\n' +
           '        }\n' +
           '    });\n' +
           '});');
        bt('define(["dojo/_base/declare", "my/Employee", "dijit/form/Button",\n' +
           '        "dojo/_base/lang", "dojo/Deferred"\n' +
           '    ],\n' +
           '    function(declare, Employee, Button, lang, Deferred) {\n' +
           '        return declare(Employee, {\n' +
           '            constructor: function() {\n' +
           '                new Button({\n' +
           '                    onClick: lang.hitch(this, function() {\n' +
           '                        new Deferred().then(lang.hitch(this, function() {\n' +
           '                            this.salary * 0.25;\n' +
           '                        }));\n' +
           '                    })\n' +
           '                });\n' +
           '            }\n' +
           '        });\n' +
           '    });');
        # END tests for issue 281

        # This is what I think these should look like related #256
        # we don't have the ability yet
        #bt('var a=1,b={bang:2},c=3;',
        #   'var a = 1,\n    b = {\n        bang: 2\n    },\n     c = 3;');
        #bt('var a={bing:1},b=2,c=3;',
        #   'var a = {\n        bing: 1\n    },\n    b = 2,\n    c = 3;');



    def decodesto(self, input, expectation=None):
        self.assertEqual(
            jsbeautifier.beautify(input, self.options), expectation or input)

        # if the expected is different from input, run it again
        # expected output should be unchanged when run twice.
        if not expectation == None:
            self.assertEqual(
                jsbeautifier.beautify(expectation, self.options), expectation)

    def wrap(self, text):
        return self.wrapregex.sub('    \\1', text)

    def bt(self, input, expectation=None):
        expectation = expectation or input
        self.decodesto(input, expectation)
        if self.options.indent_size == 4 and input:
            wrapped_input = '{\n%s\nfoo=bar;}' % self.wrap(input)
            wrapped_expect = '{\n%s\n    foo = bar;\n}' % self.wrap(expectation)
            self.decodesto(wrapped_input, wrapped_expect)

    @classmethod
    def setUpClass(cls):
        options = jsbeautifier.default_options()
        options.indent_size = 4
        options.indent_char = ' '
        options.preserve_newlines = True
        options.jslint_happy = False
        options.keep_array_indentation = False
        options.brace_style = 'collapse'
        options.indent_level = 0
        options.break_chained_methods = False

        cls.options = options
        cls.wrapregex = re.compile('^(.+)$', re.MULTILINE)


if __name__ == '__main__':
    unittest.main()

########NEW FILE########
__FILENAME__ = evalbased
#
# Unpacker for eval() based packers, a part of javascript beautifier
# by Einar Lielmanis <einar@jsbeautifier.org>
#
#     written by Stefano Sanfilippo <a.little.coder@gmail.com>
#
# usage:
#
# if detect(some_string):
#     unpacked = unpack(some_string)
#

"""Unpacker for eval() based packers: runs JS code and returns result.
Works only if a JS interpreter (e.g. Mozilla's Rhino) is installed and
properly set up on host."""

from subprocess import PIPE, Popen

PRIORITY = 3

def detect(source):
    """Detects if source is likely to be eval() packed."""
    return source.strip().lower().startswith('eval(function(')

def unpack(source):
    """Runs source and return resulting code."""
    return jseval('print %s;' % source[4:]) if detect(source) else source

# In case of failure, we'll just return the original, without crashing on user.
def jseval(script):
    """Run code in the JS interpreter and return output."""
    try:
        interpreter = Popen(['js'], stdin=PIPE, stdout=PIPE)
    except OSError:
        return script
    result, errors = interpreter.communicate(script)
    if interpreter.poll() or errors:
        return script
    return result

########NEW FILE########
__FILENAME__ = javascriptobfuscator
#
# simple unpacker/deobfuscator for scripts messed up with
# javascriptobfuscator.com
#
#     written by Einar Lielmanis <einar@jsbeautifier.org>
#     rewritten in Python by Stefano Sanfilippo <a.little.coder@gmail.com>
#
# Will always return valid javascript: if `detect()` is false, `code` is
# returned, unmodified.
#
# usage:
#
# if javascriptobfuscator.detect(some_string):
#     some_string = javascriptobfuscator.unpack(some_string)
#

"""deobfuscator for scripts messed up with JavascriptObfuscator.com"""

import re

PRIORITY = 1

def smartsplit(code):
    """Split `code` at " symbol, only if it is not escaped."""
    strings = []
    pos = 0
    while pos < len(code):
        if code[pos] == '"':
            word = '' # new word
            pos += 1
            while pos < len(code):
                if code[pos] == '"':
                    break
                if code[pos] == '\\':
                    word += '\\'
                    pos += 1
                word += code[pos]
                pos += 1
            strings.append('"%s"' % word)
        pos += 1
    return strings

def detect(code):
    """Detects if `code` is JavascriptObfuscator.com packed."""
    # prefer `is not` idiom, so that a true boolean is returned
    return (re.search(r'^var _0x[a-f0-9]+ ?\= ?\[', code) is not None)

def unpack(code):
    """Unpacks JavascriptObfuscator.com packed code."""
    if detect(code):
        matches = re.search(r'var (_0x[a-f\d]+) ?\= ?\[(.*?)\];', code)
        if matches:
            variable = matches.group(1)
            dictionary = smartsplit(matches.group(2))
            code = code[len(matches.group(0)):]
            for key, value in enumerate(dictionary):
                code = code.replace(r'%s[%s]' % (variable, key), value)
    return code

########NEW FILE########
__FILENAME__ = myobfuscate
#
# deobfuscator for scripts messed up with myobfuscate.com
# by Einar Lielmanis <einar@jsbeautifier.org>
#
#     written by Stefano Sanfilippo <a.little.coder@gmail.com>
#
# usage:
#
# if detect(some_string):
#     unpacked = unpack(some_string)
#

# CAVEAT by Einar Lielmanis

#
# You really don't want to obfuscate your scripts there: they're tracking
# your unpackings, your script gets turned into something like this,
# as of 2011-08-26:
#
#   var _escape = 'your_script_escaped';
#   var _111 = document.createElement('script');
#   _111.src = 'http://api.www.myobfuscate.com/?getsrc=ok' +
#              '&ref=' + encodeURIComponent(document.referrer) +
#              '&url=' + encodeURIComponent(document.URL);
#   var 000 = document.getElementsByTagName('head')[0];
#   000.appendChild(_111);
#   document.write(unescape(_escape));
#

"""Deobfuscator for scripts messed up with MyObfuscate.com"""

import re
import base64

# Python 2 retrocompatibility
# pylint: disable=F0401
# pylint: disable=E0611
try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote

from jsbeautifier.unpackers import UnpackingError

PRIORITY = 1

CAVEAT = """//
// Unpacker warning: be careful when using myobfuscate.com for your projects:
// scripts obfuscated by the free online version call back home.
//

"""

SIGNATURE = (r'["\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4A\x4B\x4C\x4D\x4E\x4F'
             r'\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5A\x61\x62\x63\x64\x65'
             r'\x66\x67\x68\x69\x6A\x6B\x6C\x6D\x6E\x6F\x70\x71\x72\x73\x74\x75'
             r'\x76\x77\x78\x79\x7A\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x2B'
             r'\x2F\x3D","","\x63\x68\x61\x72\x41\x74","\x69\x6E\x64\x65\x78'
             r'\x4F\x66","\x66\x72\x6F\x6D\x43\x68\x61\x72\x43\x6F\x64\x65","'
             r'\x6C\x65\x6E\x67\x74\x68"]')

def detect(source):
    """Detects MyObfuscate.com packer."""
    return SIGNATURE in source

def unpack(source):
    """Unpacks js code packed with MyObfuscate.com"""
    if not detect(source):
        return source
    payload = unquote(_filter(source))
    match = re.search(r"^var _escape\='<script>(.*)<\/script>'",
                      payload, re.DOTALL)
    polished = match.group(1) if match else source
    return CAVEAT + polished

def _filter(source):
    """Extracts and decode payload (original file) from `source`"""
    try:
        varname = re.search(r'eval\(\w+\(\w+\((\w+)\)\)\);', source).group(1)
        reverse = re.search(r"var +%s *\= *'(.*)';" % varname, source).group(1)
    except AttributeError:
        raise UnpackingError('Malformed MyObfuscate data.')
    try:
        return base64.b64decode(reverse[::-1].encode('utf8')).decode('utf8')
    except TypeError:
        raise UnpackingError('MyObfuscate payload is not base64-encoded.')

########NEW FILE########
__FILENAME__ = packer
#
# Unpacker for Dean Edward's p.a.c.k.e.r, a part of javascript beautifier
# by Einar Lielmanis <einar@jsbeautifier.org>
#
#     written by Stefano Sanfilippo <a.little.coder@gmail.com>
#
# usage:
#
# if detect(some_string):
#     unpacked = unpack(some_string)
#

"""Unpacker for Dean Edward's p.a.c.k.e.r"""

import re
import string
from jsbeautifier.unpackers import UnpackingError

PRIORITY = 1

def detect(source):
    """Detects whether `source` is P.A.C.K.E.R. coded."""
    return source.replace(' ', '').startswith('eval(function(p,a,c,k,e,r')

def unpack(source):
    """Unpacks P.A.C.K.E.R. packed js code."""
    payload, symtab, radix, count = _filterargs(source)

    if count != len(symtab):
        raise UnpackingError('Malformed p.a.c.k.e.r. symtab.')

    try:
        unbase = Unbaser(radix)
    except TypeError:
        raise UnpackingError('Unknown p.a.c.k.e.r. encoding.')

    def lookup(match):
        """Look up symbols in the synthetic symtab."""
        word  = match.group(0)
        return symtab[unbase(word)] or word

    source = re.sub(r'\b\w+\b', lookup, payload)
    return _replacestrings(source)

def _filterargs(source):
    """Juice from a source file the four args needed by decoder."""
    argsregex = (r"}\('(.*)', *(\d+), *(\d+), *'(.*)'\."
                 r"split\('\|'\), *(\d+), *(.*)\)\)")
    args = re.search(argsregex, source, re.DOTALL).groups()

    try:
        return args[0], args[3].split('|'), int(args[1]), int(args[2])
    except ValueError:
        raise UnpackingError('Corrupted p.a.c.k.e.r. data.')

def _replacestrings(source):
    """Strip string lookup table (list) and replace values in source."""
    match = re.search(r'var *(_\w+)\=\["(.*?)"\];', source, re.DOTALL)

    if match:
        varname, strings = match.groups()
        startpoint = len(match.group(0))
        lookup = strings.split('","')
        variable = '%s[%%d]' % varname
        for index, value in enumerate(lookup):
            source = source.replace(variable % index, '"%s"' % value)
        return source[startpoint:]
    return source


class Unbaser(object):
    """Functor for a given base. Will efficiently convert
    strings to natural numbers."""
    ALPHABET  = {
        62 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
        95 : (' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ'
              '[\]^_`abcdefghijklmnopqrstuvwxyz{|}~')
    }

    def __init__(self, base):
        self.base = base

        # If base can be handled by int() builtin, let it do it for us
        if 2 <= base <= 36:
            self.unbase = lambda string: int(string, base)
        else:
            # Build conversion dictionary cache
            try:
                self.dictionary = dict((cipher, index) for
                    index, cipher in enumerate(self.ALPHABET[base]))
            except KeyError:
                raise TypeError('Unsupported base encoding.')

            self.unbase = self._dictunbaser

    def __call__(self, string):
        return self.unbase(string)

    def _dictunbaser(self, string):
        """Decodes a  value to an integer."""
        ret = 0
        for index, cipher in enumerate(string[::-1]):
            ret += (self.base ** index) * self.dictionary[cipher]
        return ret

########NEW FILE########
__FILENAME__ = testjavascriptobfuscator
#
#     written by Stefano Sanfilippo <a.little.coder@gmail.com>
#

"""Tests for JavaScriptObfuscator unpacker."""

import unittest
from jsbeautifier.unpackers.javascriptobfuscator import (
    unpack, detect, smartsplit)

# pylint: disable=R0904
class TestJavascriptObfuscator(unittest.TestCase):
    """JavascriptObfuscator.com test case."""
    def test_smartsplit(self):
        """Test smartsplit() function."""
        split = smartsplit
        equals = lambda data, result: self.assertEqual(split(data), result)

        equals('', [])
        equals('"a", "b"', ['"a"', '"b"'])
        equals('"aaa","bbbb"', ['"aaa"', '"bbbb"'])
        equals('"a", "b\\\""', ['"a"', '"b\\\""'])

    def test_detect(self):
        """Test detect() function."""
        positive = lambda source: self.assertTrue(detect(source))
        negative = lambda source: self.assertFalse(detect(source))

        negative('')
        negative('abcd')
        negative('var _0xaaaa')
        positive('var _0xaaaa = ["a", "b"]')
        positive('var _0xaaaa=["a", "b"]')
        positive('var _0x1234=["a","b"]')

    def test_unpack(self):
        """Test unpack() function."""
        decodeto = lambda ob, original: self.assertEqual(unpack(ob), original)

        decodeto('var _0x8df3=[];var a=10;', 'var a=10;')
        decodeto('var _0xb2a7=["\x74\x27\x65\x73\x74"];var i;for(i=0;i<10;++i)'
                 '{alert(_0xb2a7[0]);} ;', 'var i;for(i=0;i<10;++i){alert'
                 '("t\'est");} ;')

if __name__ == '__main__':
    unittest.main()

########NEW FILE########
__FILENAME__ = testmyobfuscate
#
#     written by Stefano Sanfilippo <a.little.coder@gmail.com>
#

"""Tests for MyObfuscate unpacker."""

import unittest
import os
from jsbeautifier.unpackers.myobfuscate import detect, unpack
from jsbeautifier.unpackers.tests import __path__ as path

INPUT = os.path.join(path[0], 'test-myobfuscate-input.js')
OUTPUT = os.path.join(path[0], 'test-myobfuscate-output.js')

# pylint: disable=R0904
class TestMyObfuscate(unittest.TestCase):
    # pylint: disable=C0103
    """MyObfuscate obfuscator testcase."""
    @classmethod
    def setUpClass(cls):
        """Load source files (encoded and decoded version) for tests."""
        with open(INPUT, 'r') as data:
            cls.input = data.read()
        with open(OUTPUT, 'r') as data:
            cls.output = data.read()

    def test_detect(self):
        """Test detect() function."""
        detected = lambda source: self.assertTrue(detect(source))

        detected(self.input)

    def test_unpack(self):
        """Test unpack() function."""
        check = lambda inp, out: self.assertEqual(unpack(inp), out)

        check(self.input, self.output)

if __name__ == '__main__':
    unittest.main()

########NEW FILE########
__FILENAME__ = testpacker
#
#     written by Stefano Sanfilippo <a.little.coder@gmail.com>
#

"""Tests for P.A.C.K.E.R. unpacker."""

import unittest
from jsbeautifier.unpackers.packer import detect, unpack

# pylint: disable=R0904
class TestPacker(unittest.TestCase):
    """P.A.C.K.E.R. testcase."""
    def test_detect(self):
        """Test detect() function."""
        positive = lambda source: self.assertTrue(detect(source))
        negative = lambda source: self.assertFalse(detect(source))

        negative('')
        negative('var a = b')
        positive('eval(function(p,a,c,k,e,r')
        positive('eval ( function(p, a, c, k, e, r')

    def test_unpack(self):
        """Test unpack() function."""
        check = lambda inp, out: self.assertEqual(unpack(inp), out)

        check("eval(function(p,a,c,k,e,r){e=String;if(!''.replace(/^/,String)"
              "){while(c--)r[c]=k[c]||c;k=[function(e){return r[e]}];e="
              "function(){return'\\\\w+'};c=1};while(c--)if(k[c])p=p.replace("
              "new RegExp('\\\\b'+e(c)+'\\\\b','g'),k[c]);return p}('0 2=1',"
              "62,3,'var||a'.split('|'),0,{}))", 'var a=1')

if __name__ == '__main__':
    unittest.main()

########NEW FILE########
__FILENAME__ = testurlencode
#
#     written by Stefano Sanfilippo <a.little.coder@gmail.com>
#

"""Tests for urlencoded unpacker."""

import unittest

from jsbeautifier.unpackers.urlencode import detect, unpack

# pylint: disable=R0904
class TestUrlencode(unittest.TestCase):
    """urlencode test case."""
    def test_detect(self):
        """Test detect() function."""
        encoded = lambda source: self.assertTrue(detect(source))
        unencoded = lambda source: self.assertFalse(detect(source))

        unencoded('')
        unencoded('var a = b')
        encoded('var%20a+=+b')
        encoded('var%20a=b')
        encoded('var%20%21%22')

    def test_unpack(self):
        """Test unpack function."""
        equals = lambda source, result: self.assertEqual(unpack(source), result)

        equals('', '')
        equals('abcd', 'abcd')
        equals('var a = b', 'var a = b')
        equals('var%20a=b', 'var a=b')
        equals('var%20a+=+b', 'var a = b')

if __name__ == '__main__':
    unittest.main()

########NEW FILE########
__FILENAME__ = urlencode
#
# Trivial bookmarklet/escaped script detector for the javascript beautifier
#     written by Einar Lielmanis <einar@jsbeautifier.org>
#     rewritten in Python by Stefano Sanfilippo <a.little.coder@gmail.com>
#
# Will always return valid javascript: if `detect()` is false, `code` is
# returned, unmodified.
#
# usage:
#
# some_string = urlencode.unpack(some_string)
#

"""Bookmarklet/escaped script unpacker."""

# Python 2 retrocompatibility
# pylint: disable=F0401
# pylint: disable=E0611
try:
    from urllib import unquote_plus
except ImportError:
    from urllib.parse import unquote_plus

PRIORITY = 0

def detect(code):
    """Detects if a scriptlet is urlencoded."""
    # the fact that script doesn't contain any space, but has %20 instead
    # should be sufficient check for now.
    return ' ' not in code and ('%20' in code or code.count('%') > 3)

def unpack(code):
    """URL decode `code` source string."""
    return unquote_plus(code) if detect(code) else code

########NEW FILE########
__FILENAME__ = __version__
__version__ = '1.4.0'

########NEW FILE########