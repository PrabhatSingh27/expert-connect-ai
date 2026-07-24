import SwiftUI

@main
struct ExpertConnectAIApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appState)
                .task { await appState.restoreSession() }
        }
    }
}

struct RootView: View {
    @EnvironmentObject private var appState: AppState
    var body: some View {
        if appState.isSignedIn {
            MainDashboardView()
        } else {
            AuthLandingView()
        }
    }
}
