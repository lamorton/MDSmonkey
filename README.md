# MDSmonkey
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
to ~1 second, use the `dead_branches=True` option when calling `get_tree`.
The tree will now include branches whether or not they have any leaves that 
contain data -- this can be useful if you want to know about all the possible 
branches, whether or not they have data for a particular shot. The
 `dead_branches=True` option can also be helpful if you are using the `depth` 
 option to limit the depth of the tree.
 
The `noisy=True` option will print the tree as it goes: this can be helpful in
debugging, and is also reassuring if you are waiting a long time for the tree
to load when using the default `dead_branches=False` option, as it gives a
sense of progress.

The `strict=True` option will cause an error upon attempts to access a node's 
data in the case that the node cannot be properly loaded as an xarray object.
In the default `strict=False` case, this situation will instead lead yield a
dictionary that contains all the intputs that were used in the failed attempt
to build the xarray object -- this is useful for debugging or simply accessing
the data even if it is not formatted well.

There is a shortcut for loading only a subtree: use a tree name like:

    >diags = mm.get_tree("efit01.analysis",134020)
    
This can be handy when using `dead_branches=True` and looking at specific 
branches -- it is faster than looking at the full tree. Note that the naming 
convention for the tree string here looks exactly like the attribute-access
path to the resulting Python object (unless the MDSplus path includes colons.)
