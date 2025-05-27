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

document.getElementById('sort-button').addEventListener('click', (event) => {
    const sort = event.target.textContent;
    if (sort === '⬆️') {
        updateQueryParameter('sort', null);
    } else if (sort === '⬇️') {
        updateQueryParameter('sort', 'asc');
    }
})

document.getElementById('read-select').addEventListener('change', (event) => {
    const read = event.target.value;
    if (read === '0') {
        updateQueryParameter('read', null);
    } else if (read === '1') {
        updateQueryParameter('read', '1');
    }
})
