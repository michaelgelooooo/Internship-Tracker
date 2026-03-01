function openModal(row) {
    // Grab day, month, year from the row
    const day = row.dataset.day || 1;
    const month = row.dataset.month || 1;
    const year = row.dataset.year || new Date().getFullYear();

    // Populate time inputs
    const amIn = row.dataset.amIn || "";
    const amOut = row.dataset.amOut || "";
    const pmIn = row.dataset.pmIn || "";
    const pmOut = row.dataset.pmOut || "";

    document.getElementById('modal-day').value = day;
    document.getElementById('modal-month').value = month;
    document.getElementById('modal-year').value = year;

    document.getElementById('modal-am-in').value = amIn;
    document.getElementById('modal-am-out').value = amOut;
    document.getElementById('modal-pm-in').value = pmIn;
    document.getElementById('modal-pm-out').value = pmOut;

    // Populate month/year for other forms that also use the day
    ['holiday', 'weekend', 'delete'].forEach(prefix => {
        const dayInput = document.getElementById(`${prefix}-day`);
        const monthInput = document.getElementById(`${prefix}-month`);
        const yearInput = document.getElementById(`${prefix}-year`);
        if (dayInput) dayInput.value = day;
        if (monthInput) monthInput.value = month;
        if (yearInput) yearInput.value = year;
    });

    // Display the date header
    const displayDate = new Date(year, month - 1, day); // JS months are 0-indexed
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('modal-date').textContent = displayDate.toLocaleDateString(undefined, options);

    // Get holiday/weekend flags
    const isHoliday = row.dataset.isHoliday === "true";
    const isWeekend = row.dataset.isWeekend === "true";

    // Disable/enable time inputs and save button if it's a holiday/weekend
    const disableForm = isHoliday || isWeekend;
    ['modal-am-in', 'modal-am-out', 'modal-pm-in', 'modal-pm-out'].forEach(id => {
        const input = document.getElementById(id);
        if (input) input.disabled = disableForm;
    });
    const saveBtn = document.querySelector('button[form="daily-log-form"]');
    if (saveBtn) saveBtn.disabled = disableForm;

    // Update Holiday/Weekend buttons visually
    const holidayBtn = document.getElementById('holiday-btn');
    const weekendBtn = document.getElementById('weekend-btn');

    if (isHoliday) {
        holidayBtn.classList.add('bg-orange-500', 'text-white');
        holidayBtn.textContent = "Unmark as Holiday";

        weekendBtn.classList.remove('bg-orange-500', 'text-white');
        weekendBtn.textContent = "Mark as Weekend";

    } else if (isWeekend) {
        weekendBtn.classList.add('bg-orange-500', 'text-white');
        weekendBtn.textContent = "Unmark as Weekend";

        holidayBtn.classList.remove('bg-orange-500', 'text-white');
        holidayBtn.textContent = "Mark as Holiday";

    } else {
        holidayBtn.classList.remove('bg-orange-500', 'text-white');
        holidayBtn.textContent = "Mark as Holiday";

        weekendBtn.classList.remove('bg-orange-500', 'text-white');
        weekendBtn.textContent = "Mark as Weekend";
    }

    // Open the modal
    document.getElementById('log-modal').checked = true;
}

document.addEventListener("DOMContentLoaded", function () {
    // --- Ensure modal starts closed on page load ---
    const modalCheckbox = document.getElementById('log-modal');
    if (modalCheckbox) {
        modalCheckbox.checked = false; // modal always starts closed
    }

    // --- Quick Log date/time updater ---
    const dateInput = document.querySelector('input[name="log_date"]');
    const timeInput = document.querySelector('input[name="log_time"]');

    function updateDateTime() {
        const now = new Date();

        // YYYY-MM-DD
        const date = now.toISOString().split('T')[0];

        // HH:MM (24-hour)
        const time = now.toTimeString().slice(0, 5);

        if (dateInput) dateInput.value = date;
        if (timeInput) timeInput.value = time;
    }

    // Initial set
    updateDateTime();

    // Update every second
    setInterval(updateDateTime, 1000);
});