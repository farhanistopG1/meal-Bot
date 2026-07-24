Domain Lifecycle

Home is active
↓
Residents have saved MealPreferences
↓
Daily poll time arrives
↓
Create one DailyMealPoll for tomorrow
↓
Prepare poll options
↓
Poll becomes Open
↓
Residents submit votes
↓
Poll closes
↓
Count valid votes
↓
Choose winning meal
↓
Create MealPlan
↓
Tomorrow’s meal decision is complete


HomeMenu
= all meals the Home could consider

DailyMealPoll
= only three meals being considered today

MealPlan
= the one meal selected for tomorrowwh

# Business Objects

1. HomeMenu 
HomeMenu is the Home’s shared food catalogue.
It answers one question:
“What meals are available to offer this Home?”
It is born by combining active residents’ D2 meal preferences.
Resident 1 favourites
+
Resident 2 favourites
+
Resident 3 favourites
↓
HomeMenu

It can:
- Combine valid favourite meals from active residents.
- Remove duplicate meal names.
- Count how popular each meal is.
- Expose all available meals.
- Rank meals by popularity.
- Recommend the top three poll choices.


What HomeMenu cannot do
HomeMenu must not:
- Ask the database for Residents or preferences.
- Send a WhatsApp message.
- Open a DailyMealPoll.
- Accept a resident vote.
- Decide the winning meal.
- Create a MealPlan.
- Tell the Cook what to make.
- Change any Resident’s D2 MealPreference.
- Know HTTP, FastAPI, scheduling, or time of day.

HomeMenu BirthStory :
D3 workflow begins
↓
Find active Home
↓
Find active Residents
↓
Find their D2 MealPreferences
↓
Give those preferences to HomeMenu
↓
HomeMenu normalizes, merges, and counts meals
↓
HomeMenu is born
2. DailyMealPoll

The central object of D3.

It represents one meal decision for one Home on one future date.

It owns:

Home.
Meal date.
Poll options.
Poll status: open or closed.
Opening time.
Closing time.
Votes submitted for that poll.

It can:

Accept a vote.
Reject an invalid or duplicate vote.
Close itself.
Determine its winning option after it is closed.
It does not send any messages.

3. MealVote

A persistent fact:

This resident selected this meal for this poll.

It owns:
The resident.
The poll it belongs to.
The selected meal.
The time of the vote.
It is not a MealPreference.

MealPreference:
“What do I generally like?”

MealVote:
“What do I want tomorrow?”

4. MealPlan

The final decision.

It represents:
This Home will cook this meal on this date.

It owns:
Home.
Cook.
Meal date.
Winning meal.
Vote count.
The poll from which the decision came.
A MealPlan can only exist after its poll is closed.

