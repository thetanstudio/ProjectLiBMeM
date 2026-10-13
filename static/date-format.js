
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('input[type="date"]').forEach(function (dateInput) {
        // Prevent accidentally creating duplicate fields.
        if (dateInput.dataset.dateFormatReady === "true") {
            return;
        }
        dateInput.dataset.dateFormatReady = "true";

        // Preserve the original date input for Flask's YYYY-MM-DD format.
        const originalRequired = dateInput.required;
        const originalName = dateInput.name;
        const originalId = dateInput.id;

        // Create the visible DD/MM/YYYY text field.
        const textInput = document.createElement("input");
        textInput.type = "text";
        textInput.placeholder = "DD/MM/YYYY";
        textInput.autocomplete = "off";
        textInput.inputMode = "numeric";
        textInput.required = originalRequired;
        textInput.className = dateInput.className;
        textInput.setAttribute("aria-label", "Date (DD/MM/YYYY)");
        textInput.setAttribute("maxlength", "10");

        if (originalId) {
            textInput.id = originalId + "_display";
        }

        textInput.style.cssText = `
            width: 145px;
            max-width: 100%;
            height: 38px;
            box-sizing: border-box;
            padding: 0 10px;
            border: 1px solid #d1d5db;
            border-right: 0;
            border-radius: 7px 0 0 7px;
            font: inherit;
            font-size: 14px;
            color: #222;
            background: #fff;
            outline-offset: 2px;
        `;

        // Wrap the visible field and calendar control together.
        const wrapper = document.createElement("div");
        wrapper.style.cssText = `
            display: inline-flex;
            align-items: center;
            position: relative;
            vertical-align: middle;
            max-width: 100%;
        `;

        // A real button, not just an emoji.
        const calendarButton = document.createElement("button");
        calendarButton.type = "button";
        calendarButton.textContent = "📅";
        calendarButton.title = "Choose a date";
        calendarButton.setAttribute("aria-label", "Open date calendar");
        calendarButton.style.cssText = `
            width: 40px;
            min-width: 40px;
            height: 38px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 1px solid #d1d5db;
            border-radius: 0 7px 7px 0;
            background: #f5f3ff;
            cursor: pointer;
            font-size: 16px;
            padding: 0;
        `;

        // Keep the native calendar input available but visually hidden.
        // Do not remove its name: Flask still receives YYYY-MM-DD.
        dateInput.required = false;
        dateInput.removeAttribute("id");
        dateInput.setAttribute("aria-label", "Native date picker");
        dateInput.title = "Choose a date";
        dateInput.style.cssText = `
            position: absolute;
            right: 0;
            top: 0;
            width: 40px;
            height: 38px;
            opacity: 0;
            cursor: pointer;
            z-index: 2;
            margin: 0;
        `;

        // Place the wrapper where the original input was.
        dateInput.parentNode.insertBefore(wrapper, dateInput);
        wrapper.appendChild(textInput);
        wrapper.appendChild(calendarButton);
        wrapper.appendChild(dateInput);

        function showFormattedDate() {
            const iso = dateInput.value;

            if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) {
                const parts = iso.split("-");
                textInput.value = `${parts[2]}/${parts[1]}/${parts[0]}`;
            } else {
                textInput.value = "";
            }

            textInput.setCustomValidity("");
        }

        function parseDisplayDate() {
            const value = textInput.value.trim();

            if (!value) {
                dateInput.value = "";
                textInput.setCustomValidity("");

                if (originalRequired) {
                    textInput.setCustomValidity("Please enter a date.");
                    return false;
                }

                return true;
            }

            // Accept DD/MM/YYYY, including single-digit day/month.
            const match = value.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);

            if (!match) {
                textInput.setCustomValidity(
                    "Enter the date as DD/MM/YYYY, for example 07/11/2026."
                );
                return false;
            }

            const day = Number(match[1]);
            const month = Number(match[2]);
            const year = Number(match[3]);

            // Validate the actual calendar date (including leap years).
            const check = new Date(Date.UTC(year, month - 1, day));

            if (
                year < 1000 ||
                check.getUTCFullYear() !== year ||
                check.getUTCMonth() !== month - 1 ||
                check.getUTCDate() !== day
            ) {
                textInput.setCustomValidity("Please enter a real calendar date.");
                return false;
            }

            const iso =
                String(year).padStart(4, "0") + "-" +
                String(month).padStart(2, "0") + "-" +
                String(day).padStart(2, "0");

            // Preserve the ISO value expected by Flask.
            dateInput.value = iso;
            textInput.setCustomValidity("");
            return true;
        }

        textInput.addEventListener("input", function () {
            textInput.setCustomValidity("");
        });

        textInput.addEventListener("blur", function () {
            if (parseDisplayDate()) {
                showFormattedDate();
            }
        });

        dateInput.addEventListener("change", showFormattedDate);

        calendarButton.addEventListener("click", function () {
            try {
                if (typeof dateInput.showPicker === "function") {
                    dateInput.showPicker();
                } else {
                    dateInput.click();
                }
            } catch (error) {
                dateInput.focus();
                dateInput.click();
            }
        });

        const form = dateInput.closest("form");

        if (form) {
            form.addEventListener("submit", function (event) {
                if (!parseDisplayDate()) {
                    event.preventDefault();
                    textInput.reportValidity();
                    textInput.focus();
                }
            });
        }

        // Show any date already supplied by Flask.
        showFormattedDate();
    });
});