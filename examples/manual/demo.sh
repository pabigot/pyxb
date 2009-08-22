rm -f *.wxs po?.py *.pyc
sh demo1.sh \
 && python demo1.py > demo1.out \
 && cat demo1.out
sh demo2.sh \
 && python demo2.py
sh demo3a.sh \
 && python demo3.py
sh demo3b.sh \
 && python demo3.py
sh demo3c.sh \
 && sh demo3d.sh \
 && python demo3.py
