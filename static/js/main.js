document.addEventListener("DOMContentLoaded", () => {
    const messages = document.querySelectorAll(".message");

    messages.forEach((message) => {
        window.setTimeout(() => {
            message.classList.add("message-hidden");
        }, 4500);
    });
});
