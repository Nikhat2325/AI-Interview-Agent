// ======================================================
// AI INTERVIEW AGENT FRONTEND
// ======================================================


// ======================================================
// API
// ======================================================

const API_URL = "/api/interview";


// ======================================================
// STATE
// ======================================================

let sessionId = "";

let candidateId = "";

let candidateName = "";

let questionNumber = 0;

const maxQuestions = 10;

let interviewFinished = false;


// ======================================================
// ELEMENTS
// ======================================================

const startScreen =
    document.getElementById("startScreen");

const interviewScreen =
    document.getElementById("interviewScreen");

const feedbackScreen =
    document.getElementById("feedbackScreen");


const startBtn =
    document.getElementById("startBtn");

const sendBtn =
    document.getElementById("sendBtn");

const restartBtn =
    document.getElementById("restartBtn");


const candidateIdInput =
    document.getElementById("candidateId");

const candidateNameInput =
    document.getElementById("candidateName");


const candidateDisplay =
    document.getElementById("candidateDisplay");


const questionCounter =
    document.getElementById("questionCounter");


const progressFill =
    document.getElementById("progressFill");


const topicName =
    document.getElementById("topicName");


const questionText =
    document.getElementById("questionText");


const answerInput =
    document.getElementById("answerInput");


const startError =
    document.getElementById("startError");


const averageScore =
    document.getElementById("averageScore");


const summary =
    document.getElementById("summary");


const strengthsList =
    document.getElementById("strengthsList");


const gapsList =
    document.getElementById("gapsList");


const nextList =
    document.getElementById("nextList");


// ======================================================
// INITIAL STATE
// ======================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        startScreen.classList.remove("hidden");

        interviewScreen.classList.add("hidden");

        feedbackScreen.classList.add("hidden");

    }
);


// ======================================================
// START INTERVIEW
// ======================================================

startBtn.addEventListener(
    "click",
    startInterview
);


async function startInterview() {

    // ----------------------------------------------
    // GET CANDIDATE DETAILS
    // ----------------------------------------------

    candidateId =
        candidateIdInput.value.trim();


    candidateName =
        candidateNameInput.value.trim();


    startError.textContent = "";


    // ----------------------------------------------
    // VALIDATION
    // ----------------------------------------------

    if (!candidateId) {

        startError.textContent =
            "Please enter Candidate ID.";

        candidateIdInput.focus();

        return;

    }


    if (!candidateName) {

        startError.textContent =
            "Please enter Candidate Name.";

        candidateNameInput.focus();

        return;

    }


    // ----------------------------------------------
    // CREATE SESSION ID
    // ----------------------------------------------

    sessionId =
        "session-" +
        Date.now() +
        "-" +
        Math.random()
            .toString(36)
            .substring(2, 8);


    console.log(
        "Session ID:",
        sessionId
    );


    // ----------------------------------------------
    // RESET INTERVIEW
    // ----------------------------------------------

    questionNumber = 0;

    interviewFinished = false;


    questionText.textContent =
        "Preparing your first question...";


    topicName.textContent =
        "Preparing interview...";


    questionCounter.textContent =
        "Question 0";


    progressFill.style.width =
        "0%";


    answerInput.value = "";


    // ----------------------------------------------
    // DISABLE START BUTTON
    // ----------------------------------------------

    startBtn.disabled = true;

    startBtn.textContent =
        "Starting Interview...";


    try {

        // ------------------------------------------
        // API REQUEST
        // ------------------------------------------

        const response =
            await fetch(
                API_URL,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },

                    body: JSON.stringify({

                        sessionId:
                            sessionId,

                        candidate: {

                            id:
                                candidateId,

                            name:
                                candidateName

                        }

                    })

                }
            );


        const data =
            await response.json();


        console.log(
            "Start response:",
            data
        );


        // ------------------------------------------
        // ERROR
        // ------------------------------------------

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to start interview."
            );

        }


        // ------------------------------------------
        // DISPLAY CANDIDATE
        // ------------------------------------------

        candidateDisplay.textContent =
            candidateName;


        // ------------------------------------------
        // CHANGE SCREEN
        // ------------------------------------------

        startScreen.classList.add(
            "hidden"
        );


        interviewScreen.classList.remove(
            "hidden"
        );


        feedbackScreen.classList.add(
            "hidden"
        );


        // ------------------------------------------
        // SHOW FIRST QUESTION
        // ------------------------------------------

        handleInterviewResponse(data);

    }


    catch (error) {

        console.error(
            "Start interview error:",
            error
        );


        startError.textContent =
            error.message ||
            "Could not start interview.";

    }


    finally {

        startBtn.disabled = false;

        startBtn.textContent =
            "Start Interview";

    }

}


// ======================================================
// HANDLE INTERVIEW RESPONSE
// ======================================================

function handleInterviewResponse(data) {

    console.log(
        "Interview response:",
        data
    );


    // ==================================================
    // INTERVIEW COMPLETED
    // ==================================================

    if (data.done === true) {

        showResults(data);

        return;

    }


    // ==================================================
    // QUESTION NUMBER
    // ==================================================

    questionNumber =
        data.questionNumber ||
        questionNumber + 1;


    // ==================================================
    // CURRENT TOPIC
    // ==================================================

    topicName.textContent =
        data.topic ||
        "Technical Interview";


    // ==================================================
    // SHOW ONLY CURRENT QUESTION
    // ==================================================

    questionText.textContent =
        data.reply ||
        "Please answer the question.";


    // ==================================================
    // UPDATE PROGRESS
    // ==================================================

    updateProgress();


    // ==================================================
    // CLEAR ANSWER BOX
    // ==================================================

    answerInput.value = "";

    answerInput.disabled = false;

    answerInput.focus();

}


