__FILENAME__ = test_invalid
from biplist import *
import os
from test_utils import *
import unittest

class TestInvalidPlistFile(unittest.TestCase):
    def setUp(self):
        pass
    def testEmptyFile(self):
        try:
            readPlist(data_path('empty_file.plist'))
            self.fail("Should not successfully read empty plist.")
        except NotBinaryPlistException as e:
            pass
        except InvalidPlistException as e:
            pass
    
    def testTooShort(self):
        try:
            readPlistFromString(six.b("bplist0"))
            self.fail("Should not successfully read plist which is too short.")
        except InvalidPlistException as e:
            pass
    
    def testInvalid(self):
        try:
            readPlistFromString(six.b("bplist0-------------------------------------"))
            self.fail("Should not successfully read invalid plist.")
        except InvalidPlistException as e:
            pass
        
if __name__ == '__main__':
    unittest.main()

########NEW FILE########
__FILENAME__ = test_utils
import os
import subprocess
import sys
import six

def data_path(path):
    return os.path.join(os.path.dirname(globals()["__file__"]), 'data', path)

def run_command(args, verbose = False):
    """Runs the command and returns the status and the output."""
    if verbose:
        sys.stderr.write("Running: %s\n" % command)
    p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    stdin, stdout = (p.stdin, p.stdout)
    output = stdout.read()
    output = output.strip(six.b("\n"))
    status = stdin.close()
    p.wait()
    return p.returncode, output

########NEW FILE########
__FILENAME__ = test_valid
from biplist import *
import datetime
import os
from test_utils import *
import unittest
import six

class TestValidPlistFile(unittest.TestCase):
    def setUp(self):
        pass
    
    def validateSimpleBinaryRoot(self, root):
        self.assertTrue(type(root) == dict, "Root should be dictionary.")
        self.assertTrue(type(root[six.b('dateItem')]) == datetime.datetime, "date should be datetime")
        self.assertEquals(root[six.b('dateItem')], datetime.datetime(2010, 8, 19, 22, 27, 30, 385449), "dates not equal" )
        self.assertEquals(root[six.b('numberItem')], -10000000000000000, "number not of expected value")
        self.assertEquals(root[six.b('unicodeItem')], six.u('abc\u212cdef\u2133'))
        self.assertEquals(root[six.b('stringItem')], six.b('Hi there'))
        self.assertEquals(root[six.b('realItem')], 0.47)
        self.assertEquals(root[six.b('boolItem')], True)
        self.assertEquals(root[six.b('arrayItem')], [six.b('item0')])
        
    def testFileRead(self):
        try:
            result = readPlist(data_path('simple_binary.plist'))
            self.validateSimpleBinaryRoot(result)
        except NotBinaryPlistException as e:
            self.fail("NotBinaryPlistException: %s" % e)
        except InvalidPlistException as e:
            self.fail("InvalidPlistException: %s" % e)
    
    def testUnicodeRoot(self):
        result = readPlist(data_path('unicode_root.plist'))
        self.assertEquals(result, six.u("Mirror's Edge\u2122 for iPad"))
    
    def testEmptyUnicodeRoot(self):
        # Porting note: this test was tricky; it was only passing in
        # Python 2 because the empty byte-string returned by
        # readPlist() is considered equal to the empty unicode-string
        # in the assertion.  Confusingly enough, given the name of the
        # test, the value in unicode_empty.plist has the format byte
        # 0b0101 (ASCII string), so the value being asserted against
        # appears to be what is wrong.
        result = readPlist(data_path('unicode_empty.plist'))
        self.assertEquals(result, six.b(""))
    
    def testSmallReal(self):
        result = readPlist(data_path('small_real.plist'))
        self.assertEquals(result, {six.b('4 byte real'):0.5})
    
    def testKeyedArchiverPlist(self):
        """
        Archive is created with class like this:
        @implementation Archived
        ...
        - (void)encodeWithCoder:(NSCoder *)coder {
            [coder encodeObject:@"object value as string" forKey:@"somekey"];
        }
        @end
        
        Archived *test = [[Archived alloc] init];
        NSData *data = [NSKeyedArchiver archivedDataWithRootObject:test]
        ...
        """
        result = readPlist(data_path('nskeyedarchiver_example.plist'))
        self.assertEquals(result, {six.b('$version'): 100000, 
            six.b('$objects'): 
                [six.b('$null'),
                 {six.b('$class'): Uid(3), six.b('somekey'): Uid(2)}, 
                 six.b('object value as string'),
                 {six.b('$classes'): [six.b('Archived'), six.b('NSObject')], six.b('$classname'): six.b('Archived')}
                 ], 
            six.b('$top'): {six.b('root'): Uid(1)}, six.b('$archiver'): six.b('NSKeyedArchiver')})
        self.assertEquals("Uid(1)", repr(Uid(1)))
    
