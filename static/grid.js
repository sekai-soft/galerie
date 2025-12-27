// Return the existing Masonry instance for a grid, or create it if missing.
const masonryByGridId = {};
const getOrCreateMasonry = (gridEl) => {
    if (!gridEl) {
        return undefined;
    }
    if (masonryByGridId[gridEl.id]) {
        return masonryByGridId[gridEl.id];
    }
    const masonry = new Masonry(gridEl, {
        itemSelector: '.grid-item',
        columnWidth: '.grid-sizer',
        percentPosition: true,
        gutter: 32
    });
    masonryByGridId[gridEl.id] = masonry;
    imagesLoaded(gridEl).on('progress', () => {
        masonry.layout();
    });
    return masonry;
};

// Ensure any currently-rendered grids have Masonry instances.
const ensureMasonryForExistingGrids = () => {
    document.querySelectorAll('.grid').forEach((gridEl) => {
        getOrCreateMasonry(gridEl);
    });
};

// Initial page load grids need Masonry.
ensureMasonryForExistingGrids();

document.body.addEventListener('htmx:afterSwap', () => {
    // HTMX can insert new grids (e.g., load_more OOB adds a new segment block).
    ensureMasonryForExistingGrids();
});

document.body.addEventListener("append", (event) => {
    // load_more triggers an "append" event with the UIDs of newly-rendered items.
    const uids = event.detail.value;
    const elements = uids.map(uid => document.getElementById(uid)).filter(Boolean);

    // Items can belong to different segment grids, so group them by their grid.
    const byGrid = new Map();
    elements.forEach((element) => {
        const gridEl = element.closest('.grid');
        if (!gridEl) {
            return;
        }
        if (!byGrid.has(gridEl)) {
            byGrid.set(gridEl, []);
        }
        byGrid.get(gridEl).push(element);
    });
    byGrid.forEach((gridElements, gridEl) => {
        const masonry = getOrCreateMasonry(gridEl);

        // Tell Masonry about the new elements for this grid.
        masonry.appended(gridElements);

        // Re-layout as the new images load to avoid layout gaps.
        imagesLoaded(gridElements).on('progress', () => {
            masonry.reloadItems();
            masonry.layout();
        });
    });

    // Run the existing animation hook after items are appended.
    window.animateCss();
});
