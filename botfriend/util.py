import sys
major, minor, release = sys.version_info[:3]
def isstr(x):
    """Compatibility method equivalent to isinstance(x, basestring)"""
    if major == 2:
        return isinstance(x, basestring)
    return isinstance(x, bytes) or isinstance(x, str)
