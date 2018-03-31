from PyQt5.QtWidgets import * 
from PyQt5.QtGui import QPainter, QColor, QFont, QImage, QPixmap
from PyQt5.QtCore import Qt, QSize
import sys

import latools.helpers as helpers
import pyqtgraph as pg
import numpy as np
import uncertainties.unumpy as un

class GraphPane():
	"""
	The lower section of the stage screens that displays the graphs produced by the stage controls.
	This is currently under development and simply shows how things will be displayed when the 
	functionality is produced.
	"""
	def __init__(self, project):

		# We make a frame for this section
		self.graphFrame = QFrame()
		self.graphFrame.setFrameShape(QFrame.StyledPanel)
		self.graphFrame.setFrameShadow(QFrame.Raised)

		# We use a vertical layout for the pane as a whole
		self.graphMainLayout = QVBoxLayout(self.graphFrame)

		# We add a label
		self.graphName = QLabel("<b>Data subset name:</b> details of the data visualisation type")
		self.graphMainLayout.addWidget(self.graphName)

		# We use a horizontal layout for the content
		self.graphLayout = QHBoxLayout()
		self.graphMainLayout.addLayout(self.graphLayout)

		# GRAPH

		# This GraphTest class is now sent the project object
		self.graph = GraphWindow(project)

		self.graphLayout.addWidget(self.graph)
		self.graph.setFixedSize(900,300)

		# GRAPH OPTIONS

		# We add a vertical layout, and align the content to the top
		self.graphOptionsLayout = QVBoxLayout()
		self.graphLayout.addLayout(self.graphOptionsLayout)
		self.graphOptionsLayout.setAlignment(Qt.AlignTop)

		self.graphOptionsLabel = QLabel("Options")
		# We add a minimum width to the layout via this label
		self.graphOptionsLayout.addWidget(self.graphOptionsLabel)

		# We temporarily list a bunch of dummy options.
		self.graphCheck1 = QCheckBox("Option 1")
		self.graphOptionsLayout.addWidget(self.graphCheck1)

		self.graphCheck2 = QCheckBox("Option 2")
		self.graphOptionsLayout.addWidget(self.graphCheck2)

		self.graphCheck3 = QCheckBox("Option 3")
		self.graphOptionsLayout.addWidget(self.graphCheck3)

		self.graphCheck4 = QCheckBox("Option 4")
		self.graphOptionsLayout.addWidget(self.graphCheck4)

		self.graphCheck5 = QCheckBox("Option 5")
		self.graphOptionsLayout.addWidget(self.graphCheck5)

		self.graphCheck6 = QCheckBox("Option 6")
		self.graphOptionsLayout.addWidget(self.graphCheck6)

	# This addToLayout method is used so that the graph frame can be defined early,
	# and therefore, passed to the controls objects so that they can access it.
	# Then, after they are added to the layout, this pane is added below the controls.
	def addToLayout(self, stageLayout):
		stageLayout.addWidget(self.graphFrame)

	# TO DO: find a way to update the graph, either through passing the project object again, or by some
	# other live-updating approach.
	def updateGraph(self, stage):
		self.graph.update(None, stage)

class GraphWindow(pg.GraphicsLayoutWidget):

	def __init__(self, project):
		super().__init__()
		self.project = project
		# For testing purposes, the sample and stage is hard coded
		self.sampleName = 'Sample-1'
		self.focusStage = 'rawdata'
		# Add plot window to the layout
		graph = self.addPlot(title=self.sampleName)
		graph.setLogMode(x=False, y=True)
		graph.setLabel('left', 'Counts')
		graph.setLabel('bottom', 'Time', units='s')

		self.graph = graph

		# Add legend window to the layout
		legend = self.addViewBox()
		legend.setMaximumWidth(100)

		self.legend = legend

		l = pg.LegendItem()
		l.setParentItem(self.legend)
		l.anchor((0,0), (0,0))

		self.l = l

	# Updates the graph based off Sample and Focustage name
	def update(self, sample, stage):
		# Clear existing plot
		self.graph.clear()

		# Set stage
		self.focusStage = stage

		# We create the data object
		dat = self.project.eg.data[self.sampleName]
		# Get list of analytes (elements) from the data object
		analytes = dat.analytes

		# For each analyte: get x and y, and plot them
		# Then add it to the legend
		for a in analytes:
			x = dat.Time
			y, yerr = helpers.stat_fns.unpack_uncertainties(dat.data[self.focusStage][a])
			y[y == 0] = np.nan
			plt = self.graph.plot(x, y, pen=pg.mkPen(dat.cmap[a], width=2), label=a)
			self.l.addItem(plt, a)