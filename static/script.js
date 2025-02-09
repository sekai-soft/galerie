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
  PullToRefresh.init({
    onRefresh() {
      location.reload();
    },
  });
}

Cookies.set('tz', Intl.DateTimeFormat().resolvedOptions().timeZone)

const grid = $('.grid').masonry({
  itemSelector: '.grid-item',
  columnWidth: '.grid-sizer',
  percentPosition: true,
  gutter: 32
});

grid.imagesLoaded().progress(() => {
  grid.masonry('layout');
});

$(document).on('htmx:afterSettle', (event) => {
  if (event.detail.target.id == 'grid') {
    grid.masonry('reloadItems')
    grid.imagesLoaded().progress(() => {
      grid.masonry('layout');
    });
  }
});

const updateQueryParameter = (key, value) => {
  var url = new URL(window.location.href);
  if (value) {
    url.searchParams.set(key, value);
  } else {
    url.searchParams.delete(key);
  }
  window.location.href = url.toString();
}

$('#timeSelect').on('change', (event) => {
  const time = event.target.value;
  if (time === 'all') {
    updateQueryParameter('today', null);
  } else if (time === 'today') {
    updateQueryParameter('today', 1);
  }
})

const onGroupSelectChange = (event) => {
  const groupId = event.target.value;
  if (groupId === '_all') {
    updateQueryParameter('group', null);
  } else {
    updateQueryParameter('group', groupId);
  }
}

$('#groupSelect').on('change', onGroupSelectChange);
$('#mobileGroupSelect').on('change', onGroupSelectChange);

$('#sortSelect').on('change', (event) => {
  const sort = event.target.value;
  if (sort === 'desc') {
    updateQueryParameter('sort', null);
  } else if (sort === 'asc') {
    updateQueryParameter('sort', 'asc');
  }
})

document.body.addEventListener("toast", (event) => {
  const message = event.detail.value;
  
  const toastEl = $('#toast')
  toastEl.addClass('show');
  toastEl.text(message);

  setTimeout(() => {
    toastEl.removeClass('show');
  }, 2500);
})
