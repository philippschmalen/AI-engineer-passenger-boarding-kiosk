import pandas as pd
import logging
from datetime import datetime
from datetime import timedelta
from typing import Union


def validate_name_dob(dict_id: dict, flight_manifest: pd.DataFrame) -> pd.DataFrame:

    # get idx where name matches, if more than one, check dob
    idx_name = flight_manifest.query(
        f"name == '{(name := dict_id.get('full_name'))}'"
    ).index

    # if idx_match none, raise error
    if idx_name.empty:
        logging.warning(f"Name {name} not found in flight manifest. Check name.")
        return False
    if len(idx_name) > 1:
        logging.warning(f"Multiple names {name} found in flight manifest.")
        # TODO: handle multiple matches
        return False
    # validate dob
    elif len(idx_name) == 1:
        if (
            all(
                (dob_manifest := flight_manifest.loc[idx_name].birthdate.dt.date)
                == (dob := dict_id.get("dob"))
            )
            is True
        ):
            logging.info(f"Validated: {name}, {dob}")
            return True
        else:
            logging.warning(
                f"{dob} does not match {name}'s dob in manifest, {dob_manifest}."
            )
            return False
    else:
        logging.warning(f"{name} not found in flight manifest.")
        return False


def validate_boardingpass(
    dict_boardingpass: dict, flight_manifest: pd.DataFrame
) -> bool:

    # validate boarding pass
    dict_reference = flight_manifest.query(
        f"name == '{(dict_boardingpass.get('name'))}'"
    ).to_dict(orient="records")[0]

    # name
    valid_boarding_name = dict_reference["name"] == dict_boardingpass.get("name")

    # seat
    valid_boarding_seat = dict_reference["seat"] == dict_boardingpass.get("seat")

    # flight id
    valid_boarding_flight = dict_reference["flight_number"] == (
        dict_boardingpass["airline"] + "-" + dict_boardingpass["flight_number"]
    )

    # origin
    valid_boarding_origin = dict_reference["origin"] == dict_boardingpass.get("origin")

    # destination
    valid_boarding_destination = dict_reference["destination"] == dict_boardingpass.get(
        "destination"
    )

    # flight date
    valid_boarding_date = (
        dict_reference["flight_date"].strftime("%d.%m") == dict_boardingpass["date"]
    )

    # flight time (boarding + 30 min)
    dict_reference["flight_boarding"] = (
        datetime.strptime(dict_reference["flight_time"], "%H:%M")
        - timedelta(minutes=30)
    ).strftime("%H:%M")
    valid_boarding_time = (
        dict_reference["flight_boarding"] == dict_boardingpass["flight_boarding"]
    )

    if all(
        [
            valid_boarding_name,
            valid_boarding_seat,
            valid_boarding_flight,
            valid_boarding_origin,
            valid_boarding_destination,
            valid_boarding_date,
            valid_boarding_time,
        ]
    ):
        logging.info("Boarding pass is valid.")
        return True
    else:
        logging.warning(
            f"One or more item from boarding pass is invalid: {dict_reference}, {dict_boardingpass}"
        )
        return False


def validate_face(dict_face: dict, confidence_min: float = 0.6) -> bool:
    if (
        dict_face.get("face_is_identical")
        and dict_face.get("confidence") > confidence_min
    ):
        logging.info("Person validated. Face from video matches with ID photo.")
        return True
    else:
        return False


def has_no_lighter(result: dict, detect_threshold: float = 0.2) -> bool:
    if (
        probability := result.get("probabilities_topn").get("lighter")[0]
    ) > detect_threshold:
        logging.info(f"Lighter detected with probability {probability}")
        return False
    else:
        logging.info(f"No lighter detected with probability {probability}")
        return True


def update_manifest(
    flight_manifest: pd.DataFrame,
    idx: pd.core.indexes.numeric.Int64Index,
    column_update: Union[str, list],
) -> pd.DataFrame:

    flight_manifest.loc[idx, column_update] = True
    logging.info(f"Set {column_update} True.")

    return flight_manifest


def pipeline_validate(
    flight_manifest: pd.DataFrame,
    dict_id: dict,
    dict_boardingpass: dict,
    dict_face: dict,
    dict_lighter: dict,
):
    """Validation based on detection results"""
    idx = flight_manifest.loc[flight_manifest.name == dict_id.get("full_name"), :].index

    if len(idx) == 0:
        logging.error(f"{dict_id.get('full_name')} not found in manifest.")
        return None

    if validate_name_dob(dict_id, flight_manifest):
        update_manifest(flight_manifest, idx, ["valid_dob", "valid_name"])

    if validate_boardingpass(dict_boardingpass, flight_manifest):
        update_manifest(flight_manifest, idx, "valid_boardingpass")

    if validate_face(dict_face):
        update_manifest(flight_manifest, idx, "valid_person")

    if has_no_lighter(dict_lighter):
        update_manifest(flight_manifest, idx, "valid_luggage")

    flight_manifest.loc[idx].to_csv(
        filepath := f"data/validated/flight_manifest_{idx[0]}.csv", index=False
    )

    logging.info(
        f"Saved validated manifest for {dict_id.get('full_name')} to {filepath}"
    )

    return flight_manifest.loc[idx]


def message_to_passenger(passenger_manifest) -> None:
    df = passenger_manifest.iloc[0]

    if (df.filter(like="valid") * 1).sum() >= 3:
        logging.info("Flight manifest is valid.")
        print(
            f"""
        Dear {df.loc['name']},
        You are welcome to flight {df.loc['flight_number']} departing at {df.loc['flight_time']} from San Francisco to Chicago.
        Your seat number is {df.loc['seat']}, and it is confirmed.
        Your identity is verified so please board the plane.
        """
        )

    if (df.filter(like="valid") * 1).sum() < 3:
        print(
            """
        Dear Sir/Madam,
        Some of the information in your boarding pass does not match the flight manifest data, so you cannot board the plane.
        Please see a customer service representative.
        """
        )

    if not df.loc["valid_luggage"]:
        print(
            """
        CAUTION
        We have found a prohibited item in your carry-on baggage, and it is flagged for removal. Please remove it.
        """
        )

    if not df.loc["valid_boardingpass"]:
        print(
            """
        Dear Sir/Madam,
        Some of the information on your ID card does not match the flight manifest data, so you cannot board the plane.
        Please see a customer service representative.
        """
        )
