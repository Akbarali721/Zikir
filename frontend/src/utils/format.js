export function formatNumber(n) {
  return new Intl.NumberFormat("uz-UZ").format(n);
}

export function formatActiveTimeUz(seconds) {
  if (seconds < 0) seconds = 0;
  if (seconds < 60) return `${seconds} soniya`;
  const minutes = Math.floor(seconds / 60);
  const sec = seconds % 60;
  if (minutes < 60) {
    return sec ? `${minutes} daqiqa ${sec} soniya` : `${minutes} daqiqa`;
  }
  const hours = Math.floor(minutes / 60);
  const min = minutes % 60;
  const parts = [];
  if (hours) parts.push(`${hours} soat`);
  if (min) parts.push(`${min} daqiqa`);
  return parts.join(" ") || "0 soniya";
}

export function formatGoalRemainingUz(seconds) {
  if (seconds < 0) seconds = 0;
  if (seconds === 0) return "Maqsadgacha: 0";
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours >= 1 && minutes === 0) {
    return "Maqsadgacha: " + formatNumber(hours) + " soat";
  }
  if (hours >= 1) {
    return "Maqsadgacha: " + formatNumber(hours) + " soat " + minutes + " daqiqa";
  }
  if (minutes >= 1) {
    return "Maqsadgacha: " + minutes + " daqiqa";
  }
  return "Maqsadgacha: " + seconds + " soniya";
}
