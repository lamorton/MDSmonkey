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


#TODO: try to find a way to enable multi-shot analysis w/ single tree object

usage_table = mds.tree._usage_table
usage_integers = [usage_table[utype] for utype in ['NUMERIC','SIGNAL','AXIS','COMPOUND_DATA']]

#TODO: Combine the data_err arrays and description strings into the xarray object
# This might be too much customization, though: I am not able to test this against all 
# variations of MDSplus tree structure out there. Maybe I should just leave it like this
# for generality -- I think it should work quite well as-is.


#Taken from the class TreeNode definition in mdsplus/python/MDSplus/tree.py 
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

def get_stuff(connection,fullpath,NCI):
    """
    Get information about a node from the server

    Parameters
    ----------
    connection : MDSplus.Connection
        live connection to the server
    fullpath : string
        path into the tree
    NCI : string
        the magic code to get what you want.  See the available codes in 
        MDSmonkey.NCI_text

    Returns
    -------
    TYPE
        whatever you requested

    """
    return connection.get('GETNCI($,"%s")'%NCI,fullpath)

def get_tree(shot,tree,server,trim_dead_branches=True):
    """
    Connect to a server and construct a Python representation of the MDSplus
    tree for a specific shot. The data is pulled as-needed into 
    xarray.DataArrays and cached. If you want to analyze a different shot you
    will need to get a new tree object to avoid stale data.

    Parameters
    ----------
    shot : integer, optional
        shot number
    tree : string, optional
        the MDSplus tree to connect to
    server : string, optional
        URL of the server to connect to
    trim_dead_branches : bool, optional
        If True, trim the 'dead' branches so they do not appear in the tree. 
        The default is True. Dead branches are those which have no data for
        the shot. This operation can be slow, because evaluating the 'length'
        of the data (which is how dead branches are detected) is slow. Setting
        trim_dead_branches = False is faster, but the tree may be cluttered.

    Returns
    -------
    Branch
        The 'trunk' of the the tree


    Usage example:
    --------------
        
    > from MDSmonkey import get_tree
    > tree = get_tree(101010,"phys","my.server.com")
    > print(tree)
    
    name        : subnodes 
    _______________________
    fueling     : Branch w/ 4 subnodes
    physics     : Branch w/ 39 subnodes
    vacuum      : Branch w/ 15 subnodes
    
    > print(tree.physics)
    
    name        : subnodes 
    _______________________
    b0          : Leaf \PHYS::B0: length = 734
    b0_avg      : Leaf \PHYS::B0_AVG: length = 458
    action      : Branch w/ 1 subnodes
    decay_rates : Branch w/ 6 subnodes
    
    > b0 = tree.physics.b0.data
    >print(b0)

    <xarray.DataArray 'B0' (dim_0: 41)>
    array([0.12604433, 0.15488786, 0.08534247, 0.06027878, 0.06407972,
           0.08324956, 0.07905848, 0.08837441, 0.08049475, 0.09197565,
           0.10009823, 0.09144516, 0.08829582, 0.09927156, 0.06689333,
           0.08060841, 0.06631568, 0.0812166 , 0.0747666 , 0.08461637,
           0.06492528, 0.07736427, 0.07603952, 0.08484247, 0.06642506,
           0.08150416, 0.0671018 , 0.08052307, 0.08933112, 0.09874175,
           0.09974558, 0.08469599, 0.08020811, 0.09162582, 0.07829014,
           0.0879171 , 0.06486361, 0.08136006, 0.09306931, 0.10664426,
           0.01769459], dtype=float32)
    Coordinates:
      * dim_0    (dim_0) float64 -3.16 -3.16 -2.75 -2.75 -2.5 ... 2.5 2.75 3.06 3.06
    Attributes:
        units:    T
        
    """
    connection = mds.connection.Connection(server)
    connection.openTree(tree,shot)

    trunk = Branch()
    if  trim_dead_branches:
        lengths, fullpaths,usages,paths = [a.tolist() for a in connection.get((
        'serializeout(`(_=TreeFindNodeWild("~~~");List(,' 
        'GETNCI(_,"LENGTH"),'
        'GETNCI(_,"FULLPATH"),'
        'GETNCI(_,"USAGE"),'
        'GETNCI(_,"PATH")'
        ');))')).deserialize().data()]
        #The ~~~ is supposed 
        # to yield breadth-first search, so that I can assume all the branches
        # are encountered before the leaves that hang from them
        for length,fullpath,usage,path in zip(lengths,fullpaths,usages,paths):
            if length>0 and int(usage) > 1: #Only push non-structure, length>1 objects
                fullpath = fullpath.lower().strip()
                stringy = stringify(fullpath)
                push(trunk,stringy,shot,tree,fullpath,connection,str(path).strip(),int(usage),int(length))
    else:
        fullpaths,paths,usage =  connection.get((
        'serializeout(`(_=TreeFindNodeWild("~~~");List(,'
        'GETNCI(_,"FULLPATH"),'
        'GETNCI(_,"PATH"),'
        'GETNCI(_,"USAGE")'
        ');))')).deserialize().data()
        for fullpath,path,usage in zip(fullpaths,paths,usage):
            if int(usage) >1 : #Non-structure
                fullpath = fullpath.lower().strip()
                stringy = stringify(fullpath)
                push(trunk,stringy,shot,tree,fullpath,connection,str(path).strip(),int(usage),None)
    return trunk             

