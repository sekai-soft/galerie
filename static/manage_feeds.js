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