if __name__ == '__main__':
    unittest.main()

########NEW FILE########
__FILENAME__ = test_write
from biplist import *
from biplist import PlistWriter
import datetime
import os
#from cStringIO import StringIO
import subprocess
import tempfile
from test_utils import *
import unittest
import six

class TestWritePlist(unittest.TestCase):
    def setUp(self):
        pass
    
    def roundTrip(self, root, xml=False, expected=None):
        # 'expected' is more fallout from the
        # don't-write-empty-unicode-strings issue.
        plist = writePlistToString(root, binary=(not xml))
        self.assertTrue(len(plist) > 0)
        readResult = readPlistFromString(plist)
        self.assertEquals(readResult, (expected if expected is not None else root))
        self.lintPlist(plist)
    
    def lintPlist(self, plistString):
        if os.path.exists('/usr/bin/plutil'):
            f = tempfile.NamedTemporaryFile()
            f.write(plistString)
            f.flush()
            name = f.name
            (status, output) = run_command(['/usr/bin/plutil', '-lint', name])
            if status != 0:
                self.fail("plutil verification failed (status %d): %s" % (status, output))
    
    def testXMLPlist(self):
        self.roundTrip({'hello':'world'}, xml=True)

    def testXMLPlistWithData(self):
        for binmode in (True, False):
            binplist = writePlistToString({'data': Data(six.b('\x01\xac\xf0\xff'))}, binary=binmode)
            plist = readPlistFromString(binplist)
            self.assertTrue(isinstance(plist['data'], Data), \
                "unable to encode then decode Data into %s plist" % ("binary" if binmode else "XML"))

    def testConvertToXMLPlistWithData(self):
        binplist = writePlistToString({'data': Data(six.b('\x01\xac\xf0\xff'))})
        plist = readPlistFromString(binplist)
        xmlplist = writePlistToString(plist, binary=False)
        self.assertTrue(len(xmlplist) > 0, "unable to convert plist with Data from binary to XML")
    
    def testBoolRoot(self):
        self.roundTrip(True)
        self.roundTrip(False)
    
    def testDuplicate(self):
        l = ["foo" for i in range(0, 100)]
        self.roundTrip(l)
        
    def testListRoot(self):
        self.roundTrip([1, 2, 3])
    
    def testDictRoot(self):
        self.roundTrip({'a':1, 'B':'d'})
    
    def boolsAndIntegersHelper(self, cases):
        result = readPlistFromString(writePlistToString(cases))
        for i in range(0, len(cases)):
            self.assertTrue(cases[i] == result[i])
            self.assertEquals(type(cases[i]), type(result[i]), "Type mismatch on %d: %s != %s" % (i, repr(cases[i]), repr(result[i])))
    
    def reprChecker(self, case):
        result = readPlistFromString(writePlistToString(case))
        self.assertEquals(repr(case), repr(result))
    
    def testBoolsAndIntegersMixed(self):
        self.boolsAndIntegersHelper([0, 1, True, False, None])
        self.boolsAndIntegersHelper([False, True, 0, 1, None])
        self.reprChecker({'1':[True, False, 1, 0], '0':[1, 2, 0, {'2':[1, 0, False]}]})
        self.reprChecker([1, 1, 1, 1, 1, True, True, True, True])
    
    def testSetRoot(self):
        self.roundTrip(set((1, 2, 3)))
    
    def testDatetime(self):
        now = datetime.datetime.utcnow()
        now = now.replace(microsecond=0)
        self.roundTrip([now])
    
    def testFloat(self):
        self.roundTrip({'aFloat':1.23})
    
    def testTuple(self):
        result = writePlistToString({'aTuple':(1, 2.0, 'a'), 'dupTuple':('a', 'a', 'a', 'b', 'b')})
        self.assertTrue(len(result) > 0)
        readResult = readPlistFromString(result)
        self.assertEquals(readResult['aTuple'], [1, 2.0, 'a'])
        self.assertEquals(readResult['dupTuple'], ['a', 'a', 'a', 'b', 'b'])
    
    def testComplicated(self):
        root = {'preference':[1, 2, {'hi there':['a', 1, 2, {'yarrrr':123}]}]}
        self.lintPlist(writePlistToString(root))
        self.roundTrip(root)
    
    def testString(self):
        self.roundTrip(six.b('0'))
        self.roundTrip(six.b(''))
        self.roundTrip({six.b('a'):six.b('')})
    
    def testLargeDict(self):
        d = {}
        for i in range(0, 1000):
            d['%d' % i] = '%d' % i
        self.roundTrip(d)
        
    def testBools(self):
        self.roundTrip([True, False])
    
    def testUniques(self):
        root = {'hi':'there', 'halloo':'there'}
        self.roundTrip(root)
    
    def testWriteToFile(self):
        for is_binary in [True, False]:
            path = '/var/tmp/test.plist'
            writePlist([1, 2, 3], path, binary=is_binary)
            self.assertTrue(os.path.exists(path))
            self.lintPlist(open(path, 'rb').read())
    
    def testNone(self):
        self.roundTrip(None)
        self.roundTrip({'1':None})
        self.roundTrip([None, None, None])
    
    def testBadKeys(self):
        try:
            self.roundTrip({None:1})
            self.fail("None is not a valid key in Cocoa.")
        except InvalidPlistException as e:
            pass
        try:
            self.roundTrip({Data(six.b("hello world")):1})
            self.fail("Data is not a valid key in Cocoa.")
        except InvalidPlistException as e:
            pass
        try:
            self.roundTrip({1:1})
            self.fail("Number is not a valid key in Cocoa.")
        except InvalidPlistException as e:
            pass
    
    def testIntBoundaries(self):
        edges = [0xff, 0xffff, 0xffffffff]
        for edge in edges:
            cases = [edge, edge-1, edge+1, edge-2, edge+2, edge*2, edge/2]
            self.roundTrip(cases)
        edges = [-pow(2, 7), pow(2, 7) - 1, -pow(2, 15), pow(2, 15) - 1, -pow(2, 31), pow(2, 31) - 1]
        self.roundTrip(edges)
        
        io = six.BytesIO()
        writer = PlistWriter(io)
        bytes = [(1, [pow(2, 7) - 1]),
                 (2, [pow(2, 15) - 1]),
                 (4, [pow(2, 31) - 1]),
                 (8, [-pow(2, 7), -pow(2, 15), -pow(2, 31), -pow(2, 63), pow(2, 63) - 1])
            ]
        for bytelen, tests in bytes:
            for test in tests:
                got = writer.intSize(test)
                self.assertEquals(bytelen, got, "Byte size is wrong. Expected %d, got %d" % (bytelen, got))
        
        bytes_lists = [list(x) for x in bytes]
        self.roundTrip(bytes_lists)
        
        try:
            self.roundTrip([0x8000000000000000, pow(2, 63)])
            self.fail("2^63 should be too large for Core Foundation to handle.")
        except InvalidPlistException as e:
            pass
    
    def testWriteData(self):
        self.roundTrip(Data(six.b("woohoo")))
        
    def testUnicode(self):
        unicodeRoot = six.u("Mirror's Edge\u2122 for iPad")
        writePlist(unicodeRoot, "/tmp/odd.plist")
        self.roundTrip(unicodeRoot)
        unicodeStrings = [six.u("Mirror's Edge\u2122 for iPad"), six.u('Weightbot \u2014 Track your Weight in Style')]
        self.roundTrip(unicodeStrings)
        self.roundTrip({six.u(""):six.u("")}, expected={six.b(''):six.b('')})
        self.roundTrip(six.u(""), expected=six.b(''))
        
    def testUidWrite(self):
        self.roundTrip({'$version': 100000, 
            '$objects': 
                ['$null', 
                 {'$class': Uid(3), 'somekey': Uid(2)}, 
                 'object value as string', 
                 {'$classes': ['Archived', 'NSObject'], '$classname': 'Archived'}
                 ], 
            '$top': {'root': Uid(1)}, '$archiver': 'NSKeyedArchiver'})

if __name__ == '__main__':
    unittest.main()

########NEW FILE########