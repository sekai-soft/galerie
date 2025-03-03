// masonry grid setup
const grid = new Masonry('.grid', {
  itemSelector: '.grid-item',
  columnWidth: '.grid-sizer',
  percentPosition: true,
  gutter: 32
});

grid.layout();

imagesLoaded(grid).on('progress', () => {
  grid.layout();
});

document.body.addEventListener("append", (event) => {
  const uids = event.detail.value;
  const elements = uids.map(uid => document.getElementById(uid));
  grid.appended(elements)
});
