#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 13:38:40 2020

@author: lmorton
"""
from django.utils.functional import cached_property
import MDSplus as mds
import xarray as xr
import re


#TODO: try to find a way to enable multi-shot analysis w/ single tree object, and 
#      add shot number display to the Branch __information__ string

#TODO: Consider rebasing on mdsconnector -- it can work in 'local' mode instead of ssh

usage_table = mds.tree._usage_table
usage_integers = [usage_table[utype] for utype in ['NUMERIC','SIGNAL','AXIS','COMPOUND_DATA']]

#TODO: Combine the data_err arrays and description strings into the xarray object
# This might be too much customization, though: I am not able to test this against all 
# variations of MDSplus tree structure out there. Maybe I should just leave it like this
# for generality -- I think it should work quite well as-is.


#TODO:  

def _parser(text):
    """
    Parse this blob of text I yanked from the MDSplus code
    """
    NCI_dict ={}
    for line in text.splitlines():
        descr = re.findall(r'".*"',line)[0].strip(r"\"")
        aliases = line.split("=")[:-1]
        for alias in aliases:
            NCI_dict[alias.strip()]=descr
    return NCI_dict
            
#Taken from the class TreeNode definition in mdsplus/python/MDSplus/tree.py
_TDI_text = """    cached              =Nci._nciProp(Flags.CACHED,"True if data is cached")
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

TDI_text = _parser(_TDI_text)

def get_stuff(connection,fullpath,TDI):
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
    return connection.get('GETNCI($,"%s")'%TDI,fullpath)

def get_tree(shot,tree,server,trim_dead_branches=True):
    """
    Connect to a server and construct a Python representation of the MDSplus
    tree for a specific shot. The data is pulled as-needed into 
    xarray.DataArrays and cached. If you want to analyze a different shot you
    will need to get a new tree object to avoid stale data. This is only for
    reading, not for writing to the tree. Generality/robustness is more important 
    than advanced features -- the point is to have a tool that works on many
    devices with no site-specific set-up.  

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


    Usage examples:
    --------------
        
    > from MDSmonkey import get_tree
    > tree = get_tree(101010,"phys","my.server.com")
    > tree
    
    Branch \phys : number of subnodes: 14
    _____________________________________
    fueling     : Branch : number of subnodes: 4
    physics     : Branch : number of subnodes: 39
    vacuum      : Branch : number of subnodes: 15
    viz_only    : Branch : number of subnodes: 17
    electrodes  : Branch : number of subnodes: 6
    ...
    
    > tree.physics
    
    Branch \phys::top.physics : number of subnodes: 39
    __________________________________________________
    b0          : Leaf : number of subnodes: 4
    b0_avg      : Leaf : number of subnodes: 4
    be_max      : Leaf : number of subnodes: 4
    be_z0       : Leaf : number of subnodes: 4
    e_th        : Leaf : number of subnodes: 4
    ...
    
    > be_max = tree.physics.b0
    > be_max #has several associated Leafs below it with ancillary information

    Leaf \PHYS::B0 : length of data: 734 bytes
    __________________________________________
    data_err   : Leaf : number of subnodes: 0
    data_err_h : Leaf : number of subnodes: 0
    data_err_l : Leaf : number of subnodes: 0
    description: Leaf : number of subnodes: 0
    
    >be_max.data #A `Leaf` has the 'data' attribute, a `Branch` does not
    
    <xarray.DataArray 'BE_MAX' (dim_0: 94999)>
    array([0.08225632, 0.08221801, 0.08222205, ..., 0.0775292 , 0.07756143,
           0.07744625], dtype=float32)
    Coordinates:
      * dim_0    (dim_0) float64 -0.0004996 -0.0004992 -0.0004988 ... 0.0375 0.0375
    Attributes:
        units:    T
        
    >be_max.data.plot() #xarray.DataArray has custom plotting functionality


    > ndl = tree.diagnostics.thomson.dts02.ndl
    > ndl #Many channels that ought to be a single data array...
    
    Branch \phys::top.diagnostics.thomson.dts02.ndl : number of subnodes: 14
    ________________________________________________________________________
    ndl_01: Leaf : number of subnodes: 4
    ndl_02: Leaf : number of subnodes: 4
    ndl_03: Leaf : number of subnodes: 4
    ndl_04: Leaf : number of subnodes: 4
    ndl_05: Leaf : number of subnodes: 4
    ...
        
    > ndlarray = diagnosticXarray(ndl,behavior='concat')
    > print(ndlarray) #Combined into single 2D array by channel
        
        <xarray.DataArray 'NDL_DTS02_01' (channel: 14, dim_0: 34)>
    array([[          nan, 1.6703393e+18, 1.3293034e+18, 1.5485215e+18,
            1.7731074e+18, 2.2600095e+18, 4.0675737e+18, 2.2424507e+18,   
    ...
            3.1138925e+18, 3.2072900e+18, 2.9299945e+18, 3.1664352e+18,
            3.0876216e+18, 3.2820408e+18]], dtype=float32)
    Coordinates:
      * dim_0    (dim_0) float32 0.0025 0.0035 0.0045 ... 
      * channel  (channel) <U6 'ndl_01' 'ndl_02' 'ndl_03' ... 
    Attributes:
        units:    1/m^2
    
    
    > ts = tree.diagnostics.thomson.dts02
    > ts # ne, te belong together as part of a dataset with shared dimensions
         # but they are not part of the same array because they
         # are not the same kind of quantity & have separate units, so we
         # use 'merge' for this kind of information gathering
    
    Branch \phys::top.diagnostics.thomson.dts02 : number of subnodes: 6
    ___________________________________________________________________
    laser_energy: Leaf : number of subnodes: 4
    ne          : Leaf : number of subnodes: 4
    te          : Leaf : number of subnodes: 4
    te_max      : Leaf : number of subnodes: 4
    apd_monitors: Branch : number of subnodes: 2
    ndl         : Branch : number of subnodes: 14
    
    > tsarr = diagnosticXarray(ts,subset=['ne','te'],behavior='merge')
    > tsarr
    
    <xarray.Dataset>
    Dimensions:   (dim_0: 34, dim_1: 16)
    Coordinates:
      * dim_0     (dim_0) float32 0.0025 0.0035 0.0045 ... 0.029859 0.030859
      * dim_1     (dim_1) float32 -0.0933 -0.0533 -0.0133 ... 0.4792 0.5592 
    Data variables:
        ne  (dim_1, dim_0) float32 nan nan nan 4.2912584e+18 ... 
        te  (dim_1, dim_0) float32 nan nan nan 331.0 317.0 ... 
        
    > tsarr = tsarr.rename({"dim_0":"time","dim_1":"radius"})
    > print(tsarr) #Unfortunately MDSplus does not support dimension names so 
                    # they cannot be made available automatically -- the user
                    # needs to bring this information from somewhere else
    
    <xarray.Dataset>
    Dimensions:   (radius: 16, time: 34)
    Coordinates:
      * time      (time) float32 0.0025 0.0035 0.0045 ... 0.028859 0.029859 
      * radius    (radius) float32 -0.0933 -0.0533 -0.0133 ... 0.4792 0.5592 
    Data variables:
        ne  (radius, time) float32 nan nan nan 4.2912584e+18 ... nan nan
        te  (radius, time) float32 nan nan nan 331.0 317.0 ... nan nan 
    """
    connection = mds.connection.Connection(server)
    connection.openTree(tree,shot)

    trunk = Branch(r"\{}".format(tree))
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
                substrings = chop(fullpath)
                push(trunk,substrings,shot,tree,fullpath,connection,str(path).strip(),int(usage),int(length))
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
                substrings = chop(fullpath)
                push(trunk,substrings,shot,tree,fullpath,connection,str(path).strip(),int(usage),None)
    return trunk             

