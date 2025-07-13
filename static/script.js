// Simple JS to toggle forms
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const dashboard = document.getElementById("dashboard");

document.getElementById("show-register").addEventListener("click", e => {
  e.preventDefault();
  loginForm.style.display = "none";
  registerForm.style.display = "flex";
});

document.getElementById("show-login").addEventListener("click", e => {
  e.preventDefault();
  registerForm.style.display = "none";
  loginForm.style.display = "flex";
});

// These buttons would connect to app logic
document.getElementById("btn-logout").addEventListener("click", async () => {
  try {
    await fetch('/api/logout', { method: 'POST' });
    dashboard.style.display = "none";
    loginForm.style.display = "flex";
    document.getElementById("login-email").value = "";
    document.getElementById("login-password").value = "";
    // Hide all content sections when logging out
    document.querySelectorAll('.browse-frame, .team-container').forEach(section => {
      section.style.display = 'none';
    });
  } catch (error) {
    console.error('Logout error:', error);
  }
});

document.getElementById("btn-browse").addEventListener("click", () => {
  // Hide team content and show browse content
  document.getElementById('team-content').style.display = 'none';
  document.getElementById('browse-content').style.display = 'block';
  loadCategories();
});

document.getElementById("btn-profile").addEventListener("click", async () => {
  try {
    // Hide team content and show browse content for profile
    document.getElementById('team-content').style.display = 'none';
    document.getElementById('browse-content').style.display = 'block';
    
    const response = await fetch('/api/user');
    const userData = await response.json();
    
    const swapsResponse = await fetch('/api/swaps');
    const swapsData = await swapsResponse.json();
    
    const browseContent = document.getElementById("browse-content");
    browseContent.innerHTML = `
      <h2>Your Profile</h2>
      
      <div class="profile-section">
        <h3>Account Information</h3>
        <div class="profile-info">
          <div class="info-item">
            <div class="info-label">Name</div>
            <div class="info-value">${userData.fullName || 'N/A'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Email</div>
            <div class="info-value">${userData.email || 'N/A'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Total Points</div>
            <div class="info-value">${userData.points || 0} pts</div>
          </div>
          <div class="info-item">
            <div class="info-label">Items Swapped</div>
            <div class="info-value">${swapsData.length || 0} items</div>
          </div>
        </div>
      </div>

      <div class="profile-section">
        <h3>Recent Swaps</h3>
        <div class="items-grid">
          ${swapsData.length > 0 ? swapsData.slice(0, 5).map(swap => `
            <div class="item-card">
              <div class="item-header">
                <div class="item-name">${swap.itemName}</div>
                <div class="item-points">Swapped</div>
              </div>
              <p style="color: var(--text-secondary); font-size: 14px;">${new Date(swap.swapDate).toLocaleDateString()}</p>
            </div>
          `).join('') : '<p>No swaps yet! Start browsing items to make your first swap.</p>'}
        </div>
      </div>
    `;
  } catch (error) {
    console.error('Profile error:', error);
  }
});

document.getElementById("btn-upload").addEventListener("click", () => {
  // Hide team content and show browse content for upload
  document.getElementById('team-content').style.display = 'none';
  document.getElementById('browse-content').style.display = 'block';
  
  const browseContent = document.getElementById("browse-content");
  browseContent.innerHTML = `
    <h2>Upload New Item</h2>
    
    <div class="upload-form">
      <h3>Item Details</h3>
      <div class="form-grid">
        <div class="input-group">
          <input id="upload-name" class="input-field" placeholder="Item Name" />
        </div>
        <div class="input-group">
          <input id="upload-category" class="input-field" placeholder="Category" />
        </div>
        <div class="input-group">
          <input id="upload-condition" class="input-field" placeholder="Condition (New/Good/Fair)" />
        </div>
        <div class="input-group">
          <input id="upload-size" class="input-field" placeholder="Size" />
        </div>
      </div>
      <div class="input-group">
        <input id="upload-imgurl" class="input-field" placeholder="Image URL" style="width: 100%;" />
      </div>
      <div class="input-group">
        <textarea id="upload-description" class="input-field" placeholder="Description..." style="width: 100%; height: 80px; resize: vertical;"></textarea>
      </div>
      <button id="upload-submit" class="btn-primary" style="width: 200px;">Upload Item</button>
    </div>
  `;
  
  document.getElementById("upload-submit").addEventListener("click", async () => {
    const name = document.getElementById("upload-name").value.trim();
    const category = document.getElementById("upload-category").value.trim();
    const imageUrl = document.getElementById("upload-imgurl").value.trim();
    
    if (!name || !category || !imageUrl) {
      alert("Please fill in the item name, category, and image URL");
      return;
    }
    
    try {
      const response = await fetch('/api/upload_item', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: name,
          category: category,
          imageUrl: imageUrl
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        alert(`Item "${name}" uploaded successfully! 🎉`);
        loadCategories();
      } else {
        alert(`Error: ${data.error}`);
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload item. Please try again.');
    }
  });
});

// NEW: Team page functionality
document.getElementById("btn-team").addEventListener("click", () => {
  // Hide browse content and show team content
  document.getElementById('browse-content').style.display = 'none';
  document.getElementById('team-content').style.display = 'block';
  
  // Update active button state
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  document.getElementById('btn-team').classList.add('active');
});

async function loadCategories() {
  try {
    const response = await fetch('/api/categories');
    const categorizedItems = await response.json();
    
    const browseContent = document.getElementById("browse-content");
    browseContent.innerHTML = "<h2>Browse Categories</h2>";
    
    const categoriesGrid = document.createElement("div");
    categoriesGrid.className = "categories-grid";
    
    for(let category in categorizedItems) {
      const categoryCard = document.createElement("div");
      categoryCard.className = "category-card";
      categoryCard.onclick = () => loadItems(category, categorizedItems);
      
      categoryCard.innerHTML = `
        <h3>${category}</h3>
        <p>${categorizedItems[category].length} items available</p>
      `;
      
      categoriesGrid.appendChild(categoryCard);
    }
    
    browseContent.appendChild(categoriesGrid);
  } catch (error) {
    console.error('Categories error:', error);
  }
}

function loadItems(category, categorizedItems) {
  const browseContent = document.getElementById("browse-content");
  browseContent.innerHTML = `
    <button class="back-btn" onclick="loadCategories()">← Back to Categories</button>
    <h2>${category}</h2>
  `;

  const itemsGrid = document.createElement("div");
  itemsGrid.className = "items-grid";

  categorizedItems[category].forEach(item => {
    const itemCard = document.createElement("div");
    itemCard.className = "item-card";

    itemCard.innerHTML = `
      <div class="item-header">
        <div>
          <div class="item-name">${item.name}</div>
          <p style="color: var(--text-secondary); font-size: 14px; margin-top: 4px;">Available for swap</p>
        </div>
        <div class="item-points">+${item.points} pts</div>
      </div>
      <button class="swap-btn" onclick="handleSwap('${item.name}', ${item.points})">Swap Now</button>
    `;

    itemsGrid.appendChild(itemCard);
  });
  
  browseContent.appendChild(itemsGrid);
}

function handleSwap(itemName, points) {
  const phone = prompt("Enter your phone number:");
  const address = prompt("Enter your address:");
  const pincode = prompt("Enter your pincode:");
  
  if (!phone || !address || !pincode) {
    alert("All fields are required for swap!");
    return;
  }
  
  fetch('/api/swap', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      itemName: itemName,
      itemPoints: points,
      phone: phone,
      address: address,
      pincode: pincode
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.message) {
      alert(data.message);
      updatePointsDisplay();
    } else {
      alert('Swap failed: ' + data.error);
    }
  })
  .catch(error => {
    console.error('Swap error:', error);
    alert('Failed to process swap. Please try again.');
  });
}

