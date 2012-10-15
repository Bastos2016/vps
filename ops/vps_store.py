#!/usr/bin/env python

import os
import ops.vps_common as vps_common
import shutil
import datetime
import re
import ops._env
import conf
assert conf.MOUNT_POINT_DIR and os.path.isdir (conf.MOUNT_POINT_DIR)

def _parse_date (s):
    if s is None:
        return None
    assert isinstance (s, basestring)
    om = re.match (r'^(\d{1,4})-(\d{1,2})-(\d{1,2})', s)
    if not om:
        raise Exception ('%s is not date format' % (s))
    year = int (om.group (1))
    mon = int (om.group (2))
    day = int (om.group (3))
    return datetime.date (year, mon, day)


class VPSStoreBase (object):

    partition_name = None
    xen_dev = None
    size_g = None
    xen_path = None
    fs_type = None
    trash_date = None
    expire_date = None
    
    def __init__ (self, partition_name, xen_dev, xen_path, fs_type, mount_point, size_g):
        self.partition_name = partition_name
        self.size_g = size_g
        self.fs_type = fs_type
        self.xen_dev = xen_dev
        self.xen_path = xen_path
        self.mount_point = mount_point

    def get_fs_type (self):
        raise NotImplementedError ()

    def get_size (self):
        raise NotImplementedError ()

    def _set_expire_days (self, days):
        if days > 0:
            self.trash_date = datetime.date.today ()
            self.expire_date = self.trash_date + datetime.timedelta (days=days)
        else:
            self.trash_date = None
            self.expire_date = None
        
    def trash_str (self):
        raise NotImplementedError ()

    def create (self, fs_type=None):
        raise NotImplementedError ()

    def delete (self):
        raise NotImplementedError ()

    def delete_trash (self):
        raise NotImplementedError ()

    def exists (self):
        raise NotImplementedError ()

    def get_mounted_dir (self):
        raise NotImplementedError ()

    def mount_tmp (self, readonly=False):
        """ return mountpoint """
        raise NotImplementedError ()

    def mount_trash_temp (self, readonly=False):
        """ return mountpoint """
        raise NotImplementedError ()

    def dump_trash (self, expire_days):
        raise NotImplementedError ()

    def restore_from_trash (self):
        raise NotImplementedError ()

    def snapshot (self):
        raise NotImplementedError ()

    def to_meta (self):
        data = {}
        data['__class__'] = self.__class__.__name__
        data["partition_name"] = self.partition_name
        data["size_g"] = self.size_g
        data["fs_type"] = self.fs_type
        data["xen_dev"] = self.xen_dev
        data["xen_path"] = self.xen_path
        t_format = "%Y-%m-%d"
        data["mount_point"] = self.mount_point
        if self.trash_date:
            data['trash_date'] = self.trash_date.strftime (t_format)
        else:
            data['trash_date'] = None
        if self.expire_date:
            data['expire_date']  = self.expire_date.strftime (t_format)
        else:
            self.expire_date = None
        return data

    @classmethod
    def from_meta (cls, data):
        assert data
        _class = data['__class__']
        if _class == VPSStoreImage.__name__:
            self = VPSStoreImage.from_meta (data)
        elif _class == VPSStoreLV.__name__:
            self = VPSStoreLV.from_meta (data)
        else:
            raise TypeError (_class)
        if data.has_key ('trash_date'):
            self.trash_date = _parse_date (data['trash_date'])
        else:
            self.trash_date = None
        if data.has_key ('expire_date'):
            self.expire_date = _parse_date (data['expire_date'])
        else:
            self.expire_date = None
        return self


    
