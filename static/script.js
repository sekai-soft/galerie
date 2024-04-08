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
