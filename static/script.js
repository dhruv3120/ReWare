function sendDatareg() {

    event.preventDefault();

    let username = document.getElementById('Name').value;
    let useremail = document.getElementById('Email').value;
    let userpassword = document.getElementById('Password').value;
    let usersubmit = document.getElementById('Submit').value;
    let ipassword = document.getElementById('Ipassword').value;

    if (userpassword == ipassword) {
        document.getElementById("Email").classList.remove("incorrect");
        document.getElementById("Name").classList.remove("incorrect");
        document.getElementById("Password").classList.remove("incorrect");
        fetch('/catch', {
        method: 'POST',
        body: JSON.stringify({ name: username, email: useremail, password: userpassword, submit: usersubmit, ipassword: document.getElementById('Ipassword').value }),
        headers: {
            'Content-Type': 'application/json'
        }
        
        })
         .then(res => res.json())
        .then(data => {
            console.log("Server said:", data);
            if (data.status === "success") {
                // Redirect to login page if registration was successful
                window.location.href = "/";
            } else {
                document.getElementById("Email").classList.add("incorrect");
                document.getElementById("Name").classList.add("incorrect");
                document.getElementById("Password").classList.add("incorrect");
                
            }
        })
        .catch(error => {
            console.error("Fetch error:", error);
            document.getElementById("output").innerText = "Something went wrong. Try again!";
        });
    } else {
        document.getElementById("Email").classList.add("incorrect");
        document.getElementById("Name").classList.add("incorrect");
        document.getElementById("Password").classList.add("incorrect");
    }

}

