import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Analytics } from "@lib/analytics";
import { registerServiceWorker } from "@lib/service-worker";
import App from "@components/App";
import "@styles/index.css";
import "@styles/tokens.css";

const root = document.getElementById("root");
if (!root) throw new Error("Root element not found");

const app = createRoot(root);

app.render(
  <StrictMode>
    <App />
  </StrictMode>
);

Analytics.init();
registerServiceWorker();