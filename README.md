# Stroop Behavioral Experiment Web Application

A minimal, scientifically grounded computerized **Stroop Color-Word Interference Task** implemented in Python, Flask, and JavaScript, paired with an offline statistical data cleaning and analysis pipeline.

---

## 1. What the Project Does

This project provides an end-to-end behavioral psychology testing environment. It allows a participant to:
1. Register or sign in with an anonymous Participant ID.
2. Review clear task instructions and color-key mappings.
3. Complete a 10-trial practice phase with immediate accuracy feedback.
4. Complete a 100-trial experimental phase measuring high-resolution reaction times.
5. Review immediate, calculated behavioral feedback (accuracy, mean RT, median RT, variability, and Stroop interference).
6. Store granular trial-by-trial data for offline statistical analysis (`analysis/analyze.py`).

---

## 2. What the Stroop Task Measures Conceptually

The Stroop task (Stroop, 1935) assesses **selective attention**, **cognitive flexibility**, and **inhibitory control** (the executive ability to suppress an automated prepotent response in favor of a task-relevant target).

In literate humans, reading written words is an overlearned, automatic cognitive process. Naming ink colors requires deliberate, controlled processing. When the word name and the ink color conflict (e.g., the word `RED` presented in green ink), the automated reading process interferes with color naming, increasing response latency and error probability.

---

## 3. Experimental Design

- **Stimulus Domain**: 4 colors — **Red**, **Blue**, **Green**, **Yellow**.
- **Response Modality**: Direct keyboard keys:
  - `R` → Red
  - `B` → Blue
  - `G` → Green
  - `Y` → Yellow
- **Trial Conditions**:
  - **Congruent**: The word meaning matches the ink color (e.g., `RED` in red).
  - **Incongruent**: The word meaning conflicts with the ink color (e.g., `RED` in blue).
- **Trial Balancing**: 50% congruent and 50% incongruent trials, presented in a randomized order to prevent expectation bias or sequential order confounds.

---

## 4. Trial Structure

Each trial proceeds through the following temporal stages:
1. **Fixation Cross (`+`)**: Displayed for 500 ms at the center of the display to orient gaze.
2. **Stimulus Presentation**: The stimulus word appears in its assigned font color.
3. **Timer Initiation**: Reaction time clock starts immediately upon stimulus presentation.
4. **Participant Response**: The participant presses `R`, `B`, `G`, or `Y`.
5. **Data Capture**: Reaction time (ms) and response accuracy are recorded.
6. **Inter-Trial Interval (ITI)**: 300 ms pause before the next fixation cross.
7. **Practice Feedback**: In the 10-trial practice phase, immediate feedback (`CORRECT` or `INCORRECT`) is displayed for 800 ms. No feedback is shown during experimental trials.

---

## 5. High-Precision Reaction Time Measurement

Reaction times are measured in the browser using the high-resolution timestamp API:
```javascript
// At the moment of stimulus rendering:
trialStartTime = performance.now();

// Upon participant keypress:
const reactionTimeMs = performance.now() - trialStartTime;
```
### Why Browser-Side Timing?
Network latency, HTTP handshake delays, and server queuing introduce dozens to hundreds of milliseconds of jitter. Measuring `performance.now()` directly in the client runtime isolates the behavioral latency to the millisecond scale without network confounding.

---

## 6. Data Collected

Each trial records the following parameters:
- `participant_id`: Unique identifier for the subject.
- `session_id`: Unique test session foreign key.
- `trial_number`: Ordinal position in the sequence (1 to 100).
- `stimulus_word`: The lexical word presented (`RED`, `BLUE`, etc.).
- `ink_color`: The color font rendered (`red`, `blue`, etc.).
- `congruent`: Boolean (`true` if word matches ink color; `false` otherwise).
- `response`: The color key selected by the participant.
- `correct`: Boolean indicating whether response matched ink color.
- `reaction_time_ms`: Milliseconds elapsed from stimulus render to keypress.
- `created_at`: UTC timestamp of trial completion.

---

## 7. Database Structure

The application persists data in SQLite (`data/psychometrics.db`) using SQLAlchemy models:
- **`User`**: Participant demographics (username, age, gender, role, participant ID).
- **`TestSession`**: Session header recording total trials, summary metrics, test configuration parameters, start and completion timestamps.
- **`TestTrial`**: Granular trial records containing stimulus JSON, response JSON, reaction time, correctness, and session foreign key.

---

## 8. How to Run the Application

### 1. Requirements
Ensure Python 3.10+ is installed:
```powershell
pip install -r requirements.txt
pip install pandas matplotlib
```

### 2. Start the Server
Run either launcher command:
```powershell
python run.py
```
or
```powershell
python app.py
```
Open your browser to: **http://127.0.0.1:5000/**

---

## 9. How to Run the Analysis

An offline data processing script extracts trial data from the SQLite database, applies data-cleaning rules, and outputs summary statistics and a visualization:
```powershell
python analysis/analyze.py
```

### Data Cleaning Protocol:
- **Accuracy Calculation**: Calculated across all experimental trials.
- **Reaction Time Calculation**: Calculated strictly on **correct** trials (standard psychometric convention).
- **Anticipation Outlier Exclusion**: Reaction times `< 200 ms` are flagged and excluded as motor anticipation rather than cognitive discrimination.
- **Lapse Outlier Exclusion**: Reaction times `> 2,500 ms` are flagged and excluded as attentional lapses or task interruptions.
- **Plot Generation**: Saves a publication-quality comparison chart to `analysis/stroop_effect.png`.

---

## 10. Understanding the Stroop Effect

The **Stroop Effect** (in milliseconds) is calculated as:
$$\text{Stroop Effect} = \text{Mean RT}_{\text{Incongruent}} - \text{Mean RT}_{\text{Congruent}}$$

- A **positive value** indicates that incongruent stimuli induced cognitive interference, requiring additional processing time to inhibit word reading and select the ink color.
- A **larger interference value** signifies greater vulnerability to interference under the test conditions.

---

## 11. Limitations of this Implementation

1. **Consumer Hardware Latency**: Browser rendering engines and consumer keyboards introduce minor input polling delays (typically 10–30 ms) compared to dedicated lab millisecond hardware (e.g., photo-diode calibrated response boxes).
2. **Visual Environment**: Lighting, monitor refresh rate, viewing distance, and screen calibration vary across participant screens.
3. **Practice Effects**: Repeated participation on the same day can reduce interference due to motor learning.

---

## What This Project Does NOT Measure

> **IMPORTANT NOTICE: EDUCATIONAL TOOL ONLY**
> 
> This web application is designed strictly for **educational demonstrations and behavioral research modeling**.
> 
> - **It does NOT provide clinical diagnosis.**
> - **It does NOT measure intelligence, IQ, brain health, or mental capability.**
> - **It is NOT a diagnostic instrument for Attention Deficit Hyperactivity Disorder (ADHD), Obsessive-Compulsive Disorder (OCD), depression, dementia, or any neuropsychological disorder.**
> - Performance on this test can be influenced by transient factors such as sleep deprivation, caffeine intake, screen glare, stress, keyboard familiarity, or temporary distraction.
> - Do not use this application or its results for medical, clinical, or diagnostic self-evaluation. Consult a licensed neuropsychologist or healthcare provider for clinical assessments.
