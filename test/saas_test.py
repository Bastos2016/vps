#!/usr/bin/env python

import os
import sys
import _env
import conf
import saas
from saas.ttypes import Cmd
from vps_mgr import VPSMgr
import time
from zthrift.client import get_client
import unittest

class TestSAASClient (unittest.TestCase):

    def test_invalid (self):
        trans, client = get_client (saas.VPS)
        trans.open ()
        print "connected"
        try:
            vps = client.vps (0)
            print VPSMgr.dumpy_vps_info (vps)
            self.assert_ (not VPSMgr.vps_is_valid (vps))
            vps = client.vps (100000000)
            print VPSMgr.dumpy_vps_info (vps)
            self.assert_ (not VPSMgr.vps_is_valid (vps))
        finally:
            trans.close ()

    def test_51 (self):
        trans, client = get_client (saas.VPS)
        print "test vps 51"
        trans.open ()
        try:
            vps = client.vps (51)
            print VPSMgr.dumpy_vps_info (vps)
        finally:
            trans.close ()

if __name__ == '__main__':
   unittest.main () 

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :