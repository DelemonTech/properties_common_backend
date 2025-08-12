document.addEventListener("DOMContentLoaded", function () {
    const ratingInput = document.querySelector("#id_rating");
    if (!ratingInput) return;

    // Create preview container
    const preview = document.createElement("div");
    preview.id = "rating-preview";
    preview.style.marginTop = "8px";
    preview.style.fontSize = "1.5rem";
    ratingInput.parentNode.appendChild(preview);

    // Function to update stars
    function updatePreview(value) {
        const val = parseFloat(value) || 0;
        let stars = "";
        for (let i = 1; i <= 5; i++) {
            if (i <= val) {
                stars += "★"; // full star
            } else if (i - val < 1 && i > val) {
                stars += "☆"; // empty star (you can add half-star logic if needed)
            } else {
                stars += "☆";
            }
        }
        preview.textContent = stars + ` (${val.toFixed(1)})`;
    }

    // Initial preview
    updatePreview(ratingInput.value);

    // Update when typing
    ratingInput.addEventListener("input", function () {
        updatePreview(this.value);
    });
});
