'''
LICENSING
-------------------------------------------------

Smartyparse: A python library for smart dynamic binary de/encoding.
    Copyright (C) 2016 Muterra, Inc.
    
    Contributors
    ------------
    Nick Badger 
        badg@muterra.io | badg@nickbadger.com | nickbadger.com

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the 
    Free Software Foundation, Inc.,
    51 Franklin Street, 
    Fifth Floor, 
    Boston, MA  02110-1301 USA

------------------------------------------------------

'''

# Global dependencies
import struct
import abc
import collections

# ###############################################
# Parsers
# ###############################################


class ParserBase(metaclass=abc.ABCMeta):
    length = None
    
    @abc.abstractmethod
    def unpack(self, data):
        ''' unpacks raw bytes into python objects.
        '''
        pass
        
    @abc.abstractmethod
    def pack(self, obj):
        ''' packs python objects into raw bytes.
        '''
        # Note that the super() implementation here makes it possible for
        # children to support callables when parsing.
        # If a child parser wants to customize handling a callable, don't
        # call super(). Take extra care with callable classes.
        pass
            
            
class _StructParserBase(ParserBase):
    def __init__(self, endian, descriptor):
        if endian == 'big':
            e = '>'
        elif endian == 'little':
            e = '<'
        else:
            raise ValueError('endian must be "big" or "little".')
            
        self._packer = struct.Struct(e + descriptor)
    
    @property
    def length(self):
        return self._packer.size
    
    def unpack(self, data):
        return self._packer.unpack(data)[0]
        
    def pack(self, obj):
        return self._packer.pack(obj)
        

class Blob(ParserBase):
    ''' Class for a binary blob. Creates a bytes object from a 
    memoryview, and a memoryview from bytes.
    '''    
    def __init__(self, length=None):
        self._length = None
        
    @property
    def length(self):
        return self._length
    
    def unpack(self, data):
        if self.length != None and len(data) != self.length:
            raise ValueError('Data length does not match fixed-length blob parser.')
        
        # Efficiently expose the data
        return memoryview(data)
        
    def pack(self, obj):
        if self.length != None and len(obj) != self.length:
            raise ValueError('Data length does not match fixed-length blob parser.')
        
        # Try to freeze the data
        if isinstance(obj, memoryview):
            out = bytes(obj)
        elif isinstance(obj, bytearray):
            out = bytes(obj)
        else:
            out = obj
            
        return out
        

class Padding(ParserBase):
    ''' Class for a padding blob. Unpacks to its length.
    '''    
    def __init__(self, length, padding_byte=b'\x00'):
        self._length = length
        self._padding = bytes(padding_byte * self.length)
        
    @property
    def length(self):
        return self._length
    
    def unpack(self, data):
        if len(data) != self.length:
            raise ValueError('Data length does not match fixed-length padding parser.')
        # Could check the padding is 'valid' if we'd like, but no need yet
        
        # Always return None
        return None
        
    def pack(self, obj):
        # No object validation or anything.
        # Return it as bytes.
        return self._padding
    

class Null(ParserBase):
    ''' Parses nothing. unpack returns None, pack returns b''
    '''
    length = 0
    
    def unpack(self, data):
        return None
        
    def pack(self, obj):
        return b''
        

class Int8(_StructParserBase):
    ''' Create a parser for an 8-bit integer.
    '''
    def __init__(self, signed=True, endian='big'):
        if signed:
            desc = 'b'
        else:
            desc = 'B'
            
        super().__init__(endian, desc)
        

class Int16(_StructParserBase):
    ''' Create a parser for a 16-bit integer.
    '''
    def __init__(self, signed=True, endian='big'):
        if signed:
            desc = 'h'
        else:
            desc = 'H'
            
        super().__init__(endian, desc)
        

class Int32(_StructParserBase):
    ''' Create a parser for a 32-bit integer.
    '''
    def __init__(self, signed=True, endian='big'):
        if signed:
            desc = 'i'
        else:
            desc = 'I'
            
        super().__init__(endian, desc)
        

class Int64(_StructParserBase):
    ''' Create a parser for a 32-bit integer.
    '''
    def __init__(self, signed=True, endian='big'):
        if signed:
            desc = 'q'
        else:
            desc = 'Q'
            
        super().__init__(endian, desc)
        

class Float(_StructParserBase):
    ''' Create a parser for a floating-point decimal (4 bytes). 
    double=True creates a double precision float.
    '''
    def __init__(self, double=True, endian='big'):
        if double:
            desc = 'd'
        else:
            desc = 'f'
            
        super().__init__(endian, desc)
        

class ByteBool(_StructParserBase):
    ''' Create a parser for a byte-oriented boolean.
    '''
    def __init__(self, endian='big'):
        super().__init__(endian, '?')
        

class String(ParserBase):
    ''' Create a parser for a string.
    '''
    def __init__(self, encoding='utf-8'):
        # Test the encoding before applying it
        __ = str.encode('hello', encoding=encoding)
        self.encoding = encoding
    
    def unpack(self, data):
        # Don't forget to recast, in cast of memoryview
        return bytes.decode(bytes(data), encoding=self.encoding)
        
    def pack(self, obj):
        return str.encode(obj, encoding=self.encoding)