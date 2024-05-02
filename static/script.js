Cookies.set('tz', Intl.DateTimeFormat().resolvedOptions().timeZone)

const grid = $('.grid').masonry({
  itemSelector: '.grid-item',
  columnWidth: '.grid-sizer',
  percentPosition: true,
  gutter: 4
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

$('#groupSelect').on('change', (event) => {
  const groupId = event.target.value;
  if (groupId === '_all') {
    updateQueryParameter('group', null);
  } else {
    updateQueryParameter('group', groupId);
  }
})

$('#sortSelect').on('change', (event) => {
  const sort = event.target.value;
  if (sort === 'desc') {
    updateQueryParameter('sort', null);
  } else if (sort === 'asc') {
    updateQueryParameter('sort', 'asc');
  }
})

window.toast = (message) => {
  const toastEl = $('#toast')
  toastEl.addClass('show');
  toastEl.text(message);

  setTimeout(() => {
    toastEl.removeClass('show');
  }, 500);
}
