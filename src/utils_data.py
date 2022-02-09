import json
from requests import get, post
import logging
import yaml
import time
import pandas as pd
import numpy as np
from faker import Faker
from azure.ai.formrecognizer import FormRecognizerClient


def load_config(filepath: str = "config.yaml") -> dict:
    "load config file from filepath with yaml safe_load"
    with open(filepath, "r") as stream:
        try:
            config = yaml.safe_load(stream)
            logging.info(f"Loaded config file: {filepath}")
        except yaml.YAMLError as exc:
            logging.error(f"Error in config file: {str(exc)}")
            config = None

    return config


def get_data():

    config = load_config()

    # Faker to generate data
    fake = Faker()
    Faker.seed(config["data"]["faker"]["seed"])
    n_records = config["data"]["n_records"]
    passengers = [fake.simple_profile() for _ in range(n_records)]
    validations = [False for _ in range(n_records)]
    flight_date = fake.date_time_this_year()

    return pd.DataFrame(
        {
            # flight data
            "flight_number": np.repeat(fake.bothify("LH-###"), n_records),
            "flight_date": np.repeat(flight_date.date(), n_records),
            "flight_time": np.repeat(flight_date.time(), n_records),
            "origin": np.repeat(config["data"]["origin"], n_records),
            "destination": np.repeat(config["data"]["destination"], n_records),
            # passenger data
            "name": [p.get("name") for p in passengers],
            "sex": [p.get("sex") for p in passengers],
            "birthdate": [p.get("birthdate") for p in passengers],
            "seat": [
                str(fake.random_int(min=1, max=25))
                + fake.bothify("?", letters="ABCDEF")
                for _ in range(n_records)
            ],
            "valid_dob": validations,
            "valid_person": validations,
            "valid_luggage": validations,
            "valid_name": validations,
            "valid_boardingpass": validations,
        }
    )


def load_img(filepath: str) -> bytes:
    "Returns image as byte array"

    logging.info(f"Loading {filepath}")

    with open(filepath, "rb") as image_file:
        return image_file.read()


def get_id_details(
    form_recognizer_client: FormRecognizerClient,
    input_img: bytes,
    verbose: bool = False,
) -> dict:
    "Gets text from"
    poller = form_recognizer_client.begin_recognize_identity_documents(input_img)
    id_documents = poller.result()

    for idx, id_document in enumerate(id_documents):
        logging.info("Recognizing ID document")
        first_name = id_document.fields.get("FirstName")
        if verbose and first_name:
            print(
                "First Name: {} has confidence: {}".format(
                    first_name.value, first_name.confidence
                )
            )
        last_name = id_document.fields.get("LastName")
        if verbose and last_name:
            print(
                "Last Name: {} has confidence: {}".format(
                    last_name.value, last_name.confidence
                )
            )
        document_number = id_document.fields.get("DocumentNumber")
        if verbose and document_number:
            print(
                "Document Number: {} has confidence: {}".format(
                    document_number.value, document_number.confidence
                )
            )
        dob = id_document.fields.get("DateOfBirth")
        if verbose and dob:
            print(f"Date of Birth: {dob.value} has confidence: {dob.confidence}")
        doe = id_document.fields.get("DateOfExpiration")
        if verbose and doe:
            print(
                "Date of Expiration: {} has confidence: {}".format(
                    doe.value, doe.confidence
                )
            )
        sex = id_document.fields.get("Sex")
        if verbose and sex:
            print("Sex: {} has confidence: {}".format(sex.value, sex.confidence))
        address = id_document.fields.get("Address")
        if verbose and address:
            print(
                "Address: {} has confidence: {}".format(
                    address.value, address.confidence
                )
            )
        country_region = id_document.fields.get("CountryRegion")
        if verbose and country_region:
            print(
                "Country/Region: {} has confidence: {}".format(
                    country_region.value, country_region.confidence
                )
            )
        region = id_document.fields.get("Region")
        if verbose and region:
            print(
                "Region: {} has confidence: {}".format(region.value, region.confidence)
            )

    try:
        return {
            "first_name": first_name.value,
            "last_name": last_name.value,
            "full_name": first_name.value + " " + last_name.value,
            "dob": dob.value,
        }
    except UnboundLocalError:
        logging.error("Not possible to extract ID details. Return None.")
        return None


def get_url_boardingpass(
    input_img: bytes, apikey: str, endpoint: str, model_id: str
) -> dict:
    "Returns dataframe of boarding pass tags"

    if apikey is None:
        raise ValueError("apikey missing")

    if endpoint is None:
        raise ValueError("Form recognizer endpoint missing")

    if model_id is None:
        raise ValueError("model_id missing")

    post_url = f"{endpoint}/formrecognizer/v2.1/custom/models/{model_id}/analyze"

    params = {"includeTextDetails": True}

    headers = {
        "Content-Type": "application/pdf",
        "Ocp-Apim-Subscription-Key": apikey,
    }

    try:
        resp = post(url=post_url, data=input_img, headers=headers, params=params)
        if resp.status_code != 202:
            logging.error("POST analyze failed:\n%s" % json.dumps(resp.json()))
            quit()
        logging.info("POST analyze succeeded:\n%s" % resp.headers)

        return resp.headers["operation-location"]

    except Exception as e:
        logging.error("POST analyze failed:\n%s" % str(e))
        quit()


def get_dict_boardingpass(
    get_url: str, apikey: str, n_retries: int = 4, sleep_seconds: int = 2
) -> dict:
    "Returns dataframe of boarding pass tags"
    for i in range(n_retries):
        try:
            time.sleep(sleep_seconds)
            resp_get = get(
                url=get_url,
                headers={"Ocp-Apim-Subscription-Key": apikey},
            )

            dict_values = {
                k: v["valueString"]
                for k, v in resp_get.json()
                .get("analyzeResult")
                .get("documentResults")[0]
                .get("fields")
                .items()
            }

            logging.info("SUCCESS. Return boardingpass details as dict.")

            return dict_values
        except AttributeError:
            logging.error(f"GET returned None. Retry {n_retries-i} times.")

            if i == n_retries - 1:
                quit()
            else:
                continue
