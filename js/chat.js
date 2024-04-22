const targetElement = document.getElementById("chat");
let isScrolled = false;

targetElement.addEventListener("scroll", function() {
  let diff = targetElement.scrollHeight - targetElement.clientHeight;
  if(Math.abs(targetElement.scrollTop - diff) <= 10 || diff == 0) {
    isScrolled = false;
  } else {
    isScrolled = true;
    console.log("eventFired");
  }
});

// Create a MutationObserver instance
const observer = new MutationObserver(function(mutations) {
  mutations.forEach(function(mutation) {
    if(!isScrolled) {
      targetElement.scrollTop = targetElement.scrollHeight;
    }
    console.log("observerFired")
  });
});

// Configure the observer to watch for changes in the subtree and attributes
const config = {
  childList: true,
  subtree: true,
  characterData: true,
  attributeOldValue: true,
  characterDataOldValue: true
};

// Start observing the target element
observer.observe(targetElement, config);