let studentAnswers = {
  major: null,
  max_budget: null,
  region: null,
  learning_style: null,
  career_goal: null,
  campus_type: null,
  social_scene: null,
  priority_major: 5,
  priority_cost: 5,
  priority_region: 5,
  diploma_type: null,
};

function saveMajor() {
  const major = document.getElementById("student-major").value.trim();

  if (!major) {
    alert("Please tell us what you want to study before continuing.");
    return;
  }

  studentAnswers.major = major;
  showStep(2);
}

function saveBudget() {
  const budget = document.getElementById("student-budget").value;

  if (!budget) {
    alert("Please enter a monthly budget before continuing.");
    return;
  }

  studentAnswers.max_budget = budget;
  showStep(3);
}

function saveRegion() {
  const region = document.getElementById("student-region").value.trim();
  studentAnswers.region = region;
  showStep(4);
}

function selectLearningStyle(value) {
  studentAnswers.learning_style = value;
  showStep(5);
}

function selectCareerGoal(value) {
  studentAnswers.career_goal = value;
  showStep(6);
}

function selectCampusType(value) {
  studentAnswers.campus_type = value;
  showStep(7);
}

function selectSocialScene(value) {
  studentAnswers.social_scene = value;
  showStep(8);
}

function savePriorities() {
  studentAnswers.priority_major = document.getElementById("priority-major-slider").value;
  studentAnswers.priority_cost = document.getElementById("priority-cost-slider").value;
  studentAnswers.priority_region = document.getElementById("priority-region-slider").value;
  showStep(9);
}

function selectDiplomaType(value) {
  studentAnswers.diploma_type = value;
  findMatches();
}

function findMatches() {
  fetch("/api/find-universities", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(studentAnswers)
  })
    .then(response => response.json())
    .then(data => {
      console.log("Matches:", data.results);
      console.log("Purchasing power context:", data.purchasing_power);
      renderPurchasingPower(data.purchasing_power);
      renderResults(data.results);
      showStep(10);
    })
    .catch(error => {
      console.error("Error finding matches:", error);
      alert("Something went wrong. Check the console.");
    });
}

function renderPurchasingPower(pp) {
  const container = document.getElementById("purchasing-power-info");

  if (!pp) {
    container.classList.add("hidden");
    return;
  }

  container.innerHTML = `
    <h3>Living in ${pp.country}</h3>
    <p>General cost-of-living context — same for all results shown, since this covers the whole country, not individual cities.</p>
    <div class="pp-grid">
      <div class="pp-stat"><div class="pp-value">${pp.cost_index}/100</div><div class="pp-label">Overall affordability</div></div>
      <div class="pp-stat"><div class="pp-value">$${pp.monthly_estimate_usd}</div><div class="pp-label">Avg. monthly cost</div></div>
      <div class="pp-stat"><div class="pp-value">${pp.grocery_index}/100</div><div class="pp-label">Grocery affordability</div></div>
      <div class="pp-stat"><div class="pp-value">${pp.transport_index}/100</div><div class="pp-label">Transport affordability</div></div>
    </div>
    <p class="pp-source">Source: ${pp.source}. Higher scores = more affordable.</p>
  `;
  container.classList.remove("hidden");
}

let lastViewedProgram = null;

function renderResults(results) {
  const container = document.getElementById("results-container");
  container.innerHTML = "";

  if (results.length === 0) {
    container.innerHTML = "<p>No programs in the database yet. Add universities and programs via the admin panel first.</p>";
    return;
  }

  results.forEach((r, index) => {
    const card = document.createElement("div");
    card.className = "result-card";

    const totalCost = (r.cost_of_living_monthly || 0) + (r.rent_estimate_monthly || 0);
    const numerusLabel = r.numerus_fixus === "yes" ? "Numerus fixus (restricted enrollment)"
      : r.numerus_fixus === "no" ? "Open enrollment" : "Numerus fixus status unknown";

    card.innerHTML = `
      <h3>${index + 1}. ${r.program_name} — ${r.university_name} (${r.city || "Unknown city"})</h3>
      <p><strong>Match Score:</strong> ${r.score}/100</p>
      <p><strong>Estimated monthly cost:</strong> €${totalCost.toFixed(0)}</p>
      <p><strong>Application deadline:</strong> ${r.application_deadline || "Not specified — check website"}</p>
      <p><strong>${numerusLabel}</strong></p>
      ${r.prerequisites ? `<p><strong>Prerequisites:</strong> ${r.prerequisites}</p>` : ""}
      <ul>
        ${r.reasons.map(reason => `<li>${reason}</li>`).join("")}
      </ul>
      ${r.website_url ? `<a href="${r.website_url}" target="_blank">Visit official website</a>` : ""}
    `;

    if (index === 0) {
      lastViewedProgram = `${r.program_name} — ${r.university_name}`;
    }

    container.appendChild(card);
  });

  document.getElementById("next-steps").classList.remove("hidden");
}

