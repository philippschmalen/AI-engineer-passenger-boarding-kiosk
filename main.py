import logging
from azure.ai.formrecognizer import FormRecognizerClient
from azure.core.credentials import AzureKeyCredential
from src.utils_data import load_img
from src.utils_data import get_id_details
from src.utils_data import get_url_boardingpass
from src.utils_data import get_dict_boardingpass
from dotenv import load_dotenv
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


if __name__ == "__main__":

    load_dotenv()
    AZURE_FORM_RECOGNIZER_ENDPOINT = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
    AZURE_FORM_RECOGNIZER_KEY = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
    AZURE_FORM_RECOGNIZER_MODEL_ID = os.getenv("AZURE_FORM_RECOGNIZER_MODEL_ID")

    form_recognizer_client = FormRecognizerClient(
        AZURE_FORM_RECOGNIZER_ENDPOINT,
        AzureKeyCredential(AZURE_FORM_RECOGNIZER_KEY),
    )

    # ID DOCUMENTS
    input_img_id = load_img(filepath="data/raw/id_amybennett.jpg")
    # get id details
    dict_id = get_id_details(form_recognizer_client, input_img_id)
    print(dict_id)

    # BOARDING PASS
    input_img_boardingpass = load_img(filepath="data/raw/boarding_amybennett.pdf")
    get_url = get_url_boardingpass(
        input_img_boardingpass,
        apikey=AZURE_FORM_RECOGNIZER_KEY,
        endpoint=AZURE_FORM_RECOGNIZER_ENDPOINT,
        model_id=AZURE_FORM_RECOGNIZER_MODEL_ID,
    )
    dict_boardingpass = get_dict_boardingpass(
        get_url=get_url, apikey=AZURE_FORM_RECOGNIZER_KEY
    )
    print(dict_boardingpass)
