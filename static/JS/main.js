// Poem text
const kiplingPoem = `<p><span>ChatGPA.</span> Unlock your full potential. Your personalized study planner. <span>ChatGPA.</span> Tailor your learning experience with AI-powered insights. <span>ChatGPA.</span> Smart study plans designed just for you. <span>ChatGPA.</span> Optimize your academic success with intelligent recommendations. <span>ChatGPA.</span> Your journey to better grades starts here. <span>ChatGPA.</span> Study smarter, not harder, with AI-driven planning. <span>ChatGPA.</span> Stay ahead with adaptive study schedules. <span>ChatGPA.</span> Personalized learning paths to help you excel. <span>ChatGPA.</span> Your academic companion, ready to assist. <span>ChatGPA.</span> Transform the way you study with customized plans. Loading your personalized study experience... Please wait.</p>`;

// Function to insert poem into divs
function insertPoemIntoDivs() {
	// Get all .text divs
	const textDivs = document.querySelectorAll(".text");

	// Insert poem into all .text divs
	textDivs.forEach((div) => {
		div.innerHTML = kiplingPoem;
	});
}

// Call the function when the DOM is fully loaded
document.addEventListener("DOMContentLoaded", insertPoemIntoDivs);

const contentDiv = document.querySelector(".content");
function adjustContentSize() {
	const viewportWidth = window.innerWidth;
	const baseWidth = 1000;
	const scaleFactor =
		viewportWidth < baseWidth ? (viewportWidth / baseWidth) * 0.8 : 1;
	contentDiv.style.transform = `scale(${scaleFactor})`;
}
window.addEventListener("load", adjustContentSize);
window.addEventListener("resize", adjustContentSize);

function loadPage() {
    // Change button text to 'Loading...' and hide the button
    const button = document.querySelector('.custom-btn');
    const buttonSpan = document.querySelector('.button-span');
    
    buttonSpan.textContent = "Loading...";
    button.style.pointerEvents = "none"; // Disable button click
    button.style.opacity = 0.5; // Make button semi-transparent

    // Wait for a manual delay (e.g., 5 seconds) before redirecting
    setTimeout(() => {
      window.location.href = "http://localhost:5000/dashboard"; // Redirect to next page
    }, 10000); // Adjust the timer as needed
  }