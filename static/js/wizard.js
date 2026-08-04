let studentAnswers = {
  major: null,
  max_budget: null,
  region: null,
  learning_style: null,
  career_goal: null,
  campus_type: null,
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
      showStep(8);
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

    container.appendChild(card);
  });

  document.getElementById("next-steps").classList.remove("hidden");
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
  // Reset the answers object
  studentAnswers = {
    major: null,
    max_budget: null,
    region: null,
    learning_style: null,
    career_goal: null,
    campus_type: null,
    diploma_type: null,
  };

  // Clear old text left in the input fields
  document.getElementById("student-major").value = "";
  document.getElementById("student-budget").value = "";
  document.getElementById("student-region").value = "";

  // Clear old results and letter feedback so nothing lingers
  document.getElementById("results-container").innerHTML = "";
  document.getElementById("next-steps").classList.add("hidden");
  document.getElementById("purchasing-power-info").classList.add("hidden");
  document.getElementById("letter-text").value = "";
  document.getElementById("letter-feedback-result").classList.add("hidden");
  document.getElementById("letter-feedback-result").innerHTML = "";

  showStep(1);
}

function showStep(stepNumber) {
  document.querySelectorAll(".wizard-step").forEach(el => el.classList.add("hidden"));
  document.getElementById(`step-${stepNumber}`).classList.remove("hidden");
}