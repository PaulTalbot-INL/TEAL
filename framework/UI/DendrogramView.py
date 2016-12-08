#!/usr/bin/env python

import numpy as np
import sys

from PySide import QtCore as qtc
from PySide import QtGui as qtg
from PySide import QtSvg as qts

from BaseView import BaseView
from ZoomableGraphicsView import ZoomableGraphicsView
from Tree import Node
import colors

def linakgeToTree(*linkages):
  """
    Convert a linkage matrix into a tree that knows how to perform its own
    layout.
    In @ linkages, np.array(s), one or more linkage matrices that will each be
    made into a single tree with a null node used to connect them allowing
    them to be tied together into a single data structure.
  """

  maxLevel = 0

  for linkage in linkages:
    maxLevel = max(maxLevel, linkage[-1,2])

  ## This empty root allows us to create a fake node that connects the forest
  root = Node('None', None, maxLevel,0)

  for linkage in linkages:
    ## Iterate through the linkage matrix in reverse order since the last merge
    ## will be the root node of this tree
    n = linkage.shape[0]+1

    for i in range(linkage.shape[0]-1,-1,-1):
      newIdx = n+i
      leftChildIdx,rightChildIdx,level,size = linkage[i,:]
      leftChildIdx = int(leftChildIdx)
      rightChildIdx = int(rightChildIdx)
      size = int(size)

      print('%d %d %d %f %d' % (newIdx, leftChildIdx, rightChildIdx, level, size))

      node = root.getNode(newIdx)

      if node is None:
        ## If the node does not exist yet, then we are constructing a new
        ## subtree
        node = root.addChild(newIdx, level, size)
        ## This is a new subtree, so in order to get the correct size at the
        ## root, we need to add the total size of this subtree.
        root.size += size
      else:
        ## Otherwise, we need to update this node's level and size with the
        ## information from this merge of the linkage matrix
        node.level = level
        node.size = size

      ## We will update these children when we get to their merges, if they are
      ## leaves, then they are at level zero and have only one item, themselves.
      node.addChild(leftChildIdx, 0, 1)
      node.addChild(rightChildIdx, 0, 1)

  return root