class VPSStoreImage (VPSStoreBase):

    file_path = None
    trash_path = None
    trash_dir = None

    def __init__ (self, partition_name, xen_dev, fs_type=None, mount_point=None, size_g=None):
        om = re.match (r'^(vps\d+)_(root|swap)$', partition_name)
        if om:
            if om.group (2) == 'root':
                img_name = "%s.img" % (om.group (1))
                self.file_path = os.path.join (conf.VPS_IMAGE_DIR, img_name)
            else:
                img_name = "%s.swp" % (om.group (1))
                self.file_path = os.path.join (conf.VPS_SWAP_DIR, img_name)
        else:
            img_name = "%s.img" % (partition_name)
            self.file_path = os.path.join (conf.VPS_IMAGE_DIR, img_name)
        self.trash_path = os.path.join (conf.VPS_TRASH_DIR, img_name)
        self.trash_dir = conf.VPS_TRASH_DIR
        xen_path = "file:" + self.file_path
        VPSStoreBase.__init__ (self, partition_name, xen_dev, xen_path, fs_type, mount_point, size_g)



    def to_meta (self):
        data = VPSStoreBase.to_meta (self)
        data['file_path'] = self.file_path
        return data

    @classmethod
    def from_meta (cls, data):
        return cls (data['partition_name'],
                data['xen_dev'], 
                data['fs_type'],
                data['mount_point'],
                data['size_g'])


    def __str__ (self):
        return self.file_path

    def trash_str (self):
        return self.trash_path

    def exists (self):
        return os.path.isfile (self.file_path)

    def trash_exists (self):
        return os.path.isfile (self.trash_path)

    def get_fs_type (self):
        if self.exists ():
            self.fs_type = vps_common.get_fs_type (self.file_path)
            return self.fs_type
        elif self.trash_exists ():
            self.fs_type = vps_common.get_fs_type(self.trash_path)
            return self.fs_type
        elif self.fs_type:
            return self.fs_type
        else:
            raise Exception ("not exist")

    def get_size (self):
        if self.exists ():
            return vps_common.file_getsize (self.file_path)
        elif self.trash_exists ():
            return vps_common.file_getsize (self.trash_path)
        elif self.size_g is not None:
            return self.size_g
        else:
            raise Exception ("no size")


    def create (self, fs_type=None):
        if not self.size_g:
            return
        vps_common.create_raw_image (self.file_path, self.size_g, sparse=True)
        if not self.fs_type:
            self.fs_type = fs_type
        assert self.fs_type
        vps_common.format_fs (self.fs_type, self.file_path)

    def get_mounted_dir (self):
        return vps_common.get_mountpoint (self.file_path)

    def delete_trash (self):
        if os.path.exists (self.trash_path):
            os.remove (self.trash_path)

    def delete (self):
        #TODO check whether in use !!!!!!!!!
        if os.path.exists (self.file_path):
            os.remove (self.file_path)

    def mount_tmp (self, readonly=False):
        return vps_common.mount_loop_tmp (self.file_path, readonly, temp_dir=conf.MOUNT_POINT_DIR)

    def mount_trash_temp (self, readonly=False):
        return vps_common.mount_loop_tmp (self.trash_path, readonly, temp_dir=conf.MOUNT_POINT_DIR)

    def dump_trash (self, expire_days):
        if not os.path.exists (self.file_path):
            raise Exception ("%s not exist" % (self.file_path))
        if os.path.exists (self.trash_path):
            os.remove (self.trash_path)
        shutil.move (self.file_path, self.trash_path)
        self._set_expire_days (expire_days)

    def restore_from_trash (self):
        if not os.path.exists (self.trash_path):
            raise Exception ("%s not exist" % (self.trash_path))
        shutil.move (self.trash_path, self.file_path)
        self._set_expire_days (None)


