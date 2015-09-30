import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

import time

class AutoSurfaceRecontruction(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "AutoSurfaceRecontruction" # TODO make this more human readable by adding spaces
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

class AutoSurfaceRecontructionWidget(ScriptedLoadableModuleWidget):

  def setup(self):
    self.AutoSurfaceRecontructionLogic = AutoSurfaceRecontructionLogic() 
  
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    # Icons stuff
    self.moduleDirectoryPath = slicer.modules.autosurfacerecontruction.path.replace("AutoSurfaceRecontruction.py","")
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

    pointSetProcessingCollapsibleButton = ctk.ctkCollapsibleButton()
    pointSetProcessingCollapsibleButton.text = "Automatic Surface Reconstruction"
    self.layout.addWidget(pointSetProcessingCollapsibleButton)
    pointSetProcessingFormLayout = qt.QFormLayout(pointSetProcessingCollapsibleButton)
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


    # Input model

    self.modelSelector = slicer.qMRMLNodeComboBox()
    self.modelSelector.nodeTypes = ( ("vtkMRMLModelNode"), "" )
    self.modelSelector.selectNodeUponCreation = True
    self.modelSelector.addEnabled = False
    self.modelSelector.removeEnabled = False
    self.modelSelector.noneEnabled = False
    self.modelSelector.showHidden = False
    self.modelSelector.showChildNodeTypes = False
    self.modelSelector.setMRMLScene( slicer.mrmlScene )
    self.modelSelector.setToolTip( "Pick the input to the algorithm." )
    pointSetProcessingFormLayout.addRow("Input Model: ", self.modelSelector) 

    self.nbrOfPointsLabel = qt.QLabel('Number of Points in Input Model: - ')
    pointSetProcessingFormLayout.addRow(self.nbrOfPointsLabel)

    self.inputPointSizeSlider = ctk.ctkSliderWidget()
    self.inputPointSizeSlider.setDecimals(0)
    self.inputPointSizeSlider.singleStep = 1
    self.inputPointSizeSlider.minimum = 1
    self.inputPointSizeSlider.maximum = 10
    self.inputPointSizeSlider.value = 1
    pointSetProcessingFormLayout.addRow('Input Model Point Size: ', self.inputPointSizeSlider)

    self.vtkCalculateSurfaceButton = qt.QPushButton("Exit Surface")
    self.vtkCalculateSurfaceButton.enabled = True
    self.vtkCalculateSurfaceButton.checkable = True
    pointSetProcessingFormLayout.addRow(self.vtkCalculateSurfaceButton)
    
    
    # connections
    self.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.recordButton.connect('clicked(bool)', self.onRecordClicked)
    self.resetButton.connect('clicked(bool)', self.onResetClicked)
    self.saveButton.connect('clicked(bool)', self.onSaveClicked)
    self.vtkCalculateSurfaceButton.connect('clicked(bool)', self.onCalculateSurface)
    self.inputPointSizeSlider.connect('valueChanged (double)', self.onInputPointSliderModified)
    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

    self.AutoSurfaceRecontructionLogic.setLayout()

  def onInputPointSliderModified(self, value):
    inputModelNode = self.modelSelector.currentNode()
    if inputModelNode:
      inputModelNode.GetModelDisplayNode().SetPointSize(value)
    
  def onSaveClicked(self):
    self.AutoSurfaceRecontructionLogic.saveData()
    
  def onRecordClicked(self):   
    if not self.AutoSurfaceRecontructionLogic.observedNode:
      self.AutoSurfaceRecontructionLogic.removeUpdateObserver()
      self.AutoSurfaceRecontructionLogic.addUpdateObserver(self.modelSelector.currentNode(), self.fixedSelector.currentNode())
      self.AutoSurfaceRecontructionLogic.clearPointsInPolyData()
    if self.singlePointCheckBox.checked:
      self.AutoSurfaceRecontructionLogic.acquireSingleMeasurement(self.fixedSelector.currentNode())
      self.recordButton.checked = False
      return    
    if self.recordButton.checked:
      self.AutoSurfaceRecontructionLogic.record = True
      self.enableWidgets(False)
    elif not self.recordButton.checked:
      self.AutoSurfaceRecontructionLogic.record = False
      self.enableWidgets(True)
    
  def onResetClicked(self):
    reply = qt.QMessageBox.question(slicer.util.mainWindow(), 'Reset recorded points', 'Are you sure you want to reset?', qt.QMessageBox.Yes, qt.QMessageBox.No)
    if reply == qt.QMessageBox.Yes:
      self.AutoSurfaceRecontructionLogic.reset = True
    else:
      return    

  def enableWidgets(self, enable):
    self.saveButton.enabled = enable
    self.singlePointCheckBox.enabled = enable
    
  def onSelect(self):
    self.recordButton.enabled = self.inputSelector.currentNode()
    self.resetButton.enabled = self.inputSelector.currentNode()
    if self.inputSelector.currentNode():
      self.AutoSurfaceRecontructionLogic.record = False
      self.AutoSurfaceRecontructionLogic.removeUpdateObserver()      
      self.AutoSurfaceRecontructionLogic.clearPointsInPolyData()
      self.recordButton.enabled = True

  def onCalculateSurface(self):
    inputModel = self.modelSelector.currentNode()
    self.AutoSurfaceRecontructionLogic.calculateSurface(inputModel)


class AutoSurfaceRecontructionLogic(ScriptedLoadableModuleLogic):
 
  def __init__(self):
    self.observedNode = None
    self.outputObserverTag = -1
    self.record = False
    self.recordedModelNode = None
    self.reset = False       
    self.fixedNode = None
    

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
      self.recordedModelNode = self.addModelToScene(recordedPolyData, "RecordedModel")    
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
    pid = vtk.vtkIdList()
    pid.SetNumberOfIds(1);
    temp = polyData.GetPoints().InsertNextPoint(ras[0], ras[1], ras[2])    
    pid.SetId(0, temp)    
    polyData.GetVerts().InsertNextCell(pid)        
    polyData.Modified() 
    
  def clearPointsInPolyData(self,): 
    if self.recordedModelNode:
      newPoints = vtk.vtkPoints()
      newVertices = vtk.vtkCellArray()               
      newPolyData = vtk.vtkPolyData()
      newPolyData.SetPoints(newPoints)
      newPolyData.SetVerts(newVertices)    
      self.recordedModelNode.GetPolyData().DeepCopy(newPolyData)     
      self.recordedModelNode.GetPolyData().Modified()  
      
  def addModelToScene(self, polyData, name):
    scene = slicer.mrmlScene
    node = slicer.vtkMRMLModelNode()
    node.SetScene(scene)
    node.SetName(name)
    node.SetAndObservePolyData(polyData)
    modelDisplay = slicer.vtkMRMLModelDisplayNode()
    modelDisplay.SetColor(0, 1, 0)
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
    shareDirPath = slicer.modules.autosurfacereconstruction.path.replace("AutoSurfaceRecontruction.py","") + 'Output/' + date
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

  ####### Calculate Surface 

  def calculateSurface(self, inputModel):
    
    ## Esta funcion es la que llama la funcionalidad siguiente para hallar las normales
    #logic.vtkPointSetNormalEstimation(self.modelSelector.currentNode(), self.modeTypeComboBox.currentIndex, self.numberOfNeighborsSlider.value, self.radiusSlider.value, self.knnSlider.value, self.graphTypeComboBox.currentIndex, self.runtimeLabel)
    
    outputModelNode = slicer.util.getNode('ComputedNormals')
    
    if not outputModelNode:
      outputModelNode = self.createModelNode('ComputedNormals', [0, 0, 1])  
      outputModelNode.SetDisplayVisibility(False)
    orientatedGlyphs = slicer.util.getNode('OrientatedGlyphs')
    if not orientatedGlyphs:
      orientatedGlyphs = self.createModelNode('OrientatedGlyphs', [0, 1, 0])        
    
    slicer.modules.pointsetprocessingcpp.logic().Apply_vtkPointSetNormalEstimation(inputModel, outputModelNode, orientatedGlyphs, 1, 4, 50.00, 70, 1, True, True)
    orientatedGlyphsNode = slicer.util.getNode('orientatedGlyphs')
   # if orientatedGlyphsNode:
    #  orientatedGlyphsNode.SetDisplayVisibility(visible)

    ##Esta funcion es la que llama la reconstruccion de la superficie, pero la funcionalidad es la siguiente
    #logic.vtkPoissionReconstruction(self.depthSlider.value, self.scaleSlider.value, self.solverDivideSlider.value, self.isoDivideSlider.value, self.samplesPerNodeSlider.value, self.confidenceComboBox.currentIndex, self.verboseComboBox.currentIndex, self.runtimeLabel)
    inputModelNode = slicer.util.getNode('ComputedNormals')
    outputModelNode = slicer.util.getNode('ComputedSurface')
    if not outputModelNode:
      outputModelNode = self.createModelNode('ComputedSurface', [1, 0, 0])
    
    slicer.modules.pointsetprocessingcpp.logic().Apply_vtkPoissionReconstruction(inputModelNode, outputModelNode, 6, 1.25, 8, 8, 1, False, False, True)
    
    return True


  def createModelNode(self, name, color):
    scene = slicer.mrmlScene
    modelNode = slicer.vtkMRMLModelNode()
    modelNode.SetScene(scene)
    modelNode.SetName(name)
    modelDisplay = slicer.vtkMRMLModelDisplayNode()
    modelDisplay.SetColor(color)
    modelDisplay.SetScene(scene)
    scene.AddNode(modelDisplay)
    modelNode.SetAndObserveDisplayNodeID(modelDisplay.GetID())
    scene.AddNode(modelNode)  
    return modelNode