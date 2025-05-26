// set timezone
Cookies.set('tz', Intl.DateTimeFormat().resolvedOptions().timeZone)

// remove glossy glass style for selects on macOS Safari
const isMacSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent) && /Mac/i.test(navigator.platform);
if (isMacSafari) {
  const style = document.createElement('style');
  style.innerHTML = `
    select {
      -webkit-appearance: none;
    }
  `;
  document.head.appendChild(style);

  document.querySelectorAll('select').forEach(select => {
    const updateArrow = () => {
      select.querySelectorAll('option').forEach(option => {
        option.textContent = option.textContent.replace(' ▼', '');
      });
      const selectedOption = select.options[select.selectedIndex];
      selectedOption.textContent += ' ▼';
    };

    updateArrow();
    select.addEventListener('change', updateArrow);
  });
}

// toast listener
document.body.addEventListener("toast", (event) => {
  const message = event.detail.value;
  
  const toastEl = document.getElementById('toast');
  toastEl.classList.add('show');
  toastEl.textContent = message;

  setTimeout(() => {
    toastEl.classList.remove('show');
  }, 2500);
})

// only show back button if there is history
const canGoBack = window.history.length > 1 && document.referrer !== '';
if (!canGoBack) {
  const backButton = document.getElementById('back-button');
  if (backButton) {
    backButton.style.display = 'none';
  }
}

document.addEventListener('DOMContentLoaded', window.animateCss);

// back listener
document.body.addEventListener("back", () => {
  window.history.back();
})