#! /usr/bin/env /usr/bin/python3

'''
@file msom.py
@author Scott L. Williams
@package POLI
@brief Self organizing map POLI operator using Minisom.
@LICENSE
#
#  Copyright (C) 2020-2022 Scott L. Williams.
# 
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
'''
msom_copyright = 'msom.py Copyright (c) 2020-2022 Scott L. Williams, released under GNU GPL V3.0'

# self organizing map poli operator using minisom

import wx
import os
import sys
import math
import getopt
import datetime
import numpy as np

from minisom import MiniSom, _build_iteration_indexes
from op_panel import op_panel

# return an instance of 'msom' class 
# without having to know its name
def instantiate():	
    return msom( get_name() )

def get_name(): 
    return 'msom'

def const_decay( learning_rate, t, max_iter ):
    return 1 - 0.95*t/max_iter

def exp_decay( learning_rate, t, max_iter ):
    # review: why 16?
    return learning_rate * math.exp( -t/(max_iter/math.log(16)) )

def inv_decay( learning_rate, t, max_iter ):
    # 
    return learning_rate/(1+100*t/max_iter)

def linear_decay( learning_rate, t, max_iter ):
    return learning_rate*(1-t/max_iter)

def power_decay( learning_rate, t, max_iter ):
    return learning_rate*(0.005/learning_rate)**(t/max_iter)
                 
class msom_parameters():             # hold arguments values here
    def __init__( self ):

        self.shape = (4,4)           # nodal topology

        self.sigma = 2.0             # spread of the neighborhood function,
                                     # needs to be adequate to the dimensions
                                     # of the map. (at the iteration t we have
                                     # sigma(t) = sigma / (1 + t/T)
                                     # where T is num_iteration/2)

        self.nepochs = 2             # number of full data set to sample

        self.rate =  0.1             # initial learning rate (at the
                                     # iteration t we have
                                     # learning_rate(t) = learning_rate / (1 + t/T)
                                     # where T is #num_iteration/2
       
        self.init_weights = 'random' # initiate training with random or pca weights
                                     # use 'random' or pca'

        self.neighborhood_function = 'gaussian'
                                     # function that weights the neighborhood of a
                                     # position in the map.
                                     # possible values: 'gaussian', 'mexican_hat',
                                     # 'bubble', 'triangle'

        self.topology = 'rectangular'
                                     # topology of the map.
                                     # possible values: 'rectangular', 'hexagonal'

        self.activation_distance = 'euclidean'
                                     # distance used to activate the map.
                                     # possible values:
                                     # 'euclidean', 'cosine', 'manhattan', 'chebyshev'
        self.output_type = 'labels'  # image output type: 'labels' or 'quantize'

        # map file path prefix, a suffix is added 
        # for quantized and labels outputs later
        self.mapfile_prefix = 'msom_weights'

        # apply classifications to dataset?
        self.apply_classification = True
        self.activation_map = False   # reports number of pixels in a class and
                                      # writes out activation map
        self.actmapfile_prefix = 'actmap'
        
        self.seed = None              # generate seed for None,
                                      # otherwise use value.
        self.rorder = True            # use random sampling

        self.custom_initfile = None   # neuron weight initialization file

        self.decay_function = 0       # 0 = asymptotic (default)
                                      # 1 = constant
                                      # 2 = exponential
                                      # 3 = inverse
                                      # 4 = linear
                                      # 5 = power

        self.show_progress = True
        self.calc_epoch_errors = False    # calculate QE and TE after each epoch
        
        # TODO: update GUI panel on new parameters
        
    def print_params( self, nfile=sys.stderr ):

        # TODO: put source image name and date
        # image name is more difficult as we would have to keep track of
        # original source file and filter applications (with params).
        # .. is doable
        print( 'timestamp=               ', datetime.datetime.now().isoformat(),
               file=nfile )
        print( 'shape=                   ', self.shape, file=nfile )
        print( 'sigma=                   ', self.sigma,file=nfile )
        print( 'nepochs=                 ', self.nepochs,file=nfile )
        print( 'rate=                    ', self.rate,file=nfile )
        print( 'neighborhood function=   ', self.neighborhood_function, file=nfile )
        print( 'init weights=            ', self.init_weights, file=nfile )
        print( 'topology=                ', self.topology, file=nfile )
        print( 'activation distance=     ', self.activation_distance, file=nfile )
        print( 'output type=             ', self.output_type, file=nfile )
        print( 'mapfile_prefix=          ', self.mapfile_prefix, file=nfile )
        print( 'apply classification=    ', self.apply_classification, file=nfile )
        print( 'activation map=          ', self.activation_map, file=nfile )
        print( 'activation map_prefix=   ', self.actmapfile_prefix, file=nfile )
        print( 'seed=                    ', self.seed, file=nfile )
        print( 'random order=            ', self.rorder, file=nfile )
        print( 'custom init file=        ', self.custom_initfile, file=nfile )
        print( 'decay function=          ', self.decay_function, file=nfile )
        print( 'show progress=           ', self.show_progress, file=nfile )
        print( 'calc epoch errors=       ', self.calc_epoch_errors, file=nfile )
               