def stringify(path,depth=2):
    delimiters = ".","::",":"
    regexPattern = '|'.join(map(re.escape, delimiters))
    return re.split(regexPattern, path)[depth:]

def push(base,stringy,shot,tree,fullpath,connection,path,usage,length):
    if len(stringy) > 1:
        if not hasattr(base,stringy[0]):
            if usage == mds.tree._usage_table['TEXT']:
                return  #Don't push a branch just b/c there is text under it
                #Note that by using breadth-first search in TreeFindNodeWild,
                #any string arrays that are 'attributes' of data arrays will
                #be found *after* their corresponding data array. So, in the
                #case of dead_branches = True, the arrays below will hold the
                #tree open and allow the descriptions to appear, but if False,
                #then they will not show up and neither will their parents.
            setattr(base,stringy[0],Branch())
        push(getattr(base,stringy[0]),stringy[1:],shot,tree,fullpath,connection,path,
             usage=usage,length=length)
    else:
        if hasattr(base,stringy[0]):
            raise Exception("TreeNodeWild returned data out of order, attempting\
                            to place a Leaf where a Branch was. Fail! Full path: \
                                %s; current substring: %s"%(fullpath,stringy))
        else:
            setattr(base,stringy[0],Leaf(shot,tree,fullpath,connection,path,usage=usage,
                                         length=length))

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
    def __init__(self,shot,tree,fullpath,connection,path,usage=-1,length=None):
        """
        Create a new Leaf object

        Parameters
        ----------
        fullpath : string
            MDSplus path to the node
        connection : MDSplus.Connection
            the connection object for this tree
        path : string
            a short path (tag) to this Leaf
        usage : int, optional
            Integer specifying the usage. The default is -1. Values < 1 indicate
            no data is stored, while 8 indicates text.
        length : int, optional
            Length of the stored data at the node, in bytes. It takes quite a 
            while for this number to be counted, so this is optional. The 
            default is None.  The __repr__ method needs this info tho, so it
            may request this value from the connection.

        """
        self.__fullpath__ = fullpath
        self.__connection__ = connection
        self.__usage__ = usage
        self.__length__ = length
        self.__path__ = path
        self.__tree__ = tree
        self.__shot__ = shot
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
        if self.__usage__ == -1: #Hasn't been checked b/c we did dead_branches == True
            self.__usage__ = get_stuff(self.__connection__,self.__fullpath__,"usage")
        if self.__usage__ in usage_integers:
            try:
                return getXarray(self)
            except mds.mdsExceptions.MDSplusException:
                self.__connection__.reconnect()
                self.__connection__.openTree(self.__tree__,self.__shot__)
                return getXarray(self)
        else:
            data = self.__connection__.get(self.__fullpath__).data()
            if data.dtype == np.str_:
                data = str(data)
            return data

    def __repr__(self):
        """
        Pretty-printing for the Leaf type. This operation causes the __Length__
        data to be pulled from the server, if not already available.  This can
        fail, needs to be handled.
        """
        if self.__length__ is None:
            try:
                self.__length__ = int(self.__connection__.get('GETNCI({},"LENGTH")'.format(self.__fullpath__)))
            except mds.mdsExceptions.MDSplusException:
                print("Error: could not connect to the server")
                return "Leaf %s"%self.__path__
        return "Leaf %s: length = %d"%(self.__path__,self.__length__)
    
    def __getDescendants__(self):
        """
        Get list of the descendant of this Leaf
        """
        return  [key for key in self.__dict__.keys() if not key.startswith('__')]  
    
    
    #TODO: give branch a fullpath property
