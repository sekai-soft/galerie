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

document.body.addEventListener("update_read_percentage", (event) => {
    const percentage = event.detail.value;
    document.getElementById('read-percentage').innerText = percentage + '%';
});

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('group-select').addEventListener('change', (event) => {
        const id = event.target.value;
        if (id === '_all') {
            updateQueryParameter('group', null);
            return;
        }
        if (id.startsWith('group-')) {
            const groupId = id.split('group-')[1];
            updateQueryParameter('group', groupId);
            return;
        }
        if (id.startsWith('feed-')) {
            const feedId = id.split('feed-')[1];
            window.location.href = '/feed?fid=' + feedId;
            return;
        }
    });

    document.getElementById('sort-select').addEventListener('change', (event) => {
        const sort = event.target.value;
        if (sort === '0') {
            updateQueryParameter('sort', null);
        } else if (sort === '1') {
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
})
