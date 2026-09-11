export async function downloadImage(url, filename) {
  const response = await fetch(url, { credentials: "omit" });
  if (!response.ok) throw new Error(`Download failed with status ${response.status}`);

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = filename;
    anchor.rel = "noopener";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {

    setTimeout(() => URL.revokeObjectURL(objectUrl), 10_000);
  }
}
