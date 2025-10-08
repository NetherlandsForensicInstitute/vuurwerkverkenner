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

The application is developed and maintained by the Netherlands Forensic Institute (NFI) and is hosted at the following 
domains: www.vuurwerkverkenner.nl, www.vuurwerkverkenner.com, www.vuurwerkverkenner.ai, 
www.fireworksexplorer.eu, www.fireworksexplorer.com, www.fireworksexplorer.ai.

## Model and database
The application relies on a **trained AI model** and a **background database** of fireworks, both maintained by the NFI.
They are both stored on the HuggingFace organization page of the NFI (see [here](https://huggingface.co/NetherlandsForensicInstitute)).
* The model, as well as a description of how it was trained, can be found [here](https://huggingface.co/NetherlandsForensicInstitute/vuurwerkverkenner).
* The background database can be found [here](https://huggingface.co/datasets/NetherlandsForensicInstitute/vuurwerkverkenner-data).

## Running the app locally
The following describes how to run the application on your own machine. 
It can be run with the live model and database, which are stored on HuggingFace.

### Prerequisites
* Python 3.12
* Any web browser
* An internet connection (required for downloading the data when running the application for the first time)

#### Recommended:  
* A Python virtual environment
* A HuggingFace account + access token  
  Set the token as an environment variable named `HF_TOKEN`  
  NOTE: It is possible to download the data without this token, but you will likely have to restart the process
  a few times for it to fully complete te download.

### Requirements
All package requirements for running the application are specified in `pyproject.toml`. 

### Model and data
The model and data are downloaded from HuggingFace when running the app for the first time. These data are saved 
to the paths `MODEL_DIR` and `META_DATA_DIR`,
which are listed in `setup.cfg`.

### Running the application
Simply run `flask run` inside a terminal.
Now access the application by navigating to http://localhost:5000 in your web browser.
