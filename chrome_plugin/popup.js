const loader = document.querySelector("#loading");
const regenerateButton = document.querySelector("#regenerateButton");
var pageContent = ""
var pageUrl = ""
var chatHistory = []
//const rootUrlProd = "http://35.231.223.7:8001/api/v1"
const rootUrl = "http://35.231.223.7:8001/api/v1"

// showing loading
function displayLoading() {
    loader.classList.add("display");
    // to stop loading after some time
    setTimeout(() => {
        loader.classList.remove("display");
    }, 500000);
}

// hiding loading
function hideLoading() {
    loader.classList.remove("display");
}

// showing button
function displayReGenerateButton() {
    regenerateButton.style.visibility = 'visible';
}

// hiding the button
function hideReGenerateButton() {
    regenerateButton.style.visibility = 'hidden';
}

const chatbotToggler = document.querySelector(".chatbot-toggler");
const closeBtn = document.querySelector(".close-btn");
const chatbox = document.querySelector(".chatbox");
const chatInput = document.querySelector(".chat-input textarea");
const sendChatBtn = document.querySelector(".chat-input span");

let userMessage = null; // Variable to store user's message
const API_KEY = "ls8rkzbh2qtudjn94k4b42os1pparh"; // Paste your API key here
const inputInitHeight = chatInput.scrollHeight;

const createChatLi = (message, className) => {
    // Create a chat <li> element with passed message and className
    const chatLi = document.createElement("li");
    chatLi.classList.add("chat", `${className}`);
    let chatContent = className === "outgoing" ? `<p></p>` : `<span class="material-symbols-outlined">smart_toy</span><p></p>`;
    chatLi.innerHTML = chatContent;
    chatLi.querySelector("p").textContent = message;
    return chatLi; // return chat <li> element
}

const generateResponse = (chatElement) => {
    const API_URL = rootUrl+"/generateAnswer";
    const messageElement = chatElement.querySelector("p");

    // Define the properties and message for the API request
    const requestOptions = {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": `${API_KEY}`
        },
        body: JSON.stringify({
            question_text: userMessage,
            page_url: pageUrl,
            chat_history: chatHistory,
        })
    }

    // Send POST request to API, get response and set the reponse as paragraph text
    fetch(API_URL, requestOptions).then(res => res.json()).then(data => {
        messageElement.textContent = data.response.trim();
        chatHistory.push([userMessage, data.response.trim()])
    }).catch((error) => {
        console.error("generateResponse failed error: " + error)
        messageElement.classList.add("error");
        messageElement.textContent = "Oops! Something went wrong. Please try again.";
    }).finally(() => chatbox.scrollTo(0, chatbox.scrollHeight));
}

const generateSummaryHelper = () => {
    summaryElement = document.getElementById('summaryResponse')
    setTimeout(() => {
        // Display "Thinking..." message while waiting for the response
        displayLoading()
        generateIndex(pageContent, pageUrl)
        generateSummary(pageContent, pageUrl, summaryElement, false)
    }, 600);
}

const reGenerateSummaryHelper = () => {
    summaryElement = document.getElementById('summaryResponse')
    setTimeout(() => {
        // Display "Thinking..." message while waiting for the response
        displayLoading()
        generateSummary(pageContent, pageUrl, summaryElement, true)
    }, 600);
}

const generateIndex = (pageContent, pageUrl) => {
    const API_URL = rootUrl+"/generateIndex";
    // Define the properties and message for the API request
    const requestOptions = {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": `${API_KEY}`
        },
        body: JSON.stringify({
            page_content: pageContent,
            page_url: pageUrl,
        })
    }
    // Send POST request to API, get response and set the response as paragraph text
    fetch(API_URL, requestOptions).then(res => res.json()).then(data => {
       console.log("Index generation successful: ", data.response.trim())
    }).catch((error) => {
        console.error("Index generation failed: " + error)
    })
}

const generateSummary = (pageContent, pageUrl, summaryElement, isRegenerate) => {
    hideReGenerateButton()
    summaryElement.textContent = "Generating Summary..."
    const API_URL = rootUrl+"/generateSummary";

    // Define the properties and message for the API request
    const requestOptions = {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "x-api-key": `${API_KEY}`
        },
        body: JSON.stringify({
            page_content: pageContent,
            page_url: pageUrl,
            is_regenerate: isRegenerate,
        })
    }

    // Send POST request to API, get response and set the response as paragraph text
    fetch(API_URL, requestOptions).then(res => res.json()).then(data => {
        hideLoading()
        summaryElement.textContent = data.response.trim();
        displayReGenerateButton()
    }).catch((error) => {
        hideLoading()
        console.error("generateSummary failed error: " + error)
        summaryElement.textContent = "Oops! Something went wrong. Please try again.";
        displayReGenerateButton()
    })
}

const handleChat = () => {
    userMessage = chatInput.value.trim(); // Get user entered message and remove extra whitespace
    if(!userMessage) return;

    // Clear the input textarea and set its height to default
    chatInput.value = "";
    chatInput.style.height = `${inputInitHeight}px`;

    // Append the user's message to the chatbox
    chatbox.appendChild(createChatLi(userMessage, "outgoing"));
    chatbox.scrollTo(0, chatbox.scrollHeight);

    setTimeout(() => {
        // Display "Thinking..." message while waiting for the response
        const incomingChatLi = createChatLi("Thinking...", "incoming");
        chatbox.appendChild(incomingChatLi);
        chatbox.scrollTo(0, chatbox.scrollHeight);
        generateResponse(incomingChatLi);
    }, 600);
}

chatInput.addEventListener("input", () => {
    // Adjust the height of the input textarea based on its content
    chatInput.style.height = `${inputInitHeight}px`;
    chatInput.style.height = `${chatInput.scrollHeight}px`;
});

chatInput.addEventListener("keydown", (e) => {
    // If Enter key is pressed without Shift key and the window
    // width is greater than 800px, handle the chat
    if(e.key === "Enter" && !e.shiftKey && window.innerWidth > 800) {
        e.preventDefault();
        handleChat();
    }
});

// Inject the payload.js script into the current tab after the popout has loaded
window.addEventListener('load', function (evt) {
	chrome.extension.getBackgroundPage().chrome.tabs.executeScript(null, {
		file: 'payload.js'
	});;
});

// Listen to messages from the payload.js script and write to popout.html
chrome.runtime.onMessage.addListener(function (message, pageUrlMessage) {
    pageContent = message.pageContent
    pageUrl = message.pageUrl
    generateSummaryHelper()
});

sendChatBtn.addEventListener("click", handleChat);
closeBtn.addEventListener("click", () => document.body.classList.remove("show-chatbot"));
chatbotToggler.addEventListener("click", () => document.body.classList.toggle("show-chatbot"));
regenerateButton.addEventListener("click", reGenerateSummaryHelper);