const homeName = document.getElementById("homeName");
const residentName = document.getElementById("residentName");
const residentNumber = document.getElementById("residentNumber");
const cookName = document.getElementById("cookName");
const cookNumber = document.getElementById("cookNumber");
const createHomeButton = document.getElementById("createHomeButton");
const result = document.getElementById("result");

createHomeButton.addEventListener("click", function () {
    const homeData = {
        home_name: homeName.value,
        resident_name: residentName.value,
        resident_number: residentNumber.value,
        cook_name: cookName.value,
        cook_number: cookNumber.value
    };
    console.log(homeData);
    fetch("https://meal-bot.duckdns.org/api/v1/homes", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(homeData)
    })
    .then(response => response.json())
    .then(data =>{
        result.textContent = "Home Created successfully: "+ data.home_name;
    });
});




