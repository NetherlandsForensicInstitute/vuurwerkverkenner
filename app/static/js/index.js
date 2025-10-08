let selectedImage = null;
let resultsId = null;
let returnToPage = "results";

const maxChars = window.MAX_CHARS_TEXT_FILTER;
const maxImageSize = window.MAX_UPLOAD_SIZE;
const allowedExtensions = window.ALLOWED_EXTENSIONS;

window.onload = addEventHandlersIndexPage;

function onImageChanged() {
    let imageSelector = document.getElementById("image-selector");
    if (imageSelector.files.length === 0) {
        return; // user cancelled, ignore
    }

    selectedImage = imageSelector.files[0];
    onInputChange();

    if (!verifyFileExtensionSelectedImage(selectedImage)) {
        resetAfterIncorrectUserInput();
        return;
    }

    if (selectedImage.size > maxImageSize) {
        resetAfterTooLargeImageSelection();
        return;
    }

    // Unhide the textFilterDiv when the image has been uploaded
    displayFlex('text-filter-option1');

    showImagePreview();
    updateLabelText();
}


function verifyFileExtensionSelectedImage(image) {
    let fileExtension = image.name.split('.').pop().toLowerCase();
    let verified = allowedExtensions.toLowerCase().includes(fileExtension);
    if (!verified) {
        openModal("wrong-file-format-modal");
    }
    return verified;
}

function resetAfterTooLargeImageSelection() {
    openModal("wrong-file-size-modal");
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
    resultsId = null;
}

function resetTextInput() {
    document.getElementById("text").value = null;
}

function printInputLength() {
    let nChars = document.getElementById("text").value.length;
    displayBlock("char-counter-text-input");
    document.getElementById("char-counter-text-input").textContent =
        nChars + ' / ' + maxChars;
}

function onInputChange() {
    printInputLength();
    // Access the text and checkbox
    let text = document.getElementById("text").value;
    let text_filter_checkbox = document.getElementById("use-text-filter");
    let digit_filter_checkbox = document.getElementById("include-digits");

    if (text.length > 0 && selectedImage === null) {
        text_filter_checkbox.checked = true;
        text_filter_checkbox.disabled = true;
        digit_filter_checkbox.checked = true;
        displayFlex('text-filter-option1');
    } else {
        text_filter_checkbox.disabled = false;
        digit_filter_checkbox.checked = false;
        displayFlex('text-filter-option1');
    }
}

