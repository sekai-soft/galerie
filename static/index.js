// only show refresh on iOS PWA
const isStandalone = navigator.standalone || window.matchMedia("(display-mode: standalone)").matches;
if (!window.isIos || !isStandalone) {
    const refreshButton = document.getElementById('refresh-button');
    refreshButton.style.display = 'none';
}

// redirect on select changes
const updateQueryParameter = (key, value) => {
    var url = new URL(window.location.href);
    if (value) {
        url.searchParams.set(key, value);
    } else {
        url.searchParams.delete(key);
    }
    window.location.href = url.toString();
}

document.getElementById('group-select').addEventListener('change', (event) => {
    const groupId = event.target.value;
    if (groupId === '_all') {
        updateQueryParameter('group', null);
    } else {
        updateQueryParameter('group', groupId);
    }
});

document.getElementById('sort-select').addEventListener('change', (event) => {
    const sort = event.target.value;
    if (sort === 'desc') {
        updateQueryParameter('sort', null);
    } else if (sort === 'asc') {
        updateQueryParameter('sort', 'asc');
    }
})
