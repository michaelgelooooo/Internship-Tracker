function openModal(row) {
    const day = row.dataset.day;

    // Update the time-edit form
    document.getElementById('modal-day').value = day;
    document.getElementById('modal-am-in').value = row.dataset.amIn || "";
    document.getElementById('modal-am-out').value = row.dataset.amOut || "";
    document.getElementById('modal-pm-in').value = row.dataset.pmIn || "";
    document.getElementById('modal-pm-out').value = row.dataset.pmOut || "";

    // Update the hidden day inputs for Holiday and Weekend buttons
    document.getElementById('holiday-day').value = day;
    document.getElementById('weekend-day').value = day;

    document.getElementById('delete-day').value = day;

    // Display the date under the header
    const today = new Date(); // current month/year for context
    const displayDate = new Date(today.getFullYear(), today.getMonth(), day);
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('modal-date').textContent = displayDate.toLocaleDateString(undefined, options);

    // Open the modal
    document.getElementById('log-modal').checked = true;
}

document.addEventListener("DOMContentLoaded", function () {
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