document.addEventListener('DOMContentLoaded', () => {
  const startBtn = document.getElementById('start-test');
  const profileLink = document.getElementById('profile-link');
  const progressText = document.getElementById('progress');
  const stimulusEl = document.getElementById('stimulus');
  const resultBox = document.getElementById('result-box');
  const choiceButtons = document.querySelectorAll('.choice');
  const choiceGrid = document.getElementById('choice-grid');

  const COLORS = ['red', 'blue', 'green', 'yellow'];
  const COLOR_MAP = {
    'r': 'red',
    'b': 'blue',
    'g': 'green',
    'y': 'yellow'
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
    'red': '#ef4444',
    'blue': '#3b82f6',
    'green': '#22c55e',
    'yellow': '#eab308'
  };

  // Start the test sequence
  startBtn.addEventListener('click', () => {
    if (isRunning) return;
    startBtn.classList.add('hidden');
    choiceGrid.classList.remove('opacity-40', 'pointer-events-none');
    isRunning = true;
    isPractice = true;
    currentTrialIndex = 0;
    practiceData = [];
    experimentalData = [];
    generateTrials();
    runNextTrial();
  });

  // Handle choice button clicks (if they prefer mouse or on mobile/fallback)
  choiceButtons.forEach(button => {
    button.addEventListener('click', () => {
      if (!canRespond) return;
      const selectedColor = button.getAttribute('data-color');
      handleResponse(selectedColor);
    });
  });

  // Handle keyboard responses
  document.addEventListener('keydown', (event) => {
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
        const otherColors = COLORS.filter(c => c !== word);
        color = otherColors[Math.floor(Math.random() * otherColors.length)];
      }

      trials.push({
        word: word.toUpperCase(),
        color: color,
        congruent: word === color
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
    progressText.innerText = `${isPractice ? 'Practice' : 'Test'} Trial ${currentTrialIndex + 1} of ${totalTrials}`;

    // Show fixation cross
    stimulusEl.innerText = '+';
    stimulusEl.style.color = '#73777f'; // Neutral outline color
    
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
      correct: isCorrect
    };

    if (isPractice) {
      practiceData.push(trialRecord);
      // Practice feedback
      stimulusEl.innerText = isCorrect ? 'CORRECT' : 'INCORRECT';
      stimulusEl.style.color = isCorrect ? '#22c55e' : '#ef4444';
      
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
    progressText.innerText = 'Practice complete';
    stimulusEl.innerText = 'READY TO BEGIN?';
    stimulusEl.style.color = 'var(--color-primary)';
    
    startBtn.innerText = 'Begin Test';
    startBtn.classList.remove('hidden');
    choiceGrid.classList.add('opacity-40', 'pointer-events-none');
    
    // Set up transition to experimental phase
    isRunning = false;
    
    // We override click to start the real experiment next
    const startRealExperiment = () => {
      startBtn.removeEventListener('click', startRealExperiment);
      startBtn.classList.add('hidden');
      choiceGrid.classList.remove('opacity-40', 'pointer-events-none');
      isRunning = true;
      isPractice = false;
      currentTrialIndex = 0;
      generateTrials();
      runNextTrial();
    };
    
    startBtn.addEventListener('click', startRealExperiment);
  }

  function endExperimentalPhase() {
    progressText.innerText = 'Test complete';
    stimulusEl.innerText = 'SAVING RESULTS...';
    stimulusEl.style.color = 'var(--color-primary)';
    choiceGrid.classList.add('opacity-40', 'pointer-events-none');
    
    // Calculate metrics
    const correctTrials = experimentalData.filter(d => d.correct);
    const accuracy = (correctTrials.length / experimentalData.length) * 100;
    
    // Mean RT of correct trials
    const meanRt = correctTrials.reduce((sum, d) => sum + d.rt, 0) / (correctTrials.length || 1);

    // Save to server
    fetch('/test/stroop/result', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        accuracy: accuracy,
        mean_rt: meanRt,
        total_trials: experimentalData.length
      })
    })
    .then(response => response.json())
    .then(data => {
      if (data.saved) {
        stimulusEl.innerText = 'COMPLETED';
        stimulusEl.style.color = '#22c55e';
        
        // Show summary inside result box
        const congruentTrials = experimentalData.filter(d => d.congruent);
        const incongruentTrials = experimentalData.filter(d => !d.congruent);
        
        const congCorrect = congruentTrials.filter(d => d.correct);
        const incongCorrect = incongruentTrials.filter(d => d.correct);
        
        const congMeanRt = congCorrect.reduce((sum, d) => sum + d.rt, 0) / (congCorrect.length || 1);
        const incongMeanRt = incongCorrect.reduce((sum, d) => sum + d.rt, 0) / (incongCorrect.length || 1);
        
        const stroopEffect = incongMeanRt - congMeanRt;
        
        resultBox.innerHTML = `
          <h3 class="text-xl font-bold mb-4 text-center">Your Results</h3>
          <div class="grid grid-cols-3 gap-4 mb-4 text-center">
            <div class="p-3 bg-surface-container-low rounded-lg">
              <span class="block text-sm text-outline mb-1">Accuracy</span>
              <span class="text-2xl font-bold font-data-mono">${accuracy.toFixed(1)}%</span>
            </div>
            <div class="p-3 bg-surface-container-low rounded-lg">
              <span class="block text-sm text-outline mb-1">Mean RT</span>
              <span class="text-2xl font-bold font-data-mono">${meanRt.toFixed(0)} ms</span>
            </div>
            <div class="p-3 bg-surface-container-low rounded-lg">
              <span class="block text-sm text-outline mb-1">Stroop Effect</span>
              <span class="text-2xl font-bold font-data-mono">${stroopEffect.toFixed(0)} ms</span>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4 text-center text-sm border-t border-outline-variant pt-4">
            <div>
              <span class="font-semibold block text-primary mb-1">Congruent Trials</span>
              <p>Mean RT: <span class="font-data-mono">${congMeanRt.toFixed(0)} ms</span></p>
              <p>Accuracy: <span class="font-data-mono">${((congCorrect.length / congruentTrials.length) * 100 || 0).toFixed(1)}%</span></p>
            </div>
            <div>
              <span class="font-semibold block text-secondary mb-1">Incongruent Trials</span>
              <p>Mean RT: <span class="font-data-mono">${incongMeanRt.toFixed(0)} ms</span></p>
              <p>Accuracy: <span class="font-data-mono">${((incongCorrect.length / incongruentTrials.length) * 100 || 0).toFixed(1)}%</span></p>
            </div>
          </div>
          <p class="text-xs text-outline mt-6 text-center leading-relaxed">
            The Stroop effect refers to the increase in response difficulty that can occur when the meaning of a word conflicts with its ink color.
            This is an educational behavioral experiment, not a diagnostic instrument.
          </p>
        `;
        resultBox.classList.remove('hidden');
        profileLink.classList.remove('hidden');
      } else {
        stimulusEl.innerText = 'ERROR SAVING';
        stimulusEl.style.color = '#ef4444';
      }
    })
    .catch(err => {
      console.error(err);
      stimulusEl.innerText = 'NETWORK ERROR';
      stimulusEl.style.color = '#ef4444';
    });
  }
});
