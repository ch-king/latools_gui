""" A filter for correlated elements """

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import logging

class DefragmentFilter:
	"""
	The options and controls for creating a defragment filter within a filterTab
	"""
	def __init__(self, filterTab):
		"""
		Creates the unique aspects of this filter, housed within the filterTab

		Parameters
		----------
		filterTab : FilterTab
			The general tab in which this filter's unique aspects will be created.
		"""
		# This filter has access to the general filter structure
		self.filterTab = filterTab

		# The layout that this filter will put its option controls in
		self.optionsLayout = QGridLayout(self.filterTab.optionsWidget)

		# The threshold option
		self.thresholdLabel = QLabel(self.filterTab.filterInfo["threshold_label"])
		self.thresholdEdit = QLineEdit()
		self.thresholdEdit.setPlaceholderText("int")
		#self.thresholdEdit.setMaximumWidth(100)
		self.thresholdLabel.setToolTip(self.filterTab.filterInfo["threshold_description"])
		self.thresholdEdit.setToolTip(self.filterTab.filterInfo["threshold_description"])
		self.optionsLayout.addWidget(self.thresholdLabel, 0, 0)
		self.optionsLayout.addWidget(self.thresholdEdit, 0, 1)

		# An option to select the mode
		self.modeLabel = QLabel(self.filterTab.filterInfo["mode_label"])
		self.optionsLayout.addWidget(self.modeLabel, 1, 0)
		self.modeCombo = QComboBox()
		self.optionsLayout.addWidget(self.modeCombo, 1, 1)
		self.modeCombo.addItem("include")
		self.modeCombo.addItem("exclude")
		self.modeLabel.setToolTip(self.filterTab.filterInfo["mode_description"])
		self.modeCombo.setToolTip(self.filterTab.filterInfo["mode_description"])

		# The filt check box
		self.filtCheckBox = QCheckBox(self.filterTab.filterInfo["filt_label"])
		self.filtCheckBox.setToolTip(self.filterTab.filterInfo["filt_description"])
		self.optionsLayout.addWidget(self.filtCheckBox, 0, 2)
		#self.filtCheckBox.setMinimumWidth(120)
		self.filtCheckBox.setChecked(True)

		# We add a stretch that will fill any extra space on the right-most column
		self.optionsLayout.setColumnStretch(3, 1)

		# We create the control buttons
		self.createButton = QPushButton("Create filter")
		self.createButton.clicked.connect(self.createClick)
		self.filterTab.addButton(self.createButton)

		
		self.thresholdEdit.setValidator(QIntValidator())
		
		#log
		self.logger = logging.getLogger(__name__)


	def createClick(self):
		""" Adds the new filter to the Summary tab """

		# We record the current tab index so that we know which tab to update the name of
		tabIndex = self.filterTab.tabsArea.currentIndex()

		# We take a reading of the current number of filters so that we can determine how many new
		# ones this will create
		egSubset = self.filterTab.project.eg.subsets['All_Samples'][0]
		oldFilters = len(list(self.filterTab.project.eg.data[egSubset].filt.components.keys()))

		# We make sure that we can cast the contents of the threshold field to an int
		try:
			threshold = int(self.thresholdEdit.text())
		except:
			self.raiseError("The " + self.filterTab.filterInfo["threshold_label"] + " value must be an integer.")
			return

		# We create the filter
		try:
			self.filterTab.project.eg.filter_defragment(threshold = threshold,
													mode = self.modeCombo.currentText(),
													filt = self.filtCheckBox.isChecked())
		except:
			try:    # This has no reference to the latools log currently
					#for l in self.project.eg.log:
					#	self.logger.error(l)
					self.logger.error('Attempting defragment filter with variables: [mode]:{}\n[filt]:{}'.format( self.modeCombo.currentText(),
									self.filtCheckBox.isChecked()))
			except:
				self.logger.exception('Failed to log history:')
			finally:
				self.logger.exception('Exception creating filter:')
			self.raiseError("An error occurred while trying to create this filter. <br> There may be a problem with " +
							"the input values.")
			return

		# We update the name of the tab with the filter details
		self.createName(tabIndex, "Defrag", self.modeCombo.currentText(), str(threshold))

		# We determine how many filters have been created
		egSubset = self.filterTab.project.eg.subsets['All_Samples'][0]
		currentFilters = list(self.filterTab.project.eg.data[egSubset].filt.components.keys())

		# We create filter rows for each new filter
		for i in range(len(currentFilters) - oldFilters):
			self.filterTab.createFilter(currentFilters[i + oldFilters])

		# We disable all of the option fields so that they record the parameters used in creating the filter
		self.freezeOptions()

	def raiseError(self, message):
		""" Creates an error box with the given message """
		errorBox = QMessageBox.critical(self.filterTab.filter, "Error", message, QMessageBox.Ok)

	def createName(self, index, name, mode, thresh):
		""" We create a more descriptive name to display on the tab """
		self.filterTab.name = name + " " + mode + " " + thresh
		self.filterTab.updateName(index)

	def loadFilter(self, params):
		""" When loading an lalog file, the parameters of this filter are added to the gui, then the
			create button function is called.

			Parameters
			----------
			params : dict
				The key-word arguments of the filter call, saved in the lalog file.
		"""
		# For the args in params, we update each filter option, using the default value if the argument is not in the dict.
		self.thresholdEdit.setText(str(params.get("threshold", "")))
		self.modeCombo.setCurrentIndex(self.modeCombo.findText(params.get("mode", "include")))
		self.filtCheckBox.setChecked(params.get("filt", True))

		# We act as though the user has added these options and clicked the create button.
		self.createClick()

	def freezeOptions(self):
		"""
		We lock the option fields after the filter has been created so that they will give a representation
		of the details of the filter
		"""
		self.thresholdEdit.setEnabled(False)
		self.modeCombo.setEnabled(False)
		self.filtCheckBox.setEnabled(False)
		self.createButton.setEnabled(False)

	def updateOptions(self):
		""" Delivers the current state of each option to the plot pane. """
		return {
			"threshold": self.thresholdEdit.text(),
			"mode": self.modeCombo.currentText(),
			"filt": self.filtCheckBox.isChecked()
		}
