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

const isIos = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
const isStandalone = navigator.standalone || window.matchMedia("(display-mode: standalone)").matches;
if (isIos && isStandalone) {
  for (const el of document.getElementsByClassName('refresh')) {
    el.style.display = 'block';
  }
}

Cookies.set('tz', Intl.DateTimeFormat().resolvedOptions().timeZone)

const grid = new Masonry('.grid', {
  itemSelector: '.grid-item',
  columnWidth: '.grid-sizer',
  percentPosition: true,
  gutter: 32
});

imagesLoaded(grid).on('progress', () => {
  grid.layout();
});

document.body.addEventListener("append", (event) => {
  const uids = event.detail.value;
  const elements = uids.map(uid => document.getElementById(uid));
  grid.appended(elements)
})

const updateQueryParameter = (key, value) => {
  var url = new URL(window.location.href);
  if (value) {
    url.searchParams.set(key, value);
  } else {
    url.searchParams.delete(key);
  }
  window.location.href = url.toString();
}

document.getElementById('groupSelect').addEventListener('change', (event) => {
  const groupId = event.target.value;
  if (groupId === '_all') {
    updateQueryParameter('group', null);
  } else {
    updateQueryParameter('group', groupId);
  }
});

document.getElementById('sortSelect').addEventListener('change', (event) => {
  const sort = event.target.value;
  if (sort === 'desc') {
    updateQueryParameter('sort', null);
  } else if (sort === 'asc') {
    updateQueryParameter('sort', 'asc');
  }
})

document.body.addEventListener("toast", (event) => {
  const message = event.detail.value;
  
  const toastEl = document.getElementById('toast');
  toastEl.classList.add('show');
  toastEl.textContent = message;

  setTimeout(() => {
    toastEl.removeClass('show');
  }, 2500);
})
