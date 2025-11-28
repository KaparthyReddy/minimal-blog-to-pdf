// script.js
document.addEventListener("DOMContentLoaded", function () {
  const form = document.querySelector("form");
  const blogInput = document.getElementById("blogUrl");

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const blogUrl = blogInput.value.trim();

    if (!blogUrl) {
      alert("Please enter a valid blog URL.");
      return;
    }

    // Show loading status
    const button = form.querySelector("button");
    button.disabled = true;
    button.innerText = "Converting...";
    button.style.opacity = "0.7";

    try {
      // Changed to 127.0.0.1 to match your Flask server
      const response = await fetch("http://127.0.0.1:3000/convert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: blogUrl })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to generate PDF. Try again.");
      }

      // Get PDF blob and trigger download
      const blob = await response.blob();
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = "blog.pdf";
      link.click();

    } catch (err) {
      console.error("Error:", err);
      alert(err.message);
    } finally {
      // Reset button
      button.disabled = false;
      button.innerText = "Convert to PDF";
      button.style.opacity = "1";
      blogInput.value = "";
    }
  });
});