def chop(path,depth=2):
    """
    Chop an MDSplus path up into a list of substrings

    Parameters
    ----------
    path : string
        an MDSplus path
    depth : integer, optional
       How many of the initial substrings to throw out. The default is 2.

    Returns
    -------
    list of substrings
    """
    delimiters = ".","::",":"
    regexPattern = '|'.join(map(re.escape, delimiters))
    return re.split(regexPattern, path)[depth:]

def push(base,substrings,shot,tree,fullpath,connection,path,usage,length):
    """
    Place a Leaf on the tree by recursively putting Branches as attributes of
    Branches ... until the Leaf is ready to be placed.
    
    Works on the assumption that the deeper Leafs are pushed later in order,
    so that here is no danger of needing to replace a Branch (which cannot 
    have data) with a Leaf.  It is possible for Leafs to have further Branches
    or Leafs below them.
    
    Parameters
    ----------
    base : Branch
        the branch we are attempting to extend with the Leaf
    substrings : list of strings
        the substrings composing the path to the Leaf
    shot : int
        shot number (necessary for the Leaf to know this so it can reconnect
        in the event that the connection is interupted)
    tree : string
        MDS tree name (necessary for the Leaf to know this so it can reconnect
        in the event that the connection is interupted)
    fullpath : string
        the full MDS path to the leaf (necessary for the Leaf to be able
        to request its data from the server)
    connection : MDS.Connection
        the connection object to the server
    path : string
        shorter path name for display purposes
    usage : integer
        describes the type of MDS node in question (ie, branch or leaf)
    length : integer
        length in bytes of the data stored at the node. -1 represents not having
        checked.

    Raises
    ------
    Exception
        If the breadth-first ordering requirement for the nodes is not achieved
        then an error will be raised instead of clobbering a Branch to put a
        Leaf there or ignoring data that should be present.

    Returns
    -------
    This is very much a side-effectful operation. The outcome is that a Leaf
    is installed, and branches are installed below it if need-be.

    """
    if len(substrings) > 1: #We're not at the Leaf depth yet...
        if not hasattr(base,substrings[0]): #...and the current Branch at this depth doesn't have the next Branch that we want to go down
            current_path = fullpath.split(substrings[1])[0].strip('.:')
            if usage == mds.tree._usage_table['TEXT']:
                return #Text isn't worthy of opening a whole Branch. However,
                        # text WILL show up if the Branch it needs already exists 
                        # due to the presence of a 'real' Leaf with numerical data.
                        # This allows for descriptor strings to exist without
                        # ruining the intent of trim_dead_branches==True.
            setattr(base,substrings[0],Branch(fullpath=current_path))#...put a new empty Branch here so that we can go out onto and ...
        push(getattr(base,substrings[0]),substrings[1:],shot,tree,fullpath,connection,path,
             usage=usage,length=length) #...continue out onto this next Branch
    else: #...we are at the point where we'd like to install the Leaf on the current Branch...
        if hasattr(base,substrings[0]): #...uh-oh, there's already something here! 
            raise Exception("TreeNodeWild returned data out of order, attempting\
                            to place a Leaf where a Branch was. Fail! Full path: \
                                %s; current substring: %s"%(fullpath,substrings))
        else:#...whew, we're all set. Push the Leaf into place.
            setattr(base,substrings[0],Leaf(shot,tree,fullpath,connection,path,usage=usage,
                                         length=length))

