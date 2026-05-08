document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('existing-or-new-group-select').addEventListener('change', (event) => {
        const id = event.target.value;
        if (id === 'existing_group') {
            document.getElementById('existing-group-select').hidden = false
            document.getElementById('new-group-input').hidden = true
            return;
        }
        if (id === 'new_group') {
            document.getElementById('existing-group-select').hidden = true
            document.getElementById('new-group-input').hidden = false
            return;
        }
    });
});
