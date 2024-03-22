var selectedImage = null;
var resultsId = null;

const maxChars = window.MAX_CHARS_TEXT_FILTER
const maxImageSize = window.MAX_UPLOAD_SIZE;
const allowedExtensions = window.ALLOWED_EXTENSIONS;

window.onload = addEventHandlersIndexPage;

function onImageChanged() {
    let imageSelector = document.getElementById("image-selector");
    if (imageSelector.files.length === 0) {
        return; // user cancelled, ignore
    }

    selectedImage = imageSelector.files[0];
    if (!verifyFileExtensionSelectedImage(selectedImage)) {
        resetAfterIncorrectUserInput();
        return;
    }

    if (selectedImage.size > maxImageSize) {
        resetAfterTooLargeImageSelection();
        return;
    }
    showImagePreview();
    updateLabelText();
}


function verifyFileExtensionSelectedImage(image) {
    let fileExtension = image.name.split('.').pop().toLowerCase();
    let verified = allowedExtensions.toLowerCase().includes(fileExtension);
    if (!verified) {
        alert(`Bestandstype ${fileExtension} wordt niet ondersteund.\nToegestane bestandstypes zijn: ${allowedExtensions}`);
    }
    return verified;
}

function resetAfterTooLargeImageSelection() {
    alert(`Bestand is te groot (maximaal ${Math.round(maxImageSize / 1e6)} MB)`);
    resetAfterIncorrectUserInput();
}

function resetAfterIncorrectUserInput() {
    resetImageInput();
    hide("preview");
    updateLabelText();
}

function resetImageInput() {
    selectedImage = null;
    document.getElementById("preview").src = null;
    document.getElementById("image-selector").value = null;
}

function resetTextInput() {
    document.getElementById("text").value = null;
}

function printInputLength() {
    let nChars = document.getElementById("text").value.length;
    document.getElementById("char-counter-text-input").textContent =
        nChars + ' / ' + maxChars + ' tekens';
}

function onNewResultsButtonClicked() {
    let text = document.getElementById("text").value;

    if (text.trim() === "" && selectedImage === null) {
        alert("Voer een foto en/of tekst in");
        return;
    }
    switchMode("view-all-results");
    showLoaderForResults();
    retrieveNewResults();
}

function showImagePreview() {
    let fileReader = new FileReader();
    fileReader.readAsDataURL(selectedImage);
    fileReader.onload = function (fileReaderEvent) {
        document.getElementById("preview").src = fileReaderEvent.target.result;
        displayBlock("preview");
    }
}

function updateLabelText() {
    let fileNameLabel = document.getElementById('image-selector-label');
    fileNameLabel.textContent = (selectedImage !== null) ? selectedImage.name : 'Maak of selecteer foto';
}

function retrieveNewResults() {
    let data = new FormData();
    data.append("text", document.getElementById("text").value);
    data.append("file", selectedImage);

    fetch("results", {
        "method": "POST",
        "body": data,
    })
        .then(response => response.json())
        .then(json => onNewResultsIdRetrieved(json));
}

function onNewResultsIdRetrieved(json) {
    let resultsElement = getResultsElement();
    if (json.errors !== undefined) {
        hide("new-results-button");
        displayInline("clear-query");
        resultsElement.innerHTML = json.errors;
        resultsElement.classList.add('error-message');
    } else {
        resultsElement.classList.remove('error-message');
        resultsId = json.results_id;
        retrieveResults(1);
    }
}

function retrieveResults(page) {
    fetch("results?id=" + resultsId + "&page=" + page)
        .then(response => response.text())
        .then(text => showInResults(text));
}

function getGroupData(groupId, page) {
    switchMode("view-result-group");
    showLoaderForResults();

    fetch("result/group?id=" + groupId + "&page=" + page)
        .then(response => response.text())
        .then(text => showInResults(text));
}

function getItemData(groupId, itemId, source) {
    switchMode("view-result-item", source);
    showLoaderForResults();

    fetch("result/item?group_id=" + groupId + "&item_id=" + itemId)
        .then(response => response.text())
        .then(text => showInResults(text));
}

function openModal(modalName) {
    let modal = document.getElementById(modalName);
    modal.style.display = "block";
    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function (event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    }
}

function closeModal(modalName) {
    let modal = document.getElementById(modalName);
    modal.style.display = "none";
}

function toggleMeta(element) {
    element.classList.toggle('active');
    let button = element.getElementsByClassName("toggle-meta")[0];
    let content = element.getElementsByClassName("toggle-content")[0];

    if (element.classList.contains('active')) {
        content.style.display = "block";
        button.innerHTML = '\uFE3F';
    } else {
        content.style.display = "none";
        button.innerHTML = '\uFE40';
    }
}

function toggleSearchHeaders() {
    document.getElementById("photo-header").innerHTML = "Geüploade foto";
    document.getElementById("text-header").innerHTML = "Ingevoerde tekst";

    let imageSelectorWrapper = document.getElementById("image-selector-wrapper");

    if (mode === Modes.INPUT) {
        imageSelectorWrapper.classList.add('clickable');
    } else {
        imageSelectorWrapper.classList.remove('clickable');
    }
}

function toggleSearchInput() {
    let text = document.getElementById("text").value;
    text = (text === "") ? "Geen tekst ingevoerd" : text;
    document.getElementById("input-text-preview").innerHTML = text;

    if (selectedImage == null) {
        displayInline("photo-preview-text");
    }
}

function addEventHandlersIndexPage() {
    document.getElementById("image-selector-wrapper").addEventListener("click",
        event => handleImageSelectorWrapperClick(event));
}

function handleImageSelectorWrapperClick(e) {
    if (e.target.classList.contains("clickable-info")) {
        openModal('image-selector-modal');
        return;
    }
    if (mode === Modes.INPUT) {
        document.getElementById('image-selector').click();
    }
}