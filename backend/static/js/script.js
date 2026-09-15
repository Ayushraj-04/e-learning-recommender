document.addEventListener("DOMContentLoaded", () => {
    const tabs = document.querySelectorAll(".tab-btn");
    const contents = document.querySelectorAll(".tab-content");
    const durationFilter = document.getElementById("durationFilter");

    tabs.forEach((button) => {
        button.addEventListener("click", () => {
            const target = button.dataset.tab;

            tabs.forEach((tab) => tab.classList.remove("active"));
            contents.forEach((content) => content.classList.remove("active"));

            button.classList.add("active");
            document.getElementById(target)?.classList.add("active");
        });
    });

    durationFilter?.addEventListener("change", () => {
        const selected = durationFilter.value;

        document.querySelectorAll(".result-card").forEach((card) => {
            card.hidden = selected !== "all" && card.dataset.duration !== selected;
        });
    });
});
