"""
Validation pipeline that checks
1. Name and DOB from id card
2. Boarding pass
3. Face from video
4. Lighter
"""

from dotenv import load_dotenv
from azure.ai.formrecognizer import FormRecognizerClient
from azure.cognitiveservices.vision.face import FaceClient
from azure.core.credentials import AzureKeyCredential
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.customvision.training import (
    CustomVisionTrainingClient,
)
from azure.cognitiveservices.vision.customvision.prediction import (
    CustomVisionPredictionClient,
)
from msrest.authentication import ApiKeyCredentials
import os
from glob import glob
from src.utils_data import load_img
from src.utils_data import get_id_details
from src.utils_data import get_flight_manifest
from src.utils_data import get_url_boardingpass
from src.utils_data import get_dict_boardingpass
from src.utils_data import compare_faces
from src.utils_lighterdetection import pipeline_prediction_lighterdetection
from src.utils_validate import pipeline_validate
from src.utils_validate import message_to_passenger
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main():
    load_dotenv()

    AZURE_FORM_RECOGNIZER_ENDPOINT = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
    AZURE_FORM_RECOGNIZER_KEY = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
    AZURE_FORM_RECOGNIZER_ENDPOINT = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
    AZURE_FORM_RECOGNIZER_MODEL_ID = os.getenv("AZURE_FORM_RECOGNIZER_MODEL_ID")
    AZURE_FORM_RECOGNIZER_KEY = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
    # VIDEO_ID = os.getenv("AZURE_VIDEO_ANALYZER_VIDEO_ID")

    AZURE_FACE_RECOGNITION_ENDPOINT = os.getenv("AZURE_FACE_RECOGNITION_ENDPOINT")
    AZURE_FACE_RECOGNITION_KEY = os.getenv("AZURE_FACE_RECOGNITION_KEY")

    AZURE_CUSTOMVISION_ENDPOINT = os.getenv("AZURE_CUSTOMVISION_ENDPOINT")
    AZURE_CUSTOMVISION_TRAINING_KEY = os.getenv("AZURE_CUSTOMVISION_TRAINING_KEY")
    AZURE_CUSTOMVISION_PREDICTION_KEY = os.getenv("AZURE_CUSTOMVISION_PREDICTION_KEY")
    AZURE_CUSTOMVISION_PROJECTNAME = os.getenv("AZURE_CUSTOMVISION_PROJECTNAME")
    AZURE_CUSTOMVISION_PUBLISHNAME = os.getenv("AZURE_CUSTOMVISION_PUBLISHNAME")

    # auth clients
    form_recognizer_client = FormRecognizerClient(
        AZURE_FORM_RECOGNIZER_ENDPOINT,
        AzureKeyCredential(AZURE_FORM_RECOGNIZER_KEY),
    )

    # vi = VideoIndexer(
    #     vi_subscription_key=os.getenv("AZURE_VIDEO_ANALYZER_SUBSCRIPTION"),
    #     vi_location=os.getenv("AZURE_VIDEO_ANALYZER_LOCATION"),
    #     vi_account_id=os.getenv("AZURE_VIDEO_ANALYZER_ACCOUNT_ID"),
    # )

    face_client = FaceClient(
        AZURE_FACE_RECOGNITION_ENDPOINT,
        CognitiveServicesCredentials(AZURE_FACE_RECOGNITION_KEY),
    )

    credentials = ApiKeyCredentials(
        in_headers={"Training-key": AZURE_CUSTOMVISION_TRAINING_KEY}
    )
    trainer = CustomVisionTrainingClient(AZURE_CUSTOMVISION_ENDPOINT, credentials)
    prediction_credentials = ApiKeyCredentials(
        in_headers={"Prediction-key": AZURE_CUSTOMVISION_PREDICTION_KEY}
    )
    predictor = CustomVisionPredictionClient(
        AZURE_CUSTOMVISION_ENDPOINT, prediction_credentials
    )

    # load reference data
    flight_manifest = get_flight_manifest()
    images_lighter = glob(
        os.path.join("data/raw/lighter_test_images", "lighter_test_set_*.jpg")
    )
    images_boarding = glob(os.path.join("data/raw", "boarding_*.pdf"))
    images_id = glob(os.path.join("data/raw", "id_*.jpg"))
    images_thumb = glob(os.path.join("data/video/thumbnail", "ps-*.jpg"))

    for i in range(len(images_boarding)):
        img_boarding = load_img(images_boarding[i])
        img_id = load_img(images_id[i])
        img_lighter = load_img(images_lighter[i])
        img_thumb = load_img(images_thumb[0])

        # ID
        dict_id = get_id_details(form_recognizer_client, img_id)

        # boarding pass
        get_url = get_url_boardingpass(
            img_boarding,
            apikey=AZURE_FORM_RECOGNIZER_KEY,
            endpoint=AZURE_FORM_RECOGNIZER_ENDPOINT,
            model_id=AZURE_FORM_RECOGNIZER_MODEL_ID,
        )
        dict_boardingpass = get_dict_boardingpass(
            get_url, apikey=AZURE_FORM_RECOGNIZER_KEY
        )

        # video
        dict_face = compare_faces(
            face_client, img_reference=img_id, img_compare=img_thumb
        )

        # lighter detection
        dict_lighter = pipeline_prediction_lighterdetection(
            trainer,
            predictor,
            AZURE_CUSTOMVISION_PROJECTNAME,
            AZURE_CUSTOMVISION_PUBLISHNAME,
            img_lighter,
        )

        # validate
        passenger_manifest = pipeline_validate(
            flight_manifest,
            dict_id,
            dict_boardingpass,
            dict_face,
            dict_lighter,
        )

        message_to_passenger(passenger_manifest)


if __name__ == "__main__":
    main()
