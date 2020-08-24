#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 13:38:40 2020

@author: lmorton
"""
from django.utils.functional import cached_property
import MDSplus as mds
try:
    import xarray as xr
except Exception as ex:
    print(ex)
import re

#TODO: package the connection with the tree & get the reset button to happen
# automatically in case the connection is lost
conn = mds.connection.Connection("c2wmds.trialphaenergy.com")
conn.openTree("phys",121249)

#TODO: appears I can only access one shot at a time this way... pretty clunky for
# doing multi-shot analysis. I might also get mixed data if I open a new shot with the
# connection object and then use the same tree object to load new leafs, b/c the
# Leafs remember the connection but aren't aware of the shot number!
usage_table = mds.tree._usage_table
usage_integers = [usage_table[utype] for utype in ['NUMERIC','SIGNAL','AXIS','COMPOUND_DATA']]

#TODO: This method doesn't deal with members of a signal very well. For instance, the
# descriptions I either don't get, or else they can be allowed to cause a dead branch
# to persist. It looks like descriptions are not a first-class object in the system.
# Also, the data_err arrays and description strings could be combined into the xarray object
# This might be too much customization, though: I am not able to test this against all the idiotic
# variations of MDSplus tree structure out there. Maybe I should just leave it lilke this
# for generality -- I think it should work quite well as-is.


#Taken from the class TreeNode definition in mdsplus/python/MDSplus/tree.py 
# should be on the webpage instead of buried in here for God's sake.


def stripper(text):
    NCI_dict ={}
    for line in text.splitlines():
        descr = re.findall(r'".*"',line)[0].strip(r"\"")
        aliases = line.split("=")[:-1]
        for alias in aliases:
            NCI_dict[alias.strip()]=descr
    return NCI_dict
            

NCI_text = """    cached              =Nci._nciProp(Flags.CACHED,"True if data is cached")
    compress_segments   =Flags._nciFlag(Flags.COMPRESS_SEGMENTS,"should segments be compressed")
    compressible        =Nci._nciProp(Flags.COMPRESSIBLE,"is the data stored in this node compressible")
    essential           =Flags._nciFlag(Flags.ESSENTIAL,"essential action defined in this node")
    do_not_compress     =Flags._nciFlag(Flags.DO_NOT_COMPRESS,"is this node set to disable any compression of data stored in it")
    compress_on_put     =Flags._nciFlag(Flags.COMPRESS_ON_PUT,"should data be compressed when stored in this node")
    include_in_pulse    =Flags._nciFlag(Flags.INCLUDE_IN_PULSE,"include subtree in pulse")
    nid_reference       =Nci._nciProp(Flags.NID_REFERENCE,"node data contains nid references")
    no_write_model      =Flags._nciFlag(Flags.NO_WRITE_MODEL,"is storing data in this node disabled if model tree")
    no_write_shot       =Flags._nciFlag(Flags.NO_WRITE_SHOT,"is storing data in this node disabled if not model tree")
    parent_state        =Nci._nciProp(Flags.PARENT_STATE,"is parent disabled")
    path_reference      =Nci._nciProp(Flags.PATH_REFERENCE,"node data contains path references")
    segmented           =Nci._nciProp(Flags.SEGMENTED,"is data segmented")
    setup_information=setup=Nci._nciProp(Flags.SETUP_INFORMATION,"was this data present in the model");
    state               =Flags._nciFlag(Flags.STATE,"Use on property instead. on/off state of this node. False=on,True=off.")
    versions            =Nci._nciProp(Flags.VERSIONS,"does the data contain versions")
    write_once          =Flags._nciFlag(Flags.WRITE_ONCE,"is no write once")
    brother             =Nci._nciProp(Nci.BROTHER,"brother node of this node")
    child               =Nci._nciProp(Nci.CHILD,"child node of this node")
    class_str           =Nci._nciProp(Nci.CLASS_STR,"class name of the data stored in this node")
    conglomerate_elt    =Nci._nciProp(Nci.CONGLOMERATE_ELT,"what element of a conglomerate is this node")
    conglomerate_nids   =Nci._nciProp(Nci.CONGLOMERATE_NIDS,"what are the nodes of the conglomerate this node belongs to")
    data_in_nci         =Nci._nciProp(Nci.DATA_IN_NCI,"is the data of this node stored in its nci")
    depth               =Nci._nciProp(Nci.DEPTH,"what is the depth of this node in the tree structure")
    dtype               =Nci._nciProp(Nci.DTYPE,"the numeric value of the data type stored in this node")
    dtype_str           =Nci._nciProp(Nci.DTYPE_STR,"the name of the data type stored in this node")
    error_on_put        =Nci._nciProp(Nci.ERROR_ON_PUT,"was there an error storing data for this node")
    fullpath            =Nci._nciProp(Nci.FULLPATH,"full node path")
    get_flags           =Nci._nciProp(Nci.GET_FLAGS,"numeric flags mask for this node")
    length              =Nci._nciProp(Nci.LENGTH,"length of data stored in this node (uncompressed)")
    mclass=_class       =Nci._nciProp(Nci.CLASS,"class of the data stored in this node")
    member              =Nci._nciProp(Nci.MEMBER,"first member immediate descendant of this node")
    minpath             =Nci._nciProp(Nci.MINPATH,"minimum path string for this node based on current default node")
    node_name=name      =Nci._nciProp(Nci.NODE_NAME,"node name")
    number_of_children  =Nci._nciProp(Nci.NUMBER_OF_CHILDREN,"number of children")
    number_of_elts      =Nci._nciProp(Nci.NUMBER_OF_ELTS,"number of nodes in a conglomerate")
    number_of_members   =Nci._nciProp(Nci.NUMBER_OF_MEMBERS,"number of members")
    original_part_name  =Nci._nciProp(Nci.ORIGINAL_PART_NAME,"original part name of this node")
    owner_id            =Nci._nciProp(Nci.OWNER_ID,"id of the last person to write to this node")
    parent              =Nci._nciProp(Nci.PARENT,"parent node of this node")
    parent_relationship =Nci._nciProp(Nci.PARENT_RELATIONSHIP,"parent relationship")
    rfa                 =Nci._nciProp(Nci.RFA,"data offset in datafile")
    rlength             =Nci._nciProp(Nci.RLENGTH,"length of data in node")
    status              =Nci._nciProp(Nci.STATUS,"status of action execution")
    time_inserted       =Nci._nciProp(Nci.TIME_INSERTED,"64-bit timestamp when data was stored")
    usage_str           =Nci._nciProp(Nci.USAGE_STR,"formal name of the usage of this node")"""

def get_stuff(conn,fullpath,NCI):
    return conn.get('GETNCI($,"%s")'%NCI,fullpath)

def treeify(conn,dead_branches = False):
    base = Branch()
    if not dead_branches:
        lengths, fullpaths,usages,paths = [a.tolist() for a in conn.get((
        'serializeout(`(_=TreeFindNodeWild("~~~");List(,' #The ~~~ is supposed to yield breadth-first search, so that I can assume all the branches are encountered before the leaves that hang from them
        'GETNCI(_,"LENGTH"),'
        'GETNCI(_,"FULLPATH"),'
        'GETNCI(_,"USAGE"),'
        'GETNCI(_,"PATH")'
        ');))')).deserialize().data()]
        for length,fullpath,usage,path in zip(lengths,fullpaths,usages,paths):
            if length>0 and int(usage) in usage_integers: 
                fullpath = fullpath.lower().strip()
                stringy = stringify(fullpath)
                push(base,stringy,fullpath,conn,path,int(usage),int(length))
    else:
        fullpaths,paths =  conn.get((
        'serializeout(`(_=TreeFindNodeWild("***");List(,'
        'GETNCI(_,"FULLPATH"),'
        'GETNCI(_,"PATH")'
        ');))')).deserialize().data()
        for fullpath,path in zip(fullpaths,paths):
            fullpath = fullpath.lower().strip()
            stringy = stringify(fullpath)
            push(base,stringy,fullpath,conn,path,-1,None)  
    return base             

def stringify(path):
    delimiters = ".","::",":"
    regexPattern = '|'.join(map(re.escape, delimiters))
    return re.split(regexPattern, path)[2:]

def push(base,stringy,fullpath,connection,path,usage,length):
    if len(stringy)>1:
        if not hasattr(base,stringy[0]):
            setattr(base,stringy[0],Branch())
        push(getattr(base,stringy[0]),stringy[1:],fullpath,connection,path,usage=usage,length=length)
    else:
        if hasattr(base,stringy[0]):
            raise Exception("TreeNodeWild returned data out of order, attempting to place a Leaf where a Branch was. Fail! Full path: %s; current substring: %s"%fullpath,stringy)
        else:
            setattr(base,stringy[0],Leaf(fullpath,connection,path,usage=usage,length=length))

#TODO: make the node name more accessible, so I can easily use it elsewhere.
class Leaf(object):
    """
    Dummy class that is used as the object type for the terminus of every branch
    of the python version of the MDSplus tree.  Instead of actually forcing the
    loading of all the data at the time that we traverse the tree, all we do is 
    set up Leaf objects which have a reference to the MDSplus node.  The first 
    time you try to acess the 'data' attribute of a leaf, the leaf calls 
    'getXarray' on the hidden TreeNode and actually places the xarray object 
    at the location of the 'data' attribute of the leaf, so the xarray object
    can be used normally from then on.
    """
    def __init__(self,fullpath,connection,path,strict=False,usage=0,length=None):
        """
        mdsnode should be of type mds.treenode.TreeNode
        """
        self.__strict__ = strict
        self.__fullpath__ = fullpath
        self.__connection__ = connection
        self.__usage__ = usage
        self.__length__ = length
        self.__path__ = path
    @cached_property
    def data(self):
        """
        The @cached_property takes this method and makes it behave like an
        attribute instead. An ipython user will see the 'leaf.data' attribute,
        but what they are seeing is a cached_property instance built around 
        this function, not an xarray object. However, once the user requests 
        the data (eg, 'signal=leaf.data'), the cached_property calls this
        function and sets the 'leaf.data' equal to the result. Ever after,
        'leaf.data' refers to leaf.__dict__['data'] which is the xarray object.
        """
        if self.__usage__ in usage_integers:
            return getXarray(self)
        else:
            return self.__connection__.get(self.__fullpath__).data()

    def __repr__(self):
        if self.__length__ is None:
            self.__length__ = int(self.__connection__.get('GETNCI({},"LENGTH")'.format(self.__fullpath__)))
        return "Data (length = %d)"%self.__length__
    
class Branch(object):
    """
    Dummy class whose only real function is to look nice and keep track of 
    references to mds.treenode.Treenode objects. A Branch object only has other
    Branch or Leaf objects as attributes, but no data.
    """
    def __repr__(self):
        """
        Controls how the Node instance is displayed.  Lets you see the number
        of subbranches that any branch has, or else a description of the leaf
        if the attribute is a leaf.
        """
        strings=[]
        try:            
            for name,value in self.__dict__.items():
                if '__' in name: continue
                obj=self.__dict__[name]
                if isinstance(obj,self.__class__):
                    description=str(len(obj.__getDescendants__()))
                else:
                    description=obj.__repr__()
                strings.append(name+": " +description)
        except Exception as ex:
            print(type(ex), ex)
        return "name:   subnodes \n"+"\n".join(strings)
    def __getDescendants__(self):
        return  [key for key in self.__dict__.keys() if not key.startswith('__')]  


def getXarray(Leaf):
    conn = Leaf.__connection__
    path = Leaf.__path__
    data = conn.get(path).data()
    try:
        units = conn.get("UNITS_OF({})".format(path)).data()
    except (mds.mdsExceptions.MDSplusException):
        units = ""
    ndim = len(data.shape)
    dims_dict = {}
    for ii in range(ndim):
        dimname = "dim_{}".format(ii) #TODO: try getting name instead
        coord = conn.get("DIM_OF({},{})".format(path,ii)).data()
        coord_units = conn.get("UNITS_OF(DIM_OF({},{}))".format(path,ii)).data()
        dims_dict[dimname] = ((dimname,),coord,{"units":coord_units})#TODO: deal with case when the 'dims' are actually coords
    dims = list(dims_dict.keys())
    try:
        return xr.DataArray(data,dims=dims,coords=dims_dict,attrs={"units":units})
    except:
        dims.reverse()
        return xr.DataArray(data,dims=dims,coords=dims_dict,attrs={"units":units})
        
        
        
       