function onNewResultsButtonClicked() {
    let text = document.getElementById("text").value;

    // When the text is empty and no image is provided, throw an alert modal
    if (text.trim() === "" && selectedImage === null) {
        openModal("no-photo-text-modal");
        return;
    }
    switchMode("view-results");
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

/**
 * Update the text in the upload photo box by showing either the 'image-selector-label'
 * or 'image-selector-label-empty' span. The separate 'image-selector-label-empty' span
 * is used to be compatible with Flask-babel. 'image-selector-label-empty' contains the
 * default text. 'image-selector-label' is set to the selected filename, if any. Only one
 * of the two spans is visible at any time.
 */
function updateLabelText() {
    let fileNameLabel = document.getElementById('image-selector-label');
    if (selectedImage !== null) {
        fileNameLabel.textContent = selectedImage.name;
        displayBlock("image-selector-label");
        hide("image-selector-label-empty");
        hide("photo-preview-text");
    } else {
        fileNameLabel.textContent = "";
        hide("image-selector-label");
        displayBlock("image-selector-label-empty");
        displayBlock("photo-preview-text");
    }
}

function retrieveNewResults() {
    let data = new FormData();
    data.append("file", selectedImage);
    data.append("query_text", document.getElementById("text").value);
    data.append("text_filter", document.getElementById("use-text-filter").checked);
    data.append("include_digits", document.getElementById("include-digits").checked);
    fetch("search", {
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
        resultsElement.classList.add("error-message");
    } else {
        resultsElement.classList.remove("error-message");
        resultsId = json.results_id;
        retrieveResults(1);
    }
}

function checkBoxClicked() {
    let text = document.getElementById("text").value;

    if (text.trim() === "" && selectedImage === null) {
        return;
    }

    retrieveNewResults();
}


function buildURLParameters(page) {
    let queryText = (document.getElementById("use-text-filter").checked) ? document.getElementById("text").value : "";
    let includeDigits = document.getElementById("include-digits").checked;
    let includeResultsId = (resultsId) ? `&resultsId=${resultsId}` : "";

    return encodeURI(
        `queryText=${queryText}${includeResultsId}&includeDigits=${includeDigits}&page=${page}`
    );
}

function retrieveResults(page) {
    fetch("search/results?" + buildURLParameters(page))
        .then(response => response.text())
        .then(text => showInResults(text));
        scrollToAnchor("results-header")
}

function scrollToAnchor(id) {
    // Get the height of the topbar, since that takes up space in the frame
    const header = document.querySelector('#topbar');
    const headerOffset = header ? header.offsetHeight : 0;

    // Sometimes the scrolling started before all the rendering was complete, resulting in scrolling to the wrong
    // position. requestAnimationFrame didn't work, so a small timeout is used instead to wait for the rendering
    // to complete.
    setTimeout(() => {
        const el = document.getElementById(id);
        if (el) {
            // Calculate the position where the top of the Anchor should be
            const elementPosition = el.offsetTop;
            const offsetPosition = elementPosition - headerOffset;

            window.scrollTo({
                top: offsetPosition,
                behavior: 'auto' // Instant scroll — no animation
            });
        }
    }, 30);
}

function getCategoryData(category, page) {
    switchMode("view-category");
    showLoaderForResults();
    fetch(`categories/${category}?` + buildURLParameters(page))
        .then(response => response.text())
        .then(text => showInResults(text));
    scrollToAnchor("category-header");
}

function getArticleData(category, label, source) {
    switchMode("view-article", source);
    returnToPage = source;
    showLoaderForResults();

    fetch(`categories/${category}/articles/${label}`)
        .then(response => response.text())
        .then(text => showInResults(text));
}

function goBackFromArticle() {
    if (returnToPage === "category") {
        switchMode("view-category");
    } else if (returnToPage === "results") {
        switchMode("view-results");
    }
}

function openModal(modalName) {
    let modal = document.getElementById(modalName);
    modal.style.display = "block";
    // When the user clicks anywhere outside the modal, close it
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
    // Get the parent element, which is the accordion-meta-data div
    let parentElement = element.parentElement;
    parentElement.classList.toggle("active");
    let button = parentElement.getElementsByClassName("toggle-meta")[0];
    let content = parentElement.getElementsByClassName("toggle-content")[0];

    if (parentElement.classList.contains("active")) {
        content.style.display = "block";
        button.innerHTML = "\uFE3F";
    } else {
        content.style.display = "none";
        button.innerHTML = "\uFE40";
    }
}

/**
 * Toggle the headers of the photo upload and text form field and the clickability
 * of the photo selector depending on whether the mode is INPUT.
 * The headers are set up using different h1 tags in html to facilitate the use of Flask-babel.
 */
function toggleSearchHeaders() {
    let imageSelectorWrapper = document.getElementById("image-selector-wrapper");

    if (mode === Modes.INPUT) {
        displayBlock("text-header");
        displayBlock("photo-header");

        hide("text-header-searched");
        hide("photo-header-searched");

        imageSelectorWrapper.classList.add("clickable");
    } else {
        displayBlock("text-header-searched");
        displayBlock("photo-header-searched");
        hide("text-header");
        hide("photo-header");

        imageSelectorWrapper.classList.remove("clickable");
    }

    if (selectedImage == null) {
        displayInline("photo-preview-text");
    } else {
        hide("photo-preview-text");
    }
}

/**
 * Ensure that the entered text is kept when adjusting the search, so the user
 * doesn't have to retype their search.
 */
function toggleSearchInput() {
    let text = document.getElementById("text").value;

    if (text) {
        document.getElementById("input-text-preview").textContent = text;
        hide("input-text-preview-empty");
        displayBlock("input-text-preview");
    } else {
        hide("input-text-preview");
        displayBlock("input-text-preview-empty");
    }

    if (mode === mode.INPUT && text) {
        printInputLength();
    }
}

function addEventHandlersIndexPage() {
    document.getElementById("image-selector-wrapper").addEventListener("click",
        event => handleImageSelectorWrapperClick(event));
    document.getElementById("image-selector-wrapper").addEventListener("drop", fileDropHandler);
    document.getElementById("image-selector-wrapper").addEventListener("dragover", fileDragOverHandler);
    document.addEventListener('keydown', function (event) {
        // On escape key, find the open modals and close them if their display is set to "block"
        if (event.key === 'Escape') {
            const modals = document.querySelectorAll(".modal");
            modals.forEach(modal => {
                if (modal.style.display === "block") {
                    closeModal(modal.id);
                }
            });
        }
        // On Enter key, act as the new results button is clicked and retrieve the results
        if (event.key === 'Enter'){
            onNewResultsButtonClicked();
        }
    });

    let acc = document.getElementsByClassName("accordion-index-page");
    for (let i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function () {
            /* Toggle between adding and removing the "active" class,
            to highlight the button that controls the panel */
            this.classList.toggle("active");

            /* Toggle between hiding and showing the active panel */
            let panel = this.nextElementSibling;
            if (panel.style.display === "block") {
                panel.style.display = "none";
            } else {
                panel.style.display = "block";
            }
        });
    }
}

function handleImageSelectorWrapperClick(e) {
    if (e.target.classList.contains("clickable-info")) {
        openModal("image-selector-modal");
        return;
    }
    if (mode === Modes.INPUT) {
        document.getElementById("image-selector").click();
    }
}

function fileDragOverHandler(e) {
    // Prevent default behavior (Prevent file from being opened)
    e.preventDefault();
}

function fileDropHandler(e) {
    // Prevent default behavior (Prevent file from being opened)
    e.preventDefault();

    if (mode === Modes.INPUT) {
        const droppedFiles = e.dataTransfer.files;
        if (droppedFiles.length === 0) return;

        selectedImage = droppedFiles[0];

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
}