class Branch(object):
    """
    Dummy class whose only real function is to look nice and keep track of 
    references to mds.treenode.Treenode objects. A Branch object only has other
    Branch or Leaf objects as attributes, but no data.
    """
    def __init__(self,fullpath):
        self.__fullpath__ = fullpath
    def __information__(self):
        return "%s %s : number of subnodes: %d\n"%(self.__class__.__name__,self.__fullpath__,self.__getNumberDescendants__())
    def __info__(self):
        return "%s : number of subnodes: %d"%(self.__class__.__name__,self.__getNumberDescendants__())
    def __repr__(self):
        """
        Controls how the Branch instance is displayed.  Lets you see the number
        of subbranches that any Branch has, along with a little blurb about
        this particular Branch (__info__).
        """
        line1 = self.__information__()
        if self.__getNumberDescendants__() >0:
            descendants = self.__getDescendants__()
            name_max_length = max(map(len,descendants.keys())) #Find longest name so can pad the strings
            strings = [name.ljust(name_max_length)+": " + descendant.__info__() for name,descendant in descendants.items()] 
            line2 = "\n".rjust(len(line1),"_")
            rest = line2 + "\n".join(strings)
        else:
            rest = ''

        return line1 + rest
    def __getDescendants__(self):
        return  {key:value for key,value in self.__dict__.items() if isinstance(value,Branch)} 
    def __getNumberDescendants__(self):
        return len(self.__getDescendants__().keys())

class Leaf(Branch):
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

    def __information__(self):
        """
        Causes __length__ data to be pulled from the server, if not already 
        available.  This can  fail, needs to be handled.
        """
        if self.__length__ is None:
            try:
                self.__length__ = int(self.__connection__.get('GETNCI({},"LENGTH")'.format(self.__fullpath__)))
            except mds.mdsExceptions.MDSplusException:
                print("Error: could not connect to the server")
                return "Leaf %s\n"%self.__path__
        return "Leaf %s : length of data: %d bytes\n"%(self.__path__,self.__length__)
    
    



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
        dimname = "dim_{}".format(ii) 
        coord = conn.get("DIM_OF({},{})".format(path,ii)).data()
        coord_units = conn.get("UNITS_OF(DIM_OF({},{}))".format(path,ii)).data()
        assert len(coord.shape) == 1, "Dimensions must be 1-dimensional"
        dims_dict[dimname] = ((dimname,),coord,{"units":coord_units})
    dims = list(dims_dict.keys())
    try:
        return xr.DataArray(data,dims=dims,coords=dims_dict,attrs={"units":units},
                            name = chop(leaf.__path__,depth=0)[-1])
    except:
        dims.reverse()
        return xr.DataArray(data,dims=dims,coords=dims_dict,attrs={"units":units},
                            name =  chop(leaf.__path__,depth=0)[-1])
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
        If 'list', returns a list of the DataArrays.

    Returns
    -------
    xarray.Dataset or xarray.DataArray or dct
        the collected data from this diagnostic

    """
    xrdct = {}
    if subset is None:
        subset = branch.__getDescendants__()
    for descendant in subset:
        descendant = str(descendant)
        obj= getattr(branch,descendant)
        if (type(obj) == Leaf) and (obj.__usage__ in usage_integers):
            data = obj.data
            xrdct[descendant] = data
    if behavior == 'concat':
        ndlxr = xr.concat(xrdct.values(),dim='channel')
        return ndlxr.assign_coords({'channel':np.array(list(xrdct.keys()))})
    elif behavior == 'merge':
        return xr.Dataset(xrdct)
    elif behavior == 'dump':
        return xrdct
    elif behavior == 'list':
        return list(xrdct.values())
    else:
        print("Invalid selection for 'behavior'.")
 

       