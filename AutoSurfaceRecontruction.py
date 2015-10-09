import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np

import time

class autoSurfaceReconstruction(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "autoSurfaceReconstruction" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

class autoSurfaceReconstructionWidget(ScriptedLoadableModuleWidget):

  def setup(self):
    self.autoSurfaceReconstructionLogic = autoSurfaceReconstructionLogic() 
  
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    # Icons stuff
    self.moduleDirectoryPath = slicer.modules.autosurfacereconstruction.path.replace("PointRecorder.py","")
    self.playIcon = qt.QIcon(self.moduleDirectoryPath + '/Resources/Icons/playIcon.png')
    self.stopIcon = qt.QIcon(self.moduleDirectoryPath + '/Resources/Icons/stopIcon.png')
    self.recordIcon = qt.QIcon(self.moduleDirectoryPath + '/Resources/Icons/recordIcon.png')
    self.restartIcon = qt.QIcon(self.moduleDirectoryPath + '/Resources/Icons/restartIcon.png')
    self.saveIcon = qt.QIcon(self.moduleDirectoryPath + '/Resources/Icons/saveIcon.png')                             
    
    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input transform selector
    #
    self.inputSelector = slicer.qMRMLNodeComboBox()
    self.inputSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.inputSelector.selectNodeUponCreation = True
    self.inputSelector.addEnabled = False
    self.inputSelector.removeEnabled = False
    self.inputSelector.noneEnabled = False
    self.inputSelector.showChildNodeTypes = False
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Modified Transform: ", self.inputSelector)

        #
    # input transform selector
    #
    self.fixedSelector = slicer.qMRMLNodeComboBox()
    self.fixedSelector.nodeTypes = ["vtkMRMLLinearTransformNode"]
    self.fixedSelector.selectNodeUponCreation = True
    self.fixedSelector.addEnabled = False
    self.fixedSelector.removeEnabled = False
    self.fixedSelector.noneEnabled = False
    self.fixedSelector.showChildNodeTypes = False
    self.fixedSelector.setMRMLScene( slicer.mrmlScene )
    self.fixedSelector.setToolTip( "Pick the input to the algorithm." )
    parametersFormLayout.addRow("Spatial Transform: ", self.fixedSelector)
    
     # Controls
    self.controlsGroupBox = ctk.ctkCollapsibleGroupBox()
    self.controlsGroupBox.setTitle("Controls")
    controlsFormLayout = qt.QFormLayout(self.controlsGroupBox)
    parametersFormLayout.addRow(self.controlsGroupBox)
    
    hBoxLayoutControls = qt.QHBoxLayout()
    controlsFormLayout.addRow(hBoxLayoutControls)

    self.recordButton = qt.QPushButton(" Record")
    self.recordButton.setIcon(self.recordIcon)
    self.recordButton.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
    self.recordButton.enabled = False
    self.recordButton.checkable = True
    hBoxLayoutControls.addWidget(self.recordButton)

    self.saveButton = qt.QPushButton(" Save")
    self.saveButton.setIcon(self.saveIcon)
    self.saveButton.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
    self.saveButton.enabled = False
    hBoxLayoutControls.addWidget(self.saveButton)
    
    self.resetButton = qt.QPushButton(" Reset")
    self.resetButton.setIcon(self.restartIcon)
    self.resetButton.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
    self.resetButton.enabled = False
    hBoxLayoutControls.addWidget(self.resetButton)
    
    hBoxCheckBoxes = qt.QHBoxLayout()
    controlsFormLayout.addRow(hBoxCheckBoxes)

    self.singlePointCheckBox = qt.QCheckBox('Single Measurements')
    self.singlePointCheckBox.checked = False
    self.singlePointCheckBox.enabled = False
    hBoxCheckBoxes.addWidget(self.singlePointCheckBox)  
    
    # connections
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.recordButton.connect('clicked(bool)', self.onRecordClicked)
    self.resetButton.connect('clicked(bool)', self.onResetClicked)
    self.saveButton.connect('clicked(bool)', self.onSaveClicked)
    
    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

    self.autoSurfaceReconstructionLogic.setLayout()
    
  def onSaveClicked(self):
    self.autoSurfaceReconstructionLogic.saveData()
    
  def onRecordClicked(self):   
    if not self.autoSurfaceReconstructionLogic.observedNode:
      self.autoSurfaceReconstructionLogic.removeUpdateObserver()
      self.autoSurfaceReconstructionLogic.addUpdateObserver(self.inputSelector.currentNode(), self.fixedSelector.currentNode())
      self.autoSurfaceReconstructionLogic.clearPointsInPolyData()
    if self.singlePointCheckBox.checked:
      self.autoSurfaceReconstructionLogic.acquireSingleMeasurement(self.fixedSelector.currentNode())
      self.recordButton.checked = False
      return    
    if self.recordButton.checked:
      self.autoSurfaceReconstructionLogic.record = True
      self.enableWidgets(False)
    elif not self.recordButton.checked:
      self.autoSurfaceReconstructionLogic.record = False
      self.enableWidgets(True)
    
  def onResetClicked(self):
    reply = qt.QMessageBox.question(slicer.util.mainWindow(), 'Reset recorded points', 'Are you sure you want to reset?', qt.QMessageBox.Yes, qt.QMessageBox.No)
    if reply == qt.QMessageBox.Yes:
      self.autoSurfaceReconstructionLogic.reset = True
      self.autoSurfaceReconstructionLogic.pointCounter = 0
    else:
      return    

  def enableWidgets(self, enable):
    self.saveButton.enabled = enable
    self.singlePointCheckBox.enabled = enable
    
  def onSelect(self):
    self.recordButton.enabled = self.inputSelector.currentNode()
    self.resetButton.enabled = self.inputSelector.currentNode()
    if self.inputSelector.currentNode():
      self.autoSurfaceReconstructionLogic.record = False
      self.autoSurfaceReconstructionLogic.removeUpdateObserver()      
      self.autoSurfaceReconstructionLogic.clearPointsInPolyData()
      self.recordButton.enabled = True

class autoSurfaceReconstructionLogic(ScriptedLoadableModuleLogic):
 
  def __init__(self):
    self.observedNode = None
    self.outputObserverTag = -1
    self.record = False
    self.recordedModelNode = None
    self.reset = False       
    self.fixedNode = None
    self.pointCounter = 0
   # self.pointCounter = 30
  ############## Record
  def addUpdateObserver(self, inputNode, fixedNode):
    self.observedNode = inputNode
    self.fixedNode = fixedNode
    self.recordedModelNode = slicer.util.getNode('RecordedModel')
    if not self.recordedModelNode:
      recordedPoints = vtk.vtkPoints()
      recordedVertices = vtk.vtkCellArray()               
      recordedPolyData = vtk.vtkPolyData()
      recordedPolyData.SetPoints(recordedPoints)
      recordedPolyData.SetVerts(recordedVertices)
      self.recordedModelNode = self.addModelToScene(recordedPolyData, "RecordedModel", [0, 1, 0])    
      self.recordedModelNode.GetModelDisplayNode().SetPointSize(3)
    if self.outputObserverTag == -1:
      self.outputObserverTag = inputNode.AddObserver('ModifiedEvent', self.updateSceneCallback)

  def removeUpdateObserver(self):
    if self.outputObserverTag != -1:
      self.observedNode.RemoveObserver(self.outputObserverTag)
      self.outputObserverTag = -1
      self.observedNode = None
          
  def updateSceneCallback(self, modifiedNode, event=None):            
    if self.reset:
      self.clearPointsInPolyData()
      self.reset = False
    if self.record:
      self.acquireSingleMeasurement(self.fixedNode)
      
  def acquireSingleMeasurement(self, transformNode):
    ras = [0,0,0]
    m = vtk.vtkMatrix4x4()
    transformNode.GetMatrixTransformToWorld(m)
    print m
    ras[0] = m.GetElement(0, 3)
    ras[1] = m.GetElement(1, 3)
    ras[2] = m.GetElement(2, 3)   
    self.addPointToPolyData(self.recordedModelNode.GetPolyData(), ras)
    
  def addPointToPolyData(self, polyData, ras):     

    print "nuevo punto!!!"
    self.pointCounter = self.pointCounter + 1;
    pid = vtk.vtkIdList()
    pid.SetNumberOfIds(1);
    temp = polyData.GetPoints().InsertNextPoint(ras[0], ras[1], ras[2])    
    pid.SetId(0, temp)    
    polyData.GetVerts().InsertNextCell(pid)        
    polyData.Modified() 

    
    # check every 30 recorded points if the standard deviation is low
    if (self.pointCounter%30) == 0:
      
      sd = self.testStandardDeviation(polyData)
      if sd < 1:

        self.record = False
        if self.pointCounter>100:
          self.calculateSurface(self.recordedModelNode)
        print "El standard deviation es bajo ya no se mueve"


  def testStandardDeviation(self, polyData):
    print "ya hay guardados 15 puntos!"
        
    coord = [0,0,0]
    for i in range(30):
      ras = [0,0,0] 

      polyData.GetPoint(self.pointCounter - 30 + i,ras) #save coordinates in ras. 

      if i == 0:
        coord = ras
      else:
        coord = np.vstack((coord,ras))

    sd0 = np.std(coord, axis=0)
    sdMean = np.mean(sd0)

    print coord
    print "El standard deviation es: {}".format(sdMean)
    print "el pointCounter es: {}".format(self.pointCounter)

    return sdMean

  def clearPointsInPolyData(self,): 
    if self.recordedModelNode:
      newPoints = vtk.vtkPoints()
      newVertices = vtk.vtkCellArray()               
      newPolyData = vtk.vtkPolyData()
      newPolyData.SetPoints(newPoints)
      newPolyData.SetVerts(newVertices)    
      self.recordedModelNode.GetPolyData().DeepCopy(newPolyData)     
      self.recordedModelNode.GetPolyData().Modified()  
      
  def addModelToScene(self, polyData, name, color):

    scene = slicer.mrmlScene
    node = slicer.vtkMRMLModelNode()
    node.SetScene(scene)
    node.SetName(name)
    if polyData is not None:
      node.SetAndObservePolyData(polyData)

    modelDisplay = slicer.vtkMRMLModelDisplayNode()
    modelDisplay.SetColor(color)
    modelDisplay.SetScene(scene)
    scene.AddNode(modelDisplay)
    node.SetAndObserveDisplayNodeID(modelDisplay.GetID())
    scene.AddNode(node)
    return node
    
  ############## Save
  def saveData(self):
    self.pathToCreatedSaveDir = self.createShareDirectory()  
    dateAndTime = time.strftime("_%Y-%m-%d_%H-%M-%S")  
    path = self.pathToCreatedSaveDir + '/Points' + dateAndTime  
    # Save model to .vtk
    slicer.modules.models.logic().SaveModel(path + '.vtk', self.recordedModelNode)
    
  def createShareDirectory(self): 
    date = time.strftime("%Y-%m-%d")        
    shareDirPath = slicer.modules.autosurfacereconstruction.path.replace("autoSurfaceReconstruction.py","") + 'Output/' + date
    if not os.path.exists(shareDirPath):
      os.makedirs(shareDirPath)   
    return shareDirPath    
    slicer.modules.models.logic().SaveModel(path + '.vtk', self.recordedModelNode)    
    
  ############## Layout
  def setLayout(self):
    lm=slicer.app.layoutManager()
    lm.setLayout(4) # One 3D-view
    self.resetLayoutFocalPoint(0)  
    self.zoomInThreeDView(0, 8)    
    self.setAxisAndBoxVisibility('View1', False)  
  
  def setAxisAndBoxVisibility(self, viewName, visible):
    view = slicer.mrmlScene.GetFirstNodeByName(viewName)               
    view.SetAxisLabelsVisible(visible)
    view.SetBoxVisible(visible)  
  
  def resetLayoutFocalPoint(self, viewIdx):
    threeDWidget = slicer.app.layoutManager().threeDWidget(viewIdx)
    threeDView = threeDWidget.threeDView()
    threeDView.resetFocalPoint()   
  
  def zoomInThreeDView(self, viewIdx, zoomFactor):
    threeDWidget = slicer.app.layoutManager().threeDWidget(viewIdx)
    threeDView = threeDWidget.threeDView()
    for zoom in range(zoomFactor):
      threeDView.zoomIn()    

  def calculateSurface(self, inputModel):
    
    outputModelNode = slicer.util.getNode('ComputedNormals')
    
    if not outputModelNode:
      outputModelNode = self.addModelToScene(None, 'ComputedNormals', [0, 0, 1])  
      outputModelNode.SetDisplayVisibility(False)
    orientatedGlyphs = slicer.util.getNode('OrientatedGlyphs')
    if not orientatedGlyphs:
      orientatedGlyphs = self.addModelToScene(None, 'OrientatedGlyphs', [0, 1, 0])   #green     
    
    slicer.modules.pointsetprocessingcpp.logic().Apply_vtkPointSetNormalEstimation(inputModel, outputModelNode, orientatedGlyphs, 1, 4, 50.00, 70, 1, True, True)
    orientatedGlyphsNode = slicer.util.getNode('orientatedGlyphs')

    inputModelNode = slicer.util.getNode('ComputedNormals')
    outputModelNode = slicer.util.getNode('ComputedSurface')

    if not outputModelNode:
      outputModelNode = self.addModelToScene(None, 'ComputedSurface', [1, 0, 0])#red
    
    # call to cpp function from slicerPontSetProccesing module
    slicer.modules.pointsetprocessingcpp.logic().Apply_vtkPoissionReconstruction(inputModelNode, outputModelNode, 6, 1.25, 8, 8, 1, False, False, True)
    
    return True


 