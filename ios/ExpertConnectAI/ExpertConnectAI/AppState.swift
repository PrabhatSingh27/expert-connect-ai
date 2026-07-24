import Foundation
import SwiftUI

@MainActor
final class AppState: ObservableObject {
    @Published var user: AuthUser?
    @Published var isLoading = false
    @Published var errorMessage = ""
    @Published var apiBaseURL = APIClient.shared.baseURL

    var isSignedIn: Bool { APIClient.shared.token != nil }
    var role: UserRole { user?.role ?? UserRole(rawValue: UserDefaults.standard.string(forKey: "role") ?? "") ?? .customer }

    func saveBaseURL() {
        APIClient.shared.saveBaseURL(apiBaseURL)
    }

    func restoreSession() async {
        guard APIClient.shared.token != nil else { return }
        do { user = try await APIClient.shared.requestNoBody("/auth/me") }
        catch { signOut() }
    }

    func login(email: String, password: String, expertMode: Bool = false) async {
        await run {
            let response: LoginResponse = try await APIClient.shared.request(expertMode ? "/experts/login" : "/auth/login", method: "POST", body: LoginPayload(email: email, password: password), auth: false)
            guard let token = response.resolvedToken else { throw APIError.backend("Login token missing.") }
            APIClient.shared.token = token
            let role = response.user?.role ?? response.role ?? (expertMode ? .expert : .customer)
            UserDefaults.standard.set(role.rawValue, forKey: "role")
            user = response.user ?? AuthUser(id: "me", name: response.name ?? email, email: email, role: role, accountType: response.accountType, isExpert: response.isExpert, isAdmin: response.isAdmin, isVerified: nil)
        }
    }

    func register(name: String, email: String, password: String, role: UserRole) async {
        await run {
            let _: AuthUser = try await APIClient.shared.request("/auth/register", method: "POST", body: RegisterPayload(name: name, email: email, password: password, role: role.rawValue), auth: false)
            await login(email: email, password: password, expertMode: false)
        }
    }

    func signOut() {
        APIClient.shared.token = nil
        UserDefaults.standard.removeObject(forKey: "role")
        user = nil
    }

    func run(_ work: () async throws -> Void) async {
        isLoading = true
        errorMessage = ""
        do { try await work() }
        catch { errorMessage = error.localizedDescription }
        isLoading = false
    }
}
