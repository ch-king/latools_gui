""" A stage of the program that defines and executes one step of the data-processing """

from PyQt5.QtWidgets import *
import latools as la
import inspect
import templates.controlsPane as controlsPane
import json
import ast
import os
import sys

import time

from project.ErrLogger import logged
import logging

class ImportStage():
	"""
	Each stage has its own Controls Pane, where it defines a description and the unique options for that
	step of the data-processing. It updates the graph pane based on the modifications that are made to the
	project.
	"""
	#@logged
	def __init__(self, stageLayout, graphPaneObj, progressPaneObj, importStageWidget, project):
		"""
		Initialising creates and customises a Controls Pane for this stage.

		Parameters
		----------
		stageLayout : QVBoxLayout
			The layout for the entire stage screen, that the Controls Pane will be added to.
		graphPaneObj : GraphPane
			A reference to the Graph Pane that will sit at the bottom of the stage screen and display
			updates t the graph, produced by the processing defined in the stage.
		progressPaneObj : ProgressPane
			A reference to the Progress Pane so that the right button can be enabled by completing the stage.
		importStageWidget : QWidget
			A reference to this stage's widget in order to manage popup windows
		project : RunningProject
			A reference to the project object which contains all of the information unique to this project,
			including the latools analyse object that the stages will update.
		"""
		self.logger = logging.getLogger(__name__)
		self.logger.info('Initialised import stage!')

		self.graphPaneObj = graphPaneObj
		self.progressPaneObj = progressPaneObj
		self.importStageWidget = importStageWidget
		self.fileLocation = ""
		self.project = project
		self.importListener = None

		self.stageControls = controlsPane.ControlsPane(stageLayout)

		# We capture the default parameters for this stage's function call
		self.defaultParams = self.stageControls.getDefaultParameters(inspect.signature(la.analyse))

		# We import the stage information from a json file and set the default data folder
		if getattr(sys, 'frozen', False):
			# If the program is running as a bundle, then get the relative directory
			infoFile = os.path.join(os.path.dirname(sys.executable), 'information/importStageInfo.json')
			infoFile = infoFile.replace('\\', '/')

			self.defaultDataFolder = os.path.join(os.path.dirname(sys.executable), "./data/")
			self.defaultDataFolder = self.defaultDataFolder.replace('\\', '/')
		else:
			# Otherwise the program is running in a normal python environment
			infoFile = "information/importStageInfo.json"
			self.defaultDataFolder = "./data/"

		with open(infoFile, "r") as read_file:
			self.stageInfo = json.load(read_file)
			read_file.close()

		# We set the title and description for the stage

		self.stageControls.setDescription("Import Data", self.stageInfo["stage_description"])

		# The space for the stage options is provided by the Controls Pane.
		self.optionsGrid = QGridLayout(self.stageControls.getOptionsWidget())

		# We define the stage options and add them to the Controls Pane

		self.findDataButton = QPushButton(self.stageInfo["find_data_label"])
		self.findDataButton.setMaximumWidth(100)
		self.findDataButton.clicked.connect(self.findDataButtonClicked)
		self.optionsGrid.addWidget(self.findDataButton,0,0)
		self.findDataButton.setToolTip(self.stageInfo["find_data_description"])

		self.fileLocationLine = QLineEdit(self.defaultDataFolder)
		self.optionsGrid.addWidget(self.fileLocationLine, 0, 1)
		self.fileLocationLine.setReadOnly(True)
		self.fileLocationLine.setToolTip(self.stageInfo["find_data_description"])

		self.configOption = QComboBox()
		# The configOption values are added based on the read_latoolscfg values
		for key in dict(la.config.read_latoolscfg()[1]):
			self.configOption.addItem(key)

		self.config_label = QLabel(self.stageInfo["config_label"])
		self.optionsGrid.addWidget(self.config_label, 1,0)
		self.optionsGrid.addWidget(self.configOption, 1,1)
		self.configOption.setToolTip(self.stageInfo["config_description"])
		self.config_label.setToolTip(self.stageInfo["config_description"])

		self.srm_identifierLabel = QLabel(self.stageInfo["srm_label"])
		self.srm_identifierOption = QLineEdit(self.defaultParams['srm_identifier'])
		self.optionsGrid.addWidget(self.srm_identifierLabel, 2, 0)
		self.optionsGrid.addWidget(self.srm_identifierOption, 2, 1)
		self.srm_identifierOption.setToolTip(self.stageInfo["srm_description"])
		self.srm_identifierLabel.setToolTip(self.stageInfo["srm_description"])

		self.file_extensionLabel = QLabel(self.stageInfo["file_extension_label"])
		self.file_extensionOption = QLineEdit(self.defaultParams['extension'])
		self.optionsGrid.addWidget(self.file_extensionLabel, 3, 0)
		self.optionsGrid.addWidget(self.file_extensionOption, 3, 1)
		self.file_extensionOption.setToolTip(self.stageInfo["file_extension_description"])
		self.file_extensionLabel.setToolTip(self.stageInfo["file_extension_description"])

		# We create a reset to default button

		self.defaultButton = QPushButton("Defaults")
		self.defaultButton.clicked.connect(self.defaultButtonPress)
		self.stageControls.addDefaultButton(self.defaultButton)

		# We create the button for the right-most section of the Controls Pane.

		self.applyButton = QPushButton("APPLY")
		self.applyButton.clicked.connect(self.pressedApplyButton)
		self.stageControls.addApplyButton(self.applyButton)

	#@logged
	def pressedApplyButton(self):
		""" Imports data into the project when the apply button is pressed. """

		

		# The actual call to the analyse object for this stage is run, using the stage values as parameters
		self.logger.info('Button clicked')

			#Logging
			#logger.info('Executing stage Import with stage variables: [DataFolder]:%s\n[Config]:%s\n[Extension]:%s\n[srm_Identifier]:%s\n',
			#	    self.fileLocation.text(),
			#	    self.configOption.currentText(),
			#	    self.file_extensionOption.text(),
			#	    self.srm_identifierOption.text())
		self.logger.info('Executing stage Import with stage variables: [Loaction]:{}\n[Config]:{}\n[Extension]:{}\n[srm_Identifier]:{}\n'.format( self.fileLocationLine.text(),
																			       self.configOption.currentText(),
																			       self.file_extensionOption.text(),
																			       self.srm_identifierOption.text()))
		try:
			self.logger.info('Attempting to locate data')
			
			self.project.eg = la.analyse(data_folder=self.fileLocationLine.text(),
										 config=self.configOption.currentText(),
										 extension=self.file_extensionOption.text(),
										 srm_identifier=self.srm_identifierOption.text(),
										 pbar=self.progressPaneObj.progressUpdater)

			self.graphPaneObj.updateGraph(importing=True)

			self.progressPaneObj.completedStage(0)

			# When the data is imported various stage parameters are updated via the importListener
			if not self.importListener is None:
				self.importListener.dataImported()

			# The data location is recorded to be used as the default savefile location
			self.project.setDataLocation(self.fileLocationLine.text())

			# Automatically saves the project if it already has a save location
			self.project.reSave()

                except IOError:
                        self.logger.exception("Error with Importing Data")
                        
			errorBox = QMessageBox.critical(self.importStageWidget,
											"""self.stageInfo["Import Error!"]""",
											"""self.stageInfo["Unable to correctly access your data!"]""",
										QMessageBox.Ok)
		except:
			self.logger.exception("Error with Importing Data")
			print("An error occured")

			errorBox = QMessageBox.critical(self.importStageWidget,
											"""self.stageInfo["general_error_label"]""",
											"""self.stageInfo["general_error_description"]""",
										QMessageBox.Ok)
	#@logged
	def findDataButtonClicked(self):
		""" Opens a file dialog to find a file directory for data import when a button is pressed. """

		self.fileLocation = QFileDialog.getExistingDirectory(self.importStageWidget, 'Open file', '/home')
		self.fileLocationLine.setText(self.fileLocation)
	
	#@logged
	def setImportListener(self, importListener):
		self.importListener = importListener

	#@logged
	def loadValues(self):
		""" Loads the values saved in the project, and fills in the stage parameters with them """

		# The stage parameters are stored in project as dictionaries
		params = self.project.getStageParams("import")

		# The stage parameters are applied to the input fields
		self.fillValues(params)

		# The loading process then activates the stage's apply command
		self.pressedApplyButton()

	def fillValues(self, params):
		""" Fills the stage parameters from a given dictionary """

		if params is not None:
			self.fileLocationLine.setText(params.get("data_folder", ""))
			self.configOption.setCurrentText(params.get("config", ""))
			self.file_extensionOption.setText(params.get("extension", ""))
			self.srm_identifierOption.setText(params.get("srm_identifier", ""))

	#@logged
	def enterPressed(self):
		""" When enter is pressed on this stage """
		if self.applyButton.isEnabled():
			self.pressedApplyButton()

	#@logged
	def relistConfig(self):
		""" When a new configuration is added the config dropdown box needs to be updated """

		# First each item is removed
		while self.configOption.count() != 0:
			self.configOption.removeItem(0)

		# Items are then readded
		for key in dict(la.config.read_latoolscfg()[1]):
			self.configOption.addItem(key)

	#@logged
	def defaultButtonPress(self):

		params = {
			"data_folder": self.defaultDataFolder,
			"config": self.defaultParams["config"],
			"extension": self.defaultParams["extension"],
			"srm_identifier": self.defaultParams["srm_identifier"]
		}

		self.fillValues(params)


