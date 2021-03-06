import sys, os
sys.path.append('.')
sys.path.append('..')
sys.path.append('../..')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from matplotlib.widgets import Slider
import matplotlib.gridspec
from MJOLNIR import _tools
import warnings

class Viewer3D(object):  
    @_tools.KwargChecker()
    def __init__(self,Data,bins,axis=2,ax = None,**wkargs):#pragma: no cover
        """3 dimensional viewing object generating interactive Matplotlib figure. 
        Keeps track of all the different plotting functions and variables in order to allow the user to change between different slicing modes and to scroll through the data in an interactive way.

        Args:

            - Data (3D array): Intensity array in three dimensions. Assumed to have Qx, Qy, and E along the first, second, and third directions respectively.

            - bins (List of 1D arrays): Coordinates of the three directions as returned by the BinData3D functionality of DataSet.

        Kwargs:

            - axis (int): Axis along which the interactive plot slices the data (default 2).

            - ax (matplotlib axis): Matplotlib axis into which one pltos data (Default None)

        Example:

        >>> from MJOLNIR.Data import DataSet,Viewer3D
        >>> import matplotlib.pyplot as plt
        >>> import numpy as np
        >>> 
        >>> DataFile = ['../TestData/cameasim2018n000011.nxs']
        >>> Data,bins = dataset.binData3D(0.08,0.08,0.25)
        >>> 
        >>> Intensity = np.divide(Data[0]*Data[3],Data[1]*Data[2])
        >>> 
        >>> Viewer = Viewer3D.Viewer3D(Intensity,bins,axis=2)
        >>> Viewer.ax.set_title(str(title)[2:-1])
        >>> plt.show()

        .. figure:: ../../Tutorials/Visualization_E_546.png
           :width: 40%

        Interactive plot generated by above function call with a Intensity being 3D rebinned data using the simple phonon component, Ei of 10 meV and 180 steps of 1 degree in A3, A4 at -60 degrees.
        """
        self.Data = Data
        self.bins = bins
        self.dataLimits = [np.nanmin(Data),np.nanmax(Data)]

        gs = matplotlib.gridspec.GridSpec(1, 2, width_ratios=[4, 1]) 
        
        if ax is None:
            self.figure = plt.figure()
            self.ax = plt.subplot(gs[0])#self.figure.add_subplot(111)
            self.xlabel = r'Qx [$A^{-1}$]'
            self.ylabel = r'Qy [$A^{-1}$]'
            self.zlabel = r'E [meV]'
            self.rlu = False
        else:
            warnings.warn('If the provided axis is a RLU axis be aware of possibility of wrong visualization when cutting along Q!!')
            
            self.axRLU = ax
            self.figure = ax.get_figure() # Get the correct figure
            self.axNorm,ax2  = self.figure.subplots(1,2,gridspec_kw={'width_ratios':[4, 1]}) # Create figure on top of the other
            ax2.remove() # Remove the excess figure
            self.axRLU.set_position(self.axNorm.get_position()) # Update RLU to correct position

            self._axes = [self.axNorm,self.axNorm,self.axRLU]
            self.ax = self.axNorm
            self.xlabel = ax.get_xlabel()
            self.ylabel = ax.get_ylabel()
            self.zlabel = 'E [meV]'
            self.rlu = True
       
        self.value = 0
        self.figure.subplots_adjust(bottom=0.25)
        
        self.cmap = cm.jet
        self.cmap.set_bad('white',1.)
        self.value = 0
        
        axis_color='white'
        self.setAxis(axis)
        
        self.figure.canvas.mpl_connect('key_press_event',lambda event: onkeypress(event, self) )
        self.figure.canvas.mpl_connect('scroll_event',lambda event: onscroll(event, self))
        
        zeroPoint = np.argmin(np.abs(0.5*(self.Z[0,0][1:]+self.Z[0,0][:-1])))
        
    
        self.Energy_slider_ax = self.figure.add_axes([0.15, 0.1, 0.7, 0.03])#, facecolor=axis_color)
        self.Energy_slider = Slider(self.Energy_slider_ax, label=self.label, valmin=self.lowerLim, valmax=self.upperLim, valinit=zeroPoint,valfmt='%0f')
        self.Energy_slider.valtext.set_visible(False)
        
        self.Energy_slider.on_changed(lambda val: sliders_on_changed(self,val))
            
            
        textposition = [self.Energy_slider_ax.get_position().p1[0]+0.005,self.Energy_slider_ax.get_position().p0[1]+0.005]
        self.text = self.figure.text(textposition[0], textposition[1],s=self.stringValue())
        self.shading = 'flat'
        #self.imcbaxes = self.figure.add_axes([0.0, 0.2, 0.2, 0.7])
        #self.im = self.ax.imshow(self.masked_array[:,:,self.value].T,cmap=self.cmap,extent=[self.X[0],self.X[-1],self.Y[0],self.Y[-1]],origin='lower')
        if self.shading=='flat':
            self.im = self.ax.pcolormesh(self.X[:,:,0].T,self.Y[:,:,0].T,self.masked_array[:,:,self.value].T,zorder=10,shading=self.shading)
        elif self.shading=='gouraud':  # pragma: no cover
            XX = 0.5*(self.X[:-1,:-1,self.value]+self.X[1:,1:,self.value]).T
            YY = 0.5*(self.Y[:-1,:-1,self.value]+self.Y[1:,1:,self.value]).T
            self.im = self.ax.pcolormesh(XX,YY,self.masked_array[:,:,self.value].T,zorder=10,shading=self.shading) # ,vmin=1e-6,vmax=6e-6
        else:
            raise AttributeError('Did not understand shading {}.'.format(self.shading))
        self._caxis = self.im.get_clim()
        self.figpos = [0.125,0.25,0.63,0.63]#self.ax.get_position()
        
        self.cbaxes = self.figure.add_axes([0.8, 0.2, 0.03, 0.7])
        self.colorbar = self.figure.colorbar(self.im,cax = self.cbaxes)
        warnings.simplefilter("ignore")
        #self.figure.tight_layout(rect=[0,0.1,0.9,0.9])
        warnings.simplefilter("once")

        self.text.set_text(self.stringValue())
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        #if self.axis == 2:
        #    self.ax.set_xlim(np.min([xlim[0],ylim[0]]),np.max([xlim[1],ylim[1]]))
        self.Energy_slider.set_val(self.value)

        self.cid = self.figure.canvas.mpl_connect('button_press_event', onclick)
        
        self.caxis = self.dataLimits

    @property 
    def caxis(self):
        return self._caxis

    @caxis.getter
    def caxis(self):
        return self._caxis

    @caxis.setter
    def caxis(self,caxis):
        self._caxis = caxis
        self.im.set_clim(caxis)
        self.colorbar.update_bruteforce(self.im)

    def setAxis(self,axis):
        if axis==2:
            if self.rlu:
                self.figure.delaxes(self.ax)
                self.ax = self.figure.add_axes(self._axes[axis])
                #self.axRLU.set_visible(True)
                #self.axNorm.set_visible(False)
                #self.ax = self.axRLU
            axes = (0,1,2)
            self.ax.set_xlabel(self.xlabel)
            self.ax.set_ylabel(self.ylabel)
            label = self.zlabel
        elif axis==1:  # pragma: no cover
            if self.rlu:
                #self.axRLU.set_visible(False)
                #self.axNorm.set_visible(True)
                #self.ax = self.axNorm
                self.figure.delaxes(self.ax)
                self.ax = self.figure.add_axes(self._axes[axis])
            axes = (0,2,1)
            self.ax.set_xlabel(self.xlabel)
            self.ax.set_ylabel(self.zlabel)
            label = self.ylabel
        elif axis==0:  # pragma: no cover
            if self.rlu:
                #self.axRLU.set_visible(False)
                #self.axNorm.set_visible(True)
                #self.ax = self.axNorm
                self.figure.delaxes(self.ax)
                self.ax = self.figure.add_axes(self._axes[axis])
            axes = (1,2,0)
            self.ax.set_xlabel(self.ylabel)
            self.ax.set_ylabel(self.zlabel)
            label = self.xlabel
        else:
            raise AttributeError('Axis provided not recognized. Should be 0, 1, or 2 but got {}'.format(axis))
        
        X=self.bins[axes[0]].transpose(axes)
        Y=self.bins[axes[1]].transpose(axes)
        Z=self.bins[axes[2]].transpose(axes)
        

        masked_array = np.ma.array (self.Data, mask=np.isnan(self.Data)).transpose(axes)
        upperLim = self.Data.shape[axis]-1
        self.label = label
        self.X = X
        self.Y = Y
        self.Z = Z
        self.masked_array = masked_array
        self.axes = axes
        self.upperLim = upperLim
        self.lowerLim = 0
        self.axis = axis
        

        
    def stringValue(self):
        if self.axis==2:
            unit = ' meV'
        else:
            if self.rlu:
                unit = 'rlu'
            else:
                unit = ' 1/AA'
        try:
            val = 0.5*(self.Z[0,0,self.value+1]+self.Z[0,0,self.value])
        except:
            val = 0.5*(2*self.Z[0,0,self.value]-self.Z[0,0,self.value-1])
        return str(np.round(val,2))+unit
    
    
    def plot(self):
        #self.im = self.ax.imshow(self.masked_array[:,:,self.value].T,cmap=self.cmap,extent=[self.X[0],self.X[-1],self.Y[0],self.Y[-1]],origin='lower')
        #self.im.set_array(self.masked_array[:,:,self.value].T.ravel()) # = self.ax.pcolormesh(self.X.T[:-1],self.Y.T[:-1],self.masked_array[:,:,self.value].T,zorder=10,shading='gouraud')
        #self.im.autoscale()
        #self.colorbar.update_bruteforce(self.im)
        self.text.set_text(self.stringValue())
        self.im.remove()
        if self.shading=='flat':
            self.im = self.ax.pcolormesh(self.X[:,:,self.value].T,self.Y[:,:,self.value].T,self.masked_array[:,:,self.value].T,zorder=10,shading=self.shading)
        elif self.shading=='gouraud': # pragma: no cover
            XX = 0.5*(self.X[:-1,:-1,self.value]+self.X[1:,1:,self.value]).T
            YY = 0.5*(self.Y[:-1,:-1,self.value]+self.Y[1:,1:,self.value]).T
            self.im = self.ax.pcolormesh(XX,YY,self.masked_array[:,:,self.value].T,zorder=10,shading=self.shading) # ,vmin=1e-6,vmax=6e-6
        self.im.set_clim(self.caxis)
        self.ax.set_position(self.figpos)
        #ylim = [self.Y[0],self.Y[-1]]
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        if self.axis == 2:
            pass
            #self.ax.set_xlim(np.min([xlim[0],ylim[0]]),np.max([xlim[1],ylim[1]]))