class DendrogramView(ZoomableGraphicsView,BaseView):
  """
    A view that shows a hierarchical data object.
  """
  maxDiameterMultiplier = 0.1
  minDiameterMultiplier = 0.001
  def __init__(self, linkage, parent=None, level=None, debug=False):
    """
    """
    ZoomableGraphicsView.__init__(self,parent)
    BaseView.__init__(self,parent)

    self.tree = linakgeToTree(linkage)

    self.level = level
    self.levels = sorted(set(linkage[:,2]))

    if self.level is None:
      self.level = 0

    self.colorMap = {}

    levelAction = self.rightClickMenu.addAction('Set Level')
    levelAction.triggered.connect(self.setLevel)
    incAction = self.rightClickMenu.addAction('Raise Threshold Level')
    incAction.triggered.connect(self.increaseLevel)
    decAction = self.rightClickMenu.addAction('Lower Threshold Level')
    decAction.triggered.connect(self.decreaseLevel)

    self.edgeAction = self.rightClickMenu.addAction('Smooth Edges')
    self.edgeAction.setCheckable(True)
    self.edgeAction.setChecked(False)
    self.edgeAction.triggered.connect(self.createScene)

    self.scene().selectionChanged.connect(self.select)
    self.createScene()

  def increaseLevel(self):
    """
    """
    for lvl in self.levels:
      if lvl > self.level:
        self.level = lvl
        self.levelChanged()
        return

  def decreaseLevel(self):
    """
    """
    for lvl in reversed(self.levels):
      if lvl < self.level:
        self.level = lvl
        self.levelChanged()
        return

  def select(self):
    """
    """
    selectedKeys = []
    for key,graphic in self.items.iteritems():
      if graphic in self.scene().selectedItems():
        selectedKeys.append(key)
    # self.tree.SetSelection(selectedKeys)

  def setLevel(self):
    """
    """
    position = self.mapFromGlobal(self.rightClickMenu.pos())
    mousePt = self.mapToScene(position.x(),position.y()).y()

    minLevel = 0
    maxLevel = max(self.levels)
    effectiveHeight = self.scene().height()-2*self.padding
    ty = (self.padding + effectiveHeight - mousePt)/effectiveHeight
    wy = ty*float(maxLevel)

    self.level = np.clip(wy,minLevel,maxLevel)
    self.levelChanged()

  def selectionChanged(self):
    ## Disable the communication so we don't end up in infinite callbacks
    self.scene().selectionChanged.disconnect(self.select)

    selectedKeys = self.segmentation.selectedSegments
    for key,graphic in self.items.iteritems():
      if key in selectedKeys:
        graphic.setSelected(True)
      else:
        graphic.setSelected(False)

    ## Re-enable the communication
    self.scene().selectionChanged.connect(self.select)

  def levelChanged(self):
    """
    """
    # level = self.level

    # self.animation = qtg.QGraphicsItemAnimation()
    # self.animation.setItem(self.items["Threshold"])
    # self.animation.setTimeLine(self.timer)
    # self.timer.valueChanged.connect(self.animate)
    # self.timer.finished.connect(self.createScene)

    # width = self.scene().width()
    # height = self.scene().height()
    # minDim = min([width,height])
    # minDiameter = DendrogramView.minDiameterMultiplier*minDim
    # maxDiameter = DendrogramView.maxDiameterMultiplier*minDim
    # self.padding = maxDiameter/2.
    # usableHeight = height-2*self.padding

    # level = height - usableHeight*level/maxLevel-self.padding

    # finalScale = level/float(self.items["Threshold"].rect().height())
    # self.animation.setScaleAt(0, 1, 1)
    # self.animation.setScaleAt(1, 1, finalScale)

    # # totalCount = self.tree.size
    # totalCount = self.tree.getLeafCount()
    # self.animatingItems = {}
    # for key,item in self.items.iteritems():
    #   if key == 'Threshold':
    #     continue

    #   count = self.tree.getNode(key).size
    #   initialDiameter = item.rect().width()
    #   finalDiameter = float(count)/totalCount*(maxDiameter-minDiameter)+minDiameter
    #   if initialDiameter != finalDiameter:
    #     self.animatingItems[key] = {}
    #     self.animatingItems[key]['finalDiameter'] = finalDiameter
    #     self.animatingItems[key]['initialDiameter'] = initialDiameter
    #     self.animatingItems[key]['x0'] = item.rect().x()+initialDiameter/2.
    #     self.animatingItems[key]['y0'] = item.rect().y()+initialDiameter/2.
    #     self.animatingItems[key]['item'] = item

      # for i in range(self.timer.startFrame(),self.timer.endFrame()):
      #   step = (i - self.timer.startFrame()) / float(frameRange)
      #   diameter = step*finalDiameter + (1-step)*initialDiameter
      #   scale = step*finalScale + (1-step)*1
      #   x = x0 - diameter/2.
      #   y = y0 - diameter/2.
      #   # self.animations[-1].setPosAt(step, qtc.QPointF(x,y))
      # self.animations[-1].setScaleAt(0, 1, 1)
      # self.animations[-1].setScaleAt(1, finalScale, finalScale)
      # self.animations[-1].setPosAt(0, qtc.QPointF(0,0))
      # self.animations[-1].setPosAt(1, qtc.QPointF(1/finalScale,1/finalScale))
      # self.animations[-1].setPosAt(1, qtc.QPointF((x0+finalDiameter/2.)/finalScale,(y0+finalDiameter/2.)/finalScale))

    ## Disabling animation as it can cause a segfault
    # self.timer.start()
    self.createScene()

  def animate(self):
    """
    """
    step = self.timer.currentValue()
    for animatingItem in self.animatingItems.values():
      item = animatingItem['item']
      diameter = step*animatingItem['finalDiameter'] + (1-step)*animatingItem['initialDiameter']
      x = animatingItem['x0'] - diameter/2.
      y = animatingItem['y0'] - diameter/2.
      item.setRect(x,y,diameter,diameter)
    # self.scene().update()

  def createScene(self):
    """
    """
    self.items = {}
    scene = self.scene()
    scene.clear()

    selected = []
    level = self.level
    maxLevel = self.levels[-1]

    if self.fillAction.isChecked():
      aspectRatio = float(self.width())/float(self.height())
      scene.setSceneRect(0, 0,
                         ZoomableGraphicsView.defaultSceneDimension*aspectRatio,
                         ZoomableGraphicsView.defaultSceneDimension)
    else:
      scene.setSceneRect(0, 0,
                         ZoomableGraphicsView.defaultSceneDimension,
                         ZoomableGraphicsView.defaultSceneDimension)

    width = scene.width()
    height = scene.height()
    minDim = min([width,height])

    minDiameter = DendrogramView.minDiameterMultiplier*minDim
    maxDiameter = DendrogramView.maxDiameterMultiplier*minDim

    self.padding = maxDiameter/2.

    usableWidth = width-2*self.padding
    usableHeight = height-2*self.padding

    white = qtg.QColor('#FFFFFF')
    gray = qtg.QColor('#999999')
    black = qtg.QColor('#000000')
    transparentGray = gray.lighter()
    transparentGray.setAlpha(127)

    scene.addRect(0,0,width,height,qtg.QPen(qtc.Qt.black))
    level = height - usableHeight*level/maxLevel-self.padding
    self.items['Threshold'] = scene.addRect(0,0,width,level,qtg.QPen(gray),qtg.QBrush(transparentGray))

    root = self.tree

    totalCount = root.getLeafCount()
    xOffset = 0
    ids = []
    points = []
    edges = []
    for node in root.children:
      count = node.getLeafCount()
      myWidth = float(count)/totalCount*usableWidth
      (myIds,myPoints,myEdges) = node.Layout(xOffset,myWidth)
      ids.extend(myIds)
      points.extend(myPoints)
      edges.extend(myEdges)
      xOffset += myWidth

    # totalCount = root.size

    for edge in edges:
      idx1 = ids.index(edge[0])
      idx2 = ids.index(edge[1])

      x1 = points[idx1][0]+self.padding
      x2 = points[idx2][0]+self.padding

      y1 = height - usableHeight*points[idx1][1]/maxLevel-self.padding
      y2 = height - usableHeight*points[idx2][1]/maxLevel-self.padding

      path = qtg.QPainterPath()
      path.moveTo(x1,y1)
      if self.edgeAction.isChecked():
        path.cubicTo(x1,y1+(y2-y1)*0.25, x2,y2-(y2-y1)*0.25,x2,y2)
      else:
        path.lineTo(x2,y1)
        path.lineTo(x2,y2)

      scene.addPath(path,qtg.QPen(gray))


    for _id,point in zip(ids,points):
      node = self.tree.getNode(_id)
      count = node.size
      diameter = float(count)/totalCount*(maxDiameter-minDiameter)+minDiameter

      if _id not in self.colorMap:
        self.colorMap[_id] = qtg.QColor(colors.colorCycle.next()) # qtg.QColor(*tuple(255*np.random.rand(3)))
        # color = gray
      # else:
      color = self.colorMap[_id]

      x = point[0]+self.padding
      y = height - usableHeight*point[1]/maxLevel-self.padding
      brush = qtg.QBrush(color)
      if _id in selected:
        pen = qtg.QPen(black)
      else:
        pen = qtc.Qt.NoPen
      self.items[_id] = scene.addEllipse(x-diameter/2.,y-diameter/2.,diameter,diameter,pen,brush)
      self.items[_id].setFlag(qtg.QGraphicsItem.ItemIsSelectable)
      self.items[_id].setToolTip('   id: %d\ncount: %d\nlevel: %f' %(_id,int(count),node.level))
      if diameter == 0:
        self.items[_id].setZValue(sys.float_info.max)
      else:
        self.items[_id].setZValue(1./diameter)

    self.fitInView(scene.sceneRect(),qtc.Qt.KeepAspectRatio)