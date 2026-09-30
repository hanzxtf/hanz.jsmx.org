// Import Vite modulepreload polyfill [django-vite docs]
import "vite/modulepreload-polyfill";

// import CSS styles
import "../css/styles.css";

// Import GSAP
import { gsap } from "gsap";

// Import htmx: boosted navigation and AJAX form submissions
import "htmx.org";

// Merge the <head> (title, meta, og tags) on boosted navigation
import "htmx.org/dist/ext/hx-head.js";

// Import Stimulus
import { Application } from "@hotwired/stimulus";

// Development-only behaviour lives in dev.js and is dropped from the build
if (import.meta.env.DEV) {
  import("./dev.js");
}

// start Stimulus application
const app = Application.start();

// Auto-register Stimulus controllers
const modules = import.meta.glob("./controllers/**/*.js", { eager: true });

Object.entries(modules).forEach(([filename, module]) => {
  // Convert the filename to a controller name
  const controllerName = filename
    // Remove the leading "./controllers/"
    .replace(/^\.\//, "")
    .replace(/^controllers\//, "")
    // Remove the ".js" extension
    .replace(/\.js$/, "")
    // Replace underscores with dashes
    .replace(/_/g, "-")
    // Replace slashes with double dashes
    .replace(/\//g, "--");

  // Register the controller with the Stimulus application
  app.register(controllerName, module.default);
});

// Expose Stimulus application globally
window.Stimulus = app;
