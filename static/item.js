window.U_INDEX = parseInt(window.U_INDEX);
window.TOTAL_MEDIA_COUNT = parseInt(window.TOTAL_MEDIA_COUNT);

const toast = (message) => {
    document.body.dispatchEvent(new CustomEvent('toast', {
        detail: {
            value: message,
        }
    }));
}

// web share
if (!navigator.share) {
    document.getElementById('item-web-share-button').style.display = 'none';
}

// copy to clipboard
document.getElementById('item-copy-link-button').addEventListener('click', () => {
    navigator.clipboard.writeText(window.SHAREABLE_URL).then(() => {
        toast('Copied to clipboard');
    }).catch(() => {
        toast('Failed to copy to clipboard');
    });
})

// carousel
const flkty = new Flickity('.carousel', {
    percentagePosition: false,
    initialIndex: window.U_INDEX,
    prevNextButtons: window.TOTAL_MEDIA_COUNT > 1,
    pageDots: window.TOTAL_MEDIA_COUNT > 1,
    accessibility: false,
});

// Keyboard navigation with arrow keys (global, without needing focus)
document.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') {
        event.preventDefault();
        flkty.previous();
    } else if (event.key === 'ArrowRight') {
        event.preventDefault();
        flkty.next();
    }
});

document.querySelectorAll('.carousel img').forEach(img => {
    img.addEventListener('load', () => flkty.resize());
    img.addEventListener('error', () => flkty.resize());
});
document.querySelectorAll('.carousel video').forEach(video => {
    video.addEventListener('loadedmetadata', () => flkty.resize());
    video.addEventListener('canplay', () => flkty.resize());
});
flkty.on('change', (index) => {
    for (let i = 1; i <= window.TOTAL_MEDIA_COUNT; i++) {
        const mediaDownload = document.getElementById(`media-download-${i}`);
        if (index + 1 === i) {
            mediaDownload.style.display = 'block';
        } else {
            mediaDownload.style.display = 'none';
        }
    }
});
