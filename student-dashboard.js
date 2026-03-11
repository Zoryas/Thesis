// Calendar selection
const calendar = document.getElementById("calendar");
const selectedDateText = document.getElementById("selectedDate");

calendar.addEventListener("change", () => {
  selectedDateText.textContent = "Selected: " + calendar.value;
});

// Chart.js Line Chart
const ctx = document.getElementById("progressChart").getContext("2d");
new Chart(ctx, {
  type: "line",
  data: {
    labels: ["2026-01-10", "2026-02-15", "2026-03-24"],
    datasets: [{
      label: "Difficulty Level",
      data: [1, 2, 3],
      borderColor: "rgba(0, 123, 255, 1)",
      backgroundColor: "rgba(0, 123, 255, 0.2)",
      fill: true,
      tension: 0.4
    }]
  },
  options: {
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1
        }
      }
    }
  }
});
