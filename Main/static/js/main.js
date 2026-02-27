function openModal(row) {
    const day = row.dataset.day;

    // Populate time inputs
    const amIn = row.dataset.amIn || "";
    const amOut = row.dataset.amOut || "";
    const pmIn = row.dataset.pmIn || "";
    const pmOut = row.dataset.pmOut || "";

    document.getElementById('modal-day').value = day;
    document.getElementById('modal-am-in').value = amIn;
    document.getElementById('modal-am-out').value = amOut;
    document.getElementById('modal-pm-in').value = pmIn;
    document.getElementById('modal-pm-out').value = pmOut;

    // Hidden inputs for forms
    document.getElementById('holiday-day').value = day;
    document.getElementById('weekend-day').value = day;
    document.getElementById('delete-day').value = day;

    // Display the date header
    const today = new Date();
    const displayDate = new Date(today.getFullYear(), today.getMonth(), day);
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('modal-date').textContent = displayDate.toLocaleDateString(undefined, options);

    // Get holiday/weekend flags
    const isHoliday = row.dataset.isHoliday === "true";
    const isWeekend = row.dataset.isWeekend === "true";

    // Disable/enable time inputs and save button if it's a holiday/weekend
    const disableForm = isHoliday || isWeekend;
    const timeInputs = ['modal-am-in', 'modal-am-out', 'modal-pm-in', 'modal-pm-out'];
    timeInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) input.disabled = disableForm;
    });

    const saveBtn = document.querySelector('button[form="daily-log-form"]');
    if (saveBtn) saveBtn.disabled = disableForm;

    // Update Holiday/Weekend buttons visually
    const holidayBtn = document.querySelector('#holiday-day').closest('form').querySelector('button');
    const weekendBtn = document.querySelector('#weekend-day').closest('form').querySelector('button');

    if (isHoliday) {
        holidayBtn.classList.add('bg-orange-500', 'text-white', 'hover:bg-orange-700');
        holidayBtn.textContent = "Unmark as Holiday";
        weekendBtn.classList.remove('bg-orange-500', 'text-white');
        weekendBtn.textContent = "Mark as Weekend";
    } else if (isWeekend) {
        weekendBtn.classList.add('bg-orange-500', 'text-white', 'hover:bg-orange-700');
        weekendBtn.textContent = "Unmark as Weekend";
        holidayBtn.classList.remove('bg-orange-500', 'text-white');
        holidayBtn.textContent = "Mark as Holiday";
    } else {
        [holidayBtn, weekendBtn].forEach(btn => {
            btn.classList.remove('bg-orange-500', 'text-white');
            btn.textContent = btn.id === 'holiday-day' ? "Mark as Holiday" : "Mark as Weekend";
        });
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