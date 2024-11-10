// Is the user logged in?
const isAuthLocal = localStorage.getItem("isAuth");
const isAuthSession = sessionStorage.getItem("isAuth");

isAuth(isAuthLocal, isAuthSession);

// Non-static display value
updateAuthButtonMessage();

// Logout
let logout;
const btnPopup = document.querySelector(".btnLogin-popup");

wishLogout(logout, btnPopup);

