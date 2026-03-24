async function openModal(row) {
    const recordUrl = document.querySelector('[data-record-url]')?.dataset.recordUrl;
    const day = row.dataset.day;
    const month = row.dataset.month;
    const year = row.dataset.year;

    let data;
    try {
        const response = await fetch(`${recordUrl}?day=${day}&month=${month}&year=${year}`);
        if (!response.ok) throw new Error('Failed to fetch record');
        data = await response.json();
    } catch (error) {
        console.error('Error fetching record:', error);
        return;
    }

    // Populate update form
    document.getElementById('modal-day').value = day;
    document.getElementById('modal-month').value = month;
    document.getElementById('modal-year').value = year;
    document.getElementById('modal-am-in').value = data.am_in;
    document.getElementById('modal-am-out').value = data.am_out;
    document.getElementById('modal-pm-in').value = data.pm_in;
    document.getElementById('modal-pm-out').value = data.pm_out;

    ['holiday', 'weekend', 'delete'].forEach(prefix => {
        document.getElementById(`modal-${prefix}-day`).value = day;
        document.getElementById(`modal-${prefix}-month`).value = month;
        document.getElementById(`modal-${prefix}-year`).value = year;
    });

    const displayDate = new Date(year, month - 1, day);
    document.getElementById('modal-date').textContent = displayDate.toLocaleDateString(
        undefined,
        { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
    );

    const disableForm = data.is_holiday || data.is_weekend;
    ['modal-am-in', 'modal-am-out', 'modal-pm-in', 'modal-pm-out'].forEach(id => {
        document.getElementById(id).disabled = disableForm;
    });
    document.querySelector('button[form="daily-log-form"]').disabled = disableForm;

    const holidayBtn = document.getElementById('holiday-btn');
    const weekendBtn = document.getElementById('weekend-btn');

    holidayBtn.classList.toggle('bg-orange-500', data.is_holiday);
    holidayBtn.classList.toggle('text-white', data.is_holiday);
    holidayBtn.textContent = data.is_holiday ? "Unmark as Holiday" : "Mark as Holiday";

    weekendBtn.classList.toggle('bg-orange-500', data.is_weekend);
    weekendBtn.classList.toggle('text-white', data.is_weekend);
    weekendBtn.textContent = data.is_weekend ? "Unmark as Weekend" : "Mark as Weekend";

    // Open modal with fallback for browsers without native dialog support
    const modal = document.getElementById('log-modal');
    if (typeof modal.showModal === 'function') {
        modal.showModal();
    } else {
        modal.setAttribute('open', '');
    }
}

function closeModal() {
    const modal = document.getElementById('log-modal');
    if (typeof modal.close === 'function') {
        modal.close();
    } else {
        modal.removeAttribute('open');
    }
}

function getOrdinal(n) {
    if (n >= 11 && n <= 13) return n + 'th';
    switch (n % 10) {
        case 1: return n + 'st';
        case 2: return n + 'nd';
        case 3: return n + 'rd';
        default: return n + 'th';
    }
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('dialog').forEach(dialog => {
        if (typeof dialogPolyfill !== 'undefined') {
            dialogPolyfill.registerDialog(dialog);
        }
    });

    const dateInput = document.querySelector('input[name="log_date"]');
    const timeInput = document.querySelector('input[name="log_time"]');

    function updateDateTime() {
        const now = new Date();

        const weekday = now.toLocaleDateString(undefined, { weekday: 'long' });
        const day = getOrdinal(now.getDate());
        const month = now.toLocaleDateString(undefined, { month: 'long' });
        const year = now.getFullYear();
        const formattedDate = `${weekday}, ${day} of ${month} ${year}`;

        const hours24 = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const hours12 = now.getHours() % 12 || 12;
        const ampm = now.getHours() >= 12 ? 'PM' : 'AM';
        const formattedTime = `${hours24}:${minutes} ⟵ or ⟶ ${String(hours12).padStart(2, '0')}:${minutes} ${ampm}`;

        if (dateInput) dateInput.value = formattedDate;
        if (timeInput) timeInput.value = formattedTime;
    }

    updateDateTime();
    setInterval(updateDateTime, 1000);
});