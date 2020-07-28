#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
MDSmonkey helps the user explore a new (to the user) MDSplus database and read
the array-type data into xarray DataArray objects. See use example below to get
started. This assumes that you are set up to use the thick-client Python
interface to the MDSplus tree you want to access. MDSmonkey was designed and
tested to work on the NSTX / NSTX-U MDSplus installation.

Dependencies:
    django
    MDSplus
    xarray (optional but recommended)

Usage example to get started:
    >from MDSmonkey import MDSmonkey as mm
    >tree = mm.get_tree('efit01', 134020) #mdsplus tree type returned
    >tree  #hit <Return> to print attribute list, or tab-complete in ipython
     name: subnodes
     analysis: 3
     raw_data: 2
     tags: 103 #special branch to separate out the tags so you aren't overwhelmed
    >tree.analysis
     flux: Data (length=1000)
     current: Data (length=2500)
     q_on_axis: Data (length=5000)
    >flux = tree.analysis.flux.data #Now you will receive an xarray data-array
    >flux #return to print, will show array dimensions & names & units.
          #If xarray is not installed, these will instead be branches
          
Note that getting the tree may take a few minutes, due to the ~20ms it takes to
determine whether data resides at a node.  If you want to accelerate the loading
to ~1 second, use the 'dead_branches=True' option when calling 'get_tree'.
The tree will now include branches whether or not they have any leaves that 
contain data -- this can be useful if you want to know about all the possible 
branches, whether or not they have data for a particular shot. The
 'dead_branches=True' option can also be helpful if you are using the 'depth' 
 option to limit the depth of the tree.
 
The "noisy=True" option will print the tree as it goes: this can be helpful in
debugging, and is also reassuring if you are waiting a long time for the tree
to load when using the default "dead_branches=False" option, as it gives a
sense of progress.

The "strict=True" option will cause an error upon attempts to access a node's 
data in the case that the node cannot be properly loaded as an xarray object.
In the default "strict=False" case, this situation will instead lead yield a
dictionary that contains all the intputs that were used in the failed attempt
to build the xarray object -- this is useful for debugging or simply accessing
the data even if it is not formatted well.

