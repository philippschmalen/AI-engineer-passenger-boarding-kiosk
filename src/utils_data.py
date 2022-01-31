import logging
import yaml
import pandas as pd
import numpy as np
from faker import Faker


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
