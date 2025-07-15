const videoElement = document.getElementById("camera-stream");

function startCamera() {
    // kirim permintaan ke backend untuk memulai kamera
    fetch('/start-camera')
        .then(response => {
            if (response.ok) {
                alert('Kamera dinyalakan!');
                videoElement.src = "/video"; // set sumber video ke endpoint streaming kamera
            } else {
                alert('Gagal menyalakan kamera');
            }
        })
        .catch(error => {
            console.error("Gagal menyalakan kamera:", error);
        });
}

function stopCamera() {
    fetch('/stop-camera')
        .then(response => {
            if (response.ok) {
                alert('Kamera dimatikan!');
                videoElement.src = "";
            } else {
                alert('Gagal mematikan kamera');
        }})
        .catch(error => {
            console.error("Gagal mematikan kamera:", error);
        });
}

function toggleTheme() {
    const body = document.body;
    if (body.classList.contains("light")) {
        body.classList.remove("light");
        body.classList.add("dark");
    } else {
        body.classList.remove("dark");
        body.classList.add("light");
    }
}

// fungsi untuk mencatat hasil deteksi ke log riwayat di halaman
function logDetection(className, confidence) {
  const logDiv = document.getElementById("log");
  const time = new Date().toLocaleTimeString();

  // buat elemen div baru untuk entry log
  const entry = document.createElement("div");
  entry.className = "entry";
  // isi teks log dengan waktu, nama kelas hasil deteksi, dan confidence (kepercayaan)
  entry.textContent = `🔍 [${time}] Terdeteksi: ${className} (confidence: ${confidence.toFixed(2)})`;

  logDiv.prepend(entry);

  if (logDiv.childElementCount > 20) {
    logDiv.removeChild(logDiv.lastChild);
  }
}
