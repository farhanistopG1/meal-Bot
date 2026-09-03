const mealSets = {
    veg: [
        "Paneer Butter Masala",
        "Paneer Biryani",
        "Palak Paneer",
        "Shahi Paneer",
        "Dal Tadka",
        "Dal Fry",
        "Rajma Rice",
        "Chole Bhature",
        "Chole Rice",
        "Veg Biryani",
        "Veg Pulao",
        "Jeera Rice",
        "Curd Rice",
        "Sambar Rice",
        "Masala Dosa",
        "Idli Sambar",
        "Masala Vada",
        "Pav Bhaji",
        "Aloo Paratha",
        "Gobi Paratha",
        "Veg Fried Rice",
        "Veg Noodles",
        "Khichdi",
        "Kadhi Rice",
        "Matar Paneer",
        "Mixed Veg Curry",
        "Vegetable Korma",
        "Dahi Puri",
        "Pani Puri",
        "Vada Pav"
    ],

    non_veg: [
        "Chicken Biryani",
        "Mutton Biryani",
        "Chicken Thali",
        "Mutton Thali",
        "Haleem",
        "Butter Chicken",
        "Chicken Curry",
        "Chicken 65",
        "Chicken Kebab",
        "Chicken Tikka",
        "Chicken Fried Rice",
        "Chicken Noodles",
        "Mutton Curry",
        "Mutton Kebab",
        "Mutton Fry",
        "Keema",
        "Fish Curry",
        "Fish Fry",
        "Fish Biryani",
        "Prawn Curry",
        "Prawn Fry",
        "Egg Curry",
        "Egg Biryani",
        "Egg Fried Rice",
        "Omelette",
        "Pepper Chicken",
        "Chicken Korma",
        "Chicken Pulao",
        "Mutton Pulao",
        "Chicken 65 Biryani"
    ]
};


let selectedFoodType = "veg";
const selectedMeals = new Set();

const mealGrid = document.getElementById("mealGrid");
const mealCounter = document.getElementById("mealCounter");

const proteinButtons = document.querySelectorAll(
    "#proteinOptions button"
);

const spiceButtons = document.querySelectorAll(
    "#spiceOptions button"
);

const submitButton = document.getElementById("submitButton");
const result = document.getElementById("result");

const urlParams = new URLSearchParams(window.location.search);

const chatId = urlParams.get("chat_id");
const telegramUserId = urlParams.get("telegram_user_id");
const isHost = urlParams.get("mode") === "host";


function renderMeals() {
    mealGrid.innerHTML = "";

    mealSets[selectedFoodType].forEach(meal => {
        const button = document.createElement("button");

        button.type = "button";
        button.className = "meal-card";
        button.textContent = meal;

        if (selectedMeals.has(meal)) {
            button.classList.add("selected");
        }

        button.addEventListener("click", () => {

            if (selectedMeals.has(meal)) {
                selectedMeals.delete(meal);
                button.classList.remove("selected");
            } else {

                if (selectedMeals.size >= 5) {
                    return;
                }

                selectedMeals.add(meal);
                button.classList.add("selected");
            }

            updateCounter();
        });

        mealGrid.appendChild(button);
    });
}


function updateCounter() {
    mealCounter.textContent =
        `${selectedMeals.size}/5 selected`;
}


function setupFoodTypeToggle() {

    const toggleContainer = document.createElement("div");

    toggleContainer.className = "food-toggle";

    toggleContainer.innerHTML = `
        <button type="button" data-type="veg">
            🥬 Vegetarian
        </button>

        <button type="button" data-type="non_veg">
            🍗 Non-vegetarian
        </button>
    `;

    mealGrid.parentElement.insertBefore(
        toggleContainer,
        mealGrid
    );

    const buttons =
        toggleContainer.querySelectorAll("button");

    buttons.forEach(button => {

        if (button.dataset.type === selectedFoodType) {
            button.classList.add("selected");
        }

        button.addEventListener("click", () => {

            selectedFoodType =
                button.dataset.type;

            buttons.forEach(item =>
                item.classList.remove("selected")
            );

            button.classList.add("selected");

            /*
             * Changing the food category resets the meal
             * selection so the final five meals all belong
             * to the selected category.
             */
            selectedMeals.clear();

            updateCounter();
            renderMeals();
        });
    });
}


function setupOptionButtons(buttons) {

    buttons.forEach(button => {

        button.addEventListener("click", () => {

            buttons.forEach(item =>
                item.classList.remove("selected")
            );

            button.classList.add("selected");
        });
    });
}


function getSelectedValue(buttons) {

    const selected =
        [...buttons].find(
            button =>
                button.classList.contains("selected")
        );

    return selected
        ? selected.dataset.value
        : null;
}


if (isHost) {
    document.getElementById("residentName").closest("section").style.display = "none";
    document.getElementById("residentNumber").closest("section").style.display = "none";

    document.querySelector(".header h1").textContent =
        "Configure your meal preferences";

    document.querySelector(".header p").textContent =
        "You are already the Home host. Tell MealBot what you like to eat.";

    submitButton.textContent = "Save Meal Preferences";
}

setupFoodTypeToggle();

renderMeals();

updateCounter();

setupOptionButtons(proteinButtons);

setupOptionButtons(spiceButtons);


submitButton.addEventListener("click", async () => {

    const residentName =
        document
            .getElementById("residentName")
            .value
            .trim();

    const residentNumber =
        document
            .getElementById("residentNumber")
            .value
            .trim();

    const proteinPreference =
        getSelectedValue(proteinButtons);

    const spicePreference =
        getSelectedValue(spiceButtons);


    if (!chatId || !telegramUserId) {

        result.textContent =
            "This onboarding link is missing Telegram context.";

        return;
    }


    if (!isHost && (!residentName || !residentNumber)) {

        result.textContent =
            "Please enter your name and phone number.";

        return;
    }


    if (selectedMeals.size !== 5) {

        result.textContent =
            "Please choose exactly 5 favourite meals.";

        return;
    }


    if (!proteinPreference) {

        result.textContent =
            "Please choose your protein preference.";

        return;
    }


    if (!spicePreference) {

        result.textContent =
            "Please choose your spice preference.";

        return;
    }


    submitButton.disabled = true;
    submitButton.textContent = "Setting up...";


    const payload = {

        chat_id: Number(chatId),

        telegram_user_id:
            Number(telegramUserId),

        mode:
            isHost ? "host" : "resident",

        resident_name:
            residentName,

        resident_number:
            residentNumber,

        fav_meals:
            [...selectedMeals],

        protein_preference:
            proteinPreference,

        spice_preference:
            spicePreference
    };


    try {

        const response = await fetch(
            "https://meal-bot.duckdns.org/api/v1/residents/telegram-onboarding",
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body:
                    JSON.stringify(payload)
            }
        );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Onboarding failed."
            );
        }


        result.textContent =
            `You're all set, ${data.resident_name}! 🎉`;

        submitButton.textContent =
            "MealBot Ready";


    } catch (error) {

        console.error(error);

        result.textContent =
            error.message ||
            "Something went wrong.";

        submitButton.disabled = false;

        submitButton.textContent =
            "Join MealBot";
    }
});
