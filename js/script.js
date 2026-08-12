// AniWise — Homepage Interactivity

function scrollToSection(sectionId) {
    const target = document.getElementById(sectionId);

    if (!target) return;

    const startY = window.scrollY;
    const targetY = target.getBoundingClientRect().top + startY;
    const distance = targetY - startY;

    const duration = 700;
    let startTime = null;

    function easeInOutQuad(t) {
        return t < 0.5
            ? 2 * t * t
            : 1 - Math.pow(-2 * t + 2, 2) / 2;
    }

    function step(currentTime) {
        if (startTime === null) {
            startTime = currentTime;
        }

        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        window.scrollTo(
            0,
            startY + distance * easeInOutQuad(progress)
        );

        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }

    requestAnimationFrame(step);
}