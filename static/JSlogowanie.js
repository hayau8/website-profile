function addAlert(message) {
  const container = document.getElementById("notifications-container");
  const notification = document.createElement("div");
  notification.className = "alert alert-info text-center notification";
  notification.textContent = message;
  container.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 6000);
}
document.addEventListener("DOMContentLoaded", () => {
  message = "{{msg}}";
  console.log("ROWEREK");
  addAlert(message);
});