def onclick(event): # pragma: no cover
    if event.xdata is not None:
        print('x={}, y={}, xdata={}, ydata={}'.format(event.x, event.y, event.xdata, event.ydata))



def onkeypress(event,self): # pragma: no cover
    if event.key in ['+','up']:
        increaseAxis(event,self)
    elif event.key in ['-','down']:
        decreaseAxis(event,self)
    elif event.key in ['0']:
        if self.axis!=0:
            reloadslider(self,0)
            #del self.im
            if self.shading=='flat':
                self.im = self.ax.pcolormesh(self.X[:,:,0].T,self.Y[:,:,0].T,self.masked_array[:,:,self.value].T,zorder=10,shading=self.shading)
            elif self.shading=='gouraud':
                self.im = self.ax.pcolormesh(0.5*(self.X[:-1,:-1,0]+self.X[1:,1:,0]).T,0.5*(self.Y[:-1,:-1,0]+self.Y[1:,1:,0]).T,self.masked_array[:,:,self.value].T,zorder=10,shading=self.shading) # ,vmin=1e-6,vmax=6e-6
            else:
                raise AttributeError('Did not understand shading {}.'.format(self.shading))
            self.im.set_clim(self.caxis)
            self.Energy_slider.set_val(0)
            self.plot()
            self.ax.set_xlim([np.min(self.X),np.max(self.X)])
            self.ax.set_ylim([np.min(self.Y),np.max(self.Y)])
    elif event.key in ['1']:
        if self.axis!=1:
            reloadslider(self,1)
            #del self.im
            if self.shading=='flat':
                self.im = self.ax.pcolormesh(self.X[:,:,0].T,self.Y[:,:,0].T,self.masked_array[:,:,self.value].T,zorder=10,shading=self.shading)
            elif self.shading=='gouraud':
                self.im = self.ax.pcolormesh(0.5*(self.X[:-1,:-1]+self.X[1:,:1:]).T,0.5*(self.Y[:-1,-1]+self.Y[1:,1:]).T,self.masked_array[:,:,self.value].T,zorder=10,shading=self.shading) # ,vmin=1e-6,vmax=6e-6
            else:
                raise AttributeError('Did not understand shading {}.'.format(self.shading))
            self.im.set_clim(self.caxis)
            self.Energy_slider.set_val(0)
            self.plot()
            self.ax.set_xlim([np.min(self.X),np.max(self.X)])
            self.ax.set_ylim([np.min(self.Y),np.max(self.Y)])
    elif event.key in ['2']:
        if self.axis!=2:
            reloadslider(self,2)
            #del self.im
            if self.shading=='flat':
                self.im = self.ax.pcolormesh(self.X[:,:,0].T,self.Y[:,:,0].T,self.masked_array[:,:,self.value].T,zorder=10,shading=self.shading)
            elif self.shading=='gouraud':
                XX = 0.5*(self.X[:-1,:-1,self.value]+self.X[1:,1:,self.value]).T
                YY = 0.5*(self.Y[:-1,:-1,self.value]+self.Y[1:,1:,self.value]).T
                self.im = self.ax.pcolormesh(XX,YY,self.masked_array[:,:,self.value].T,zorder=10,shading=self.shading) # ,vmin=1e-6,vmax=6e-6
            else:
                raise AttributeError('Did not understand shading {}.'.format(self.shading))
            self.im.set_clim(self.caxis)
            self.Energy_slider.set_val(0)
            self.plot()
            self.ax.set_xlim([np.min(self.X),np.max(self.X)])
            self.ax.set_ylim([np.min(self.Y),np.max(self.Y)])


