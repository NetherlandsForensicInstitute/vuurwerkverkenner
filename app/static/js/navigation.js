const Modes = Object.freeze({
    INPUT: "input",
    VIEW_RESULTS: "view-all-results",
    VIEW_GROUP: "view-result-group",
    VIEW_ITEM: "view-result-item"
});

var mode = Modes.INPUT;

// Some browsers keep user input, even when location.reload is triggered
function resetInputsAndNavigateHome() {
    resetImageInput();
    resetTextInput();
    location.reload();
}

function showPage(pageId) {
    hideElementsWithClass("content-container");
    displayBlock(pageId);
    showNavigation(pageId);
}

function showNavigation(pageId) {
    hideElementsWithClass("navigation");
    displayBlock(navigationElementForPageAndMode(pageId));
}

function navigationElementForPageAndMode(pageId) {
    return (pageId === "help-page") ? "navigation-help" : (mode === Modes.INPUT ? "navigation-title" : "navigation-results");
}

function loadHelp() {
    fetch("help")
        .then(response => response.text())
        .then(text => showHelp(text));
}

function showHelp(text) {
    document.getElementById("help-page").innerHTML = text;
    addEventHandlersHelpPage();
    showPage("help-page");
    hideAllTextBlocks();
}

function showLoaderForResults() {
    showInResults('<div class="loader"></div>');
}

function showInResults(html) {
    getResultsElement().innerHTML = html;
}

function getResultsElement() {
    switch (mode) {
        case Modes.VIEW_RESULTS:
            return document.getElementById("results");
        case Modes.VIEW_GROUP:
            return document.getElementById("result-group");
        default:
            return document.getElementById("result-item");
    }
}

function switchMode(newMode, optionalSource) {
    mode = newMode;

    hideElementsWithClass("results-container");
    hideElementsWithClass("menu-item");
    hide("image-selector-container");
    hide("text");
    hide("char-counter-text-input");
    hide("new-results-button");

    toggleSearchHeaders();
    toggleSearchInput();

    displayInline("input-text-preview");
    displayBlock("clear-query");

    showNavigation();

    switch (mode) {
        case Modes.VIEW_RESULTS:
            displayBlock("results");
            displayInline("menu-navigate-home");
            displayInline("menu-results");
            break;
        case Modes.VIEW_GROUP:
            displayBlock("result-group");
            displayInline("menu-navigate-home");
            displayInline("menu-navigate-results");
            displayInline("menu-result-group");
            break;
        case Modes.VIEW_ITEM:
            displayBlock("result-item");
            displayInline("menu-navigate-home");
            displayInline("menu-navigate-results");
            if (optionalSource === 'group') {
                displayInline("menu-navigate-result-group");
            }
            displayInline("menu-result-item");
            break;
    }
}

function hideElementsWithClass(className) {
    displayElementsWithClass(className, "none");
}

function displayElementsWithClass(className, display) {
    let elements = document.getElementsByClassName(className);

    for (let i = 0; i < elements.length; i++) {
        elements[i].style.display = display;
    }
}

function hide(id) {
    document.getElementById(id).style.display = "none";
}

function displayBlock(id) {
    document.getElementById(id).style.display = "block";
}

function displayInline(id) {
    document.getElementById(id).style.display = "inline";
}
