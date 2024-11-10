// Non-static display value
updateAuthButtonMessage();

// Image slideshow

// Image indexing dots
const dot1 = document.querySelector("#dot1");
const dot2 = document.querySelector("#dot2");
const dot3 = document.querySelector("#dot3");

let slideIndex = 2;

showSlidesAuto(); // Automatically change the slide

// Next image
function plusSlides(n) {
  showSlides((slideIndex += n));
}

// Previous image
function currentSlide(n) {
  showSlides((slideIndex = n));
}

// Manual slide control
function showSlides(n) {
  let i;
  let slides = document.getElementsByClassName("slides");
  let dots = document.getElementsByClassName("dot");

  if (n > slides.length) slideIndex = 1;
  if (n < 1) slideIndex = slides.length;

  for (i = 0; i < slides.length; i++) slides[i].style.display = "none";
  for (i = 0; i < dots.length; i++)
    dots[i].className = dots[i].className.replace(" active", "");

  slides[slideIndex - 1].style.display = "block";
  dots[slideIndex - 1].className += " active";
}

// Automatic slide control
function showSlidesAuto() {
  let i = slideIndex;
  let slides = document.getElementsByClassName("slides");

  for (i = 0; i < slides.length; i++) slides[i].style.display = "none";

  slideIndex++;

  if (slideIndex > slides.length) slideIndex = 1;

  slides[slideIndex - 1].style.display = "block";

  dotsCurrentState(slideIndex);
  setTimeout(showSlidesAuto, 5000); // Change the image every 5.000 seconds
}

// Image indexing dots' behavior
function dotsCurrentState(index) {
  switch (index - 1) {
    case 0:
      dot1.classList.add("active");
      dot2.classList.remove("active");
      dot3.classList.remove("active");
      break;
    case 1:
      dot1.classList.remove("active");
      dot2.classList.add("active");
      dot3.classList.remove("active");
      break;
    case 2:
      dot1.classList.remove("active");
      dot2.classList.remove("active");
      dot3.classList.add("active");
      break;
    default:
      dot1.classList.remove("active");
      dot2.classList.remove("active");
      dot3.classList.remove("active");
  }
}

// Authentication widget
let logout;
const wrapper = document.querySelector(".wrapper");
const loginLink = document.querySelector(".login-link");
const registerLink = document.querySelector(".register-link");
const btnPopup = document.querySelector(".btnLogin-popup");
const iconClose = document.querySelector(".icon-close");

// Display the auth page if user tries to use services without logging in
if (sessionStorage.getItem("isLogin") === "false")
  wrapper.classList.add("active-popup");

// active-popup: login/registration form visible
// active: registration form

registerLink.addEventListener("click", () => {
  wrapper.classList.add("active");
});

loginLink.addEventListener("click", () => {
  wrapper.classList.remove("active");
});

btnPopup.addEventListener("click", () => {
  if (
    localStorage.getItem("isAuth") == "true" ||
    sessionStorage.getItem("isAuth") == "true"
  ) {
    logout = window.prompt("Do you wish to logout (y/n): ");
    logout = logout.toLowerCase();

    if (logout === "y") {
      localStorage.clear();
      sessionStorage.clear();
      window.location.assign("../index.html");
    } else console.log("The user does not wish to logout.");
  } else {
    wrapper.classList.add("active-popup");
  }
});

iconClose.addEventListener("click", () => {
  sessionStorage.removeItem("isLogin");
  wrapper.classList.remove("active-popup");
  setTimeout(() => {
    wrapper.classList.remove("active");
  }, 300);
});

let usernameInput, emailInput, passwordInput;
let usernameInputLength, emailInputLength, passwordInputLength;

// Test
/*
console.log("Username:", usernameInput);
console.log("Password:", passwordInput);
console.log("Email:", emailInput);
*/

let currentUser;

const warningLoginMessage = document.getElementById("warningLogin");
const warningRegisterMessage = document.getElementById("warningRegister");
const rememberMe = document.getElementById("rememberMe");
const agreeToTerms = document.getElementById("agreeToTerms");

login.onclick = function () {
  // Evaluate checkbox status
  if (rememberMe.checked) console.log("The data is stored.");
  else console.log("The data will be forgotten.");

  // Scope the input
  const loginForm = document.querySelector(".form-box.login");

  // Get email and password
  usernameInput = loginForm.querySelector('input[type="username"]').value;
  passwordInput = loginForm.querySelector('input[type="password"]').value;

  // Check the validity of the input
  usernameInputLength = Number(usernameInput.length);
  passwordInputLength = Number(passwordInput.length);

  checkLogin(usernameInputLength, passwordInputLength);

  // Test
  /*
  console.log(`Username: ${usernameInput}`);
  console.log(`Password: ${passwordInput}`);
  */

  // Create a user instance
  currentUser = new User(usernameInput, passwordInput, null);
  // logUser(currentUser);

  // Authenticate with the server.
  console.log(authentication(currentUser));
  // warningLoginMessage.textContent = authentication(currentUser);
};

