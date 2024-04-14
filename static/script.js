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

$('#timeSelect').on('change', (event) => {
  const time = event.target.value;
  if (time === 'all') {
    window.location.href = '/';
  } else if (time === 'today') {
    window.location.href = `/?today=1`;
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
