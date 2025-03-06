// native share
if (!navigator.share) {
    document.getElementById('item-share-web-share-button').style.display = 'none';
}

// carousel
let mediaIndex = 1;

const nextMedia = (totalMediaCount) => {
    const currentMedia = document.getElementById(`media-${mediaIndex}`);
    const currentMediaOverlay = document.getElementById(`media-overlay-${mediaIndex}`);
    currentMedia.style.display = 'none';
    currentMediaOverlay.style.display = 'none';

    mediaIndex += 1;
    if (mediaIndex > totalMediaCount) {
        mediaIndex = 1;
    }

    const nextMedia = document.getElementById(`media-${mediaIndex}`);
    const nextMediaOverlay = document.getElementById(`media-overlay-${mediaIndex}`);
    nextMedia.style.display = 'block';
    nextMediaOverlay.style.display = 'block';
}