class msom( op_panel ):
    def __init__( self, name ):      # initialize op_panel but no graphics
        op_panel.__init__( self, name )
        self.op_id = 'msom version 0.0'
        self.params = msom_parameters()
    
    # write settings and neuron weights to file
    def writefile( self, QE, TE, weights, actmap ):

        ny, nx, ndim = weights.shape

        if isinstance( actmap, np.ndarray ):
            # check if arrays match up
            if ny != actmap.shape[0] or nx != actmap.shape[1]:
                print( 'msom: weight and active map shapes do not match...exiting',
                       file=sys.stderr, flush=True )
                sys.exit( 2 )

        try:
            nfile = open( self.params.mapfile_prefix + '.labels', 'w' ) 
            self.params.print_params( nfile )

            nfile.write( '\nquantization error=       %.8f\n'%QE )
            nfile.write( 'topographic error=        %.8f\n'%TE )
            
            # flag for reading later
            nfile.write( '\n############ NEURONS #############\n' )
            
            # report number of neurons and dimensionality                
            nfile.write( '%3i'%(ny*nx) + ' %3i'%ndim + '\n' )

            # report class weights and number of pixels in the class
            label = 0
            for j in range( ny ):
                for i in range( nx ):
                    
                    # grey level (class label) used
                    nfile.write( '%3i'%label + ' ' )  
                    for k in range( ndim ):
                        nfile.write(  '%10.6f'%weights[j,i,k] + ' ' )
                    
                    if isinstance( actmap, np.ndarray ):
                        # report number of pixels in class
                        nfile.write( '%3i\n'%actmap[j,i] )
                    else:
                        nfile.write( '\n' )
                        
                    label += 1
            nfile.close()

            # write out activation map
            if isinstance( actmap, np.ndarray ):
                actmap.dump( self.params.activation_map_prefix + '.npy' )
            
        except IOError:
            print( 'writefile: IOError', file=sys.stderr )

    # match image sample to closest map weights
    def classify( self, weights, image ):

        height,width,nbands = image.shape
        
        # flatten weights for label indexing
        neurons = np.reshape( weights,
                              (weights.shape[0]*weights.shape[1],
                               weights.shape[2]) )

        num_neurons,nnbands = neurons.shape
        height,width,nbands = image.shape

        if nnbands != nbands:
            print('somclass: dimensions do not match',
                  nnbands, nbands, file=sys.stderr )
            return None

        # set up arrays
        min = np.empty( (height,width,1), dtype=np.float32 )
        new = np.empty( (height,width,1), dtype=np.float32 )

        # initialize to the zeroth neuron
        classified = np.zeros( (height,width,1), dtype=np.uint8 )

        diff = image-neurons[0]        # initialize min array
        diff = np.abs( diff )          # using no-square euclid metric
        min = np.sum( diff, axis=2 )   # TODO: determine metric and use

        for i in range( 1,num_neurons ):    # test each neuron.
            diff = image-neurons[i]         # keep track of minimal distances
            diff = np.abs( diff )           # and compare/adjust with each 
            new = np.sum( diff, axis=2 )    # new distance array

            mask = min > new

            np.putmask( min, mask, new )       # use same mask to
            np.putmask( classified, mask, i  ) # keep track of class

        return classified

    def init_SOM( self, nbands ) :
        
        if self.params.decay_function == 0:

            # use default decay_function
            print( 'using default asymptotic decay function', file=sys.stderr, flush=True )
            som = MiniSom( self.params.shape[1], self.params.shape[0],
                           nbands, sigma=self.params.sigma,
                           neighborhood_function=self.params.neighborhood_function,
                           activation_distance=self.params.activation_distance,
                           learning_rate=self.params.rate,
                           random_seed=self.params.seed )

        else:
            if self.params.decay_function == 1:
                print( 'using constant decay function',
                       file=sys.stderr, flush=True )
                decay_function = const_decay
            elif self.params.decay_function == 2:
                print( 'using exponential decay function',
                       file=sys.stderr, flush=True )
                decay_function = exp_decay
            elif self.params.decay_function == 3:
                print( 'using inverse decay function',
                       file=sys.stderr, flush=True )
                decay_function = inv_decay
            elif self.params.decay_function == 4:
                print( 'using linear decay function',
                       file=sys.stderr, flush=True )
                decay_function = linear_decay
            elif self.params.decay_function == 5:
                print( 'using power decay function',
                       file=sys.stderr, flush=True )
                decay_function = power_decay
            else:

                raise ValueError( 'msom: unknown decay function' )

            som = MiniSom( self.params.shape[1], self.params.shape[0],
                           nbands, sigma=self.params.sigma,
                           neighborhood_function=self.params.neighborhood_function,
                           activation_distance=self.params.activation_distance,
                           learning_rate=self.params.rate,
                           random_seed=self.params.seed,
                           decay_function=decay_function )

        return som

    # initialize the neuron weights
    def init_weights( self, som, pixels ):
        
        if self.params.init_weights == 'random':
            
            print( 'random initializing neuron weights...',
                   end='',file=sys.stderr, flush=True )
            som.random_weights_init( pixels )
            
        elif self.params.init_weights == 'pca':
            
            print( 'pca initializing neuron weights...',
                   end='',file=sys.stderr, flush=True )
            som.pca_weights_init( pixels )
            
        elif self.params.init_weights == 'custom':
        
            print( 'custom initializing neuron weights...',
                   end='',file=sys.stderr, flush=True )

            # read custom weight file
            wfile = open( self.params.custom_initfile, 'r' ) 

            # look for flag
            found = False
            for line in wfile:
                if line.find( 'NEURONS' ) != -1:
                    found = True
                    break
                
            if not found:
                print( 'msom: could not find flag', file=sys.stderr )
                sys.exit(2)
                
            nneurons,ndims = wfile.readline().split()
            nneurons = int( nneurons )
            ndims = int( ndims )

            # read weights into a 2d data array
            data = []
            for i in range( nneurons ):
                
                # read and load the weights into 'data'
                line = wfile.readline().split()
                data.append([])
                for j in range( 1, ndims+1 ):       # skip grey level label and size
                    data[i].append( float( line[j] ) )

            it = np.nditer(som._activation_map, flags=['multi_index'])
            i=0 
            while not it.finished:
                som._weights[it.multi_index] = data[i]
                it.iternext()
                i += 1
        else:
            raise ValueError( "msom: unknown weight initialization." )

        print( 'done', file=sys.stderr, flush=True )

    # train using epoch intervals
    def epoch_train( self, som, data, nepochs, rorder, show_progress ):
        
        ndata = len( data )           # number of data points
        nsamples = nepochs*ndata      # number of total sample points (iterations)
        
        random_generator = None                                                              
        if rorder == True:                                                                   
            random_generator = som._random_generator

        # force som to consider the full data set in epoch steps.
        # this allows all data points to be sampled first before
        # considering another pass (epoch) on the data
        for epoch in range( nepochs ):

            print( '\nepoch =', epoch, file=sys.stderr, flush=True )
            iterations = _build_iteration_indexes( ndata, ndata, 
                                                   show_progress, random_generator )
        
            for t, iteration in enumerate( iterations ):
                som.update( data[iteration], som.winner( data[iteration] ),
                            ndata*epoch + t, nsamples )
                
            # if calculating epoch QE don't do last one
            if self.params.calc_epoch_errors and epoch < nepochs-1:
                QE = som.quantization_error( data )
                print( '\nQE=', QE, file=sys.stderr, flush=True )
                TE = som.topographic_error( data )
                print( 'TE=', TE, file=sys.stderr, flush=True )

        print( '\ncalculating quantization error...', file=sys.stderr, end='', flush=True )
        QE = som.quantization_error( data )
        print( 'done.', file=sys.stderr, flush=True )
        print( 'quantization error=', QE, file=sys.stderr,  flush=True )

        print( '\ncalculating topographic error....', file=sys.stderr, end='', flush=True )
        TE = som.topographic_error( data ) 
        print( 'done.', file=sys.stderr, flush=True )
        print( 'topographic error=', TE, '\n', file=sys.stderr,  flush=True )

        return QE, TE

    def run( self ):                 # override superclass run      
     
        # flatten the input image; just a stream of pixels with n-bands
        shape = self.source.shape
        npix = shape[0]*shape[1]
        pixels = np.reshape( self.source, (npix, shape[2]) )

        # instantiate minisom
        som = self.init_SOM( shape[2] )
        
        # initialize the neuron weights
        self.init_weights( som, pixels )
        
        # cluster (train) the image data, return quantization and topographic errors
        QE, TE = self.epoch_train( som, pixels, self.params.nepochs,
                                   self.params.rorder, self.params.show_progress )

        # get trained neuron weights and write to file
        print( 'getting weights...', file=sys.stderr, end='', flush=True )
        weights = som.get_weights()
        print( 'done', file=sys.stderr, flush=True )

        actmap = None
        if self.params.activation_map == True:
            print( 'getting pixel class frequency...',
                   file=sys.stderr, end='', flush=True )
            actmap = som.activation_response( pixels )
            print( 'done', file=sys.stderr, flush=True )

        # write parameter values and class weights to file
        self.writefile( QE, TE, weights, actmap )

        if self.params.apply_classification == False:
            return
        
        if self.params.output_type == 'labels' :

            # classify the image with index labels 
            print( 'labeling...', end='', file=sys.stderr, flush=True )
            self.sink = self.classify( weights, self.source )
            print( 'done', file=sys.stderr )
            
        elif self.params.output_type == 'quantize' :
            
            print( 'quantization...', end='', file=sys.stderr, flush=True )
            qnt = som.quantization( pixels )  # quantize each pixel of the image

            # place the quantized values into a new image
            self.sink = np.zeros( self.source.shape, dtype=pixels.dtype )
            for i, q in enumerate(qnt):      
                self.sink[ np.unravel_index(i, dims=(shape[0],shape[1])) ] = q
            print( 'done', file=sys.stderr )

        else:
            raise ValueError( "msom:run: unknown output type " +
                              self.params.output_type)
        
    ####################################################################
    # gui section
    ####################################################################

    def str2tuple(self, s):
        # convert tuple-like strings to real tuples.
        # eg '(1,2,3,4)' -> (1, 2, 3, 4)
        
        if s[0] + s[-1] != "()":
            raise ValueError("str2tuple:bad string (missing brackets).")

        # remove leading and trailing brackets
        items = s[1:-1]              
        items = items.split(',')

        # clean up spaces, convert to ints
        t = [int(x.strip()) for x in items] 
        return tuple( t )

    def read_params_from_panel( self ):  # scan panel parameters

        self.params.sigma = float( self.t_sigma.GetValue() )
        self.params.rate = float( self.t_rate.GetValue() )

        shape_str = self.t_shape.GetValue()
        self.params.shape = self.str2tuple( shape_str )
         
        if len(self.params.shape) != 2:
            raise ValueError( 'msom:shape must be 2-Dimensional, eg.(3,3)' )

        # TODO: check for reasonable values
        self.params.sigma = float( self.t_sigma.GetValue() )
        self.params.nepochs = int( self.t_nepochs.GetValue() )
        self.params.rate = float( self.t_rate.GetValue() )

        # neighborhood function
        if self.r_gaussian.GetValue():
            self.params.neighborhood_function = 'gaussian'
        if self.r_mexican_hat.GetValue():
            self.params.neighborhood_function = 'mexican_hat'
        if self.r_bubble.GetValue():
            self.params.neighborhood_function = 'bubble'
        if self.r_triangle.GetValue():
            self.params.neighborhood_function = 'triangle'

        # init weights
        if self.r_random.GetValue():
            self.params.init_weights = 'random'
        if self.r_pca.GetValue():
            self.params.init_weights = 'pca'

        # topology
        if self.r_rectangular.GetValue():
            self.params.topology = 'rectangular'
        if self.r_hexagonal.GetValue():
            self.params.topology = 'hexagonal'

        # activation distance
        if self.r_euclidean.GetValue():
            self.params.activation_distance = 'euclidean'
        if self.r_cosine.GetValue():
            self.params.activation_distance = 'cosine'
        if self.r_manhattan.GetValue():
            self.params.activation_distance = 'manhattan'
        if self.r_chebyshev.GetValue():
            self.params.activation_distance = 'chebyshev'

        # check boxes
        if self.c_activation_map.GetValue():
            self.params.activation_map = True
        else:
            self.params.activation_map = False

        if self.c_calc_epoch_errors.GetValue():
            self.params.calc_epoch_errors= True
        else:
            self.params.calc_epoch_errors = False

        # decay function
        if self.r_asymptotic.GetValue():
            self.params.decay_function = 0
        if self.r_constant.GetValue():
            self.params.decay_function = 1
        if self.r_exponential.GetValue():
            self.params.decay_function = 2
        if self.r_inverse.GetValue():
            self.params.decay_function = 3
        if self.r_linear.GetValue():
            self.params.decay_function = 4
        if self.r_power.GetValue():
            self.params.decay_function = 5

        # image output type
        if self.r_label.GetValue():
            self.params.output_type = 'labels'
        if self.r_quantize.GetValue():
            self.params.output_type = 'quantize'

        self.params.mapfile_prefix = self.t_mapfile_prefix.GetValue()
        self.params.actmapfile_prefix = self.t_actmapfile_prefix.GetValue()

    def write_params_to_panel( self ):   # write parameters to panel

        self.t_shape.SetValue( str(self.params.shape) )
        self.t_sigma.SetValue( str(self.params.sigma) )
        self.t_nepochs.SetValue( str(self.params.nepochs) )
        self.t_rate.SetValue( str(self.params.rate) )

        # neighborhood function
        if self.params.neighborhood_function == 'gaussian':
            self.r_gaussian.SetValue( True )
        if self.params.neighborhood_function == 'mexican_hat':
            self.r_mexican_hat.SetValue( True )
        if self.params.neighborhood_function == 'bubble':
            self.r_bubble.SetValue( True )
        if self.params.neighborhood_function == 'triangle':
            self.r_triangle.SetValue( True )

        # init weights
        if self.params.init_weights == 'random':
            self.r_random.SetValue( True )            
        if self.params.init_weights == 'pca':
            self.r_pca.SetValue( True )

        # topology 
        if self.params.topology == 'rectangular':
            self.r_rectangular.SetValue( True )
        if self.params.neighborhood_function == 'hexaganol':
            self.r_hexoganol.SetValue( True )

        # activation distance
        if self.params.activation_distance == 'euclidean':
            self.r_euclidean.SetValue( True )
        if self.params.activation_distance == 'cosine':
            self.r_cosine.SetValue( True )
        if self.params.activation_distance == 'manhattan':
            self.r_manhattan.SetValue( True )
        if self.params.activation_distance == 'chebysev':
            self.r_chebysev.SetValue( True )

        # decay function
        if self.params.decay_function == 0:
            self.r_asymptotic.SetValue( True )
        if self.params.decay_function == 1:
            self.r_constant.SetValue( True )
        if self.params.decay_function == 2:
            self.r_exponential.SetValue( True )
        if self.params.decay_function == 3:
            self.r_inverse.SetValue( True )
        if self.params.decay_function == 4:
            self.r_linear.SetValue( True )
        if self.params.decay_function == 5:
            self.r_power.SetValue( True )

        if self.params.activation_map == True:
            self.c_activation_map.SetValue( True )
            self.t_actmapfile_prefix.Enable( True )
                        
        else:
            self.c_activation_map.SetValue( False )
            self.t_actmapfile_prefix.Enable( False )

        if self.params.calc_epoch_errors == True:
            self.c_calc_epoch_errors.SetValue( True )
        else:
            self.c_calc_epoch_errors.SetValue( False )

        # image output type
        if self.params.output_type == 'labels':
            self.r_label.SetValue( True )
        if self.params.output_type == 'quantize':
            self.r_quantize.SetValue( True )

        self.t_mapfile_prefix.SetValue( self.params.mapfile_prefix )
        self.t_actmapfile_prefix.SetValue( self.params.actmapfile_prefix )

        # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        panel = self.parms_panel()
        h_sizer.Add( panel, 0, wx.ALL, 1 ) 
        
        panel = self.neighborhood_panel()
        h_sizer.Add( panel, 0, wx.ALL, 1 ) 

        vv_sizer = wx.BoxSizer( wx.VERTICAL )
        panel = self.init_weights_panel()
        vv_sizer.Add( panel, 1, wx.EXPAND )
        
        panel = self.topology_panel()
        vv_sizer.Add( panel, 1, wx.EXPAND )

        self.c_calc_epoch_errors = wx.CheckBox( self.p_client, 0, 'calculate epoch errors' )
        vv_sizer.Add( self.c_calc_epoch_errors, 0, wx.ALL, 1 )

        h_sizer.Add( vv_sizer, 1, wx.EXPAND )

        panel = self.activation_panel()
        h_sizer.Add( panel, 0, wx.ALL, 1 ) 

        vv_sizer = wx.BoxSizer( wx.VERTICAL )

        panel = self.decay_panel()
        vv_sizer.Add( panel, 0, wx.ALL, 1 )
        self.c_activation_map = wx.CheckBox( self.p_client, 0, 'write activation map' )
        self.c_activation_map.Bind( wx.EVT_CHECKBOX, self.on_activation_map )

        vv_sizer.Add( self.c_activation_map, 0, wx.ALL, 1 )
        h_sizer.Add( vv_sizer )

        panel = self.output_panel()
        h_sizer.Add( panel, 1, wx.ALL, 1  )

        v_sizer.Add( h_sizer )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( self.p_client, -1, 'enter map pathname prefix:' )
        h_sizer.Add( prompt, 0, wx.TOP, 5 )
        self.t_mapfile_prefix = wx.TextCtrl( self.p_client, -1, "" )
        self.t_mapfile_prefix.SetToolTip( 'enter prefix to save SOM map to' )
        h_sizer.Add( self.t_mapfile_prefix, 1, wx.EXPAND, 0 )
        
        prompt = wx.StaticText( self.p_client, -1, 'enter activation map prefix:' )
        h_sizer.Add( prompt, 0, wx.TOP, 5 )
        self.t_actmapfile_prefix = wx.TextCtrl( self.p_client, -1, "" )
        self.t_actmapfile_prefix.SetToolTip( 'enter prefix to save activation map to' )
        h_sizer.Add( self.t_actmapfile_prefix, 1, wx.EXPAND, 0 )
       
        v_sizer.Add( h_sizer, 1, wx.EXPAND )
        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    # respond to file browse click
    def on_activation_map( self, event ):
        if self.c_activation_map.GetValue():
            self.t_actmapfile_prefix.Enable( True )
        else:
            self.t_actmapfile_prefix.Enable( False )
        
    def output_panel( self ):
        p_output = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )

        sizer = wx.GridSizer( 2, 2, 1, 1 )
        prompt = wx.StaticText( p_output, -1, 'output type:' )
        sizer.Add( prompt )
        sizer.Add( (1,1) )

        self.r_label = wx.RadioButton( p_output, -1, 'labels', 
                                          style = wx.RB_GROUP )
        sizer.Add( self.r_label )
        self.r_quantize = wx.RadioButton( p_output, -1, 'quantize' )
        sizer.Add( self.r_quantize )

        p_output.SetSizer( sizer )
        
        return p_output

    # decay functions
    # possible values: 'asymptotic', 'constant', 'exponential', 'inverse', 'linear', 'power'
    def decay_panel( self ):
        p_decay = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )

        sizer = wx.GridSizer( 4, 2, 1, 1 )
        prompt = wx.StaticText( p_decay, -1, 'decay function:' )
        sizer.Add( prompt )
        sizer.Add( (1,1) )

        self.r_asymptotic = wx.RadioButton( p_decay, -1, 'asymptotic', 
                                          style = wx.RB_GROUP )
        sizer.Add( self.r_asymptotic )
        
        self.r_constant = wx.RadioButton( p_decay, -1, 'constant' )
        sizer.Add( self.r_constant )

        self.r_exponential = wx.RadioButton( p_decay, -1, 'exponential' )
        sizer.Add( self.r_exponential )

        self.r_inverse = wx.RadioButton( p_decay, -1, 'inverse' )
        sizer.Add( self.r_inverse )

        self.r_linear = wx.RadioButton( p_decay, -1, 'linear' )
        sizer.Add( self.r_linear )
        
        self.r_power = wx.RadioButton( p_decay, -1, 'power' )
        sizer.Add( self.r_power )

        p_decay.SetSizer( sizer )
        
        return p_decay
    
    # distance metric used to activate the map.
    # possible values: 'euclidean', 'cosine', 'manhattan', 'chebyshev'
    def activation_panel( self ):
        p_active = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )

        sizer = wx.GridSizer( 5, 1, 1, 1 )
        prompt = wx.StaticText( p_active, -1, 'activation distance:' )
        sizer.Add( prompt )
        #sizer.Add( (1,1) )

        self.r_euclidean = wx.RadioButton( p_active, -1, 'euclidean', 
                                          style = wx.RB_GROUP )
        sizer.Add( self.r_euclidean )
        
        self.r_cosine = wx.RadioButton( p_active, -1, 'cosine' )
        sizer.Add( self.r_cosine )

        self.r_manhattan = wx.RadioButton( p_active, -1, 'manhattan' )
        sizer.Add( self.r_manhattan )

        self.r_chebyshev = wx.RadioButton( p_active, -1, 'chebyshev' )
        sizer.Add( self.r_chebyshev )

        p_active.SetSizer( sizer )
        
        return p_active
    
    # Topology of the map.
    # Possible values: 'rectangular', 'hexagonal'
    def topology_panel( self ):
        p_topo = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )

        sizer = wx.GridSizer( 2, 2, 1, 1 )
        prompt = wx.StaticText( p_topo, -1, 'topology:' )
        sizer.Add( prompt )
        sizer.Add( (1,1) )

        self.r_rectangular = wx.RadioButton( p_topo, -1, 'rectangular', 
                                          style = wx.RB_GROUP )
        sizer.Add( self.r_rectangular )
        
        self.r_hexagonal = wx.RadioButton( p_topo, -1, 'hexagonal' )
        sizer.Add( self.r_hexagonal )

        p_topo.SetSizer( sizer )
        
        return p_topo

    def init_weights_panel( self ):
        p_init_weights = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )

        sizer = wx.GridSizer( 2, 2, 1, 1 )
        prompt = wx.StaticText( p_init_weights, -1, 'init weights:' )
        sizer.Add( prompt )
        sizer.Add( (1,1) )

        self.r_random = wx.RadioButton( p_init_weights, -1, 'random', 
                                          style = wx.RB_GROUP )
        sizer.Add( self.r_random )
        self.r_pca = wx.RadioButton( p_init_weights, -1, 'pca' )
        sizer.Add( self.r_pca )

        p_init_weights.SetSizer( sizer )
        
        return p_init_weights


    def neighborhood_panel( self ):
        p_neigh = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )

        sizer = wx.GridSizer( 5, 1, 1, 1 )
        prompt = wx.StaticText( p_neigh, -1, 'neighborhood:' )
        sizer.Add( prompt )
        #sizer.Add( (1,1) )

        self.r_gaussian = wx.RadioButton( p_neigh, -1, 'gaussian', 
                                          style = wx.RB_GROUP )
        sizer.Add( self.r_gaussian )
        self.r_mexican_hat = wx.RadioButton( p_neigh, -1, 'mexican hat' )
        sizer.Add( self.r_mexican_hat )
        self.r_bubble = wx.RadioButton( p_neigh, -1, 'bubble' )
        sizer.Add( self.r_bubble )
        self.r_triangle = wx.RadioButton( p_neigh, -1, 'triangle' )
        sizer.Add( self.r_triangle )

        p_neigh.SetSizer( sizer )
        
        return p_neigh

    def parms_panel( self ):
        p_parms = wx.Panel( self.p_client, -1,
                            style=wx.SUNKEN_BORDER )
        
        sizer = wx.GridSizer( 5, 2, 1, 1 )
        prompt = wx.StaticText( p_parms, -1, 'parms:' )
        sizer.Add( prompt )
        sizer.Add( (1,1) )

        # nodal topology
        prompt = wx.StaticText( p_parms, -1, 'shape' )
        sizer.Add( prompt, 1, wx.BOTTOM, 1 )
        self.t_shape = wx.TextCtrl( p_parms, -1, size=(70,20),
                                   style=wx.ALIGN_RIGHT ) 

        self.t_shape.SetToolTip( 'enter nodal topology shape eg.(2,2,3)' )
        sizer.Add( self.t_shape, 1, wx.BOTTOM, 1 )

        # spread of neighborhood function
        prompt = wx.StaticText( p_parms, -1, 'sigma' )
        sizer.Add( prompt, 1, wx.BOTTOM, 1 )
        self.t_sigma = wx.TextCtrl( p_parms, -1, size=(70,20),
                                    style=wx.ALIGN_RIGHT ) 
        self.t_sigma.SetToolTip( 'spread of neighborhood function ' )
        sizer.Add( self.t_sigma, 1, wx.BOTTOM, 1 )

        # number of epochs
        prompt = wx.StaticText( p_parms, -1, 'nepochs' )
        sizer.Add( prompt, 1, wx.BOTTOM, 2 )
        self.t_nepochs = wx.TextCtrl( p_parms, -1, size=(70,20),
                                    style=wx.ALIGN_RIGHT )
        self.t_nepochs.SetToolTip( 'enter number of epochs' )
        sizer.Add( self.t_nepochs, 1, wx.BOTTOM, 2 )

        # learning rate
        prompt = wx.StaticText( p_parms, -1, 'rate' )
        sizer.Add( prompt, 1, wx.BOTTOM, 2 )
        self.t_rate = wx.TextCtrl( p_parms, -1, size=(70,20),
                                    style=wx.ALIGN_RIGHT )
        self.t_rate.SetToolTip( 'enter learning rate' )
        sizer.Add( self.t_rate, 1, wx.BOTTOM, 2 )

        p_parms.SetSizer( sizer )
                                 
        return p_parms

    ############################################################
    # command line options
    ############################################################

    # TODO: read and process a parameter file
    def usage( self ):
        print( 'usage: msom.py', file=sys.stderr )
        print( '       -h, --help', file=sys.stderr )
        print( '       -p paramfile, --params=paramfile', file=sys.stderr )
        print( '       input is stdin, output is stdout', file=sys.stderr )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 'hp:', ['help','params='] )
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0) 
            elif opt in ('-p', '--params'):
                params = arg  

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                print( 'msom:set_params: bad params file read',
                       file=sys.stderr )

                sys.exit(2)

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':
    import tempfile
    
    oper = instantiate()   
    oper.set_params( sys.argv[1:] )

    # numpy needs to 'seek' in the file to load
    # so read from stdin to temporary file first
    temp_name = next(tempfile._get_candidate_names()) + '.tmp'
    temp = open( temp_name, 'wb' )
    temp.write( sys.stdin.buffer.read() )
    temp.close()

    # load the pickled data
    oper.source = np.load( temp_name, allow_pickle=True,fix_imports=False)
    os.remove( temp_name )

    oper.run()                  
    oper.sink.dump( sys.stdout.buffer )          # send down stream    
    
