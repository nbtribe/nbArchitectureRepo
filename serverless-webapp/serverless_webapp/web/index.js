const counter = document.querySelector(".counter-number");
async function updateCounter() {
    let response = await fetch("$LAMBDA_FUNCTION_URL");
    let data = await response.json();
    counter.innerHTML = `Serverless WebApp has ${data} views`;
}
updateCounter();