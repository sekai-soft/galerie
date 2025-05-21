window.isIos = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

// Add animate css classes to elements
window.animateCss = () => {
    const animateLongClasses = ['.button', '.link-button']

    for (const selector of animateLongClasses) {
        document.querySelectorAll(selector).forEach(element => {
            if (!element.classList.contains('animate-long')) {
                element.classList.add('animate-long');
            }
        });
    }

    if (window.isIos) {
        document.querySelectorAll('.animate-long').forEach(element => {
            if (!element.hasAttribute('data-touch-listeners-added')) {
                element.addEventListener('touchstart', () => {
                    element.classList.add('pressed');
                }, {passive: true});

                element.addEventListener('touchend', () => {
                    element.classList.remove('pressed');
                }, {passive: true});

                element.addEventListener('touchcancel', () => {
                    element.classList.remove('pressed');
                }, {passive: true});
                
                element.setAttribute('data-touch-listeners-added', 'true');
            }
        });
    }
}