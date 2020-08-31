# -*- coding: utf-8 -*-
'''
Functions for manipulating or otherwise processing strings
'''

# Import Python libs
import logging
import unicodedata

log = logging.getLogger(__name__)

def to_unicode(string_to_convert, encoding=None, errors='strict', normalize=False):
    '''
    Given str or unicode, return unicode (str for python 3)
    '''
    if encoding is None:
        # Try utf-8 first, and fall back to detected encoding
        encoding = ('utf-8', __salt_system_encoding__)
    if not isinstance(encoding, (tuple, list)):
        encoding = (encoding,)

    if not encoding:
        raise ValueError('encoding cannot be empty')

    if isinstance(string_to_convert, str):
        return _normalize(string_to_convert, normalize)
    elif isinstance(string_to_convert, (bytes, bytearray)):
        return _normalize(to_str(string_to_convert, encoding, errors), normalize)
    raise TypeError('expected str, bytes, or bytearray')

def to_bytes(string_to_convert, encoding=None, errors='strict'):
    '''
    Given bytes, bytearray, str, or unicode, return bytes
    '''
    if encoding is None:
        # Try utf-8 first, and fall back to detected encoding
        encoding = ('utf-8', __salt_system_encoding__)
    if not isinstance(encoding, (tuple, list)):
        encoding = (encoding,)

    if not encoding:
        raise ValueError('encoding cannot be empty')

    exc = None
    if isinstance(string_to_convert, bytes):
        return string_to_convert
    if isinstance(string_to_convert, bytearray):
        return bytes(string_to_convert)
    if isinstance(string_to_convert, str):
        for enc in encoding:
            try:
                return string_to_convert.encode(enc, errors)
            except UnicodeEncodeError as err:
                exc = err
                continue
        # The only way we get this far is if a UnicodeEncodeError was
        # raised, otherwise we would have already returned (or raised some
        # other exception).
        raise exc  # pylint: disable=raising-bad-type
    raise TypeError('expected bytes, bytearray, or str')

def to_str(string_to_convert, encoding=None, errors='strict', normalize=False):
    '''
    Given str, bytes, bytearray, or unicode (py2), return str
    '''
    if encoding is None:
        # Try utf-8 first, and fall back to detected encoding
        encoding = ('utf-8', __salt_system_encoding__)
    if not isinstance(encoding, (tuple, list)):
        encoding = (encoding,)

    if not encoding:
        raise ValueError('encoding cannot be empty')

    # This shouldn't be six.string_types because if we're on PY2 and we already
    # have a string, we should just return it.
    if isinstance(string_to_convert, str):
        return _normalize(string_to_convert, normalize)

    exc = None
    if isinstance(string_to_convert, (bytes, bytearray)):
        for enc in encoding:
            try:
                return _normalize(string_to_convert.decode(enc, errors), normalize)
            except UnicodeDecodeError as err:
                exc = err
                continue
        # The only way we get this far is if a UnicodeDecodeError was
        # raised, otherwise we would have already returned (or raised some
        # other exception).
        raise exc  # pylint: disable=raising-bad-type
    raise TypeError('expected str, bytes, or bytearray not {}'.format(type(string_to_convert)))

def _normalize(string_to_convert, normalize=False):
    '''
    a utility method for normalizing string
    '''
    try:
        return unicodedata.normalize('NFC', string_to_convert) if normalize else string_to_convert
    except TypeError:
        return string_to_convert

def is_binary(data):
    '''
    Detects if the passed string of data is binary or text
    '''
    if not data or not isinstance(data, (str, bytes)):
        return False

    if isinstance(data, bytes):
        if b'\0' in data:
            return True
    elif str('\0') in data:
        return True

    text_characters = ''.join([chr(x) for x in range(32, 127)] + list('\n\r\t\b'))
    # Get the non-text characters (map each character to itself then use the
    # 'remove' option to get rid of the text characters.)
    if isinstance(data, bytes):
        import hubblestack.utils.data
        nontext = data.translate(None, hubblestack.utils.data.encode(text_characters))
    else:
        trans = ''.maketrans('', '', text_characters)
        nontext = data.translate(trans)

    # If more than 30% non-text characters, then
    # this is considered binary data
    if float(len(nontext)) / len(data) > 0.30:
        return True
    return False

def to_num(text):
    '''
    Convert a string to a number.
    Returns an integer if the string represents an integer, a floating
    point number if the string is a real number, or the string unchanged
    otherwise.
    '''
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text

def get_context(template, line, num_lines=5, marker=None):
    '''
    Returns debugging context around a line in a given string

    Returns:: string
    '''
    template_lines = template.splitlines()
    num_template_lines = len(template_lines)

    # In test mode, a single line template would return a crazy line number like,
    # 357. Do this sanity check and if the given line is obviously wrong, just
    # return the entire template
    if line > num_template_lines:
        return template

    context_start = max(0, line - num_lines - 1)  # subt 1 for 0-based indexing
    context_end = min(num_template_lines, line + num_lines)
    error_line_in_context = line - context_start - 1  # subtr 1 for 0-based idx

    buf = []
    if context_start > 0:
        buf.append('[...]')
        error_line_in_context += 1

    buf.extend(template_lines[context_start:context_end])

    if context_end < num_template_lines:
        buf.append('[...]')

    if marker:
        buf[error_line_in_context] += marker

    return '---\n{0}\n---'.format('\n'.join(buf))
