""" Builds and updates the graph, and displays it at the bottom of the stages screen.
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt

import latools.helpers as helpers
import re
import itertools
import pyqtgraph as pg
import numpy as np
import uncertainties.unumpy as un
import matplotlib.pyplot as plt
from functools import partial

class GraphPane():
	"""
	The lower section of the stage screens that displays the graphs produced by the stage controls.
	All of the stages share the one Graph Pane instance.
	"""
	def __init__(self, project):
		"""
		Initialising builds the graph pane and prepares it to display data when the stages activate it.

		Parameters
		----------
		project : RunningProject
			This object contains all of the information unique to the current project.
			The stages update the project object and the graph displays its current state.
		"""
		self.project = project

		# We make a frame for this section
		self.graphFrame = QFrame()
		self.graphFrame.setFrameShape(QFrame.StyledPanel)
		self.graphFrame.setFrameShadow(QFrame.Raised)

		# We use a vertical layout for the pane as a whole
		self.graphMainLayout = QVBoxLayout(self.graphFrame)
		self.graphMainLayout.stretch(1)

		# We use a horizontal layout for the content
		self.graphLayout = QHBoxLayout()
		self.graphMainLayout.addLayout(self.graphLayout)

		# GRAPH
		# The project object is sent to the GraphWindow object
		self.graph = MainGraph(project)
		self.bkgGraph = BkgGraph(project)
		self.caliGraph = CaliGraph(project)
		self.crossPlot = Crossplot(project)

		#  We add the graph to the pane and set minimum dimensions
		self.graphLayout.addWidget(self.graph)
		self.graph.setMinimumWidth(900)
		self.graph.setMinimumHeight(300)


	def addToLayout(self, stageLayout):
		""" Adds the graph to the stage layout. It is a function so that this can occur after the rest of the
			stage screens are built.

			Parameters
			----------
			stagelayout : QVBoxLayout
				The layout for the stage screen that the graph pane will be added to the bottom of.
		"""
		stageLayout.addWidget(self.graphFrame)

	# Updates the graph
	def updateGraph(self, importing=False, showRanges=False):
		""" Updates all currently active graphs. Call this function whenever the graphs need to be updated
			to reflect new settings

			Parameters
			----------
			stage : String
				The name of the stage you want the graph to display for the current dataset
			importing: Boolean
				This determines whether or not to update graph's settings (available samples, etc).
				By default this is set to False.

		"""

		# Initialise graph when importing new data
		if importing:
			self.graph.initialiseGraph()
			self.bkgGraph.initialiseGraph()
			self.crossPlot.initialiseGraph()
		self.graph.updateFocus(showRanges)
		self.graph.hideInternalStandard()
		self.graph.autorange()

	def updateBkg(self):
		if self.bkgGraph.populated:
			self.bkgGraph.updateData()
		else:
			self.bkgGraph.populateGraph()

	def showAuxGraph(self, bkg=False, cali=False, cross=False):
		if bkg:
			self.bkgGraph.showGraph()
		if cali:
			self.caliGraph.populateGraph()
			self.caliGraph.showGraph()
		if cross:
			self.crossPlot.startup()
			self.crossPlot.showGraph()


class GraphWindow(QWidget):
	def __init__(self, project):
		"""	Initialises an empty PyQtGraph plot, containers for all graph settings, a new window button
		that is initially hidden till data is set

		Parameters
		----------
		project : RunningProject
			This object contains all of the information unique to the current project.
			The stages update the project object and the graph displays its current state.

		"""
		super().__init__()
		self.project = project
		self.sampleName = ""	
		self.graph = None
		self.highlightedAnalytes = []
		self.currentInternalStandard = None
		self.populated = False
		

		# dicts for storing {analyte: checkbox pairs, analyte: pg.PlotDataItem pairs}
		self.legendEntries = {}
		self.filts = {}
		self.graphLines = {}
		self.graphErrorbars = {}
		self.graphScatters = {}
		self.graphLines = {}
		self.graphHistograms = {}
		self.graphFills = {}

		self.layout = QHBoxLayout()

		self.setLayout(self.layout)

	# function to aid connection development
	def dummy(self, *args, **kwargs):
		"""
		Dummy function for identifying connection content.
		"""
		for arg in args:
			print(arg, type(arg))
		for k, v in kwargs.items():
			print(k, v, type(v))

	def hex_2_rgba(self, value, alpha=255):
		"""
			convert hex to rgb colour
		"""
		value = value.lstrip('#')
		lv = len(value)
		rgba = [int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)] + [int(alpha)]
		srgba = ['{:.0f}'.format(s) for s in rgba]
		return rgba
		#return 'rgba(' + ','.join(srgba) + ')'

	def initialiseSamples(self):
		"""
			Add list of samples to the layout
		"""

		samples = QWidget()
		samplesLayout = QVBoxLayout()
		samplesLayout.setAlignment(Qt.AlignTop)
		samples.setLayout(samplesLayout)

		self.samplesLayout = samplesLayout

		# Add List widget
		sampleList = QListWidget()
		sampleList.setMaximumWidth(100)
		sampleList.itemSelectionChanged.connect(self.swapSample)
		samplesLayout.addWidget(sampleList)

		self.sampleList = sampleList

		self.layout.addWidget(samples)

		# log-scale check box
		yLogCheckBox = QCheckBox()
		yLogCheckBox.setMaximumWidth(100)
		yLogCheckBox.setText('log(y)')
		yLogCheckBox.setChecked(True)
		yLogCheckBox.stateChanged.connect(self.updateLogScale)
		samplesLayout.addWidget(yLogCheckBox)

		self.yLogCheckBox = yLogCheckBox

		autorangeButton = QPushButton('Centre Graph')
		autorangeButton.clicked.connect(self.autorange)
		samplesLayout.addWidget(autorangeButton)

		self.autorangeButton = autorangeButton

	def autorange(self):
		"""
			Recentres the graph window
		"""
		if self.graph != None:
			self.graph.autoRange()

	# to be implemented in child classes
	def updateLogScale(self):
		pass

	def initialiseLegend(self):
		"""
			Generate default legend wigets and adds it to the graph layout
		"""
		# Add setting to the layout
		setting = QWidget()
		settingLayout = QGridLayout()
		setting.setLayout(settingLayout)

		# Add legend widget to the settings

		scroll = QScrollArea()
		scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		scroll.setWidgetResizable(False)

		self.scroll = scroll

		legend = QWidget()
		legendLayout = QVBoxLayout()
		legendLayout.setAlignment(Qt.AlignTop)
		legend.setLayout(legendLayout)
		legend.setMinimumWidth(150)

		self.legend = legend
		self.legendLayout = legendLayout

		settingLayout.addWidget(scroll, 0, 0, 1, 2)

		toggleButton = QPushButton('Toggle Legend Items')
		toggleButton.clicked.connect(self.toggleLegendItems)
		settingLayout.addWidget(toggleButton, 1, 0, 1, 2)

		self.save_current = QPushButton("Save plot")
		self.save_all = QPushButton("Save all plots")

		self.save_current.clicked.connect(self.save_current_button)
		self.save_all.clicked.connect(self.save_all_button)

		settingLayout.addWidget(self.save_current, 2, 0)
		settingLayout.addWidget(self.save_all, 2, 1)
		settingLayout.setRowStretch(1, 1)

		self.setting = settingLayout

		self.layout.addWidget(setting)

	def save_current_button(self):
		"""
			When the 'Save all' button is pressed we export all plots
		"""
		if self.project.eg is not None:

			# We make a list of analytes to include based on the checkboxes
			analyte_list = []
			for item in range(self.legendLayout.count()):
				if self.legendLayout.itemAt(item).widget().isChecked():
					analyte_list.append(self.legendLayout.itemAt(item).widget().text())

			# We find the reports folder created on import to use as a default location for the save dialogue
			reports_folder = self.project.dataLocation
			if reports_folder[-1] == "/":
				reports_folder = reports_folder[:-1]
			reports_folder = reports_folder + "_reports"

			# We bring up a dialogue to select the save directory
			self.fileLocation = QFileDialog.getExistingDirectory(self.legend, 'Save report', reports_folder)
			if self.fileLocation == "":
				return

			try:
				self.project.eg.trace_plots(analytes=analyte_list,
											samples=self.sampleList.currentItem().text(),
											focus=self.project.eg.focus_stage,
											outdir=self.fileLocation,
											subset=None)
				infoBox = QMessageBox.information(self.legend, "Export",
												  "The current data plot has been saved as a pdf in the folder.",
												  QMessageBox.Ok)
			except:
				infoBox = QMessageBox.information(self.legend, "Export",
												  "Encountered an error when attempting to export the plot.",
												  QMessageBox.Ok)

	def save_all_button(self):
		"""
			When the 'save plot' button is pressed we export the current plot
		"""
		if self.project.eg is not None:

			# We make a list of analytes to include based on the checkboxes
			analyte_list = []
			for item in range(self.legendLayout.count()):
				if self.legendLayout.itemAt(item).widget().isChecked():
					analyte_list.append(self.legendLayout.itemAt(item).widget().text())

			# We find the reports folder created on import to use as a default location for the save dialogue
			reports_folder = self.project.dataLocation
			if reports_folder[-1] == "/":
				reports_folder = reports_folder[:-1]
			reports_folder = reports_folder + "_reports"

			# We bring up a dialogue to select the save directory
			fileLocation = QFileDialog.getExistingDirectory(self.legend, 'Save report', reports_folder)
			if fileLocation == "":
				return

			try:
				self.project.eg.trace_plots(analytes=analyte_list,
											focus=self.project.eg.focus_stage,
											outdir=fileLocation)
				infoBox = QMessageBox.information(self.legend, "Export",
												  "The current data plots have been saved as pdfs in the folder.",
												  QMessageBox.Ok)
			except:
				infoBox = QMessageBox.information(self.legend, "Export",
												  "Encountered an error when attempting to export the plots.",
												  QMessageBox.Ok)

	# populate sample list
	def populateSamples(self):
		"""
			Updates the list of available samples from the dataset viewable on the graph
		"""

		samples = self.project.eg.samples
		self.sampleName = samples[0]

		self.sampleList.clear()
		for sample in samples:
			self.sampleList.addItem(sample)

	# populate legend check-boxes
	def populateLegend(self):
		"""
			Populate legend with all analytes
		"""
		# clear legend Entries
		for i in reversed(range(self.legendLayout.count())):
			self.legendLayout.itemAt(i).widget().deleteLater()


		for analyte in self.project.eg.analytes:
			# Create legend entry for the element and add it to the legend widget
			legendEntry = QCheckBox()
			legendEntry.setChecked(True)
			legendEntry.setText(analyte)
			legendEntry.setStyleSheet("color: {:s}".format(self.project.eg.cmaps[analyte]))
			legendEntry.stateChanged.connect(partial(self.legendStateChange, legendEntry.text()))
			# record identity of check box in dict
			self.legendEntries[analyte] = legendEntry
			# add to layout
			self.legendLayout.addWidget(legendEntry)

		self.scroll.setWidget(self.legend)

	def hideInternalStandard(self):
		"""
			Hides the analyte set as the internal standard from line graphs, and the legend
		"""
		if self.currentInternalStandard != None:
			self.legendEntries[self.currentInternalStandard].show()
			self.graphLines[self.currentInternalStandard].show()
		analyte = self.project.eg.internal_standard
		self.currentInternalStandard = analyte
		if self.focusStage not in ['rawdata', 'despiked', 'bkgsub']:
			self.legendEntries[analyte].hide()
			self.graphLines[analyte].hide()
			if analyte in self.filts:
				self.filts[analyte].hide()
		else:
			self.legendEntries[analyte].show()
			self.graphLines[analyte].show()

	def toggleLegendItems(self):
		"""
			Checks/unchecks all legend analytes
		"""
		for item in reversed(range(self.legendLayout.count())):
			if self.legendLayout.itemAt(item).widget().isChecked():
				self.legendLayout.itemAt(item).widget().setChecked(False)
			else:
				self.legendLayout.itemAt(item).widget().setChecked(True)
				if self.legendLayout.itemAt(item).widget().text() == self.currentInternalStandard:
					self.hideInternalStandard()

	def showGraph(self):
		"""
			Display graph window
		"""
		self.showNormal()


class AnalyteGridGraph(GraphWindow):
	def __init__(self, project):
			"""	
				Parent class for graphs that have a grid of graph, one for each analyte.

			"""
			super().__init__(project)
			self.grids = {}
			self.cells = {}

		

class MainGraph(GraphWindow):
	"""
		Widget that contains a PyQtGraph plot, and all the settings that control it.

	"""
	def __init__(self, project):
		super().__init__(project)
		self.showRanges = False
		self.ranges = []
		self.graphWins = []

		# By default the focus stage is 'rawdata'
		self.focusStage = 'rawdata'
		self.filtering = False
		self.calibrated = False

		self.initialiseSamples()

		# Add plot window to the layout
		###
		self.backgroundColour = 'w'

		pg.setConfigOption('background', self.backgroundColour)
		pg.setConfigOption('foreground', 'k')
		graph = pg.PlotWidget()
		graph.hideButtons()

		self.graphWins.append(graph)

		self.layout.addWidget(graph, 1)
		###

		self.initialiseLegend()

	# create lines (only happens once)
	def drawLines(self):
		"""
			Draw lines on graph for the first time.
		"""
		dat = self.project.eg.data[self.sampleName]

		for key, line in self.graphLines.items():
			for graph in self.graphWins:
				graph.removeItem(line)

		for analyte in dat.analytes:
			x = dat.Time
			y, yerr = helpers.stat_fns.unpack_uncertainties(dat.data[self.focusStage][analyte])
			line = pg.PlotDataItem(x, y, pen=pg.mkPen(dat.cmap[analyte], width=2), label=analyte, name=analyte, connect='finite')
			line.curve.setClickable(True)
			line.curve.sigClicked.connect(partial(self.onClickLine, analyte))
			self.graphLines[analyte] = line

			for graph in self.graphWins:
				graph.addItem(line)
	
	# draw labels
	def drawLabels(self):
		"""
			Draw axis labels, depending on self.focusStage
		"""
		ud = {'rawdata': 'counts',
              'despiked': 'counts',
              'bkgsub': 'background corrected counts',
              'ratios': 'counts/{:s} count',
              'calibrated': 'mol/mol {:s}'}
		
		ylabel = ud[self.focusStage].format(self.project.eg.internal_standard)
		if self.focusStage in ['ratios', 'calibrated']:
			ylabel.format(self.project.eg.internal_standard)

		for graph in self.graphWins:
			graph.setLabel('left', ylabel)
			graph.setLabel('bottom', 'Time', units='s')
		
		
	# function for setting all graph objects at initialisation
	def initialiseGraph(self):
		"""
			Draw graph for the first time
		"""
		self.focusStage = self.project.eg.focus_stage

		self.populateSamples()
		self.populateLegend()
		self.drawLabels()
		self.drawLines()
		self.updateLogScale()

		# set sample in list - has to happen *after* lines are drawn
		self.sampleList.setCurrentItem(self.sampleList.item(0))

	def autorange(self):
		"""
			Recentres the main graph window
		"""
		for graph in self.graphWins:
			graph.autoRange()

	# update graph when swapping between samples
	def swapSample(self):
		"""
			Grabs the name of the currently selected sample and passes it to the "updateGraphs" function
		"""
		# sets current sample to selected sample
		selectedSamples = self.sampleList.selectedItems()
		if len(selectedSamples) > 0:
			selectedSample = selectedSamples[0]
			self.sampleName = selectedSample.text()

			self.updateLines()
			if self.filtering:
				self.applyFilters()
			# self.updateLogScale()
	
	# change between log/linear y scale
	def updateLogScale(self):
		"""
			When log(y) checkbox is modified, update y-axis scale
		"""
		for graph in self.graphWins:
			graph.setLogMode(x=False, y=self.yLogCheckBox.isChecked())
		self.updateLines()

	# action when legend check-boxes are changed
	def legendStateChange(self, analyte):
		"""
			Actions to perform when legend check box changes state

			Parameters
			----------
			analyte : String
				The analyte that is associated with the check-box
		"""
		# change line visibility
		self.graphLines[analyte].setVisible(self.legendEntries[analyte].isChecked())
		if analyte in self.filts:
			self.filts[analyte].setVisible(self.legendEntries[analyte].isChecked())
	
	def updateLines(self):
		"""
			Update lines for new self.sampleName and/or self.focusStage
		"""
		dat = self.project.eg.data[self.sampleName]
		for graph in self.graphWins:
			# update line data for new sample
			for analyte in dat.analytes:
				x = dat.Time
				y, yerr = helpers.stat_fns.unpack_uncertainties(dat.data[self.focusStage][analyte])
				# if in log mode, transform y
				if self.yLogCheckBox.isChecked():
					y = np.log10(y)
				self.graphLines[analyte].curve.setData(x=x, y=y)
				if analyte in self.filts:
					self.filts[analyte].hide()

			# this plots the ranges after 'autorange' calculation
			for gRange in self.ranges:
				graph.removeItem(gRange)
				
			if self.showRanges:
				for lims in dat.bkgrng:
					self.addRegion(graph, lims, pg.mkBrush((255,0,0,25)))
				for lims in dat.sigrng:
					self.addRegion(graph, lims, pg.mkBrush((0,0,0,25)))
		
		
	
	def updateFocus(self, showRanges):
		"""
			Update graph for new focus stage. Focus-specific tasks should be included here.

			Parameters
			----------
			showRanges : Boolean
				Whether highlighed regions are displayed or not
		"""
		self.showRanges = showRanges
		
		self.focusStage = self.project.eg.focus_stage
		
		self.updateLines()
		self.drawLabels()
	
	def onClickLine(self, analyte):
		"""	
			This function is called when a line on the graph is clicked

			Parameters
			----------
			analyte : String
				The analyte that was clicked

		"""
		if analyte in self.highlightedAnalytes:
			self.highlightedAnalytes.remove(analyte)
		else:
			self.highlightedAnalytes.append(analyte)
		if len(self.highlightedAnalytes) > 0:
			for a in self.project.eg.analytes:
				if a not in self.highlightedAnalytes:
					self.graphLines[a].curve.setPen(pg.mkPen(self.project.eg.cmaps[a], width=0.5))
					self.legendEntries[a].setStyleSheet("color: {:s}".format(self.project.eg.cmaps[a]))
				else:
					self.graphLines[a].curve.setPen(pg.mkPen(self.project.eg.cmaps[a], width=3))
					self.legendEntries[a].setStyleSheet("color: white; background-color: {:s}".format(self.project.eg.cmaps[a]))
		else:
			self.resetColours()
	
	def resetColours(self):
		"""
			Resets all graph lines and legend entries to default stylings
		"""
		for a in self.project.eg.analytes:
			self.graphLines[a].curve.setPen(pg.mkPen(self.project.eg.cmaps[a], width=2))
			self.legendEntries[a].setStyleSheet("color: {:s}".format(self.project.eg.cmaps[a]))

	def addRegion(self, targetGraph, lims, brush):
		"""
			Adds highlight region to graph with given ranges and brush

			Parameters
			----------
			targetGraph : pg.plotItem
				Graph that the region is being added to
			lims : [???]
				The range that the region occupies
			brush : pg.mkBrush
				Brush that styles the region
		"""
		region = pg.LinearRegionItem(values=lims, brush=brush, movable=False)
		region.lines[0].setPen(pg.mkPen((0,0,0,0)))
		region.lines[1].setPen(pg.mkPen((0,0,0,0)))
		self.ranges.append(region)
		targetGraph.addItem(region)

	def applyFilters(self):
		"""
			Using filtering data to grey out segments of the line graph
		"""
		dat = self.project.eg.data[self.sampleName]
		for graph in self.graphWins:
			for analyte in dat.analytes:
				x = dat.Time
				y, yerr = helpers.stat_fns.unpack_uncertainties(dat.data[self.focusStage][analyte])
				ind = dat.filt.grab_filt(True, analyte)
				xf = x.copy()
				yf = y.copy()
				#yerrf = yerr.copy()
				#print(any(~ind))
				if any(~ind):
					xf[~ind] = np.nan
					yf[~ind] = np.nan
					#yerrf[~ind] = np.nan
				
				self.graphLines[analyte].setData(xf, yf)
				if analyte in self.filts:
					self.filts[analyte].setData(x, y)
					self.filts[analyte].show()
				elif self.filtering and any(~ind):
					line = pg.PlotDataItem(x,
					y,
					pen=pg.mkPen(color=self.hex_2_rgba(self.project.eg.cmaps[analyte], 127), width=0.6), connect='finite')
					graph.addItem(line)
					self.filts[analyte] = line
			self.hideInternalStandard()
		
class BkgGraph(GraphWindow):
	"""
		Openable window from the Background Subtraction stage. Graphs background subtraction data between all samples
	"""
	def __init__(self, project, err='stderr'):
		super().__init__(project)
		self.bkgSamplelines = {}
		self.highlightRegions = {}
		self.err = err
		
		self.setWindowTitle("LAtools bkg Plot")

		# Initialise samples menu
		self.initialiseSamples()

		# Create graph
		graph = pg.PlotWidget()
		graph.setLogMode(x=False, y=self.yLogCheckBox.isChecked())
		graph.hideButtons()

		self.graph = graph

		self.layout.addWidget(graph, 1)

		# Initialise Legend
		self.initialiseLegend()

	def initialiseGraph(self):
		"""
			Clears the elements in the graph, populates the samples list and legend with items
		"""
		self.populated = False
		self.populateSamples()
		self.populateLegend()

	def getDatapoints(self, dat, analyte):
		"""
			Retrieve data points from LaTools Data object

			Parameters
			----------
			dat : la.latools.analyse
				LaTools analyse object
			analyte : String
				The analyte being considered for background data points
		"""
		sy = dat.bkg['raw'].loc[:, analyte]

		x = dat.bkg['calc']['uTime']
		y = dat.bkg['calc'][analyte]['mean']
		yl = dat.bkg['calc'][analyte]['mean'] - dat.bkg['calc'][analyte][self.err]
		yu = dat.bkg['calc'][analyte]['mean'] + dat.bkg['calc'][analyte][self.err]

		if self.yLogCheckBox.isChecked():
			sy = np.log10(sy)
			#x = np.log10(x)
			#y = np.log10(y)
			yl = np.log10(yl)
			yu = np.log10(yu)

		return [sy, x, y, yl, yu]

	def populateGraph(self):
		"""
			Processes subtraction data and populates the graph with the processed data
		"""
		dat = self.project.eg
		for analyte in self.project.eg.analytes:
			datapoints = self.getDatapoints(dat, analyte)

			# Add items to graph

			scatter = pg.ScatterPlotItem(dat.bkg['raw'].uTime, datapoints[0], pen=None, brush=pg.mkBrush(self.hex_2_rgba(dat.cmaps[analyte], 127)), size=3)
			self.graphScatters[analyte] = scatter

			line = pg.PlotDataItem(datapoints[1], datapoints[2], pen=pg.mkPen(dat.cmaps[analyte], width=2), label=analyte, name=analyte, connect='finite')
			self.graphLines[analyte] = line

			fill = pg.FillBetweenItem(pg.PlotDataItem(datapoints[1], datapoints[3], pen=pg.mkPen(0,0,0,0)), pg.PlotDataItem(datapoints[1], datapoints[4], pen=pg.mkPen(0,0,0,0)), brush=pg.mkBrush(self.hex_2_rgba(dat.cmaps[analyte], 204)))
			self.graphFills[analyte] = fill

			self.graphLines[analyte] = (scatter, line, fill)

			self.graph.addItem(scatter)
			self.graph.addItem(line)
			self.graph.addItem(fill)
				

		# Add/update highlighted sample regions to graph
		for s, d in dat.data.items():
			self.addRegion(s, self.graph, (d.uTime[0], d.uTime[-1]), pg.mkBrush((0,0,0,25)))
			sampleLine = pg.InfiniteLine(pos=d.uTime[0], pen=pg.mkPen(color=(0,0,0,51), style=Qt.DashLine, width=2), label=s, labelOpts={'position': .999, 'anchors': ((0., 0.), (0., 0.))})
			self.bkgSamplelines[d] = sampleLine
			self.graph.addItem(sampleLine)

		self.populated = True				
		self.sampleList.setCurrentItem(self.sampleList.item(0))

	def updateData(self):
		"""
			Updates the data of the graph
		"""
		dat = self.project.eg
		for analyte in self.project.eg.analytes:
			datapoints = self.getDatapoints(dat, analyte)

			# Update graph data
			self.graphScatters[analyte].setData(dat.bkg['raw'].uTime, datapoints[0])
			self.graphLines[analyte].setData(datapoints[1], datapoints[2])
			self.graphFills[analyte].setCurves(pg.PlotDataItem(datapoints[1], datapoints[3], pen=pg.mkPen(0,0,0,0)), pg.PlotDataItem(datapoints[1], datapoints[4], pen=pg.mkPen(0,0,0,0)))
		
		# Update highlight region data
		for s, d in dat.data.items():
			self.highlightRegions[s].setRegion((d.uTime[0], d.uTime[-1]))
			self.bkgSamplelines[d].setValue(d.uTime[0])

	# populate sample list
	def populateSamples(self):
		"""
			Updates the list of available samples from the dataset viewable on the graph
		"""

		samples = self.project.eg.samples
		self.sampleName = samples[0]

		self.sampleList.clear()
		self.sampleList.addItem("NONE")
		for sample in samples:
			self.sampleList.addItem(sample)

	def swapSample(self):
		"""
			sets current sample to selected sample
		"""
		selectedSamples = self.sampleList.selectedItems()
		if len(selectedSamples) > 0:
			selectedSample = selectedSamples[0]
			self.sampleName = selectedSample.text()

			for s, d in self.project.eg.data.items():
				if self.sampleName == 'NONE' or s != self.sampleName:
					self.highlightRegions[s].setVisible(False)
				else:
					self.highlightRegions[s].setVisible(True)

	# action when legend check-boxes are changed
	def legendStateChange(self, analyte):
		"""
			Actions to perform when legend check box changes state

			Parameters
			----------
			analyte : String
				Analyte attributed to the tickbox clicked
		"""

		for item in self.graphLines[analyte]:
			item.setVisible(self.legendEntries[analyte].isChecked())

		box = self.graph.getViewBox()
		box.update()

	# change between log/linear y scale
	def updateLogScale(self):
		"""
			When log(y) checkbox is modified, update y-axis scale
		"""
		self.graph.setLogMode(x=False, y=self.yLogCheckBox.isChecked())
		self.populateGraph()

	def addRegion(self, name, targetGraph, lims, brush):
		"""
			Based of given parameters creates a region item and adds it to target graph

			Parameters
			----------
			name : String
				Name given to created region
			targetGraph : pg.PlotItem
				Graph that the region will be added to
			lims : [???]
				Pair of data points that are the limits of the region
			brush : pg.mkBrush
				Brush that defines the look of the region
		
		"""
		region = pg.LinearRegionItem(values=lims, brush=brush, movable=False)
		region.lines[0].setPen(pg.mkPen((0,0,0,0)))
		region.lines[1].setPen(pg.mkPen((0,0,0,0)))
		region.setVisible(False)
		self.highlightRegions[name] = region
		targetGraph.addItem(region)

class CaliGraph(AnalyteGridGraph):
	"""
		Openable window from the Calibration stage. Graphs all analytes calibrated to the internal standard
	"""
	def __init__(self, project, loglog=False):
		super().__init__(project)
		self.loglog = loglog

		self.errPlots = {}
		self.histPlots = {}
		self.analyteTexts = {}
		self.eqTexts = {}

		# Create scollable area that holds all the elements of the window
		scroll = QScrollArea()
		scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		scroll.setWidgetResizable(True)

		self.scroll = scroll

		self.setWindowTitle("LAtools calibration Plot")

		# Initialise Grid that contains all the analyte graphs
		graph = QWidget()
		graphLayout = QGridLayout()
		graph.setLayout(graphLayout)
		minSize = graph.minimumSize()
		minSize.scale(1000, 1000, Qt.KeepAspectRatio)
		graph.setMinimumSize(minSize)

		self.graph = graph
		self.graphLayout = graphLayout

		self.layout.addWidget(scroll, 1)

	def populateGraph(self):
		"""
			Populations the window's grid layout with graphs of each analyte (excluding the internal standard)
		"""

		dat = self.project.eg
		analytes = [a for a in dat.analytes if dat.internal_standard not in a]

		dat.get_focus()

		row = 0
		for i in range(0, len(analytes)):
			analyte = analytes[i]
			if i % 3 == 0:
				row += 1
			
			
			meas_mean = dat.srmtabs.loc[analyte, 'meas_mean'].values
			srm_mean = dat.srmtabs.loc[analyte, 'srm_mean'].values
			meas_err = dat.srmtabs.loc[analyte, 'meas_err'].values
			srm_err = dat.srmtabs.loc[analyte, 'srm_err'].values
			
			# work out axis scaling
			xmax = np.nanmax(helpers.stat_fns.nominal_values(meas_mean) +
			helpers.stat_fns.nominal_values(meas_err))
			ymax = np.nanmax(helpers.stat_fns.nominal_values(srm_mean) +
			helpers.stat_fns.nominal_values(srm_err))
			xlim = [0, 1.05 * xmax]
			ylim = [0, 1.05 * ymax]

			# calculate line and R2
			linex = np.array(xlim)

			coefs = dat.calib_params[analyte]
			m = coefs.m.values.mean()
			m_nom = helpers.stat_fns.nominal_values(m)
			# calculate case-specific paramers
			if 'c' in coefs:
				c = coefs.c.values.mean()
				c_nom = helpers.stat_fns.nominal_values(c)
				# calculate R2
				ym = dat.srmtabs.loc[analyte, 'meas_mean'] * m_nom + c_nom
				R2 = helpers.stat_fns.R2calc(dat.srmtabs.loc[analyte, 'srm_mean'], ym, force_zero=False)
				# generate line and label
				line = linex * m_nom + c_nom
				label = 'y = {:.2e} x'.format(m)
				if c > 0:
					label += '<br />+ {:.2e}'.format(c)
				else:
					label += '<br /> {:.2e}'.format(c)
			else:
				# calculate R2
				ym = dat.srmtabs.loc[analyte, 'meas_mean'] * m_nom
				R2 = helpers.stat_fns.R2calc(dat.srmtabs.loc[analyte, 'srm_mean'], ym, force_zero=True)
				# generate line and label
				line = linex * m_nom
				label = 'y = {:.2e} x'.format(m)

			# add R2 to label
			if round(R2, 3) == 1:
				label = 'R<sup>2</sup>: >0.999<br />' + label
			else:
				label = 'R<sup>2</sup>: {:.3f}<br />'.format(R2) + label

			# write calibration equation on graph happens after data distribution

			# plot data distribution historgram alongside calibration plot
			# isolate data
			meas = helpers.stat_fns.nominal_values(dat.focus[analyte])
			meas = meas[~np.isnan(meas)]

			# check and set y scale
			if np.nanmin(meas) < ylim[0]:
				if self.loglog:
					mmeas = meas[meas > 0]
					ylim[0] = 10**np.floor(np.log10(np.nanmin(mmeas)))
				else:
					ylim[0] = 0
					

			m95 = np.percentile(meas[~np.isnan(meas)], 95) * 1.05
			if m95 > ylim[1]:
				if self.loglog:
					ylim[1] = 10**np.ceil(np.log10(m95))
				else:
					ylim[1] = m95

			# hist
			if self.loglog:
				bins = np.logspace(*np.log10(ylim), 30)
			else:
				bins = np.linspace(*ylim, 30)
			
			hy,hx = np.histogram(meas, bins=bins)

			if not self.populated:
				#Each graph is a Graphics Layout Widget; so that the error plot, histogram, and all labels are easily arranged
				cell = pg.GraphicsLayoutWidget()
				cell.ci.setSpacing(0)
				cell.ci.layout.setColumnStretchFactor(1,2)
				cell.addLabel('mol/mol ' + dat.internal_standard, 0, 0, angle=-90, rowspan=2)
				cell.addLabel('counts/counts ' + dat.internal_standard, 1, 1, colspan=2)

				self.cells[(row, i)] = cell
				self.graphLayout.addWidget(self.cells[(row, i)], row, i%3)

				errPlot = cell.addPlot(0, 1)
				errPlot.hideButtons()

				self.errPlots[(row, i)] = errPlot

				errViewbox = errPlot.getViewBox()
				errViewbox.setMouseEnabled(False, False)

				# plot calibration data
				errorbar = pg.ErrorBarItem(x=meas_mean,
				y=srm_mean,
				width=meas_err,
				height=srm_err,
				pen=pg.mkPen(self.hex_2_rgba(dat.cmaps[analyte], 153), width=2),
				beam=0)
			
				self.graphErrorbars[(row, i)] = errorbar
				errPlot.addItem(errorbar)

				scatter = pg.ScatterPlotItem(x=meas_mean,
				y=srm_mean,
				pen=None, brush=pg.mkBrush(self.hex_2_rgba(dat.cmaps[analyte], 153)), size=8)
				
				self.graphScatters[(row, i)] = scatter
				errPlot.addItem(scatter)

				errViewbox.setRange(xRange=xlim, yRange=ylim, disableAutoRange=True)

				# plot line of best fit
				graphLine = pg.PlotDataItem(linex,
				line,
				pen=pg.mkPen(color=self.hex_2_rgba(dat.cmaps[analyte], 127), style=Qt.DashLine, width=2))

				self.graphLines[(row, i)] = graphLine
				errPlot.addItem(graphLine)

				analyteText = pg.TextItem(anchor=(0,0), color='k')
				self.analyteTexts[(row, i)] = analyteText
				errPlot.addItem(analyteText)

				# hist

				histPlot = cell.addPlot(0, 2)
				histPlot.hideButtons()
				histViewbox = histPlot.getViewBox()
				histRange = histViewbox.viewRange()
				histViewbox.setMouseEnabled(False, False)
				self.histPlots[(row, i)] = histPlot

				hist = pg.PlotDataItem(hx, hy, stepMode=True, fillLevel=0, brush=pg.mkBrush(self.hex_2_rgba(dat.cmaps[analyte], 127)), pen=pg.mkPen(color=self.hex_2_rgba(dat.cmaps[analyte], 127), width=0.5))
				
				self.graphHistograms[(row, i)] = hist
				histPlot.addItem(hist)

				hist.rotate(90)

				# write calibration equation on graph
				eqText = pg.TextItem(color='k')
				
				self.eqTexts[(row, i)] = eqText
				errPlot.addItem(eqText)

			else:
				self.graphErrorbars[(row, i)].setData(x=meas_mean,
				y=srm_mean,
				width=meas_err,
				height=srm_err,
				pen=pg.mkPen(self.hex_2_rgba(dat.cmaps[analyte], 153)))

				self.graphScatters[(row, i)].setData(x=meas_mean,
				y=srm_mean,
				brush=pg.mkBrush(self.hex_2_rgba(dat.cmaps[analyte], 153)))

				self.graphLines[(row, i)].setData(linex,
				line,
				pen=pg.mkPen(color=self.hex_2_rgba(dat.cmaps[analyte], 127), style=Qt.DashLine, width=2))

				self.graphHistograms[(row, i)].setData(x=hx,
				y=hy,
				brush=pg.mkBrush(self.hex_2_rgba(dat.cmaps[analyte], 127)),
				pen=pg.mkPen(color=self.hex_2_rgba(dat.cmaps[analyte], 127), width=0.5))

			
			
			histPlot = self.histPlots[(row, i)]	
			histViewbox = histPlot.getViewBox()
			

			errViewbox = self.errPlots[(row, i)].getViewBox()

			
			if not self.populated:
				if np.nanmin(meas) < ylim[0]:
					if not self.loglog:
						errViewbox.setRange(yRange=ylim)

				if self.loglog:
					self.graphHistograms[(row, i)].setLogMode(xMode=False, yMode=True)
				histViewbox.setRange(yRange=ylim) # ylim of histogram axis
				errViewbox.setRange(yRange=ylim) # ylim of calibration axis
				histViewbox.invertX(True)
				histBottom = histPlot.getAxis('bottom')
				histBottom.setStyle()
				histBottom.setTicks([])
				histPlot.hideAxis('left')

				histRange = histViewbox.viewRange()
							
				cmax = np.nanmean(srm_mean)

				eqText = self.eqTexts[(row, i)]
				if cmax / ylim[1] > 0.5:
					eqText.setAnchor(anchor=(1,1))
					eqText.setHtml('<div style="text-align: right"><span style="font-size:8em">%(label)s</span></div>'%{"label":label})
					eqText.setPos(linex[-1],line[0])
				else:
					eqText.setAnchor(anchor=(0,-1))
					eqText.setHtml('<div style="text-align: left"><span style="font-size:8em">%(label)s</span></div>'%{"label":label})
					eqText.setPos(0,histRange[1][1])

				el = re.match('.*?([A-z]{1,3}).*?', analyte).groups()[0]
				m = re.match('.*?([0-9]{1,3}).*?', analyte).groups()[0]

				self.analyteTexts[(row, i)].setPos(0,histRange[1][1])
				self.analyteTexts[(row, i)].setHtml('<div style="text-align: center"><span style="font-size:10em;"><sup>%(m)s</sup>%(el)s</span></div>'%{"el":el, "m":m})

		
		self.populated = True
		self.scroll.setWidget(self.graph)

class Crossplot(AnalyteGridGraph):
	def __init__(self, project):
		super().__init__(project)
		self.lognorm = True
		self.bins = 25
		self.samples = None
		self.subset = None
		self.colourful = True

		self.labels = {}

		# Initialise samples menu
		self.initialiseSamples()
		self.yLogCheckBox.hide()
		self.autorangeButton.hide()

		filtCheckBox = QCheckBox()
		filtCheckBox.setMaximumWidth(100)
		filtCheckBox.setText('filt')
		filtCheckBox.setChecked(False)
		filtCheckBox.stateChanged.connect(self.updateFilt)
		self.filtCheckBox = filtCheckBox
		self.samplesLayout.addWidget(filtCheckBox)

		self.setWindowTitle("LAtools Crossplot")

		# Create scollable area that holds all the elements of the window
		scrollMain = QScrollArea()
		scrollMain.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		scrollMain.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		scrollMain.setWidgetResizable(True)

		self.scrollMain = scrollMain

		self.layout.addWidget(scrollMain, 1)

	def initialiseGraph(self):
		self.populateSamples()

	def startup(self):
		"""
			Generate holder widget to houses the various crossplots, add all samples crossplot as default
		"""
		self.sampleName = self.sampleList.item(0).text()
		self.sampleList.setCurrentItem(self.sampleList.item(0))
		if not self.populated:
			self.createCrossplot()
			holder = QWidget()
			holderLayout = QHBoxLayout(holder)
			self.holderLayout = holderLayout
			self.scrollMain.setWidget(holder)
			self.graph = self.grids[self.sampleName+'False']['grid']
			self.holderLayout.addWidget(self.graph)
			self.populated = True
	
	def createCrossplot(self):
		"""
			If non-existant, generate a crossplot based of the currently selected sample
		"""
		key = self.sampleName+str(self.filtCheckBox.isChecked())
		if not key in self.grids:
			dat = self.project.eg
			cmap = dat.cmaps

			# set up colour scales
			if self.colourful:
				cmlist = ['Blues', 'BuGn', 'BuPu', 'GnBu',
							'Greens', 'Greys', 'Oranges', 'OrRd',
							'PuBu', 'PuBuGn', 'PuRd', 'Purples',
							'RdPu', 'Reds', 'YlGn', 'YlGnBu', 'YlOrBr', 'YlOrRd']
			else:
				cmlist = ['Greys']

			#AnalyteObject

			grid = self.initialiseGrid(key)

			if self.sampleName == "ALL":
				self.createCrossplotAll(key, dat, cmap, cmlist, grid)
			else:
				self.createCrossplotDat(key, dat, cmap, cmlist, grid)

	def createCrossplotAll(self, key, dat, cmap, cmlist, grid):
		"""
			Generate crossplot spanning all samples

			Parameters
			----------
			key : String
				Name of the created plot configuration
			dat : la.latools.analyse
				LaTools analyse object
			cmap : la.latools.analyse.cmaps
				Colour maps
			cmlist : [String]
				Strings that represent colours to be used
			grid : {QWidget, QGridLayout}
				The grid that holds the plots
		"""
		analytes = dat.analytes
		if dat.focus_stage in ['ratio', 'calibrated']:
			analytes = [a for a in analytes if dat.internal_standard not in a]
		# sort analytes
		try:
			analytes = sorted(analytes, key=lambda x: float(re.findall('[0-9.-]+', x)[0]))
		except IndexError:
			analytes = sorted(analytes)

		dat.get_focus(filt=self.filtCheckBox.isChecked(), samples=self.samples, subset=self.subset)

		numvars = len(analytes)

		if cmap is None and self.mode == 'scatter':
			cmap = {k: 'k' for k in dat.analytes()}

		while len(cmlist) < len(analytes):
			cmlist *= 2

		# isolate nominal_values for all analytes
		focus = {k: helpers.stat_fns.nominal_values(dat.focus[k]) for k in analytes}
		# determine units for all analytes
		udict = {a: helpers.helpers.unitpicker(np.nanmean(focus[a]),
							focus_stage=dat.focus_stage,
							denominator=dat.internal_standard) for a in analytes}

		axes = np.zeros((numvars, numvars))
		
		for i, j in zip(*np.triu_indices_from(axes, k=1)):
			# get analytes
			ai = analytes[i]
			aj = analytes[j]

			# remove nan, apply multipliers
			pi = focus[ai] * udict[ai][0]
			pj = focus[aj] * udict[aj][0]

			# draw plots

			# remove nan
			pi = pi[~np.isnan(pi)]
			pj = pj[~np.isnan(pj)]
			
			h = np.histogram2d(pj, pi, self.bins, normed = self.lognorm)
			item = pg.ImageItem(image=h[0], autoLevels=True)
			view1 = pg.GraphicsView()
			box = pg.ViewBox()
			box.setMouseEnabled(False, False)
			box.addItem(item)
			box.setAspectLocked(False)
			box.setRange(xRange=[0, h[0].shape[0]], yRange=[0, h[0].shape[1]])
			view1.setCentralItem(box)

			self.cells[(key, (i, j))] = box
			

			h = np.histogram2d(pi, pj, self.bins, normed = self.lognorm)
			item = pg.ImageItem(image=h[0])
			view2 = pg.GraphicsView()
			box = pg.ViewBox()
			box.setMouseEnabled(False, False)
			box.addItem(item)
			box.setAspectLocked(False)
			box.setRange(xRange=[0, h[0].shape[0]], yRange=[0, h[0].shape[1]])
			view2.setCentralItem(box)

			self.cells[(key, (j, i))] = box

			grid['gridLayout'].addWidget(view1, i, j)
			grid['gridLayout'].addWidget(view2, j, i)



		# diagonal labels
		for a, n in zip(analytes, np.arange(len(analytes))):
			a2 = udict[a][1]
			a2 = a2.replace("$^{", "<sup>")
			a2 = a2.replace("}$", "</sup>")
			a2 = a2.replace("$\\mu$", "&mu;")

			item = pg.TextItem(anchor=(0.5,0.5), html='<div style="text-align: center"><span style="color: #000;font-size:8em;">%(txt)s</span></div>'%{"txt": a + '<br />' + a2})
			view = pg.GraphicsView()
			box = pg.ViewBox()
			box.autoRange()
			box.setMouseEnabled(False, False)
			box.addItem(item)
			item.setPos(0.5, 0.5)
			view.setCentralItem(box)

			self.labels[(key, n)] = item
			self.cells[(key, (n, n))] = box
			grid['gridLayout'].addWidget(view, n, n)


	def createCrossplotDat(self, key, dat, cmap, cmlist, grid):
		"""
			Generate crossplot for the specified sample

			Parameters
			----------
			key : String
				Name of the created plot configuration
			dat : la.latools.analyse
				LaTools analyse object
			cmap : la.latools.analyse.cmaps
				Colour maps
			cmlist : [String]
				Strings that represent colours to be used
			grid : {QWidget, QGridLayout}
				The grid that holds the plots
		"""
		
		#DatObject
		sampleObj = dat.data[self.sampleName]
		analytes = sampleObj.analytes
		if dat.focus_stage in ['ratio', 'calibrated']:
			analytes = [a for a in analytes if dat.internal_standard not in a]

		numvars = len(analytes)
		axes = np.zeros((numvars, numvars))

		while len(cmlist) < len(analytes):
			cmlist *= 2

		udict = {}
		for i, j in zip(*np.triu_indices_from(axes, k=1)):
			for x, y in [(i, j), (j, i)]:
				# set unit multipliers
				mx, ux = helpers.helpers.unitpicker(np.nanmean(sampleObj.focus[analytes[x]]),
									denominator=dat.internal_standard,
									focus_stage=dat.focus_stage)
				my, uy = helpers.helpers.unitpicker(np.nanmean(sampleObj.focus[analytes[y]]),
									denominator=dat.internal_standard,
									focus_stage=dat.focus_stage)
				udict[analytes[x]] = (x, ux)

				# get filter
				ind = (sampleObj.filt.grab_filt(self.filtCheckBox.isChecked(), analytes[x]) &
					sampleObj.filt.grab_filt(self.filtCheckBox.isChecked(), analytes[y]) &
					~np.isnan(helpers.stat_fns.nominal_values(sampleObj.focus[analytes[x]])) &
					~np.isnan(helpers.stat_fns.nominal_values(sampleObj.focus[analytes[y]])))

				# make plot
				pi = helpers.stat_fns.nominal_values(sampleObj.focus[analytes[x]][ind]) * mx
				pj = helpers.stat_fns.nominal_values(sampleObj.focus[analytes[y]][ind]) * my

				# draw plots
				h = np.histogram2d(pj, pi, self.bins, normed = self.lognorm)
				item = pg.ImageItem(image=h[0], autoLevels=True)
				view1 = pg.GraphicsView()
				box = pg.ViewBox()
				box.setMouseEnabled(False, False)
				box.addItem(item)
				box.setAspectLocked(False)
				box.setRange(xRange=[0, h[0].shape[0]], yRange=[0, h[0].shape[1]])
				view1.setCentralItem(box)

				self.cells[(key, (i, j))] = box
				

				h = np.histogram2d(pi, pj, self.bins, normed = self.lognorm)
				item = pg.ImageItem(image=h[0])
				view2 = pg.GraphicsView()
				box = pg.ViewBox()
				box.setMouseEnabled(False, False)
				box.addItem(item)
				box.setAspectLocked(False)
				box.setRange(xRange=[0, h[0].shape[0]], yRange=[0, h[0].shape[1]])
				view2.setCentralItem(box)

				self.cells[(key, (j, i))] = box

				grid['gridLayout'].addWidget(view1, i, j)
				grid['gridLayout'].addWidget(view2, j, i)

		# diagonal labels
		for a, (i, u) in udict.items():
			a2 = u
			a2 = a2.replace("$^{", "<sup>")
			a2 = a2.replace("}$", "</sup>")
			a2 = a2.replace("$\\mu$", "&mu;")

			item = pg.TextItem(anchor=(0.5,0.5), html='<div style="text-align: center"><span style="color: #000;font-size:8em;">%(txt)s</span></div>'%{"txt": a + '<br />' + a2})
			view = pg.GraphicsView()
			box = pg.ViewBox()
			box.autoRange()
			box.setMouseEnabled(False, False)
			box.addItem(item)
			item.setPos(0.5, 0.5)
			view.setCentralItem(box)

			self.labels[(key, i)] = item
			self.cells[(key, (i, i))] = box
			grid['gridLayout'].addWidget(view, i, i)

	def initialiseGrid(self, key):
		"""
			Creates a grid widget with default settings
		"""
		# Initialise Grid that contains all the analyte graphs
		grid = QWidget()
		gridLayout = QGridLayout()
		gridLayout.setSpacing(0)
		grid.setLayout(gridLayout)
		minSize = grid.minimumSize()
		minSize.scale(1000, 1000, Qt.KeepAspectRatio)
		grid.setMinimumSize(minSize)

		grid = { 'grid': grid, 'gridLayout': gridLayout}

		self.grids[key] = grid

		return grid
	
	# populate sample list
	def populateSamples(self):
		"""
			Updates the list of available samples from the dataset viewable on the graph
		"""

		samples = self.project.eg.samples
		self.sampleName = samples[0]

		self.sampleList.clear()
		self.sampleList.addItem("ALL")
		for sample in samples:
			self.sampleList.addItem(sample)

	def swapSample(self):
		"""
			sets current sample to selected sample
		"""
		selectedSamples = self.sampleList.selectedItems()
		if len(selectedSamples) > 0:
			selectedSample = selectedSamples[0]
			self.sampleName = selectedSample.text()

		if self.populated:
			self.createCrossplot()
			self.graph.setParent(None)
			self.graph = self.grids[self.sampleName+'False']['grid']
			self.holderLayout.addWidget(self.graph)

	def updateFilt(self):
		"""
			Generates a crossplot reflecting whether the filt checkbox is ticked or not
		"""
		if not self.filtCheckBox.isChecked():
			self.createCrossplot()
			self.graph.setParent(None)
			self.graph = self.grids[self.sampleName+'False']['grid']
			self.holderLayout.addWidget(self.graph)
		else:
			self.createCrossplot()
			self.graph.setParent(None)
			self.graph = self.grids[self.sampleName+'True']['grid']
			self.holderLayout.addWidget(self.graph)
