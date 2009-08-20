pyxbgen \
  --schema-location=a.xsd --module=A \
  --schema-location=b.xsd --module=B \
&& python tst-1.py \
&& python tst-2.py \
&& ( echo "Trac32 TESTS PASSED" ; exit 0 )
exit 1

