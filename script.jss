console.log("AI Health Monitoring System Loaded");
setTimeout(function () {
    const messages =
        document.querySelectorAll(".message");
    messages.forEach(function (message) {
        message.style.display = "none";
    });
}, 4000);
