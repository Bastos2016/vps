#!/usr/bin/env python
# coding:utf-8

class AttrWrapper (object):

    def __init__ (self, e):
        self.e = e

    def __nonzero__(self):
        return self.e and True or False

    def __getattr__ (self, name):
        if isinstance (self.e, dict):
            if self.e.has_key (name):
                v = self.e[name]
                return self.__class__.wrap (v)
            else:
                return self.__class__.wrap ({})
        raise KeyError(name)

    def __getitem__ (self, i):
        if isinstance (self.e, (list, tuple)):
            v = self.e[i]
            return self.__class__.wrap (v)
        raise IndexError (i)


    def __str__ (self):
        if self.e == {}:
            return ''
        else:
            return str(self.e)
        

    @classmethod
    def wrap (cls, e):
        if isinstance (e, (basestring, int, float)):
            return e
        else:
            return cls (e)

    def unwrap (self):
        return self.e


if __name__ == '__main__':
    d = {'a': 1, 'b':2}
    e = AttrWrapper (d)
    print "e.name.name:", e.name.name
    print "e.a:", e.a, "e.b:", e.b
    print "e:", e
    l = [1, 2, d]
    e2 = AttrWrapper (l)
    print "e2:", e2
    print "e2[0]:", e2[0]
    #print e2[3] # IndexError
    print "b:", e2[2].b
    e_empty = AttrWrapper ({})
    print "e_empty:", e_empty
    assert not e_empty
    assert not e_empty.a
    #print e2.a   # KeyError
    #print e[0]   # IndexError
    #print e.a.b  # KeyError


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :