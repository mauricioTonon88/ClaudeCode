(() => {
  // State
  let currentMode = "t2v";
  let referenceImages = []; // array of URL strings
  let history = JSON.parse(localStorage.getItem("seedance_history") || "[]");
  let polling = null;

  // DOM elements
  const tabs = document.querySelectorAll(".tab");
  const refSection = document.getElementById("refSection");
  const extendSection = document.getElementById("extendSection");
  const refImagesContainer = document.getElementById("refImages");
  const refAddBtn = document.getElementById("refAddBtn");
  const imageInput = document.getElementById("imageInput");
  const imageUrlInput = document.getElementById("imageUrlInput");
  const addUrlBtn = document.getElementById("addUrlBtn");
  const extendId = document.getElementById("extendId");
  const promptInput = document.getElementById("promptInput");
  const aspectRatio = document.getElementById("aspectRatio");
  const duration = document.getElementById("duration");
  const quality = document.getElementById("quality");
  const generateBtn = document.getElementById("generateBtn");
  const previewPlaceholder = document.getElementById("previewPlaceholder");
  const videoPlayer = document.getElementById("videoPlayer");
  const progressOverlay = document.getElementById("progressOverlay");
  const progressText = document.getElementById("progressText");
  const progressSub = document.getElementById("progressSub");
  const historyBtn = document.getElementById("historyBtn");
  const closeHistory = document.getElementById("closeHistory");
  const historySidebar = document.getElementById("historySidebar");
  const historyList = document.getElementById("historyList");

  // Tab switching
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      currentMode = tab.dataset.tab;

      refSection.style.display = currentMode === "i2v" ? "block" : "none";
      extendSection.style.display =
        currentMode === "extend" ? "block" : "none";

      // Update placeholder text
      if (currentMode === "t2v") {
        promptInput.placeholder = "Describe the video you want to generate...";
      } else if (currentMode === "i2v") {
        promptInput.placeholder =
          "Describe how the image should be animated...";
      } else {
        promptInput.placeholder =
          "Optional: describe how to continue the video...";
      }
    });
  });

  // Reference image management
  function renderRefImages() {
    // Remove existing thumbnails (keep the add button)
    refImagesContainer
      .querySelectorAll(".ref-thumb")
      .forEach((el) => el.remove());

    referenceImages.forEach((url, idx) => {
      const thumb = document.createElement("div");
      thumb.className = "ref-thumb";
      thumb.innerHTML = `
        <img src="${escapeHtml(url)}" alt="Reference ${idx + 1}" />
        <button class="ref-remove" data-idx="${idx}">&times;</button>
      `;
      refImagesContainer.insertBefore(thumb, refAddBtn);
    });
  }

  refAddBtn.addEventListener("click", () => imageInput.click());

  imageInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("image", file);

    try {
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (data.url) {
        // Convert relative path to absolute URL for API
        referenceImages.push(window.location.origin + data.url);
        renderRefImages();
      } else {
        showToast("Upload failed: " + (data.error || "Unknown error"), true);
      }
    } catch (err) {
      showToast("Upload failed: " + err.message, true);
    }
    imageInput.value = "";
  });

  addUrlBtn.addEventListener("click", () => {
    const url = imageUrlInput.value.trim();
    if (!url) return;
    if (!url.startsWith("http")) {
      showToast("Please enter a valid URL starting with http", true);
      return;
    }
    referenceImages.push(url);
    renderRefImages();
    imageUrlInput.value = "";
  });

  refImagesContainer.addEventListener("click", (e) => {
    const removeBtn = e.target.closest(".ref-remove");
    if (removeBtn) {
      const idx = parseInt(removeBtn.dataset.idx);
      referenceImages.splice(idx, 1);
      renderRefImages();
    }
  });

  // Generate
  generateBtn.addEventListener("click", async () => {
    if (currentMode === "t2v" && !promptInput.value.trim()) {
      showToast("Please enter a prompt", true);
      return;
    }
    if (currentMode === "i2v" && referenceImages.length === 0) {
      showToast("Please add at least one reference image", true);
      return;
    }
    if (currentMode === "extend" && !extendId.value.trim()) {
      showToast("Please enter a request ID to extend", true);
      return;
    }

    generateBtn.disabled = true;
    showProgress("Submitting request...", "Connecting to Seedance API");

    try {
      let res, data;

      if (currentMode === "extend") {
        res = await fetch("/api/extend", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            request_id: extendId.value.trim(),
            prompt: promptInput.value.trim(),
            duration: parseInt(duration.value),
            quality: quality.value,
          }),
        });
      } else {
        res = await fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            mode: currentMode,
            prompt: promptInput.value.trim(),
            images_list: currentMode === "i2v" ? referenceImages : undefined,
            aspect_ratio: aspectRatio.value,
            duration: parseInt(duration.value),
            quality: quality.value,
          }),
        });
      }

      data = await res.json();

      if (data.error) {
        hideProgress();
        showToast("Error: " + (data.error || JSON.stringify(data)), true);
        generateBtn.disabled = false;
        return;
      }

      const requestId = data.request_id;
      if (!requestId) {
        hideProgress();
        showToast(
          "No request_id returned: " + JSON.stringify(data),
          true
        );
        generateBtn.disabled = false;
        return;
      }

      // Save to history
      const entry = {
        id: requestId,
        prompt: promptInput.value.trim() || "(no prompt)",
        mode: currentMode,
        settings: {
          aspect_ratio: aspectRatio.value,
          duration: duration.value,
          quality: quality.value,
        },
        status: "pending",
        timestamp: Date.now(),
        url: null,
      };
      history.unshift(entry);
      saveHistory();
      renderHistory();

      // Start polling
      showProgress(
        "Generating video...",
        `Request ID: ${requestId} — This may take a few minutes`
      );
      startPolling(requestId);
    } catch (err) {
      hideProgress();
      showToast("Request failed: " + err.message, true);
      generateBtn.disabled = false;
    }
  });

  // Polling
  function startPolling(requestId) {
    let elapsed = 0;
    const interval = 5000;
    const maxTime = 600000;

    polling = setInterval(async () => {
      elapsed += interval;
      if (elapsed > maxTime) {
        clearInterval(polling);
        hideProgress();
        showToast("Generation timed out after 10 minutes", true);
        updateHistoryEntry(requestId, "failed");
        generateBtn.disabled = false;
        return;
      }

      try {
        const res = await fetch(`/api/result/${requestId}`);
        const data = await res.json();

        if (data.status === "completed" && data.url) {
          clearInterval(polling);
          hideProgress();
          showVideo(data.url);
          updateHistoryEntry(requestId, "completed", data.url);
          generateBtn.disabled = false;
          showToast("Video generated successfully!");
        } else if (data.status === "failed") {
          clearInterval(polling);
          hideProgress();
          showToast(
            "Generation failed: " + (data.error || "Unknown error"),
            true
          );
          updateHistoryEntry(requestId, "failed");
          generateBtn.disabled = false;
        } else {
          const mins = Math.floor(elapsed / 60000);
          const secs = Math.floor((elapsed % 60000) / 1000);
          progressSub.textContent = `Elapsed: ${mins}m ${secs}s — Status: ${data.status || "processing"}`;
        }
      } catch (err) {
        // Network error during poll, keep trying
        progressSub.textContent = "Connection issue, retrying...";
      }
    }, interval);
  }

  // Video display
  function showVideo(url) {
    previewPlaceholder.style.display = "none";
    videoPlayer.style.display = "block";
    videoPlayer.src = url;
    videoPlayer.load();
  }

  // Progress
  function showProgress(text, sub) {
    progressOverlay.style.display = "flex";
    progressText.textContent = text;
    progressSub.textContent = sub;
  }

  function hideProgress() {
    progressOverlay.style.display = "none";
  }

  // History
  function saveHistory() {
    localStorage.setItem("seedance_history", JSON.stringify(history));
  }

  function updateHistoryEntry(requestId, status, url) {
    const entry = history.find((h) => h.id === requestId);
    if (entry) {
      entry.status = status;
      if (url) entry.url = url;
      saveHistory();
      renderHistory();
    }
  }

  function renderHistory() {
    if (history.length === 0) {
      historyList.innerHTML = '<p class="empty-state">No generations yet</p>';
      return;
    }

    historyList.innerHTML = history
      .map(
        (h) => `
      <div class="history-item" data-url="${escapeHtml(h.url || "")}" data-id="${escapeHtml(h.id)}">
        <div class="hi-prompt">${escapeHtml(h.prompt)}</div>
        <div class="hi-meta">
          <span class="hi-status ${h.status}">${h.status}</span>
          <span>${h.mode.toUpperCase()}</span>
          <span>${h.settings.aspect_ratio}</span>
          <span>${h.settings.duration}s</span>
          <span>${new Date(h.timestamp).toLocaleTimeString()}</span>
        </div>
      </div>
    `
      )
      .join("");

    historyList.querySelectorAll(".history-item").forEach((item) => {
      item.addEventListener("click", () => {
        const url = item.dataset.url;
        if (url && url !== "null") {
          showVideo(url);
          historySidebar.classList.remove("open");
        } else {
          // If pending, re-poll
          const id = item.dataset.id;
          const entry = history.find((h) => h.id === id);
          if (entry && entry.status === "pending") {
            showProgress("Checking status...", `Request ID: ${id}`);
            startPolling(id);
            generateBtn.disabled = true;
            historySidebar.classList.remove("open");
          }
        }
      });
    });
  }

  // History sidebar
  historyBtn.addEventListener("click", () => {
    renderHistory();
    historySidebar.classList.toggle("open");
  });

  closeHistory.addEventListener("click", () => {
    historySidebar.classList.remove("open");
  });

  // Toast
  function showToast(message, isError) {
    let toast = document.querySelector(".toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.className = "toast";
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.toggle("error", !!isError);
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3500);
  }

  // Utility
  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // Init
  renderHistory();
})();
