// send the page title as a chrome message
var pageContent = document.documentElement.innerHTML;
var pageUrl = document.URL
chrome.runtime.sendMessage({pageContent: pageContent, pageUrl: pageUrl});