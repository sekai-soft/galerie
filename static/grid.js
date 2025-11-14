// masonry grid setup - initialize all grid elements
const gridElements = document.querySelectorAll('.grid');
const grids = [];

gridElements.forEach(gridElement => {
    const grid = new Masonry(gridElement, {
        itemSelector: '.grid-item',
        columnWidth: '.grid-sizer',
        percentPosition: true,
        gutter: 32
    });
    grids.push(grid);

    imagesLoaded(grid).on('progress', () => {
        grid.layout();
    });
});

document.body.addEventListener("append", (event) => {
    const uids = event.detail.value;
    const elements = uids.map(uid => document.getElementById(uid));

    // Find which grid the new elements belong to and append to that grid
    elements.forEach(element => {
        if (element) {
            const parentGrid = element.closest('.grid');
            const gridIndex = Array.from(gridElements).indexOf(parentGrid);
            if (gridIndex !== -1) {
                grids[gridIndex].appended([element]);
            }
        }
    });

    window.animateCss();
});
