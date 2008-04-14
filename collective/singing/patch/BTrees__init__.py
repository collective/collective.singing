# So this is a super-ugly hack to try and satisfy the zope.app.catalog
# dependency to a newer version of BTrees.

import BTrees
#import BTrees.Interfaces

class _Family(object):
    #zope.interface.implements(BTrees.Interfaces.IBTreeFamily)

    from BTrees import OOBTree as OO

class _Family32(_Family):
    from BTrees import OIBTree as OI
    from BTrees import IIBTree as II
    from BTrees import IOBTree as IO
    from BTrees import IFBTree as IF

    maxint = int(2**31-1)
    minint = -maxint - 1

    def __reduce__(self):
        return _family32, ()

# class _Family64(_Family):
#     from BTrees import OLBTree as OI
#     from BTrees import LLBTree as II
#     from BTrees import LOBTree as IO
#     from BTrees import LFBTree as IF

#     maxint = 2**63-1
#     minint = -maxint - 1

#     def __reduce__(self):
#         return _family64, ()

def _family32():
    return family32
_family32.__safe_for_unpickling__ = True

# def _family64():
#     return family64
# _family64.__safe_for_unpickling__ = True


BTrees.family32 = family32 = _Family32()
# family64 = _Family64()


# BTrees.family64.IO.family = family64
# BTrees.family64.OI.family = family64
# BTrees.family64.IF.family = family64
# BTrees.family64.II.family = family64

BTrees.family32.IO.family = family32
BTrees.family32.OI.family = family32
BTrees.family32.IF.family = family32
BTrees.family32.II.family = family32
