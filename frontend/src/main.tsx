import React from "react";
import ReactDOM from "react-dom/client";
import { BaseProvider, DarkTheme, type Theme } from "baseui";
import { ToasterContainer } from "baseui/toast";
import { BrowserRouter } from "react-router-dom";
import { Client as Styletron } from "styletron-engine-atomic";
import { Provider as StyletronProvider } from "styletron-react";
import App from "./App";
import "./styles.css";

const engine = new Styletron();

const appTheme: Theme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    backgroundPrimary: "#070d17",
    backgroundSecondary: "#101a2a",
    backgroundTertiary: "#162238",
    backgroundInversePrimary: "#f2f6ff",
    contentPrimary: "#e8f0ff",
    contentSecondary: "#a4b4d2",
    contentTertiary: "#8193b3",
    borderOpaque: "#243452",
    borderTransparent: "#1c2941",
    accent: "#3f7cff",
    accent50: "#132f67",
    accent100: "#1a3a77",
    accent200: "#20438a",
    accent300: "#2955ae",
    accent400: "#3468d0",
    accent500: "#3f7cff",
    accent600: "#79a0ff",
    accent700: "#aac4ff"
  }
};

function AppWithToast() {
  return (
    <>
      <App />
      <ToasterContainer autoHideDuration={2400} />
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <StyletronProvider value={engine}>
      <BaseProvider theme={appTheme}>
        <BrowserRouter>
          <AppWithToast />
        </BrowserRouter>
      </BaseProvider>
    </StyletronProvider>
  </React.StrictMode>
);