class VPSStoreLV (VPSStoreBase):

    dev = None
    trash_dev = None
    lv_name = None
    vg_name = None

    def __init__ (self, partition_name, xen_dev, fs_type=None, mount_point=None, size_g=None):
        assert conf.VPS_LVM_VGNAME
        self.lv_name = partition_name
        self.vg_name = conf.VPS_LVM_VGNAME
        self.dev = "/dev/%s/%s" % (self.vg_name, self.lv_name)
        self.trash_dev = "/dev/%s/trash_%s" % (self.vg_name, self.lv_name)
        xen_path = "phy:" + self.dev
        VPSStoreBase.__init__ (self, partition_name, xen_dev, xen_path, fs_type, mount_point, size_g)

    def __str__ (self):
        return self.dev

    def trash_str (self):
        return self.trash_dev

    def to_meta (self):
        data = VPSStoreBase.to_meta (self)
        return data

    @classmethod
    def from_meta (cls, data):
        return cls (data['partition_name'],
                data['xen_dev'],
                data['fs_type'],
                data['mount_point'],
                data['size_g'])

    def create (self, fs_type=None):
        assert self.size_g > 0
        vps_common.lv_create (self.vg_name, self.lv_name, self.size_g)
        if not self.fs_type:
            self.fs_type = fs_type
        assert self.fs_type
        vps_common.format_fs (self.fs_type, self.dev)

       
    def exists (self):
        return os.path.exists (self.dev)

    def trash_exists (self):
        return os.path.exists (self.trash_dev)

    def get_fs_type (self):
        if self.exists ():
            self.fs_type = vps_common.get_fs_type (self.dev)
            return self.fs_type
        elif self.trash_exists ():
            self.fs_type = vps_common.get_fs_type (self.trash_dev)
            return self.fs_type
        elif self.fs_type:
            return self.fs_type
        else:
            raise Exception ("not exist")

    def get_size (self):
        if self.exists ():
            return vps_common.lv_getsize (self.dev)
        elif self.trash_exists ():
            return vps_common.lv_getsize (self.trash_dev)
        elif self.size_g is not None:
            return self.size_g
        else:
            raise Exception ("no size")
 

    def get_mounted_dir (self):
        return vps_common.lv_get_mountpoint (self.dev)

    def dump_trash (self, expire_days):
        if not os.path.exists (self.dev):
            raise Exception ("%s not exist" % (self.dev))
        if os.path.exists (self.trash_dev):
            vps_common.lv_delete (self.trash_dev)
        vps_common.lv_rename (self.dev, self.trash_dev)
        self._set_expire_days (expire_days)

    def restore_from_trash (self):
        if not os.path.exists (self.trash_dev):
            raise Exception ("%s not exist" % (self.trash_dev))
        vps_common.lv_rename (self.trash_dev, self.dev)
        self._set_expire_days (None)

    def delete_trash (self):
        #TODO check whether in use !!!!!!!!!
        if os.path.exists (self.trash_dev):
            vps_common.lv_delete (self.trash_dev)

    def delete (self):
        #TODO check whether in use !!!!!!!!!
        if os.path.exists (self.dev):
            vps_common.lv_delete (self.dev)

    def mount_tmp (self, readonly=False):
        return vps_common.mount_partition_tmp (self.dev, readonly=readonly, temp_dir=conf.MOUNT_POINT_DIR)

    def mount_trash_temp (self, readonly=False):
        return vps_common.mount_partition_tmp (self.trash_dev, readonly, temp_dir=conf.MOUNT_POINT_DIR)

    def snapshot (self):
        snapshot_name = "snap_%s" % self.lv_name
        snapshot_dev = vps_common.lv_snapshot (self.dev, snapshot_name, self.vg_name) 
        return snapshot_dev

##############

def vps_store_new (partition_name, xen_dev, fs_type=None, mount_point=None, size_g=None):
    if conf.USE_LVM:
        return VPSStoreLV (partition_name, xen_dev, fs_type=fs_type, mount_point=mount_point, size_g=size_g)
    else:
        return VPSStoreImage (partition_name, xen_dev, fs_type=fs_type, mount_point=mount_point, size_g=size_g)

def vps_store_clone (storage):
    return vps_store_new (storage.partition_name, storage.xen_dev, storage.fs_type, storage.mount_point, storage.size_g)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 :
