// Check if the user is authorizezd
function isAuth(isAuthLocal, isAuthSession) {
  if (isAuthLocal != "true" && isAuthSession != "true") {
    window.location.assign("../index.html");
    sessionStorage.setItem("isLogin", false);
  }
}

// Non-static display value
function updateAuthButtonMessage() {
  const authBtnMessage = document.getElementById("authBtn");

  if (localStorage.getItem("isAuth") === "true") {
    if (localStorage.getItem("username") != null) {
      authBtnMessage.textContent = localStorage.getItem("username");
    } else {
      console.log("Some values in local storage are missing.");
    }
  } else if (sessionStorage.getItem("isAuth") === "true") {
    if (sessionStorage.getItem("username") != null) {
      authBtnMessage.textContent = sessionStorage.getItem("username");
    } else console.log("Some values in session storage are missing.");
  } else {
    console.log("Unauthorized");
  }
}

// Logout (temporary)
function wishLogout(wantLogout, btnPopup) {
  btnPopup.addEventListener("click", () => {
    wantLogout = window.prompt("Do you wish to logout (y/n): ");
    wantLogout = wantLogout.toLowerCase();

    if (wantLogout === "y") {
      localStorage.clear();
      sessionStorage.clear();
      window.location.assign("../index.html");
    } else console.log("The user does not wish to logout.");
  });
}

class User {
  constructor(username, password, email) {
    this.username = username;
    this.password = password;
    this.email = email;
  }

  set username(newUsername) {
    this._username = newUsername;
  }

  set password(passwordInput) {
    this._password = passwordInput;
  }

  set email(newEmail) {
    this._email = newEmail;
  }

  get username() {
    return this._username;
  }

  get password() {
    return this._password;
  }

  get email() {
    return this._email;
  }
}