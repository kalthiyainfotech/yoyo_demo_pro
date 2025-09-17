document.addEventListener("DOMContentLoaded", () => {
    console.log("Switch_Acc.js loaded");
    
    // dropdown open/close
    const profileBtn = document.getElementById("profile-button");
    const dropdown = document.getElementById("profile-dropdown");
    
    console.log("Profile button found:", !!profileBtn);
    console.log("Profile dropdown found:", !!dropdown);
    
    if (profileBtn && dropdown) {
      console.log("Setting up profile dropdown functionality");
      profileBtn.addEventListener("click", (e) => {
        console.log("Profile button clicked");
        dropdown.classList.toggle("hidden");
      });
      // optional: click outside to close
      document.addEventListener("click", (e) => {
        if (!profileBtn.contains(e.target) && !dropdown.contains(e.target)) {
          dropdown.classList.add("hidden");
        }
      });
    }
  
    // show/hide other accounts
    const toggleBtn = document.getElementById("toggleAccountsBtn");
    const accountList = document.getElementById("accountList");
    const toggleText = document.getElementById("toggleText");
    const iconExpand = document.getElementById("iconExpand");
    
    console.log("Toggle button found:", !!toggleBtn);
    console.log("Account list found:", !!accountList);
    console.log("Toggle text found:", !!toggleText);
    console.log("Icon expand found:", !!iconExpand);
  
    if (toggleBtn && accountList) {
      console.log("Setting up account toggle functionality");
      toggleBtn.addEventListener("click", () => {
        console.log("Toggle button clicked");
        accountList.classList.toggle("hidden");
        if (accountList.classList.contains("hidden")) {
          toggleText.textContent = "Show more accounts";
          iconExpand.classList.remove("rotate-180");
        } else {
          toggleText.textContent = "Show fewer accounts";
          iconExpand.classList.add("rotate-180");
        }
      });
    } else {
      console.log("Missing required elements for account toggle");
    }
  });