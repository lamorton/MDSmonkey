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

Useage example to get started:
    >from MDSmonkey import MDSmonkey as mm
    >tree = mm.get_tree('efit01', 134020) #mdsplus tree type returned
    >tree  #hit <Return> to print attribute list, or tab-complete in ipython
     name: number of sub-branches 
     analysis: 3
     raw_data: 2
     tags: 103 #special branch to separate out the tags so you aren't overwhelmed
     help        #no sub-branches
    >tree.analysis
     flux: (time: 20, z: 50, r: 30)
     current: (time: 20, z: 50, r: 30)
     q_on_axis: (time: 20)
    >flux = tree.analysis.flux.data #Now you will receive an xarray data-array
    >flux #return to print, will show array dimensions & names & units.
          #If xarray is not installed, these will instead be branches
