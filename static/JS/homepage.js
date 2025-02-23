
async function login() {
    var formData = new FormData();
    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;

    if (!username || !password) {
    alert("Please enter both username and password.");
    return;
    }

    // Prepare data to be sent in the request
    formData.append('username', username);
    formData.append('password', password);

    // Use fetch API to send POST request
    fetch('/login', {
        method: 'POST',
        body: formData,
    })

}

    function logout() {
    window.location.href = "http://localhost:5000/logout";
}