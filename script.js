// AniWise — homepage interactivity
// At this stage there's only one page, so the only real behavior
// we need is toggling the mobile menu open/closed.

const menuBtn = document.getElementById('mobile-menu-btn');
const mobileMenu = document.getElementById('mobile-menu');

menuBtn.addEventListener('click', function () {
    // toggle() adds the class if it's missing, removes it if it's there —
    // so one line handles both "open" and "close"
    mobileMenu.classList.toggle('mobile-menu-open');
});

function scrollToSection(sectionId) {
    const target = document.getElementById(sectionId);
    if (!target) return;

    const startY = window.scrollY;
    const targetY = target.getBoundingClientRect().top + startY;
    const distance = targetY - startY;
    const duration = 700; // milliseconds — adjust for faster/slower scroll
    let startTime = null;

    function easeInOutQuad(t) {
        return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    }

    function step(currentTime) {
        if (startTime === null) startTime = currentTime;
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        window.scrollTo(0, startY + distance * easeInOutQuad(progress));

        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }

    requestAnimationFrame(step);
    mobileMenu.classList.remove('mobile-menu-open');
}