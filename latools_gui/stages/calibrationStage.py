""" A stage of the program that defines and executes one step of the data-processing """

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl, Qt
import latools as la
import inspect
import templates.controlsPane as controlsPane

class CalibrationStage():
	"""
	Each stage has its own Controls Pane, where it defines a description and the unique options for that
	step of the data-processing. It updates the graph pane based on the modifications that are made to the
	project.
	"""
	def __init__(self, stageLayout, graphPaneObj, progressPaneObj, calibrationWidget, project):
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
		project : RunningProject
			A reference to the project object which contains all of the information unique to this project,
			including the latools analyse object that the stages will update.
		"""

		self.graphPaneObj = graphPaneObj
		self.progressPaneObj = progressPaneObj
		self.calibrationWidget = calibrationWidget
		self.project = project

		self.stageControls = controlsPane.ControlsPane(stageLayout)
		self.srmfile = None

		# We capture the default parameters for this stage's function call
		self.defaultParams = self.stageControls.getDefaultParameters(inspect.signature(la.analyse.calibrate))

		# We set the title and description for the stage

		self.stageControls.setDescription("Calibration", """
			Once all your data are normalised to an internal standard, you’re ready to calibrate 
			the data. This is done by creating a calibration curve for each element based on SRMs 
			measured throughout your analysis session, and a table of known SRM values.""")

		# The space for the stage options is provided by the Controls Pane.
		self.optionsHBox = QHBoxLayout(self.stageControls.getOptionsWidget())

		self.optionsLeftWidget = QWidget()
		self.optionsLeft = QGridLayout(self.optionsLeftWidget)
		self.optionsHBox.addWidget(self.optionsLeftWidget)

		self.optionsRightWidget = QScrollArea()
		self.optionsRightWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.optionsRightWidget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.optionsRightWidget.setWidgetResizable(False)
		self.optionsRightWidget.setMinimumWidth(70)
		self.optionsRight = QVBoxLayout(self.optionsRightWidget)
		self.optionsHBox.addWidget(self.optionsRightWidget)

		# We define the stage options and add them to the Controls Pane

		self.drift_correctOption = QCheckBox("drift_correct")
		self.drift_correctOption.setChecked(self.defaultParams['drift_correct'] == 'True')
		self.optionsLeft.addWidget(self.drift_correctOption, 0, 0, 1, 2)

		self.optionsRight.addWidget(QLabel("srms_used"))
		self.optionsRight.addWidget(QCheckBox("NIST610"))
		self.optionsRight.addWidget(QCheckBox("NIST612"))
		self.optionsRight.addWidget(QCheckBox("NIST614"))
		self.optionsRight.addStretch(1)

		self.zero_interceptOption = QCheckBox("zero_intercept")
		self.zero_interceptOption.setChecked(self.defaultParams['zero_intercept'] == 'True')
		self.optionsLeft.addWidget(self.zero_interceptOption, 1, 0)

		self.n_minOption = QLineEdit(self.defaultParams['n_min'])
		self.optionsLeft.addWidget(QLabel("n_min"), 2, 0)
		self.optionsLeft.addWidget(self.n_minOption, 2, 1)

		self.reloadButton = QPushButton("View SRM table")
		self.reloadButton.clicked.connect(self.pressedReloadButton)
		self.stageControls.addApplyButton(self.reloadButton)

		# We create the button for the right-most section of the Controls Pane.

		self.applyButton = QPushButton("APPLY")
		self.applyButton.clicked.connect(self.pressedApplyButton)
		self.stageControls.addApplyButton(self.applyButton)

	def pressedApplyButton(self):
		""" Calibrates the project data when a button is pressed. """

		myn_min = int(self.defaultParams['n_min'])
		if self.n_minOption.text() != "":
			try:
				myn_min = int(self.n_minOption.text())
			except:
				self.raiseError("The 'n_min' value must be an integer")
				return
		try:
			self.project.eg.calibrate(analytes=None,
								drift_correct=self.drift_correctOption.isChecked(),
								srms_used=['NIST610', 'NIST612', 'NIST614'],
								zero_intercept=self.zero_interceptOption.isChecked(),
								n_min=myn_min)
		except:
			self.raiseError("A problem occurred. There may be a problem with the input values.")
			return

		self.progressPaneObj.setRightEnabled()

	def pressedReloadButton(self):
		""" Performs a reload when the button is pressed. """

		url = QUrl.fromLocalFile(self.srmfile)
		QDesktopServices.openUrl(url)

		print(self.srmfile)

	def updateStageInfo(self):
		self.srmfile = self.project.eg.srmfile

	def raiseError(self, message):
		errorBox = QMessageBox.critical(self.calibrationWidget, "Error", message, QMessageBox.Ok)