register.onclick = function () {
  // Evaluate checkbox status
  if (agreeToTerms.checked)
    console.log("The user has agreed to the terms and conditions.");
  else {
    console.log("The user does not accept the terms and conditions.");

    return 0;
  }

  // Scope the input
  const registerForm = document.querySelector(".form-box.register");

  // Get username and password
  usernameInput = registerForm.querySelector('input[type="username"]').value;
  emailInput = registerForm.querySelector('input[type="email"]').value;
  passwordInput = registerForm.querySelector('input[type="password"]').value;

  // Check the validity of the input
  usernameInputLength = Number(usernameInput.length);
  passwordInputLength = Number(passwordInput.length);
  emailInputLength = Number(emailInput.length);

  checkRegistration(usernameInputLength, emailInputLength, passwordInputLength);

  // Test
  /*
  console.log(`Username: ${usernameInput}`);
  console.log(`Email: ${emailInput}`);
  console.log(`Password: ${passwordInput}`);
  */

  // Create a user instance
  currentUser = new User(usernameInput, passwordInput, emailInput);
  // logUser(currentUser);

  registerUser(currentUser);
};

function logUser(user) {
  console.log(currentUser.username);
  console.log(currentUser.email);
  console.log(currentUser.password);
}

// Check login information conditions
function checkLogin(usernameInputLength, passwordInputLength) {
  if (usernameInputLength >= 3 && usernameInputLength <= 12) {
    if (passwordInputLength >= 8 && passwordInputLength <= 20) {
      warningLoginMessage.textContent = null;
    } else if (passwordInputLength >= 20)
      warningLoginMessage.textContent =
        "Password must be no longer than 20 letters.";
    else
      warningLoginMessage.textContent =
        "Password must be atleast 8 letters long.";
  } else if (usernameInputLength >= 12)
    warningLoginMessage.textContent =
      "Username must be no longer than 12 letters.";
  else
    warningLoginMessage.textContent =
      "Username must be atleast 3 letters long.";
}

// Check registration information conditions
function checkRegistration(
  usernameInputLength,
  emailInputLength,
  passwordInputLength
) {
  if (usernameInputLength >= 3 && usernameInputLength <= 12) {
    if (passwordInputLength >= 8 && passwordInputLength <= 20) {
      if (emailInputLength === 0 || !validateEmail(emailInput)) {
        warningRegisterMessage.textContent = "Email is invalid.";
        checkRegistration(usernameInputLength, emailInputLength, passwordInputLength);
      }
      else warningRegisterMessage.textContent = null;
    } else if (passwordInputLength >= 20) {
      warningRegisterMessage.textContent =
        "Password must be no longer than 20 letters.";
        checkRegistration(usernameInputLength, emailInputLength, passwordInputLength);
    }
    else {
      warningRegisterMessage.textContent =
        "Password must be atleast 8 letters long.";
        checkRegistration(usernameInputLength, emailInputLength, passwordInputLength);
    }
  } else if (usernameInputLength >= 12) {
    warningRegisterMessage.textContent =
      "Username must be no longer than 12 letters.";
      checkRegistration(usernameInputLength, emailInputLength, passwordInputLength);
  }
  else {
    warningRegisterMessage.textContent =
      "Username must be atleast 3 letters long.";
      checkRegistration(usernameInputLength, emailInputLength, passwordInputLength);
  }
}

// Backend services
const serverAddress = "http://10.241.68.145:3000/users";

// User authentication
async function authentication(user) {
  const { username, password } = user;

  $.post(
    serverAddress + "/login",
    { username, password },
    function (response, status, xhr) {
      if (xhr.status === 200) {
        if (rememberMe.checked) {
          localStorage.setItem("isAuth", true);
          localStorage.setItem("username", username);
          sessionStorage.removeItem("isLogin");
          updateAuthButtonMessage();
        } else {
          localStorage.setItem("isAuth", false);
          sessionStorage.setItem("isAuth", true);
          sessionStorage.setItem("username", username);
          sessionStorage.removeItem("isLogin");
          updateAuthButtonMessage();
        }

        // Add delay to cover the response time of the server
        /*
        setTimeout(() => {
          window.location.assign("pages/services.html");
        }, 3000);
        */
        window.location.assign("pages/services.html");
      } else return "Login unsuccessful: " + response;
    }
  ).fail(function (xhr) {
    return "Login unsuccessful: " + xhr.responseText;
  });

  return null;
}

// User registration
function registerUser(user) {
  const { username, email, password } = user;

  $.post(
    serverAddress + "/register",
    { username, email, password },
    function (response, status, xhr) {
      if (xhr.status === 201) {
        console.log("Registration successful!");
        localStorage.clear();
        sessionStorage.clear();
        localStorage.setItem("isAuth", false);
        sessionStorage.setItem("isAuth", true);
        sessionStorage.setItem("username", username);
        sessionStorage.removeItem("isLogin");
        updateAuthButtonMessage();
        window.location.assign("/pages/services.html");
      } else {
        warningRegisterMessage.textContent =
          "Registration unsuccessful: " + response;
      }
    }
  ).fail(function (xhr) {
    warningRegisterMessage.textContent =
      "Registration unsuccessful: " + xhr.responseText;
  });
}

// Email validation
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}
