#!/usr/bin/env python
# -*- coding: utf-8 -*-

#import _env
#import config
import sys

import re
import os
import subprocess
import getopt
import hashlib
import time
import shutil

import misc
import img_ops


user_script_src = os.path.join (os.path.dirname (__file__), "_create_user.py")
if not os.path.exists (user_script_src):
   raise Exception ("%s not exists" % (user_script_src)) 

def usage ():
    print "usage:\n%s --name [VM_NAME] --img [BASE_IMAGE] --ip [VM_IP/VM_MASK] --gateway [VM_GATEWAY]" % (sys.argv[0])
    print "given a vm image file, will generate a password for root and do hostname/network configuration"
    os._exit (0)


def do_vm_config (vm_root_path, vm_name=None, vm_ip=None, vm_netmask=None, vm_gateway=None, user_dict=None):
    """
        vm_netmask must be intege 
    """
    vm_root_path = os.path.abspath (vm_root_path)
    lo_dev, tmp_mount = img_ops.mount_loop (vm_root_path)
    print "mount %s on %s %s" % (vm_root_path, lo_dev, tmp_mount)
    
    vm_net_config_content = None
    if vm_ip and vm_netmask and vm_gateway:
        assert isinstance (vm_netmask, int)
        vm_net_config_content = """
    config_eth0="%s/%d"
    routes_eth0="default via %s"
        """ % (vm_ip, vm_netmask, vm_gateway)

    try:

        if vm_name:
            print "config hostname"
            f = open (os.path.join (tmp_mount, "etc/conf.d/hostname"), "w+")
            try:
                f.write ('hostname="%s"\n' % (vm_name))
            finally:
                f.close ()

        if vm_net_config_content:
            f = open (os.path.join (tmp_mount, "etc", "conf.d", "net"), "w+")
            try:
                f.write (vm_net_config_content)
            finally:
                f.close ()

        if isinstance (user_dict, dict) and user_dict:
            print "seting user & passwd"

            user_script_dest = os.path.join (tmp_mount, "tmp", "_create_user.py")
            user_data = os.path.join (tmp_mount, "tmp", "user_data")
            shutil.copy (user_script_src, user_script_dest)
            f = open (user_data, "w")
            try:
                for user, pw in user_dict.iteritems ():
                    f.write ("%s:%s\n" % (user, pw))
            finally:
                f.close ()
            if os.system ("chroot %s python /tmp/_create_user.py" % (tmp_mount)):
                print "set user & passwd failed"
            os.unlink (user_data)
            os.unlink (user_script_dest)
    finally:
        img_ops.umount_loop (lo_dev, tmp_mount)


def main ():
    optlist = []
    args = []
    vm_name = None
    vm_ip = None
    vm_netmask = None
    vm_passwd = None
    vm_gateway = None
#    user_dict = dict ()
    img_path = None

    if len (sys.argv) == 1:
        usage ()
        return 0
    try:
        optlist, args = getopt.gnu_getopt (sys.argv[1:], "h", ["help",
          'img=',
          'name=', 'ip=', 'gateway='
          ])
    except getopt.GetoptError, e:
        print >> sys.stderr, str(e)
        return -1
    for opt, v in optlist:
        if opt in ['--help', '-h'] :
            usage ()
            return 0
        elif opt == '--name':
            vm_name = v
        elif opt == '--ip':
            arr = v.split ("/")
            if len(arr) != 2:
                raise Exception ("ip format must be in XXX.XXX.XXX.XXX/number")
            vm_ip = arr[0]
            vm_netmask = int(arr[1])
        elif opt == '--gateway':
            vm_gateway = v
#        elif opt == '--user':
#            arr = v.split (":")
#            if len(arr) != 2:
#                raise Exception ("param user should be in 'USER:PASSWD' form")
#            user_dict[arr[0]] = arr[1]
        elif opt == '--img':
            img_path = v


    root_pw = misc.gen_password (10)
    user_dict = {'root': root_pw}
    print "root password will be: " + root_pw

    do_vm_config (vm_root_path=img_path, vm_name=vm_name, vm_ip=vm_ip, vm_netmask=vm_netmask, vm_gateway=vm_gateway, user_dict=user_dict)
    return 0

    
if "__main__" == __name__:
    res = main ()
    os._exit (res)