function openConsultationForm() {
  document.getElementById("consultation-form").classList.remove("hidden");

  if (window.currentUser && window.currentUser.isAuthenticated) {
    document.getElementById("lead-name").value = window.currentUser.name;
    document.getElementById("lead-email").value = window.currentUser.email;
  }
}

function submitConsultationInterest() {
  const name = document.getElementById("lead-name").value.trim();
  const email = document.getElementById("lead-email").value.trim();
  const message = document.getElementById("lead-message").value.trim();

  if (!name || !email) {
    alert("Please enter your name and email before sending.");
    return;
  }

  const resultDiv = document.getElementById("consultation-form-result");
  resultDiv.innerHTML = "<p>Sending your request…</p>";
  resultDiv.classList.remove("hidden");

  fetch("/api/consultation-interest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: name,
      email: email,
      message: message,
      program_interest: lastViewedProgram || studentAnswers.major
    })
  })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        resultDiv.innerHTML = `<p>${data.error}</p>`;
        return;
      }
      resultDiv.innerHTML = "<p>Thanks! We'll be in touch soon to set up your free 30-minute consultation.</p>";
    })
    .catch(error => {
      console.error("Error submitting consultation interest:", error);
      resultDiv.innerHTML = "<p>Something went wrong. Please try again.</p>";
    });
}

function saveMyResults() {
  if (!window.currentUser || !window.currentUser.isAuthenticated) {
    if (confirm("Please log in or sign up to save your results. Go to the login page now?")) {
      window.location.href = "/login";
    }
    return;
  }

  fetch("/api/save-answers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(studentAnswers)
  })
    .then(response => response.json())
    .then(data => {
      alert("Your results have been saved to your account!");
    })
    .catch(error => {
      console.error("Error saving answers:", error);
      alert("Something went wrong saving your results.");
    });
}

function evaluateLetter() {
  const letterText = document.getElementById("letter-text").value.trim();

  if (!letterText) {
    alert("Please paste your motivation letter draft first.");
    return;
  }

  const resultDiv = document.getElementById("letter-feedback-result");
  resultDiv.innerHTML = "<p>Analyzing your letter…</p>";
  resultDiv.classList.remove("hidden");

  fetch("/api/evaluate-letter", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ letter_text: letterText })
  })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        resultDiv.innerHTML = `<p>${data.error}</p>`;
        return;
      }
      resultDiv.innerHTML = `<h4>Feedback</h4><p>${data.feedback.replace(/\n/g, "<br>")}</p>`;
    })
    .catch(error => {
      console.error("Error evaluating letter:", error);
      resultDiv.innerHTML = "<p>Something went wrong. Check the console.</p>";
    });
}

function startOver() {
  studentAnswers = {
    major: null,
    max_budget: null,
    region: null,
    learning_style: null,
    career_goal: null,
    campus_type: null,
    social_scene: null,
    priority_major: 5,
    priority_cost: 5,
    priority_region: 5,
    diploma_type: null,
  };
  lastViewedProgram = null;

  document.getElementById("student-major").value = "";
  document.getElementById("student-budget").value = "";
  document.getElementById("student-region").value = "";

  document.getElementById("priority-major-slider").value = 5;
  document.getElementById("priority-cost-slider").value = 5;
  document.getElementById("priority-region-slider").value = 5;
  document.getElementById("major-slider-value").textContent = "5";
  document.getElementById("cost-slider-value").textContent = "5";
  document.getElementById("region-slider-value").textContent = "5";

  document.getElementById("results-container").innerHTML = "";
  document.getElementById("next-steps").classList.add("hidden");
  document.getElementById("purchasing-power-info").classList.add("hidden");

  document.getElementById("letter-text").value = "";
  document.getElementById("letter-feedback-result").classList.add("hidden");
  document.getElementById("letter-feedback-result").innerHTML = "";

  document.getElementById("consultation-form").classList.add("hidden");
  document.getElementById("lead-name").value = "";
  document.getElementById("lead-email").value = "";
  document.getElementById("lead-message").value = "";
  document.getElementById("consultation-form-result").classList.add("hidden");
  document.getElementById("consultation-form-result").innerHTML = "";

  showStep(1);
}

function showStep(stepNumber) {
  document.querySelectorAll(".wizard-step").forEach(el => el.classList.add("hidden"));
  document.getElementById(`step-${stepNumber}`).classList.remove("hidden");
}