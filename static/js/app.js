let currentUser = null;

function login() {
  currentUser = {
    name: document.getElementById("name").value,
    block: document.getElementById("block").value,
    room: document.getElementById("room").value,
  };

  document.getElementById("welcome").textContent =
    `Welcome, ${currentUser.name} (Block ${currentUser.block})`;

  document.querySelector("section").classList.add("hidden");
  document.getElementById("dashboard").classList.remove("hidden");
}

async function markAttendance() {
  await fetch("/api/attendance", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      student_name: currentUser.name,
      hostel_block: currentUser.block,
      room_number: currentUser.room,
      attendance_date: new Date().toISOString().split("T")[0],
      attendance_time: new Date().toLocaleTimeString(),
      wifi_verified: true,
      device_verified: true,
    }),
  });

  alert("Attendance marked!");
}


async function submitComplaint(event) {
    event.preventDefault();

    const text = document.getElementById("complaint-desc").value;
    const aiBox = document.getElementById("ai-analysis");
    const aiText = document.getElementById("ai-analysis-text");

    aiBox.classList.remove("hidden");
    aiText.textContent = "Analyzing complaint priority...";

    try {
      const res = await fetch("http://127.0.0.1:5000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text }),
      });

      const data = await res.json();

      aiText.innerHTML = `
            <b>Priority:</b> ${data.priority.toUpperCase()}<br>
            <b>Category:</b> ${data.category}<br>
            <b>Confidence:</b> ${data.confidence}<br>
            <b>Score:</b> ${data.priority_score}
          `;
    } catch (err) {
      aiText.textContent = "AI analysis failed. Please try again.";
      console.error(err);
    }
  }
}
