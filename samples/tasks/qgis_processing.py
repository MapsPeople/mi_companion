from functools import partial

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsMessageLog,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProject,
)

MESSAGE_CATEGORY = "My processing tasks"


def task_finished(context, successful, results):
    if not successful:
        QgsMessageLog.logMessage(
            "Task finished unsucessfully", MESSAGE_CATEGORY, Qgis.Warning
        )
    output_layer = context.getMapLayer(results["OUTPUT"])
    # because getMapLayer doesn't transfer ownership the layer will be
    # deleted when context goes out of scope and you'll get a crash.
    # takeResultLayer transfers ownership so it's then safe to add it to the
    # project and give the project ownership.
    if output_layer.isValid():
        QgsProject.instance().addMapLayer(context.takeResultLayer(output_layer.id()))


alg = QgsApplication.processingRegistry().algorithmById("qgis:randompointsinextent")
context = QgsProcessingContext()
feedback = QgsProcessingFeedback()
params = {
    "EXTENT": "4.63,11.57,44.41,48.78 [EPSG:4326]",
    "MIN_DISTANCE": 0.1,
    "POINTS_NUMBER": 100,
    "TARGET_CRS": "EPSG:4326",
    "OUTPUT": "memory:My random points",
}
task = QgsProcessingAlgRunnerTask(alg, params, context, feedback)
task.executed.connect(partial(task_finished, context))
QgsApplication.taskManager().addTask(task)
