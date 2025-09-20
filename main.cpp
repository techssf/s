#include "include/cef_app.h"
#include "include/cef_client.h"
#include "include/cef_browser.h"

class SimpleHandler : public CefClient, public CefDisplayHandler {
public:
    SimpleHandler() {}
    CefRefPtr<CefDisplayHandler> GetDisplayHandler() override { return this; }

    void OnTitleChange(CefRefPtr<CefBrowser> browser,
                       const CefString& title) override {
        // Injetar JS quando a página carregar
        browser->GetMainFrame()->ExecuteJavaScript(
            "alert('Script injetado no CEF!');",
            browser->GetMainFrame()->GetURL(), 0);
    }

    IMPLEMENT_REFCOUNTING(SimpleHandler);
};

int main(int argc, char* argv[]) {
    CefMainArgs main_args(argc, argv);
    CefRefPtr<CefApp> app;

    int exit_code = CefExecuteProcess(main_args, app, nullptr);
    if (exit_code >= 0)
        return exit_code;

    CefSettings settings;
    settings.no_sandbox = true;
    CefInitialize(main_args, settings, app, nullptr);

    CefBrowserSettings browser_settings;
    CefWindowInfo window_info;

    // Novo jeito no CEF 140: usar bounds (cef_rect_t)
    window_info.bounds.Set(100, 100, 800, 600);
    CefString(&window_info.window_name).FromASCII("CEF Example");

    CefRefPtr<SimpleHandler> handler(new SimpleHandler());
    CefBrowserHost::CreateBrowser(window_info, handler.get(),
                                  "https://example.com",
                                  browser_settings, nullptr, nullptr);

    CefRunMessageLoop();
    CefShutdown();
    return 0;
}
