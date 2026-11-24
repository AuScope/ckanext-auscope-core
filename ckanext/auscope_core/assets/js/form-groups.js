ckan.module("auscope-core-form-groups", function () {
  return {
    initialize: function () {
      const root = this.el[0];
      const form = root.closest("form");
      const reveal = (control) => {
        const group = control.closest("details.auscope-core-form-group");
        if (group && root.contains(group)) group.open = true;
      };

      root.addEventListener("invalid", (event) => reveal(event.target), true);
      if (form) {
        form.addEventListener("click", (event) => {
          const link = event.target.closest('a[href^="#"]');
          if (!link) return;
          const target = document.getElementById(link.hash.slice(1));
          if (target) reveal(target);
        });
      }
    },
  };
});
