# AI-powered passenger boarding kiosk

## TODO

- [ ] check starter code
- [ ] use [Faker](https://github.com/joke2k/faker) to get

  * Flight Number UA-123
  * Carrier Number
  * Flight Origin
  * Destination
  * Flight Date
  * Flight Time
  * Gate Number
  * Boarding Time

- [ ] 5x personal details
  * First Name
  * Last Name
  * Date of Birth
  * Sex
  * Seat Number
  * Face Image - Please use 5 distinct face images, one for each digital ID. One of these face images should be yours. Later in the project, you will perform face verification by comparing the face image on the ID card with the face shown in the 30-second video. Because face verification is done only once, you need to  add your face image to only one ID card.

- [ ] fill out drivers license with image editing


---

## Project brief

> **Goal:** Build an AI-powered boarding kiosk for a fictional airline.

![](img/process-overview.png)

**Key results**

![](img/kiosk-outcome.png)

**Data**

The data comprises the following areas:

* flight details (flight number, carrier code, departure, destination, date, time, gate, boarding)
* passenger details (name, birth date, sex, seat, face image)

![](img/data-overview.png)

---

## Getting started

Install required packages: `terraform`, `az cli`, `Anaconda/Miniconda`


```bash
# clone repo
git clone https://github.com/philippschmalen/AI-engineer-passenger-boarding-kiosk.git

# create conda env 'az-sandbox'
conda env create -f conda.yaml
conda activate az-sandbox

# init pre-commit + hooks
pre-commit install
pre-commit autoupdate
```

---


## Process flow

The kiosk does the following internal processing

* The text data collected from the boarding pass and digital ID is used to cross-reference with the flight manifest to validate flight boarding. There will be more details on this on the Project Starter Material Preparation page. If the page title is truncated on the left-side panel, you can hover your mouse over the page title and see it in full.
* The origin and destination data is used to provide more information about the destination on the kiosk screen
* ID photo validation matched with given photo (extracted from video) - X% above the threshold
* Collect passenger emotion as positive or negative feedback

* Additionally, outside of the scope of the kiosk: Perform the lighter detection from carry-on items

* Finally, upload the data (input and validated) to Azure Blob storage

## Architecture

![](img/az-architecture.png)

---

## Extensions

* add github action
