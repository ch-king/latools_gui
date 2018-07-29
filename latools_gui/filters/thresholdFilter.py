""" A filter for defining a threshold """

from PyQt5.QtWidgets import *


class ThresholdFilter:
	"""
	Threshold Filter info
	"""
	def __init__(self, filterTab):

		# This filter has access to the general filter structure
		self.filterTab = filterTab

		# The layout that this filter will put its option controls in
		self.optionsLayout = QGridLayout(self.filterTab.optionsWidget)

		# The complete set of checkboxes that can turn on or off analytes
		self.analyteCheckBoxes = {
			"controlsAbove": [],
			"controlsBelow": [],
			"summaryAbove": [],
			"summaryBelow": [],
		}

		# Determines is this filter will have "above" and "below" rows
		self.twoRows = True

		# We create each checkbox that will appear in the filter controls and summary tabs
		for i in range(len(self.filterTab.project.eg.analytes)):

			self.analyteCheckBoxes["controlsAbove"].append(QCheckBox())
			self.analyteCheckBoxes["controlsBelow"].append(QCheckBox())
			self.analyteCheckBoxes["summaryAbove"].append(QCheckBox())
			self.analyteCheckBoxes["summaryBelow"].append(QCheckBox())

			# We connect the summary and control checkboxes with functions that will activate when their state changes.
			# There are different functions because we need to know which set to override with the new states
			self.analyteCheckBoxes["controlsAbove"][i].stateChanged.connect(self.controlChecksRegister)
			self.analyteCheckBoxes["controlsBelow"][i].stateChanged.connect(self.controlChecksRegister)
			self.analyteCheckBoxes["summaryAbove"][i].stateChanged.connect(self.summaryChecksRegister)
			self.analyteCheckBoxes["summaryBelow"][i].stateChanged.connect(self.summaryChecksRegister)

		# A label for the type
		self.typeLabel = QLabel(self.filterTab.filterInfo["type_label"])
		self.optionsLayout.addWidget(self.typeLabel, 0, 0)

		# A combobox for the type
		self.typeCombo = QComboBox()
		self.typeCombo.addItem("1")
		self.typeCombo.addItem("2")
		self.typeCombo.addItem("3")
		self.typeCombo.addItem("4")

		self.optionsLayout.addWidget(self.typeCombo, 0, 1)

		# We create the control buttons
		self.crossPlotButton = QPushButton("Cross-plot")
		self.crossPlotButton.clicked.connect(self.crossPlotClick)
		self.filterTab.addButton(self.crossPlotButton)

		self.plotButton = QPushButton("Plot")
		self.plotButton.clicked.connect(self.plotClick)
		self.filterTab.addButton(self.plotButton)

		self.createButton = QPushButton("Create filter")
		self.createButton.clicked.connect(self.createClick)
		self.filterTab.addButton(self.createButton)

		# We create a row in the analytes table for the "above" version
		self.filterTab.table.addWidget(QLabel(self.filterTab.name + " (above)"), self.filterTab.table.rowCount(), 0)

		# We populate the row with checkboxes
		for i in range(self.filterTab.table.columnCount() - 1):
			self.filterTab.table.addWidget(
				self.analyteCheckBoxes["controlsAbove"][i], self.filterTab.table.rowCount() - 1, i + 1)

		# We create a row in the analytes table for the "below" version
		self.filterTab.table.addWidget(QLabel(self.filterTab.name + " (below)"), self.filterTab.table.rowCount(), 0)

		# We populate the row with checkboxes
		for i in range(self.filterTab.table.columnCount() - 1):
			self.filterTab.table.addWidget(
				self.analyteCheckBoxes["controlsBelow"][i], self.filterTab.table.rowCount() - 1, i + 1)

	def controlChecksRegister(self):
		""" Sets the checkboxes in the Summary tab to be the same as those in the Controls tab """

		for i in range(len(self.analyteCheckBoxes["controlsAbove"])):

			self.analyteCheckBoxes["summaryAbove"][i].setCheckState(
				self.analyteCheckBoxes["controlsAbove"][i].checkState())

			self.analyteCheckBoxes["summaryBelow"][i].setCheckState(
				self.analyteCheckBoxes["controlsBelow"][i].checkState())

	def summaryChecksRegister(self):
		""" Sets the checkboxes in the Controls tab to be the same as those in the Summary tab """

		for i in range(len(self.analyteCheckBoxes["controlsAbove"])):
			self.analyteCheckBoxes["controlsAbove"][i].setCheckState(
				self.analyteCheckBoxes["summaryAbove"][i].checkState())

			self.analyteCheckBoxes["controlsBelow"][i].setCheckState(
				self.analyteCheckBoxes["summaryBelow"][i].checkState())

	def createClick(self):
		""" Adds the new filter to the Summary tab """

		# We create a row in the analytes table in the Summary tab for the "above" version of this filter
		self.filterTab.summaryTab.table.addWidget(
			QLabel(self.filterTab.name + " (above)"), self.filterTab.summaryTab.table.rowCount(), 0)

		# We populate the row with checkboxes
		for i in range(self.filterTab.summaryTab.table.columnCount() - 1):
			self.filterTab.summaryTab.table.addWidget(
				self.analyteCheckBoxes["summaryAbove"][i], self.filterTab.summaryTab.table.rowCount() - 1, i + 1)

		# We create a row in the analytes table in the Summary tab for the "below" version of this filter
		self.filterTab.summaryTab.table.addWidget(
			QLabel(self.filterTab.name + " (below)"), self.filterTab.summaryTab.table.rowCount(), 0)

		# We populate the row with checkboxes
		for i in range(self.filterTab.summaryTab.table.columnCount() - 1):
			self.filterTab.summaryTab.table.addWidget(
				self.analyteCheckBoxes["summaryBelow"][i], self.filterTab.table.rowCount() - 1, i + 1)

		# We deactivate the create button
		self.createButton.setEnabled(False)

	def crossPlotClick(self):
		""" Activates when the Cross-plot button is pressed """
		pass

	def plotClick(self):
		""" Activates when the Plot button is pressed """
		pass
