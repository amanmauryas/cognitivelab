document.addEventListener("DOMContentLoaded", () => {
  const startBtn = document.getElementById("start-test");
  const profileLink = document.getElementById("profile-link");
  const progressText = document.getElementById("progress");
  const stimulusEl = document.getElementById("stimulus");
  const resultBox = document.getElementById("result-box");
  const choiceButtons = document.querySelectorAll(".choice");
  const choiceGrid = document.getElementById("choice-grid");

  const COLORS = ["red", "blue", "green", "yellow"];
  const COLOR_MAP = {
    r: "red",
    b: "blue",
    g: "green",
    y: "yellow",
  };

  let isRunning = false;
  let isPractice = true;
  let currentTrialIndex = 0;
  let trials = [];
  let trialStartTime = 0;
  let canRespond = false;
  let practiceData = [];
  let experimentalData = [];

  // Color values for styling the text
  const COLOR_HEX = {
    red: "#ef4444",
    blue: "#3b82f6",
    green: "#22c55e",
    yellow: "#eab308",
  };

  // Start the test sequence
  startBtn.addEventListener("click", () => {
    if (isRunning) return;
    startBtn.classList.add("hidden");
    choiceGrid.classList.remove("opacity-40", "pointer-events-none");
    isRunning = true;
    isPractice = true;
    currentTrialIndex = 0;
    practiceData = [];
    experimentalData = [];
    generateTrials();
    runNextTrial();
  });

  // Handle choice button clicks (if they prefer mouse or on mobile/fallback)
  choiceButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (!canRespond) return;
      const selectedColor = button.getAttribute("data-color");
      handleResponse(selectedColor);
    });
  });

  // Handle keyboard responses
  document.addEventListener("keydown", (event) => {
    if (!canRespond) return;
    const key = event.key.toLowerCase();
    if (COLOR_MAP[key]) {
      handleResponse(COLOR_MAP[key]);
    }
  });

  function generateTrials() {
    trials = [];
    const numTrials = isPractice ? 10 : 100;

    // Generate balanced congruent and incongruent trials
    for (let i = 0; i < numTrials; i++) {
      const word = COLORS[Math.floor(Math.random() * COLORS.length)];
      let color;

      // 50% chance of being congruent
      if (Math.random() < 0.5) {
        color = word;
      } else {
        // Pick a different color
        const otherColors = COLORS.filter((c) => c !== word);
        color = otherColors[Math.floor(Math.random() * otherColors.length)];
      }

      trials.push({
        word: word.toUpperCase(),
        color: color,
        congruent: word === color,
      });
    }
  }

  function runNextTrial() {
    canRespond = false;
    const totalTrials = trials.length;

    if (currentTrialIndex >= totalTrials) {
      if (isPractice) {
        endPracticePhase();
      } else {
        endExperimentalPhase();
      }
      return;
    }

    // Update progress
    progressText.innerText = `${isPractice ? "Practice" : "Test"} Trial ${currentTrialIndex + 1} of ${totalTrials}`;

    // Show fixation cross
    stimulusEl.innerText = "+";
    stimulusEl.style.color = "#73777f"; // Neutral outline color

    setTimeout(() => {
      // Show stimulus
      const currentTrial = trials[currentTrialIndex];
      stimulusEl.innerText = currentTrial.word;
      stimulusEl.style.color = COLOR_HEX[currentTrial.color];

      trialStartTime = performance.now();
      canRespond = true;
    }, 500); // 500ms fixation cross
  }

  function handleResponse(selectedColor) {
    const rt = performance.now() - trialStartTime;
    canRespond = false;

    const currentTrial = trials[currentTrialIndex];
    const isCorrect = selectedColor === currentTrial.color;

    const trialRecord = {
      ...currentTrial,
      response: selectedColor,
      rt: rt,
      correct: isCorrect,
    };

    if (isPractice) {
      practiceData.push(trialRecord);
      // Practice feedback
      stimulusEl.innerText = isCorrect ? "CORRECT" : "INCORRECT";
      stimulusEl.style.color = isCorrect ? "#22c55e" : "#ef4444";

      setTimeout(() => {
        currentTrialIndex++;
        runNextTrial();
      }, 800); // Show feedback for 800ms
    } else {
      experimentalData.push(trialRecord);
      currentTrialIndex++;
      setTimeout(() => {
        runNextTrial();
      }, 300); // 300ms inter-trial interval
    }
  }

  function endPracticePhase() {
    progressText.innerText = "Practice complete";
    stimulusEl.innerText = "READY TO BEGIN?";
    stimulusEl.style.color = "var(--color-primary)";

    startBtn.innerText = "Begin Test";
    startBtn.classList.remove("hidden");
    choiceGrid.classList.add("opacity-40", "pointer-events-none");

    // Set up transition to experimental phase
    isRunning = false;

    // We override click to start the real experiment next
    const startRealExperiment = () => {
      startBtn.removeEventListener("click", startRealExperiment);
      startBtn.classList.add("hidden");
      choiceGrid.classList.remove("opacity-40", "pointer-events-none");
      isRunning = true;
      isPractice = false;
      currentTrialIndex = 0;
      generateTrials();
      runNextTrial();
    };

    startBtn.addEventListener("click", startRealExperiment);
  }

  function endExperimentalPhase() {
    progressText.innerText = "Test complete";
    stimulusEl.innerText = "SAVING RESULTS...";
    stimulusEl.style.color = "var(--color-primary)";
    choiceGrid.classList.add("opacity-40", "pointer-events-none");

    // METRICS CALCULATION

    // 1. CORRECT TRIALS
    const correctTrials = experimentalData.filter((d) => d.correct);

    // 2. OVERALL ACCURACY
    const accuracy = (correctTrials.length / experimentalData.length) * 100;

    // 3. RESPONSE TIMES OF CORRECT TRIALS
    const sortedRts = correctTrials.map((d) => d.rt).sort((a, b) => a - b);

    const len = sortedRts.length;

    // 4. MEAN RESPONSE TIME
    const meanRt =
      correctTrials.reduce((sum, d) => sum + d.rt, 0) /
      (correctTrials.length || 1);

    // 5. MEDIAN RESPONSE TIME
    const medianRt =
      len === 0
        ? 0
        : len % 2 !== 0
          ? sortedRts[Math.floor(len / 2)]
          : (sortedRts[len / 2 - 1] + sortedRts[len / 2]) / 2;

    // 6. RESPONSE TIME VARIANCE
    const variance =
      correctTrials.length > 1
        ? correctTrials.reduce(
          (sum, d) => sum + Math.pow(d.rt - meanRt, 2),
          0,
        ) /
        (correctTrials.length - 1)
        : 0;

    // 7. RESPONSE TIME STANDARD DEVIATION
    const stdRt = Math.sqrt(variance);

    // 8. TOTAL CORRECT RESPONSES
    const totalCorrect = correctTrials.length;

    // 9. TOTAL INCORRECT RESPONSES
    const totalIncorrect = experimentalData.length - totalCorrect;

    // 10. ERROR RATE
    const errorRate = 100 - accuracy;

    // CONGRUENT VS INCONGRUENT

    // 11. GET ALL CONGRUENT TRIALS
    const congruentTrials = experimentalData.filter((d) => d.congruent);

    // 12. GET ALL INCONGRUENT TRIALS
    const incongruentTrials = experimentalData.filter((d) => !d.congruent);

    // 13. CORRECT CONGRUENT TRIALS
    const congCorrect = congruentTrials.filter((d) => d.correct);

    // 14. CORRECT INCONGRUENT TRIALS
    const incongCorrect = incongruentTrials.filter((d) => d.correct);

    // 15. CONGRUENT ACCURACY
    const congruentAccuracy =
      congruentTrials.length > 0
        ? (congCorrect.length / congruentTrials.length) * 100
        : 0;

    // 16. INCONGRUENT ACCURACY
    const incongruentAccuracy =
      incongruentTrials.length > 0
        ? (incongCorrect.length / incongruentTrials.length) * 100
        : 0;

    // 17. ACCURACY INTERFERENCE : How much accuracy drops in the incongruent condition
    const accuracyInterference = congruentAccuracy - incongruentAccuracy;

    // MEAN RT BY CONDITION

    // 18. CONGRUENT MEAN RT
    const congMeanRt =
      congCorrect.reduce((sum, d) => sum + d.rt, 0) / (congCorrect.length || 1);

    // 19. INCONGRUENT MEAN RT
    const incongMeanRt =
      incongCorrect.reduce((sum, d) => sum + d.rt, 0) /
      (incongCorrect.length || 1);

    // 20. STROOP EFFECT / RT INTERFERENCE : Positive value means incongruent trials were slower
    const stroopEffect = incongMeanRt - congMeanRt;

    // Save to server
    fetch("/test/stroop/result", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        accuracy: accuracy,
        mean_rt: meanRt,
        median_rt: medianRt,
        std_rt: stdRt,
        error_rate: errorRate,
        congruent_accuracy: congruentAccuracy,
        incongruent_accuracy: incongruentAccuracy,
        congruent_mean_rt: congMeanRt,
        incongruent_mean_rt: incongMeanRt,
        accuracy_interference: accuracyInterference,
        stroop_effect: stroopEffect,
        trials: experimentalData,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.saved) {
          stimulusEl.innerText = "COMPLETED";
          stimulusEl.style.color = "#22c55e";

          resultBox.innerHTML = `
                <h3 class="text-xl font-bold mb-4 text-center">
                  Your Results
                </h3>

                <!-- OVERALL PERFORMANCE -->
                <p class="text-sm font-semibold text-outline mb-2">
                  Overall Performance
                </p>

                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 text-center">
                  <div class="p-3 bg-surface-container-low rounded-lg">
                    <span class="block text-sm text-outline mb-1">
                      Accuracy
                    </span>
                    <span class="text-xl font-bold font-data-mono">
                      ${accuracy.toFixed(1)}%
                    </span>
                  </div>

                  <div class="p-3 bg-surface-container-low rounded-lg">
                    <span class="block text-sm text-outline mb-1">
                      Error Rate
                    </span>
                    <span class="text-xl font-bold font-data-mono">
                      ${errorRate.toFixed(1)}%
                    </span>
                  </div>

                  <div class="p-3 bg-surface-container-low rounded-lg">
                    <span class="block text-sm text-outline mb-1">
                      Correct
                    </span>
                    <span class="text-xl font-bold font-data-mono">
                      ${totalCorrect}
                    </span>
                  </div>

                  <div class="p-3 bg-surface-container-low rounded-lg">
                    <span class="block text-sm text-outline mb-1">
                      Incorrect
                    </span>
                    <span class="text-xl font-bold font-data-mono">
                      ${totalIncorrect}
                    </span>
                  </div>
                </div>

                <!-- RESPONSE TIME -->
                <p class="text-sm font-semibold text-outline mb-2">
                  Response Time
                </p>

                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6 text-center">
                  <div class="p-3 bg-surface-container-low rounded-lg">
                    <span class="block text-sm text-outline mb-1">
                      Mean RT
                    </span>
                    <span class="text-xl font-bold font-data-mono">
                      ${meanRt.toFixed(0)} ms
                    </span>
                  </div>

                  <div class="p-3 bg-surface-container-low rounded-lg">
                    <span class="block text-sm text-outline mb-1">
                      Median RT
                    </span>
                    <span class="text-xl font-bold font-data-mono">
                      ${medianRt.toFixed(0)} ms
                    </span>
                  </div>

                  <div class="p-3 bg-surface-container-low rounded-lg">
                    <span class="block text-sm text-outline mb-1">
                      RT Variability
                    </span>
                    <span class="text-xl font-bold font-data-mono">
                      ${stdRt.toFixed(0)} ms
                    </span>
                  </div>

                  <div class="p-3 bg-surface-container-low rounded-lg">
                    <span class="block text-sm text-outline mb-1">
                      Stroop Effect
                    </span>
                    <span class="text-xl font-bold font-data-mono">
                      ${stroopEffect.toFixed(0)} ms
                    </span>
                  </div>
                </div>

                <!-- CONDITION COMPARISON -->
                <p class="text-sm font-semibold text-outline mb-2">
                  Condition Comparison
                </p>

                <div class="grid grid-cols-2 gap-4 text-center text-sm border-t border-outline-variant pt-4">
                  <div class="p-4 bg-surface-container-low rounded-lg">
                    <span class="font-semibold block text-primary mb-3">
                      Congruent Trials
                    </span>
                    <p class="mb-1">
                      Accuracy:
                      <span class="font-data-mono">
                        ${congruentAccuracy.toFixed(1)}%
                      </span>
                    </p>
                    <p>
                      Mean RT:
                      <span class="font-data-mono">
                        ${congMeanRt.toFixed(0)} ms
                      </span>
                    </p>
                  </div>

                  <div class="p-4 bg-surface-container-low rounded-lg">
                    <span class="font-semibold block text-secondary mb-3">
                      Incongruent Trials
                    </span>
                    <p class="mb-1">
                      Accuracy:
                      <span class="font-data-mono">
                        ${incongruentAccuracy.toFixed(1)}%
                      </span>
                    </p>
                    <p>
                      Mean RT:
                      <span class="font-data-mono">
                        ${incongMeanRt.toFixed(0)} ms
                      </span>
                    </p>
                  </div>
                </div>

                <!-- INTERFERENCE -->
                <div class="mt-4 p-4 bg-surface-container-low rounded-lg text-center">
                  <span class="block text-sm text-outline mb-2">
                    Accuracy Interference
                  </span>
                  <span class="text-xl font-bold font-data-mono">
                    ${accuracyInterference.toFixed(1)}%
                  </span>
                </div>

                <!-- INFORMATION -->
                <p class="text-xs text-outline mt-6 text-center leading-relaxed">
                  Response time metrics are calculated from correct trials.
                  The Stroop effect represents the difference in mean response time
                  between incongruent and congruent trials.
                  This is an educational behavioral experiment, not a diagnostic instrument.
                </p>
              `;
          resultBox.classList.remove("hidden");
          profileLink.classList.remove("hidden");
        } else {
          stimulusEl.innerText = "ERROR SAVING";
          stimulusEl.style.color = "#ef4444";
        }
      })
      .catch((err) => {
        console.error(err);
        stimulusEl.innerText = "NETWORK ERROR";
        stimulusEl.style.color = "#ef4444";
      });
  }
});