class Branch(object):
    """
    Dummy class whose only real function is to look nice and keep track of 
    references to mds.treenode.Treenode objects. A Branch object only has other
    Branch or Leaf objects as attributes, but no data.
    """
    def __repr__(self):
        """
        Controls how the Branch instance is displayed.  Lets you see the number
        of subbranches that any branch has, or else a description of the leaf
        if the attribute is a leaf.
        """
        strings=[]
        name_max_length = max(map(len,self.__dict__.keys()))
        try:            
            for name,value in self.__dict__.items():
                if '__' in name: continue
                obj=self.__dict__[name]
                if isinstance(obj,Branch):
                    description="Branch w/ %d subnodes"%len(obj.__getDescendants__())
                else:
                    description=obj.__repr__()
                strings.append(name.ljust(name_max_length)+": " +description)
        except Exception as ex:
            print(type(ex), ex)
        line1 = "name".ljust(name_max_length)+": subnodes \n" 
        line2 = "\n".rjust(len(line1),"_")
        rest = "\n".join(strings)
        return line1 + line2 + rest
    def __getDescendants__(self):
        return  [key for key in self.__dict__.keys() if not key.startswith('__')]  


def getXarray(leaf):
    """
    Given a Leaf, pull the Leaf's data from the server into an xarray.DataArray
    Attempts to get the dimensions and units.  The dimension names are not 
    available because they do not exist in the MDSplus in general, and attempting 
    to infer them is not robust. You may assign dimension names to the xarray:
        
    >data = tree.diagnostic.thomson.data
    >data = data.rename({"dim_0":'time',"dim_1":"radius"})

    Parameters
    ----------
    leaf : Leaf
        the Leaf in question

    Returns
    -------
    xarray.DataArray
    
    """
    conn = leaf.__connection__
    path = leaf.__path__
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
        dims_dict[dimname] = ((dimname,),coord,{"units":coord_units})
        #TODO: deal with case when the 'dims' are actually coords
    dims = list(dims_dict.keys())
    try:
        return xr.DataArray(data,dims=dims,coords=dims_dict,attrs={"units":units},
                            name = stringify(leaf.__path__,depth=0)[-1])
    except:
        dims.reverse()
        return xr.DataArray(data,dims=dims,coords=dims_dict,attrs={"units":units},
                            name =  stringify(leaf.__path__,depth=0)[-1])
import numpy as np

def diagnosticXarray(branch,subset=None,behavior='merge'):
    """
    Produce an xarray.Dataset from a diagnostic Branch of a tree.
    This causes the data to be pulled from the server, if it has not already
    been done, so it may be slow the first time.

    Parameters
    ----------
    branch : Branch
        must be the parent of at least one Leaf that has data
    subset : list of strings, optional
        select which of the Leafs to include in the Dataset. The default is all.
    behavior : string, optional
        If 'merge,' each Leaf appears as a variable. The default is 'merge'.
        If 'concat,' each Leaf is considered one index along a new dimension
            called 'channel'
        If 'dump,' just return a dictionary of the DataArrays for debugging.

    Returns
    -------
    xarray.Dataset or xarray.DataArray or dct
        the collected data from this diagnostic

    """
    xrdct = {}
    for thing in branch.__dict__:
        obj= getattr(branch,thing)
        if type(obj) == Leaf:
            xrdct[thing] = obj.data
    if behavior == 'concat':
        ndlxr = xr.concat(xrdct.values(),dim='channel')
        return ndlxr.assign_coords({'channel':np.array(list(xrdct.keys()))})
    elif behavior == 'merge':
        return xr.merge(xrdct.values())
    elif behavior =='combine':
        return xr.Dataset(xrdct)
 

       