async function updatePointsDisplay() {
  try {
    const response = await fetch('/api/user');
    const userData = await response.json();
    document.getElementById("points-display").textContent = `Points: ${userData.points || 0}`;
  } catch (error) {
    console.error('Points update error:', error);
  }
}

// Show login by default
loginForm.style.display = "flex";
registerForm.style.display = "none";
dashboard.style.display = "none";

// Login functionality
document.getElementById("login-btn").addEventListener("click", async () => {
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value.trim();
  
  if (!email || !password) {
    alert("Please enter both email and password");
    return;
  }
  
  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email,
        password: password
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      loginForm.style.display = "none";
      dashboard.style.display = "flex";
      document.getElementById("points-display").textContent = `Points: ${data.points || 0}`;
      loadCategories();
    } else {
      alert(`Login failed: ${data.error}`);
    }
  } catch (error) {
    console.error('Login error:', error);
    alert('Login failed. Please try again.');
  }
});

// Registration functionality
function sendDatareg() {
  event.preventDefault();

  let username = document.getElementById('reg-name').value.trim();
  let useremail = document.getElementById('reg-email').value.trim();
  let userpassword = document.getElementById('reg-password').value.trim();
  let confirmPassword = document.getElementById('reg-confirm').value.trim();

  if (!username || !useremail || !userpassword || !confirmPassword) {
    alert("Please fill in all fields");
    return;
  }

  if (userpassword !== confirmPassword) {
    alert("Passwords don't match!");
    return;
  }

  fetch('/catch', {
    method: 'POST',
    body: JSON.stringify({ 
      name: username, 
      email: useremail, 
      password: userpassword, 
      submit: 'register' 
    }),
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(res => res.json())
  .then(data => {
    console.log("Server said:", data);
    if (data.status === "success") {
      alert("Registration successful! Please login.");
      registerForm.style.display = "none";
      loginForm.style.display = "flex";
      // Clear forms
      document.getElementById('reg-name').value = '';
      document.getElementById('reg-email').value = '';
      document.getElementById('reg-password').value = '';
      document.getElementById('reg-confirm').value = '';
    } else {
      alert(`Registration failed: ${data.message}`);
    }
  })
  .catch(error => {
    console.error("Fetch error:", error);
    alert("Something went wrong. Try again!");
  });
}
// Enhanced team page functionality
document.getElementById("btn-team").addEventListener("click", () => {
  // Hide browse content and show team content
  document.getElementById('browse-content').style.display = 'none';
  document.getElementById('team-content').style.display = 'block';
  
  // Create particles effect
  createTeamParticles();
  
  // Update active button state
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  document.getElementById('btn-team').classList.add('active');
});

// Create floating particles for team page
function createTeamParticles() {
  const particles = document.querySelector('.particles');
  if (!particles) return;
  
  // Clear existing particles
  particles.innerHTML = '';
  
  for (let i = 0; i < 50; i++) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    particle.style.left = Math.random() * 100 + '%';
    particle.style.top = Math.random() * 100 + '%';
    particle.style.animationDelay = Math.random() * 6 + 's';
    particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
    particles.appendChild(particle);
  }
}
