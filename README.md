# Vuurwerkverkenner

This repository contains code for the **_Vuurwerkverkenner_** ("Fireworks Explorer") web application, which can be used for linking snippets of exploded (heavy) fireworks to the type of firework that they originate from.
It is built on top of the Flask framework.

Vuurwerkverkenner is intended for aiding the investigation at a crime scene where snippets are found, and where determining the type of the exploded fireworks is of interest.
The intended use looks as follows:
1. The user **provides input**, which can consist of either or both of the following:
   * **a photo** of all retrieved snippets that originate from a wrapper (ideally of high quality, with a plain background and good lighting conditions)
   * **any text** that is present on the snippets
3. The **AI model** contained in the application compares the uploaded photo and text to its reference database
4. The application **shows the search results** in descending order of similarity (according to the AI model)
5. The user compares the snippets and the shown wrappers to **establish a match**

The application is developed and maintained by the Netherlands Forensic Institute (NFI).
It is deployed on www.vuurwerkverkenner.nl.

## Model and database
The application relies on a **trained AI model** and a **background database** of fireworks, both maintained by the NFI.
They are both stored on the HuggingFace organization page of the NFI (see [here](https://huggingface.co/NetherlandsForensicInstitute)).
* The model, as well as a description of how it was trained, can be found [here](https://huggingface.co/NetherlandsForensicInstitute/vuurwerkverkenner).
* The background database can be found [here](https://huggingface.co/datasets/NetherlandsForensicInstitute/vuurwerkverkenner-data).

If you want to run the application locally, download a copy of the model and database to your machine.

## Getting started
The following describes how to run the application on your own machine. 
It can be run with a **dummy** model and database (which are contained within this repository), or with a copy of the **real** model and database which are stored on HuggingFace.

### Prerequisites
* Python 3.8
* Any web browser
* Optionally, a local copy of the model and data (see above)

### Requirements
All package requirements for running the application are specified in `requirements.txt`.
Packages can be installed from PyPi, e.g. through `pip install -r requirements.txt`.

### Configuration
Make sure parameters in `app/setup.cfg` (in particular `MODEL_CONFIG_FILE` and `META_DATA_DIR`) match the desired configuration.
* For running the application with a **dummy** model and database, uncomment the indicated lines.
* For running the application with the **real** model and database, make sure that the paths point to the correct locations on your machine. Additionally, make sure that the filepath for the weights file (in the model configuration file) matches the filepath on your machine.

### Running the application
Simply run `flask run` inside a terminal.
Now access the application by navigating to http://localhost:5000 in your web browser.