def reloadslider(self,axis): # pragma: no cover
    self.Energy_slider.set_val(0)
    self.setAxis(axis)
    self.Energy_slider.label.remove()#self.Energy_slider.label.text('')
    self.Energy_slider.disconnect(self.Energy_slider.cids[0])
    self.Energy_slider.vline.set_visible(False)
    
    del self.Energy_slider
    
    zeroPoint = np.argmin(np.abs(0.5*(self.Z[0,0][1:]+self.Z[0,0][:-1])))
    self.Energy_slider = Slider(self.Energy_slider_ax, label=self.label, valmin=self.lowerLim, valmax=self.upperLim, valinit=zeroPoint)
    self.Energy_slider.valtext.set_visible(False)
    self.Energy_slider.on_changed(lambda val: sliders_on_changed(self,val))
    self.value=0
    self.im.remove()
    
        
def onscroll(event,self): # pragma: no cover
    if(event.button=='up'):
        increaseAxis(event,self)
    elif event.button=='down':
        decreaseAxis(event,self)


def increaseAxis(event,self): # pragma: no cover
    self.Energy_slider.set_val(self.Energy_slider.val+1)
    
    
def decreaseAxis(event,self): # pragma: no cover
    self.Energy_slider.set_val(self.Energy_slider.val-1)   
    

def sliders_on_changed(self,val): # pragma: no cover
        value = int(np.round(val))
        
        if value>self.Energy_slider.valmax:
            self.Energy_slider.set_val(self.Energy_slider.valmax)
            
        elif value<self.Energy_slider.valmin:
            self.Energy_slider.set_val(self.Energy_slider.valmin)
        
        if value<=self.Energy_slider.valmax and value>=self.Energy_slider.valmin:
            if value!=val:
                self.Energy_slider.set_val(value)
                
            else:
                self.value = val
                self.plot()

