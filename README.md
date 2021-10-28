# PyXB Extended -- Python W3C XML Schema Bindings

What is this fork for?:

Essentially the exact same reasoning as Jon discusses below, but with the intention of having a PyPI-published copy available.

## Installation

`pip install PyXB-X`

## Developer notes

### Python 3.8 testing failures

Currently, `python setup.py test` fails on Python 3.8+. This is a false failure caused by changes to the `toxml` method (https://docs.python.org/3/library/xml.dom.minidom.html#xml.dom.minidom.Node.toxml).

In Python 3.8+ `toxml` preserves the original element order, which the current tests do not assume. Since < 3.8 produces a slightly different, but equally valid output, we can't easily just change the unit tests to match.

This is something I'll work on sorting out soon.


---

Jon Foster (upstream) PyXB README follows:

What is this fork for?:

At work, I use a few closed-source tools that use PyXB - some of which I maintain. This repository has the necessary patches to make PyXB work for me.

I don't have the time, inclination or the knowledge of PyXB's internals to be a proper open-source maintainer for PyXB. This fork is just getting bugfixes as I need them. I will accept small pull requests that fix bugs, but not anything big or risky or hard-to-test. I have no interest in doing formal public releases or submitting this to PyPy.

My experience is that PyXB is very complex and seriously lacking documentation, and does not have a stable API, but it can be made to work with some trial-and-error. The concept is great, and it works, and I'm not aware of anything better (though I haven't looked for a couple of years).

**-- Jon Foster**

Original (upstream) PyXB README follows:

The source releases includes pre-built bundles for common XML namespaces,
assorted web service namespaces, and SAML. A bundle with over 75 namespaces
related to Geographic Information Systems is also available; if you want
those, read pyxb/bundles/opengis/README.txt before installing PyXB.

Installation: python setup.py install

Documentation: doc/html or https://pabigot.github.io/pyxb/

Help Forum: http://sourceforge.net/forum/forum.php?forum_id=956708

Mailing list: https://lists.sourceforge.net/lists/listinfo/pyxb-users
Archive: http://www.mail-archive.com/pyxb-users@lists.sourceforge.net

Bug reports: https://github.com/pabigot/pyxb/issues
