PyXB -- Python W3C XML Schema Bindings
Version 1.2.7.dev1

------------------------------------------------
What is this fork for?:

At work, I use a few closed-source tools that use PyXB - some of which I maintain.  This repository has the necessary patches to make PyXB work for me.

I don't have the time, inclination or the knowledge of PyXB's internals to be a proper open-source maintainer for PyXB.  This fork is just getting bugfixes as I need them.  I will accept small pull requests that fix bugs, but not anything big or risky or hard-to-test.  I have no interest in doing formal public releases or submitting this to PyPy.

My experience is that PyXB is very complex and seriously lacking documentation, and does not have a stable API, but it can be made to work with some trial-and-error.  The concept is great, and it works, and I'm not aware of anything better (though I haven't looked for a couple of years).

-- Jon Foster
------------------------------------------------
Original (upstream) PyXB README follows:

The source releases includes pre-built bundles for common XML namespaces,
assorted web service namespaces, and SAML.  A bundle with over 75 namespaces
related to Geographic Information Systems is also available; if you want
those, read pyxb/bundles/opengis/README.txt before installing PyXB.

Installation:  python setup.py install

Documentation: doc/html or https://pabigot.github.io/pyxb/

Help Forum: http://sourceforge.net/forum/forum.php?forum_id=956708

Mailing list: https://lists.sourceforge.net/lists/listinfo/pyxb-users
Archive: http://www.mail-archive.com/pyxb-users@lists.sourceforge.net

Bug reports: https://github.com/pabigot/pyxb/issues
