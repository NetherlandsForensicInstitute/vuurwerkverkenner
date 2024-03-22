function toggleVisibilityTextBlock(element) {
    if (textBlockIsVisible(element)) {
        hideTextBlock(element);
    } else {
        hideAllTextBlocks();
        showTextBlock(element);
    }
}

function textBlockIsVisible(element) {
    let textBlock = element.getElementsByClassName("accordion-text-block")[0];
    return textBlock.style.display === "inline";
}

function showTextBlock(element) {
    let textBlock = element.getElementsByClassName("accordion-text-block")[0];
    let button = element.getElementsByClassName("toggle-visibility-btn")[0];
    textBlock.style.display = "inline";
    button.innerText = '\uFE3F';
}

function hideTextBlock(element) {
    let textBlock = element.getElementsByClassName("accordion-text-block")[0];
    let button = element.getElementsByClassName("toggle-visibility-btn")[0];
    textBlock.style.display = "none";
    button.innerText = '\uFE40';
}

function hideAllTextBlocks() {
    let elements = document.getElementsByClassName("hover-table-help");
    for (let e of elements) {
        hideTextBlock(e);
    }
}

function addEventHandlersHelpPage() {
    [...document.getElementsByClassName("hover-table-help")].forEach((element) => {
        element.onclick = (function (e) {
            let node = e.target.nodeName;
            if (node && node.toLowerCase() === 'a') {
                return;
            }
            toggleVisibilityTextBlock(element);
        });
    });
}
