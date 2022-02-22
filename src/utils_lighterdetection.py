from azure.cognitiveservices.vision.customvision.training import (
    CustomVisionTrainingClient,
)
from azure.cognitiveservices.vision.customvision.prediction import (
    CustomVisionPredictionClient,
)
from azure.cognitiveservices.vision.customvision.training.models import (
    CustomVisionErrorException,
)
import time
from io import BytesIO
import logging


def train_cv_model(
    trainer,
    project,
    training_time_expected: int = 540,
    sleep_interval: int = 30,
):
    try:
        iteration = trainer.train_project(project.id)
        logging.info(f"Start training. Expected time: {training_time_expected} seconds")
        for i in range(round(training_time_expected / sleep_interval)):
            iteration = trainer.get_iteration(project.id, iteration.id)
            logging.info(f"Training status: {iteration.status}. Sleep for 30s.")

            if iteration.status == "Completed":
                break

            time.sleep(sleep_interval)

        logging.info(f"Training expected to be completed. Status: {iteration.status}")

    except CustomVisionErrorException as e:
        logging.warning(f"{e}. Skip training.")


def get_last_iteration(trainer, project):
    return next(i for i in trainer.get_iterations(project.id))


def get_project(trainer, project_name: str):
    "Loads project from trainer with project_name"
    project = next(
        filter(lambda p: p.name == project_name, trainer.get_projects()), None
    )

    # if project doesn't exist, create it
    if not project:
        object_detection_domain = next(
            domain
            for domain in trainer.get_domains()
            if domain.type == "ObjectDetection" and domain.name == "General"
        )

        project = trainer.create_project(
            project_name, domain_id=object_detection_domain.id
        )

    logging.info(f"Created/loaded project {project.name}.")

    return project


def add_tags(trainer, project, tag_name: str):
    # add tags
    try:
        tag = trainer.create_tag(project.id, tag_name)
        logging.info(f"Created tag {tag.name}.")
        return tag

    except CustomVisionErrorException:
        logging.info("Tag already exists. Load and return")
        tag = next(filter(lambda t: t.name == tag_name, trainer.get_tags(project.id)))

        return tag


def publish_last_iteration_endpoint(
    trainer, project, publish_iteration_name: str, prediction_resource_id: str
):
    last_iteration = get_last_iteration(trainer, project)

    # publish endpoint
    try:
        trainer.publish_iteration(
            project.id,
            last_iteration.id,
            publish_iteration_name,
            prediction_resource_id,
        )

        logging.info(
            f"Published {publish_iteration_name} with {last_iteration.name} ({last_iteration.id})"
        )
    except CustomVisionErrorException as e:
        logging.warning(f"{e}")


def get_published_iteration(trainer, project):
    # get prediction endpoint
    iteration_published = next(
        i for i in trainer.get_iterations(project.id) if i.publish_name
    )
    if iteration_published:
        logging.info(
            f"Found published iteration: {iteration_published.name} ({iteration_published.id})"
        )
    else:
        logging.info("No published iteration found.")

    return iteration_published


def detect_image(predictor, project, publish_iteration_name: str, image: bytes):
    logging.info("Detecting lighters")
    return predictor.detect_image(project.id, publish_iteration_name, BytesIO(image))


def get_prediction_result(result, top_n: int = 3) -> dict:
    return {
        tag_name: [p.probability for p in result.predictions if p.tag_name == tag_name][
            :top_n
        ]
        for tag_name in list(set([p.tag_name for p in result.predictions]))
    }


def pipeline_training_lighterdetection(
    trainer: CustomVisionTrainingClient,
    project_name: str,
    publish_name: str,
    prediction_resource_id: str,
):
    "Main function for training and publishing"
    project = get_project(trainer, project_name)
    add_tags(trainer, project, "lighter")
    train_cv_model(trainer, project)
    publish_last_iteration_endpoint(
        trainer, project, publish_name, prediction_resource_id
    )


def pipeline_prediction_lighterdetection(
    trainer: CustomVisionTrainingClient,
    predictor: CustomVisionPredictionClient,
    project_name: str,
    publish_name: str,
    image: bytes,
    top_n: int = 3,
):
    project = get_project(trainer, project_name)
    result = detect_image(predictor, project, publish_name, image)
    probabilities = get_prediction_result(result, top_n=top_n)

    logging.info(f"Prediction probabilities: {probabilities}")

    return {
        "result_object": result,
        "probabilities_topn": probabilities,
    }
