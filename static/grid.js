// Masonry instance for the main grid.
let masonry = null;

const initMasonry = () => {
    const gridEl = document.getElementById('grid');
    if (!gridEl || masonry) {
        return;
    }
    masonry = new Masonry(gridEl, {
        itemSelector: '.grid-item',
        columnWidth: '.grid-sizer',
        percentPosition: true,
        gutter: 32
    });
    imagesLoaded(gridEl).on('progress', () => {
        masonry.layout();
    });
};

// Initialize on page load.
initMasonry();

document.body.addEventListener("mark_as_read", (event) => {
    // Gray out items that were marked as read via scroll_as_read.
    const iids = event.detail.value;
    iids.forEach(iid => {
        document.querySelectorAll(`.grid-item[data-iid="${iid}"]`).forEach(el => {
            el.classList.add('read');
        });
    });
});

document.body.addEventListener("append", (event) => {
    // load_more triggers an "append" event with the UIDs of newly-rendered items.
    const uids = event.detail.value;
    const elements = uids.map(uid => document.getElementById(uid)).filter(Boolean);

    if (!masonry || elements.length === 0) {
        return;
    }

    // Tell Masonry about the new elements.
    masonry.appended(elements);

    // Re-layout as the new images load to avoid layout gaps.
    imagesLoaded(elements).on('progress', () => {
        masonry.reloadItems();
        masonry.layout();
    });

    // Run the existing animation hook after items are appended.
    window.animateCss();
});
