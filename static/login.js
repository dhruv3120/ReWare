function sendLogin(event) {
    event.preventDefault();

    let email = document.getElementById('Email-log').value;
    let password = document.getElementById('Pass-log').value;

    // Simple field validation
    if (email.trim() === "" || password.trim() === "") {
        document.getElementById("Email-log").classList.add("incorrect");
        document.getElementById("Pass-log").classList.add("incorrect");
        document.getElementById("output").innerText = "Fields cannot be empty!";
        return;
    }

    // Clear previous errors
    document.getElementById("Email-log").classList.remove("incorrect");
    document.getElementById("Pass-log").classList.remove("incorrect");

    fetch('/login', {
        method: 'POST',
        body: JSON.stringify({ email: email, password: password }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => {
        console.log("Server said:", data);
        if (data.status === "success") {
            window.location.href = "/index";
        } else {
            document.getElementById("output").innerText = data.message || "Invalid credentials.";
            document.getElementById("Email-log").classList.add("incorrect");
            document.getElementById("Pass-log").classList.add("incorrect");
        }
    })
    .catch(error => {
        console.error("Fetch error:", error);
        document.getElementById("output").innerText = data.message || "Invalid credentials.";
        document.getElementById("Email-log").classList.add("incorrect");
        document.getElementById("Pass-log").classList.add("incorrect");
        
    });
}
