# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TreeSeg
                                 A QGIS plugin
 tree segmentation from aerial point clouds
                              -------------------
        begin                : 2022-12-15
        git sha              : $Format:%H$
        copyright            : (C) 2022 by CS Capstone
        email                : storump@oregonstate.edu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsMessageLog, QgsVectorLayer, QgsGeometry, QgsCoordinateTransformContext, QgsPointXY, QgsProject, QgsFeature, QgsVectorFileWriter
import subprocess

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .tree_seg_dialog import TreeSegDialog
import os.path
import json
import os
import shutil
import sys
import time
import random
import processing
from PIL import Image
from numpy import asarray
import numpy as np
import pandas as pd
from osgeo import gdal, ogr
import osgeo.ogr as ogr
import osgeo.osr as osr
sys.path.append('/TrEx/scripts')
from .TrEx.scripts.qgis_setup_env import qgis_env


class TreeSeg:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):

        # set environment variables for qgis
        env_path =  os.path.join(os.path.abspath(os.path.dirname(__file__)), "env-vars.json")
        with open(env_path, "r") as f:
            d = json.loads(f.read())

        for key in os.environ:
            os.environ.pop(key)

        for key, value in d.items():
            os.environ[key] = value

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TreeSeg_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Tree Segmentation')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TreeSeg', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/tree_seg/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Tree Segementation'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Tree Segmentation'),
                action)
            self.iface.removeToolBarIcon(action)

    def segButton(self):
        #start segmentation
        inputFile = self.dlg.mQgsFileWidget.filePath()
        file_path =  os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\TrEx\\scripts\\treeseg_test.cmd")
        if inputFile[-4:] == ".las":
            pass
        elif inputFile[-4:] == ".laz":
            pass
        else:
            QgsMessageLog.logMessage("Bad File Type")
            return
        
        change_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\TrEx\\tests\\pipeline_saveall.json")
        
        #load parameters 
        f = open(change_file_path)
        data = json.load(f)
        f.close()
        data['resolution'] = float(self.dlg.resolution.displayText())
        data['discretization'] = int(self.dlg.discretization.displayText())
        data['min_height'] = int(self.dlg.min_height.displayText())
        data['gaussian_sigma'] = float(self.dlg.gaussian_sigma.displayText())
        data['weight_level_depth'] = float(self.dlg.weight_level_depth.displayText())
        data['weight_node_depth'] = float(self.dlg.weight_node_depth.displayText())
        data['weight_shared_ratio'] = float(self.dlg.weight_shared_ratio.displayText())
        data['weight_top_distance'] = float(self.dlg.weight_top_distance.displayText())
        data['weight_centroid_distance'] = float(self.dlg.weight_centroid_distance.displayText())
        data['weight_threshold'] = float(self.dlg.weight_threshold.displayText())

        data["input_file_path"] = inputFile
        json_object = json.dumps(data, indent=4)
        with open(change_file_path, "w") as outfile:
            outfile.write(json_object)

        start_time = time.time()
        subprocess.call([file_path])
        end_time = time.time()
        run_time = end_time - start_time
        run_time = round(run_time, 3)

        self.displayTallestTree(run_time)
        self.displayImages()
        self.dlg.saveAllCrown.setEnabled(True)
        self.dlg.saveAllPeak.setEnabled(True)

    def getMaxPointsFromFiles(self, gridPath, partitionPath, patchesPath):

      #open using Pillow's image module

      #.convert('L') used to make monochrome
      
      gridPNG = Image.open(gridPath).convert('L')
      #.getchannel('B') used to isolate blue channel
      partitionPNGR = Image.open(partitionPath).getchannel('R')
      partitionPNGG = Image.open(partitionPath).getchannel('G')
      partitionPNGB = Image.open(partitionPath).getchannel('B')
      
      patchesPNG = Image.open(patchesPath)

      #parse into numpy arrays
      #array goes inner array is row, outer array is column
      grid = asarray(gridPNG)
    
      #using blue + green * 255 to determine patch ID
      partitionR = asarray(partitionPNGR)
      partitionG = asarray(partitionPNGG)
      partitionB = asarray(partitionPNGB)

      #getting partition labels
      partition = np.zeros(shape=(partitionR.shape))
      for i in range(len(partition)):
        for j in range(len(partition[0])):
          partition[i][j] = int((partitionR[i][j] << 16) + (partitionG[i][j] << 8) + partitionB[i][j])

      #list of all patches
      listOfPatches = []
      for x in partition:
        for y in x:
          if y not in listOfPatches:
            listOfPatches.append(y)

      partitionMax = {}

      #maximum point of patches
      for i in range(len(partition)):
        for j in range(len(partition[0])):
          xy = partition[i][j]
          if partitionMax.get(xy) is None:
            partitionMax[xy] = (None,None,0)
          else:
            height = 255-grid[i][j]
            if height > partitionMax[xy][2]:
              partitionMax[xy] = (j,i,height)

      layer = QgsVectorLayer(f"Point?crs=EPSG:3857&field=x:double&field=y:double&field=z:double", "Points", "memory")
      provider = layer.dataProvider()
      # Add the points to the layer
      for i in partitionMax.values():
          feature = QgsFeature()
          feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(i[0], i[1])))
          feature.setAttributes([int(i[0]), int(i[1]), int(i[2])])
          provider.addFeatures([feature])
      # Add the layer to the QGIS project
      QgsProject.instance().addMapLayer(layer)

      output_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\tempSHP\\peak.shp")
      file_format = "ESRI Shapefile"

      crs = QgsCoordinateTransformContext()
      options = QgsVectorFileWriter.SaveVectorOptions()
      options.driverName='ESRI Shapefile'

      data = QgsVectorFileWriter.writeAsVectorFormatV3(layer, output_file, crs, options)
      del data


      #remove 0 patch
      partitionMax.pop(0)
      gridPNG.close()
      partitionPNGR.close()
      partitionPNGG.close()
      partitionPNGB.close()
      patchesPNG.close()
      return partitionMax

    def getTallestTree(self, maxPoints, N=1):
      maxTree = None
      minTree = None
      for x in maxPoints.values():
        
        if minTree == None:
          minTree = x
        if maxTree == None:
          maxTree = x
        else:
          if maxTree[2] < x[2]:
            maxTree = x
          if minTree[2] > x[2]:
            minTree = x
      minMaxTree = (minTree, maxTree)
      return minMaxTree

    def markedTrees(self, maxPoints, tallestTree, gridImg, partitionImg):
        image = Image.open(gridImg)
        rgba = image.convert("RGBA")
        datas = rgba.getdata()

        partitionR = asarray(Image.open(partitionImg).getchannel('R'))
        partitionG = asarray(Image.open(partitionImg).getchannel('G'))
        partitionB = asarray(Image.open(partitionImg).getchannel('B'))

        #getting partition labels
        partition = np.zeros(shape=(partitionR.shape))
        for i in range(len(partition)):
            for j in range(len(partition[0])):
                partition[i][j] = int((partitionR[i][j] << 16) + (partitionG[i][j] << 8) + partitionB[i][j])
        
        #setting seed-random values for rgb
        newImage = []
        count = 0
        for _ in datas:
            id = partition[count//image.width][count%image.width]
            random.seed(id)
            r = round(random.random() * 155 + 100)
            g = round(random.random() * 155 + 100)
            b = round(random.random() * 155 + 100)
            if id == 0:
                r, g, b = 60, 60, 60
            newImage.append((r,g,b,255))
            count+=1
        
        rgba.putdata(newImage)

        rgba.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), "treeHeights.png"), "PNG")
        
        #save output as shape file
        output = os.path.join(os.path.abspath(os.path.dirname(__file__)), "output.tif")
        src_ds = gdal.Open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "treeHeights.png"))
        driver = gdal.GetDriverByName('GTiff')
        dst_ds = driver.CreateCopy(output, src_ds)

        src_ds = None
        dst_ds = None

        img_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "output.tif")
        shp_path =  os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\tempSHP\\crown.shp")

        img_ds = gdal.Open(img_path)
        shp_ds = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(shp_path)
        shp_layer = shp_ds.CreateLayer("layer_name", geom_type=ogr.wkbPolygon)
        new_field = ogr.FieldDefn("Value", ogr.OFTInteger)
        shp_layer.CreateField(new_field)

        gdal.Polygonize(img_ds.GetRasterBand(2), None, shp_layer, 0, [])

        spatial_ref = img_ds.GetProjection()

        shp_path =  os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\tempSHP\\crown.prj")
        prj_file = open(shp_path, 'w')
        prj_file.write(spatial_ref)
        prj_file.close()

        shp_ds = None
        img_ds = None

        image.close()

    def displayTallestTree(self, time):
      #dispaly data on plugin
      gridPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\TrEx\\treeseg_output\\grid.png")
      partitionPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\TrEx\\treeseg_output\\partitions.png")
      patchesPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\TrEx\\treeseg_output\\patches.png")
      treePartitions = self.getMaxPointsFromFiles(gridPath, partitionPath, patchesPath)
      treeData = self.getTallestTree(treePartitions)
      tallestTree = treeData[1]
      shortestTree = treeData[0]
      self.markedTrees(treePartitions, tallestTree, gridPath, partitionPath)
      self.dlg.tallestTree.setText(str(f'Tallest tree:\n({tallestTree[0]}, {tallestTree[1]}) Height: {tallestTree[2]}\n\nShortest tree:\n({shortestTree[0]}, {shortestTree[1]}) Height: {shortestTree[2]}\n\nTotal Trees: {len(treePartitions)}\n\nComputation Time: {str(time)} seconds'))
      
    def displayImages(self):
        #display segmented tree map
        seg_grid_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "treeHeights.png")
        self.dlg.segGrid.setScaledContents(True)
        self.seg_grid = QPixmap(seg_grid_path)
        self.dlg.segGrid.setPixmap(self.seg_grid)
        
    def saveDataPeak(self):
        #save shape file
        save_directory = self.dlg.getSavePeak.filePath()

        seg_dbf_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\tempSHP\\peak.dbf")
        seg_shp_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\tempSHP\\peak.shp")
        seg_shx_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\tempSHP\\peak.shx")
        seg_prj_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\tempSHP\\peak.shx")
        
        filenameDBF = ""
        filenameSHP = ""
        filenameSHX = ""
        filenamePRJ = ""

        if self.dlg.peakName.text() != "":
            filenameDBF = str(self.dlg.peakName.text())  + ".dbf"
            filenameSHP = str(self.dlg.peakName.text())  + ".shp"
            filenameSHX = str(self.dlg.peakName.text())  + ".shx"
            filenamePRJ = str(self.dlg.peakName.text())  + ".prj"
        else:
            filenameDBF = "peak.dbf"
            filenameSHP = "peak.shp"
            filenameSHX = "peak.shx"
            filenamePRJ = "peak.prj"

        counter = 1

        while os.path.exists(os.path.join(save_directory, filenameDBF)):
            filenameDBF = f"peak_{counter}.dbf"
            filenameSHP = f"peak_{counter}.shp"
            filenameSHX = f"peak_{counter}.shx"
            filenamePRJ = f"peak_{counter}.prj"
            counter += 1 

        shutil.copy(seg_dbf_path, os.path.join(save_directory, filenameDBF))
        shutil.copy(seg_shp_path, os.path.join(save_directory, filenameSHP))
        shutil.copy(seg_shx_path, os.path.join(save_directory, filenameSHX))
        shutil.copy(seg_prj_path, os.path.join(save_directory, filenamePRJ))

        return
    
    def saveDataCrown(self):
        #save crown file
        save_directory = self.dlg.getSaveCrown.filePath()

        seg_dbf_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\tempSHP\\crown.dbf")
        seg_shp_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\tempSHP\\crown.shp")
        seg_shx_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\tempSHP\\crown.shx")
        seg_prj_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), ".\\tempSHP\\crown.prj")

        filenameDBF = ""
        filenameSHP = ""
        filenameSHX = ""
        filenamePRJ = ""

        if self.dlg.crownName.text() != "":
            filenameDBF = str(self.dlg.crownName.text())  + ".dbf"
            filenameSHP = str(self.dlg.crownName.text())  + ".shp"
            filenameSHX = str(self.dlg.crownName.text())  + ".shx"
            filenamePRJ = str(self.dlg.crownName.text())  + ".prj"
        else:
            filenameDBF = "crown.dbf"
            filenameSHP = "crown.shp"
            filenameSHX = "crown.shx"
            filenamePRJ = "crown.prj"

        counter = 1

        while os.path.exists(os.path.join(save_directory, filenameDBF)):
            filenameDBF = f"crown_{counter}.dbf"
            filenameSHP = f"crown_{counter}.shp"
            filenameSHX = f"crown_{counter}.shx"
            filenamePRJ = f"crown_{counter}.prj"
            counter += 1 


        shutil.copy(seg_dbf_path, os.path.join(save_directory, filenameDBF))
        shutil.copy(seg_shp_path, os.path.join(save_directory, filenameSHP))
        shutil.copy(seg_shx_path, os.path.join(save_directory, filenameSHX))
        shutil.copy(seg_prj_path, os.path.join(save_directory, filenamePRJ))

        return
    
    def closePlugin(self):
      dialog = self.dlg
      dialog.accept()

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = TreeSegDialog()

        self.dlg.startSeg.clicked.connect(self.segButton)
        self.dlg.saveAllPeak.clicked.connect(self.saveDataPeak)
        self.dlg.saveAllCrown.clicked.connect(self.saveDataCrown)
        self.dlg.closeWindow.clicked.connect(self.closePlugin)
        
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()

        if result:
            return
