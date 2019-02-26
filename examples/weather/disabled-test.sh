#! /bin/sh

sh genbindings.sh \
  && python client_get.py
