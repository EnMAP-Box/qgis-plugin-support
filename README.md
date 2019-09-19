# QGIS Plugin Support (QPS) 
![build status](https://img.shields.io/bitbucket/pipelines/jakimowb/qgispluginsupport.svg)




This is a small library to support the creation of QGIS Plugins. 

OPS is used in other project like:

EnMAP-Box https://bitbucket.org/hu-geomatics/enmap-box

EO Time Series Viewer https://bitbucket.org/jakimowb/eo-time-series-viewer

Virtual Raster Builder https://bitbucket.org/jakimowb/virtual-raster-builder


## Installation ##


1. Copy the qgs folder into your source code, e.g. ``mymodule/qps``, and ensure that the Qt resource files are compiled:

    ```python
    from mymodule.qps.setup import compileQPSResources
    compileQPSResources()
     ```

2. QPS uses the Qt resource system, e.g. to access icons. This requires to convert the ``qps/qpsresources.qrc`` file 
into a corresponding python module ``qps/qpsresources.py``.  


3. Now you can use the QPS python API. Keep in mind that some of its features need to be 
registered to a running Qt Application or the QGIS Application instance. 
This is preferably done in the ```__init__.py``` of 
your application, e.g. by calling:

    ```python
    from mymodule.qps import initAll
    initAll()
    ```


### Example: Spectral Library Widget ###
The following example shows you how to initialize (for testing) a mocked QGIS Application and to open the Spectral Library  Wdiget: 

```python
from mymodule.qps.testing import initQgisApplication
QGIS_APP = initQgisApplication()


from mymodule.qps import initAll 
from mymodule.qps.speclib.spectrallibraries import SpectralLibraryWidget
initAll()

widget = SpectralLibraryWidget()
widget.show()

QGIS_APP.exec_()
```

Note that the first two lines and the last line are not required if QGIS is already started. 



## License

QPS is released under the GNU Public License (GPL) Version 3 or above.
Developing QPS under this license means that you can (if you want to) inspect
and modify the source code and guarantees that you, our happy user will always
have access to an EnMAP-Box program that is free of cost and can be freely
modified.


