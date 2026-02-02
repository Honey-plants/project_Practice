export async function resizeAndCompressImage(blob, maxWidth = 1024) {
  const img = new Image();
  const url = URL.createObjectURL(blob);
  img.src = url;
  await img.decode();

  const scale = Math.min(1, maxWidth / img.width);
  const dpr = window.devicePixelRatio || 1;

  const canvas = document.createElement("canvas");
  canvas.width = Math.round(img.width * scale * dpr);
  canvas.height = Math.round(img.height * scale * dpr);

  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";

  ctx.drawImage(
    img,
    0,
    0,
    canvas.width / dpr,
    canvas.height / dpr
  );

  const resizedBlob = await new Promise((resolve) =>
    canvas.toBlob(resolve, "image/jpeg", 0.9)
  );

  URL.revokeObjectURL(url);

  return resizedBlob; // 🔥 여기서 끝
}