There is a shortcut for loading only a subtree: use a 'tree' name like:
>diags = mm.get_tree("efit01.analysis",134020)
This can be handy when using 'dead_branches=True' and looking at specific 
branches -- it is faster than looking at the full tree. Note that the naming 
convention for the 'tree' string here looks exactly like the attribute-access
path to the resulting Python object (unless the MDSplus path includes colons.)
"""
from django.utils.functional import cached_property
import MDSplus as mds
try:
    import xarray as xr
except Exception as ex:
    print(ex)#If xarray is not available, this whole thing still basically works!

def get_tree(treename,shotnum,**kwargs):
    """
    Get the 'monkey' version of the MDS tree, which enables easy exploration.
    Arguments:
        treename: a string naming a tree (eg, 'efit01')
        shotnum: an integer shot number (eg, 134020)
    Optional arguments:
        Any optional arguments are passed directly to traverseTree, so see that
        function for details.
    Returns:
        a nested Branch-type object (see traverseTree for more info)
    """
    if '.' in treename:
        treename, start_node = treename.split('.',maxsplit=1)
        tree = mds.Tree(treename,shotnum)
        mdsnode = tree.getNode(start_node)
    else:
        tree = mds.Tree(treename,shotnum)
        mdsnode = tree.getNode("\\TOP")
    return traverseTree(mdsnode,**kwargs)

def get_mds_shortname(node):
    """
    Get the last portion of the full name of a node (eg, if the full name
    is '\efit01::top.analysis.geqdsk' then the shortname is 'geqdsk').
    Arguments:
        node: an mds.treenode.TreeNode type object
    Returns:
        the short name of the node, as a string
    """
    return str(node.getNodeName()).lower() 

def get_mds_fullname(node):
    """
    Get the full path name of an mds.treenode.TreeNode object as a lowercase 
    string (eg, '\efit01::top.analysis.geqdsk').
    """
    return str(node.getFullPath()).lower()

def get_mds_node_tags(node):
    """
    Get a list of the tag names (lowercase) that refer to an 
    mds.treenode.TreeNode object (eg, '\efit01::top.analysis.geqdsk.psirz' has
    tags ['psirz'].
    """
    return [tag.lower() for tag in node.getTags()]

def get_mds_tree_tags(tree,wildcard=''):
    """
    Get a dictionary of all tags & nodes objects that they refer to in a tree.
    Arguments:
        tree: an mds.tree.Tree type object
    Optional arguments:
        wildcard: a string to match the tags against. If the string appears
                  anywhere in the tag, the tag is returned. The null string
                  matches everything.
    Returns:
        a dictionary whose keys are the lowercase strings (tags) and whose 
        values are the mds.treenode.TreeNode objects that the tags refer to.
        (eg, {'\\efit01::psirz':\\EFIT01::TOP.ANALYSIS.PSIRZ, ...}).
    
    Notes:
        This is essentially a 'flattened' version of the tree, with the caveat 
        that there may exist >1 tag that aliases to the same node. The tags
        must be unique in the dictionary, however.
    """
    return {tag.lower():tree.getNode(tag) for tag in tree.findTags(wildcard)}

def get_mds_members(node):
    """
    Get a dictionary containing the mds.treenode.TreeNode objects as values
    associated to their shortnames as keys, for each 'member' of a given 
    mds.treenode.TreeNode object.
    """
    members=node.getMembers()
    return {get_mds_shortname(member):member for member in members}


def get_mds_children(node):
    """
    Get a dictionary containing the mds.treenode.TreeNode objects as values
    associated to their shortnames as keys, for each 'child' of a given 
    mds.treenode.TreeNode object.
    """
    children=node.getChildren()
    return {get_mds_shortname(child):child for child in children}

#TODO: sometimes people use arrays to put text in.  Try to filter this out.
def get_mds_shape(node):
    """
    Given an mds treenode, return a list containing the length of each 
    dimension of the array that resides at that node.  If there is no array, or
    the array is zero-dimensional, the list will have no entries.
    """
    try: 
            #This will fail if node.getShape doesn't exist or if shape is 0
            shape=list(node.getShape())
            assert len(shape)>0
    except (mds.mdsExceptions.MDSplusException,AssertionError):
            return []
    shape.reverse() #put in the python order
    return shape 

def get_mds_length(node): 
    """
    Get the length of the data record for the mds.treenode.TreeNode.  This is
    useful for determining whether a node has data stored. It runs about
    4-5x faster than get_mds_shape, so I've started using it as an alternative
    for characterizing the 'dead branches'. 
    
    Note that ANY MDSplus exception -- including not being able to reach the 
    tree, bad syntax, etc -- will cause this to evaluate to zero. Make sure
    that the node actually exists in the tree before using this function.
    """
    try:
        length = node.getLength()
    except (mds.mdsExceptions.MDSplusException):
        return 0
    return length

def get_mds_dimension_names(node):
    """
    Get a list the names of the dimensions of an mds.treenode.TreeNode that  
    has an associated data array.  Complements the function get_mds_shape,
    which only gets the length of the dimensions. 
    """
    ndims=len(get_mds_shape(node))
    dimension_names=[]
    for i in range(ndims):
        dimension=node.dim_of(i)
        try:
            name=get_mds_shortname(get_mds_node_reference(dimension))
            if len(get_mds_shape(dimension))>1:
                name=name+"_index"
        except:
            name="dim%d"%i
        dimension_names.append(name)
    return dimension_names

from collections import OrderedDict
def get_mds_axis(obj,index,strict=True):
    """
    Get the coordinate axis as an mdstreenode object or die trying.
    Formulated because sometimes the axis is wrapped up inside a 
    compound.Dimension type object.
    """
    ax=obj.dim_of(index)
    if type(ax)!=mds.treenode.TreeNode:
        try:
            ax=ax.getAxis()
        except:
            if strict:
               raise Exception("Axis %s is not a treenode"%(ax))
    return ax

def get_mds_node_reference(obj):
    """
    Adapted from similarly-named routine in mdsdata.py
    Basically, the idea is to be able to get out of this pickle where I am in a
    function and I have a pure data-type object out of context of its dimensions
    so I need to go back to the tree and find them.
    """
    if type(obj)==mds.treenode.TreeNode:
        return obj
    elif isinstance(obj,mds.compound.Compound) and hasattr(obj,'args'): #This is how compound.hasNodeReference works
        for arg in obj.args:
            node_ref=get_mds_node_reference(arg)
            if not node_ref is None:
                return node_ref
    elif hasattr(obj,'getDescs') and isinstance(obj,mds.apd.Apd):
        for arg in obj.getDescs():
            node_ref = get_mds_node_reference(arg)
            if node_ref is not None:
                return node_ref
    return None

def get_mds_units(node):
    """
    Get the units of a node, as a string. Unlike the get_mds_***name methods,
    does NOT convert to lowercase because metric prefixes have different
    meaning in different cases. If no units are available, the string "-" is
    returned. The data's author, however, may not use this convention, and may
    instead opt to insert his own symbol rather than leaving the field undefined.
    """
    try:
        units=str(node.units)
    except:
        units=node.units_of()
    if not type(units)==type(""):
        try:
            units=units.value_of()
        except:
            units="-"
    return units

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
    def __init__(self,mdsnode,strict=False,length=None):
        """
        mdsnode should be of type mds.treenode.TreeNode
        """
        self.__strict__ = strict
        self.__mdsnode__ = mdsnode
        self.length = length
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
        return getXarray(self.__mdsnode__,strict=self.__strict__)

    def __repr__(self):
        if self.length is None:
            self.length = get_mds_length(self.__mdsnode__)
        return "Data (length = %d)"%self.length
    
class Branch(object):
    """
    Dummy class whose only real function is to look nice and keep track of 
    references to mds.treenode.Treenode objects. A Branch object only has other
    Branch or Leaf objects as attributes, but no data.
    """
    def __init__(self,mdsnode):
        self.__mdsnode__=mdsnode
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

#Inspired by mdsplus.org example:
#http://www.mdsplus.org/index.php?title=Documentation:Tutorial:MdsObjects&open=38101832318169843162415089&page=Documentation%2FThe+MDSplus+tutorial%2FThe+Object+Oriented+interface+of+MDSPlus

#TODO: have a look at the MDSplus interface in OMFIT; there is evidently a way
     #to get the tree structure in one TCL call, but you need to use thin-client mode
def traverseTree(mdsnode,dead_branches=False,depth=float('Nan'),current_depth=0,noisy=False,strict=False,tags=False):
    """
    Climb up an MDSplus tree and create a pretty python representation that stores
    the node references as hidden attributes of each leaf/branch, and the child
    leaf/branch objects as explicit attributes.
    Arguments:
        node: the mds Tree instance you want to use.  it should be open! It may
              also be a TreeNode instance, so that one need not traverse the 
              whole tree just to get a particular branch's leafs.
    Options:
        dead_branches: if True, show branches that do not end in array-types
        depth:  limit the depth into the tree by setting a positive integer
        noisy:  see the print-out of the tree as it unfolds, if True
        strict: if True, set the leafs of the tree to cause an error if the 
                xarray type object cannot be built correctly, rather 
                than returning a non-xarray type object
        tags: if False, put hide the 'tags' as attributes in a special branch
              called 'tags'.  If True, put the tags right into the returned
              Branch object for easier access, but a messy namespace.
    Returns:
        a nested Branch object.  Each branch has an attribute '__mdsnode__' 
        which of type mds.treenode.TreeNode, along with a set of Branch-type 
        attributes or a set of Leaf-type attributes, but not a mixed set. 
    """
    tagdict={}
        
    name = get_mds_shortname(mdsnode)  
    me = Branch(mdsnode)#put node information here if you like
    if noisy: print ("    "*current_depth + name)

    #Members are data/signals, put them directly the current Node object
    #if they are arrays
    if mdsnode.getNumMembers()>0:
        leaves=mdsnode.getMembers()
        for leaf in leaves:
            leafname=get_mds_shortname(leaf)
            if not dead_branches: #Check the data length, don't put empty Leafs in the tree
                leaf_length =  get_mds_length(leaf)
                if leaf_length > 0:
                    setattr(me,leafname,Leaf(leaf,strict,length=leaf_length)) #Use the pre-computed data length when constructing the Leaf to save time later
                    tagdict[leafname]=getattr(me,leafname)
                    if noisy: 
                        print ("    "*(current_depth+1) + leafname + ": %d"%leaf_length)
            else: #We don't know if the node has data.  This is fast to load, but it wastes the user's time going down dead-end branches
                setattr(me,leafname,Leaf(leaf,strict)) #Can't supply 'length' to Leaf b/c we're not asking for it, to save time
                tagdict[leafname]=getattr(me,leafname)
                if noisy: 
                    print("    "*(current_depth+1) + leafname)
    #Children contain no immediate data, just links to more nodes.  If depth is
    #not beyond limit, go down these 'branches' and add contents to the current
    #Node object
    if not depth <= current_depth and mdsnode.getNumChildren()>0:
        branches = mdsnode.getChildren()
        for b in branches:
            subname,subnode,subtags=traverseTree(b, dead_branches,depth,current_depth+1,noisy,strict)
            if len(subnode.__getDescendants__())>0:
                setattr(me,subname,subnode)
                tagdict[subname]=getattr(me,subname)
                for k,v in subtags.items(): #merge tags in
                    tagdict[k]=v
                    
    if current_depth==0:#we are done, returning to user
        if tags:    
            for tag,obj in tagdict.items():
                 setattr(me,tag,obj)
        else:
            tagbranch=Branch(mdsnode)
            for tag,obj in tagdict.items():
                 setattr(tagbranch,tag,obj)
            setattr(me,'tags',tagbranch)    
        return me
    return (name, me,tagdict) #else, we are still recursing back down the tree

#############################################################################
## This is the real workhorse that collects all the scattered dimension info
##There are several different ways that the coordinates/axes/dimensions can be
##set up, not only in terms of the mds tree structure but because it is possible
## to have a 'dimension' which itself has more than one actual dimension/axis
##which requires special handling (recursively!)/
#TODO: simplify by either changing the MDSplus implementation to be more uniform or
       #by going directly to the mds.TdiExecute method to bypass the interface
       #the reference for how to get even 'secret' attributes is located at
       #treenode.py in 'def __getattr__()'  The big list of attributes can all
       #be accessed by the following form:
       #conn.get(r'getnci(\psirz,"node_name")) 
       #where conn=mds.Connection('skylark.pppl.gov:8501::')
       #and conn.openTree('efit01',134020) has been run.       
def getXarray(node,noisy=False, strict=False):
    """
    Create an xarray.DataArray based on the data, dimensions & units of a node.
    If that fails, return a Branch object containing those things instead.
    Arguments:
        node: an mds.treenode.Treenode.  It might even work if you directly 
              supply an mds.compound.Signal or whatnot, but no guarrantees.
    Optional Arguments:
         noisy: default False.  If True, print debugging information.
         strict: default False.  If True, raise an exception instead of
                 returning a Branch object, in the event that it is not 
                 possible to put the data & dimensions into a DataArray.
    Returns:
        either an xarray.DataArray, or else if strict=False and the creation
        of a DataArray fails, a Branch-type object. In either event, the object
        will have the following attributes:
            data: a numpy array that contains the data
            dims: a list/tuple of strings naming the dimensions of 'data'
            coords: a dictionary whose keys are coordinate names and whose
                    values are tuples. The first element of the tuple is a 
                    tuple which names the dimensions that apply to the coord
                    and the second element is the numpy array giving the coord.
                    The third element is the units.

    """
    #assert type(node)==mds.treenode.TreeNode
    data=node.data()
    node_shape=get_mds_shape(node)
    naxes=len(node_shape)
    own_name=get_mds_shortname(node)
    coordinates=OrderedDict()        
    units =get_mds_units(node)
    dimension_names=[]
    if noisy:  print("Main body: node %s has shape %s"%(own_name,node_shape))
    for i in range(naxes):
        ax=node.dim_of(i)
        ax_dims=len(get_mds_shape(ax))#do we have a coordinate or a simple dimension?
        if noisy: print( "doing axis # %d: shape=%s"%(i,get_mds_shape(ax)))
        if ax_dims==1:
            if noisy: print( "   inside dims==1")
            try:
                name=get_mds_shortname(get_mds_node_reference(ax))
            except:
                name="dim%d"%i
                #don't assign a coordinate, because it is presumably just an index if it doesn't have a node reference
            coordinates[name]=((name,),ax.data(),{"units":get_mds_units(ax)}) #only give it a coordinate if it might be interesting
            dimension_names.append(name)
        elif ax_dims>1:
            if noisy: print( "  inside dims>1")
            #time for recursion! Look out!
            coord = getXarray(get_mds_node_reference(ax),noisy=noisy)
            coord_dim_names=set(coord.dims)
            #This is a bit tricky, because the name of the present dimension
            #gets defined by this call.  So we need to extract that name and
            #place it in the running list of dimensions for 'node':
            unique_dim_names=list(coord_dim_names.difference(set(dimension_names)))
            if len(unique_dim_names)>1:
                raise Exception("Coordinate #%d of node %s has %d>1 new dimensions, which is not allowed"%(i,own_name,len(unique_dim_names)))
            name=get_mds_shortname(get_mds_node_reference(ax))#This thing had better have a name!!!!
            coordinates[name]=((name,),coord,{"units":get_mds_units(ax)}) #refer to the coordinate by its proper name
            dimension_names.append(unique_dim_names[0]) #refer to the dimension that parameterizes this coordinate by whatever name it recieved in the recursive call, assuming that the unique dimension name defined there corresponds to the present dimension of the base array
        else:#zero-dimensional coordinate means index
            name="dim%d"%i
            dimension_names.append(name)
    try:
        return xr.DataArray(data,coords=coordinates, dims=dimension_names,attrs={'units':units},name=own_name) 
    except:
        pass
    dimension_names.reverse()
    try:
        return xr.DataArray(data,coords=coordinates, dims=dimension_names,attrs={'units':units},name=own_name)  
    except Exception as ex:#IF something goes wrong, you will at least get the inputs!
        if not strict:
            #print "WARNING: returning non-xarray object due to error in coordinates."
            dummy= Branch(node)
            dummy.dims=dimension_names
            dummy.coords=coordinates
            dummy.units=units
            dummy.node_ref=node
            dummy.data=data
            return dummy
        else:
            raise ex
#TODO: make the naming scheme mappable (ie, allow substitution)

def _diagnostic2xarray(node,names={},reverse_order=None,debug=False,noisy=False):
    """
    #Perhaps this can be revived in the future, but I'm not working on it right
    now. The function 'getAxes' morphed into 'getXarray' so this function 
    currently does not work. I'm leaving it here as an inspiration.#
    
    General method for grabbing MDSplus data from a diagnostic node or EFIT tree.
    Do not recommend using this for downloading other whole trees.
    Arguments:
        node:active MDS node object 
        names: list of names to grab.  If empty, get everything available
        reverse_order: if for some reason you get shape errors, try setting
                       this to 'True' or 'False'
        debug: if you still can't figure out the shape errors, setting this
               to 'True' will give you the raw material being shoehorned into
               xr.Dataset.  Run each dictionary through explore_xr_input
               to see what's happening.
    #TODO: allow dictionary of names, and use them to substitute for the defaults
    #TODO: allow a pattern or set of patterns to be string-matched, to help
           narrow down the number of signals in the case that a full tree is 
           supplied.
    #TODO: figure out if node is a leaf and specialize on that to produce just
           a data-array instead of whole dataset.
    """
    #Here's the deal: some trees seem to opposite conventions when it comes to
    #order of indices, ie: if you call node.dim_of(n) with i=0,j=1,k=2, you get 
    #dimensions to array[j,k,i] sometimes, but other times you get array[i,j,k]
    #EFIT trees seem to use normal order, others do not, but you may need to
    #adjust this
    raise Exception("This function is not yet operational.")
    if reverse_order is None:
        if 'efit' in str(node).lower():
            reverse_order=False
        else:
            reverse_order=True
    
    if type(node)==mds.Tree:
        #assuming we are dealing with EFIT tree where the variables are all
        #stored as tags and the tree just contains processing info
        members=[node.getNode(tag) for tag in node.findTags('') if not '::TOP' in tag]
    else:
        members = node.getMembers()#get list all the nodes for the diagnostic
        
    #If user supplies list/tuple/array of names, select only those names
    test_names = len(names) > 0
    
    #Sort the members into either coordinates or data arrays (ignore the rest)
    coord_objs=[]
    data_objs=[]
    other_objs=[]
    for member in members:
        try:
            #I'm getting a non-deterministic error here on EFITS, when the call
            #to member.getShape() sometimes causes a TDIException that escapes
            #the 'try' clause somehow!  
            naxes=len(member.getShape())
            assert naxes >0
        except:
            other_objs.append(member)
            continue #if it doesn't have a shape, or if there are no dimensions, it's not an array, so skip it
        axes_types = [type(member.dim_of(i)) for i in range(naxes)]
        if mds.compound.Range in axes_types:
            coord_objs.append(member)
        else:
            data_objs.append(member)
    if len(other_objs) >0 and noisy:
        print ("Warning: the following nodes were not used: %s"%other_objs)        
    #Assemble the desired data arrays together with their dimension names to 
    #prepare for insertion into an xr.Dataset object
    dvars={}
    labels={}
    units={}
    used_coordinates=set()
    for member in data_objs:   
        name=get_mds_shortname(member)
        if not test_names or name in names:             
            axes=getAxes(member,strict=True)
            if reverse_order: 
                axes.reverse()
            axes_names=[get_mds_shortname(ax) for ax in axes]
            axes_shape_strings=[str(ax.getShape())[1:-1] for ax in axes]
            shapestring=str(member.getShape())
            if not all([axes_shape in shapestring for axes_shape in axes_shape_strings]) and noisy:
                print("Warning: Shape mismatch: %s has shape %s, but dimensions %s have shapes %s"%(member,shapestring,axes_names,axes_shape_strings))
                continue
            units[name]=member.units_of()
            dvars[name]=axes_names, member.data() 
            for ax in axes_names:
                used_coordinates.add(ax)
    if noisy:
        unused_names=set(names).difference(set(dvars.keys()))
        if len(unused_names)>0:
            print("Warning: these requested names were not found: %s"%unused_names)

    #figure out which of the coordinates we need/have, and add them under the right name
    coords={}
    for member in coord_objs:
        name=get_mds_shortname(member)
        if name in used_coordinates:
            naxes=len(member.getShape())
            axes_names=[]
            if naxes==1:
                axes_names=[name]
            else:
                looper =range(naxes)
                if reverse_order:
                    looper.reverse()
                for i in looper:
                    ax_obj=get_mds_axis(member,i,strict=False)
                    if not isinstance(ax_obj,mds.treenode.TreeNode):
                        axes_names.append("dim%d"%i)
                    else:
                        axes_names.append(get_mds_shortname(ax_obj))
            coords[name]=axes_names,member.data()
    #protocol for metadata seems to be something like this:
    #valid=member_dict['valid']
    #valid_remark = valid.getMember().value_of()        
    if debug: 
        return dvars,coords,labels,units
    return xr.Dataset(dvars,coords=coords,attrs={'labels':labels,'units':units})


def nodedict2xarraydict(nodedict):
    """
    Turn all the leaves of a tree into a list of xarray data arrays. Use this
    with the dictionaries returned from get_mds_tree_tags or get_mds_children
    to approximate the functionality of traverseTree, except that here you are
    explicitly loading all the data from the tree into xarrays at the time you
    call this function.  This might be slow.
    """
    return {name:getXarray(node) for name,node in nodedict.items()}


def explore_shapes(node):
    """
    Examine the shapes of the data and coordinate arrays associated with an
    mds.treenode.Treenode object.
    """
    nodeshape=node.getShape()
    print( "shape: ",nodeshape)
    for i in range(len(nodeshape)):
        axis=get_mds_axis(node,i,strict=False)
        try:
            print( axis.getNodeName(),axis.getShape())
        except:
            print("blank: ",axis.getShape())