// ======================================================
// SUBMIT ANSWER
// ======================================================

sendBtn.addEventListener(
    "click",
    submitAnswer
);


async function submitAnswer() {

    const answer =
        answerInput.value.trim();


    // ----------------------------------------------
    // EMPTY ANSWER
    // ----------------------------------------------

    if (!answer) {

        alert(
            "Please enter your answer."
        );

        answerInput.focus();

        return;

    }


    // ----------------------------------------------
    // SESSION CHECK
    // ----------------------------------------------

    if (!sessionId) {

        alert(
            "Interview session not found. " +
            "Please restart the interview."
        );

        return;

    }


    // ----------------------------------------------
    // LOADING STATE
    // ----------------------------------------------

    sendBtn.disabled = true;

    sendBtn.textContent =
        "Evaluating...";


    answerInput.disabled = true;


    try {

        // ------------------------------------------
        // SEND ANSWER TO BACKEND
        // ------------------------------------------

        const response =
            await fetch(
                API_URL,
                {

                    method: "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },

                    body: JSON.stringify({

                        sessionId:
                            sessionId,

                        message:
                            answer

                    })

                }
            );


        const data =
            await response.json();


        console.log(
            "Answer response:",
            data
        );


        // ------------------------------------------
        // ERROR
        // ------------------------------------------

        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Failed to submit answer."
            );

        }


        // ------------------------------------------
        // SHOW NEXT QUESTION
        //
        // IMPORTANT:
        // Candidate answer is NOT added to screen.
        // Old question is simply replaced.
        // ------------------------------------------

        handleInterviewResponse(data);

    }


    catch (error) {

        console.error(
            "Submit answer error:",
            error
        );


        alert(
            "Could not submit answer.\n\n" +
            error.message
        );


        answerInput.disabled = false;

    }


    finally {

        sendBtn.disabled = false;

        sendBtn.textContent =
            "Submit Answer";

    }

}


// ======================================================
// PROGRESS
// ======================================================

function updateProgress() {

    questionCounter.textContent =
        `Question ${questionNumber}`;


    const percentage =
        Math.min(
            (questionNumber /
                maxQuestions) *
            100,
            100
        );


    progressFill.style.width =
        `${percentage}%`;

}


// ======================================================
// SHOW FINAL RESULTS
// ======================================================

function showResults(data) {

    interviewFinished = true;


    // ----------------------------------------------
    // CHANGE SCREEN
    // ----------------------------------------------

    startScreen.classList.add(
        "hidden"
    );


    interviewScreen.classList.add(
        "hidden"
    );


    feedbackScreen.classList.remove(
        "hidden"
    );


    // ----------------------------------------------
    // GET FEEDBACK
    // ----------------------------------------------

    const feedback =
        data.feedback || {};


    // ----------------------------------------------
    // SCORE
    // ----------------------------------------------

    averageScore.textContent =
        feedback.average_score ??
        "0.0";


    // ----------------------------------------------
    // SUMMARY
    // ----------------------------------------------

    summary.textContent =
        feedback.summary ||
        "Interview completed successfully.";


    // ----------------------------------------------
    // STRENGTHS
    // ----------------------------------------------

    renderList(
        strengthsList,
        feedback.strengths
    );


    // ----------------------------------------------
    // GAPS
    // ----------------------------------------------

    renderList(
        gapsList,
        feedback.gaps
    );


    // ----------------------------------------------
    // NEXT STEPS
    // ----------------------------------------------

    renderList(
        nextList,
        feedback.next
    );


    console.log(
        "Final feedback:",
        feedback
    );

}


// ======================================================
// RENDER FEEDBACK LIST
// ======================================================

function renderList(
    element,
    items
) {

    element.innerHTML = "";


    if (
        !Array.isArray(items) ||
        items.length === 0
    ) {

        const li =
            document.createElement("li");


        li.textContent =
            "No specific points available.";


        element.appendChild(li);


        return;

    }


    items.forEach(
        item => {

            const li =
                document.createElement("li");


            li.textContent =
                item;


            element.appendChild(li);

        }
    );

}


// ======================================================
// RESTART INTERVIEW
// ======================================================

restartBtn.addEventListener(
    "click",
    () => {

        // ------------------------------------------
        // RESET STATE
        // ------------------------------------------

        sessionId = "";

        candidateId = "";

        candidateName = "";

        questionNumber = 0;

        interviewFinished = false;


        // ------------------------------------------
        // RESET INPUTS
        // ------------------------------------------

        candidateIdInput.value = "";

        candidateNameInput.value = "";

        answerInput.value = "";


        // ------------------------------------------
        // RESET QUESTION
        // ------------------------------------------

        questionText.textContent =
            "Preparing your first question...";


        topicName.textContent =
            "Preparing interview...";


        questionCounter.textContent =
            "Question 0";


        progressFill.style.width =
            "0%";


        // ------------------------------------------
        // RESET SCREENS
        // ------------------------------------------

        feedbackScreen.classList.add(
            "hidden"
        );


        interviewScreen.classList.add(
            "hidden"
        );


        startScreen.classList.remove(
            "hidden"
        );

    }
);


// ======================================================
// CTRL + ENTER
// ======================================================

answerInput.addEventListener(
    "keydown",
    (event) => {

        if (
            event.ctrlKey &&
            event.key === "Enter"
        ) {

            event.preventDefault();

            submitAnswer();

        }

    }
);