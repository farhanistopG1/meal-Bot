homeName.addEventListener("input", function () {
    console.log(homeName.value);
});

what this does is that addEventListener("input", function () {
    console.log(homeName.value)
}); -----> this means that for homeName we are adding a even that listen to every input which the user puts into that field and consoles its value and gives its last value at the end 
so it can be pretty annoying as it will record every detail and word which the user enters inside the box so we are creating a button at the end which is configured to when clicked it will give me what the user has written into the box

and we can configure things around it 

const createHomeButton = document.getelementbyID("createHomeButton")

createHomeButton.addEventListener("click", fucntion () {
    console.log(honeName.value);
});

now what it means that make the button alive and make it work when there is any value written in the box 

