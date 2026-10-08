// Campus Lost and Found - Client Interactions
document.addEventListener("DOMContentLoaded", function () {
  // Live image preview
  const imageInput = document.getElementById("imageInput");
  const imagePreviewContainer = document.getElementById("imagePreviewContainer");
  const imagePreview = document.getElementById("imagePreview");

  if (imageInput && imagePreview) {
    imageInput.addEventListener("change", function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          imagePreview.src = e.target.result;
          if (imagePreviewContainer) {
            imagePreviewContainer.classList.remove("d-none");
          }
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Live video preview
  const videoInput = document.getElementById("videoInput");
  const videoPreviewContainer = document.getElementById("videoPreviewContainer");
  const videoPreview = document.getElementById("videoPreview");

  if (videoInput && videoPreview) {
    videoInput.addEventListener("change", function () {
      const file = this.files[0];
      if (file) {
        const fileURL = URL.createObjectURL(file);
        videoPreview.src = fileURL;
        if (videoPreviewContainer) {
          videoPreviewContainer.classList.remove("d-none");
        }
      }
    });
  }

  // Dynamic field helper according to category
  const categorySelect = document.getElementById("categorySelect");
  const idNumberGroup = document.getElementById("idNumberGroup");
  const brandGroup = document.getElementById("brandGroup");
  const keyTypeGroup = document.getElementById("keyTypeGroup");

  if (categorySelect) {
    categorySelect.addEventListener("change", function () {
      const selected = this.value;
      
      if (idNumberGroup) {
        if (selected.includes("College ID") || selected.includes("Cards")) {
          idNumberGroup.classList.remove("d-none");
        } else {
          idNumberGroup.classList.add("d-none");
        }
      }

      if (brandGroup) {
        if (selected.includes("Electronics") || selected.includes("Watches") || selected.includes("Bags")) {
          brandGroup.classList.remove("d-none");
        } else {
          brandGroup.classList.add("d-none");
        }
      }

      if (keyTypeGroup) {
        if (selected.includes("Keys")) {
          keyTypeGroup.classList.remove("d-none");
        } else {
          keyTypeGroup.classList.add("d-none");
        }
      }
    });
  }
});
