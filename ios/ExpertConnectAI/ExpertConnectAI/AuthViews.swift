import SwiftUI

struct AuthLandingView: View {
    @EnvironmentObject private var appState: AppState
    @State private var mode: AuthMode = .login
    @State private var name = ""
    @State private var email = ""
    @State private var password = ""
    @State private var role: UserRole = .customer
    @State private var expertMode = false

    var body: some View {
        ScreenBackground {
            ScrollView {
                VStack(spacing: 18) {
                    VStack(spacing: 12) {
                        GradientIcon(systemName: "sparkles")
                        Text("ExpertConnect AI")
                            .font(.largeTitle.bold())
                            .foregroundStyle(ECTheme.slate)
                        Text("Native iOS app for customer issues, expert jobs, availability, admin review and AI-assisted assignment.")
                            .font(.subheadline)
                            .foregroundStyle(ECTheme.muted)
                            .multilineTextAlignment(.center)
                    }
                    .padding(.top, 30)

                    ECCard {
                        VStack(spacing: 14) {
                            Picker("Mode", selection: $mode) {
                                Text("Login").tag(AuthMode.login)
                                Text("Signup").tag(AuthMode.signup)
                            }
                            .pickerStyle(.segmented)

                            TextField("Backend URL", text: $appState.apiBaseURL)
                                .textInputAutocapitalization(.never)
                                .keyboardType(.URL)
                                .ecField()
                                .onSubmit { appState.saveBaseURL() }

                            if mode == .signup {
                                TextField("Full name", text: $name).ecField()
                                Picker("Role", selection: $role) {
                                    ForEach([UserRole.customer, .operatorRole, .admin], id: \.self) { Text($0.title).tag($0) }
                                }
                                .pickerStyle(.segmented)
                            } else {
                                Toggle("Expert login", isOn: $expertMode)
                                    .font(.subheadline.weight(.bold))
                            }

                            TextField("Email", text: $email)
                                .textInputAutocapitalization(.never)
                                .keyboardType(.emailAddress)
                                .ecField()
                            SecureField("Password", text: $password).ecField()

                            if !appState.errorMessage.isEmpty {
                                Text(appState.errorMessage)
                                    .font(.footnote.weight(.bold))
                                    .foregroundStyle(.red)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }

                            PrimaryButton(title: mode == .login ? "Login" : "Create account", systemName: "arrow.right", loading: appState.isLoading) {
                                appState.saveBaseURL()
                                Task {
                                    if mode == .login {
                                        await appState.login(email: email, password: password, expertMode: expertMode)
                                    } else {
                                        await appState.register(name: name, email: email, password: password, role: role)
                                    }
                                }
                            }
                        }
                    }

                    NavigationLink {
                        ExpertSignupView()
                    } label: {
                        Text("Become an Expert")
                            .fontWeight(.black)
                            .foregroundStyle(ECTheme.teal)
                    }
                }
                .padding()
            }
        }
    }
}

enum AuthMode { case login, signup }

struct ExpertSignupView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var appState: AppState
    @State private var fullName = ""
    @State private var email = ""
    @State private var password = ""
    @State private var phone = ""
    @State private var governmentId = ""
    @State private var serviceCity = ""
    @State private var pinCode = ""
    @State private var address = ""
    @State private var bio = ""
    @State private var experience = "0"
    @State private var message = ""

    var body: some View {
        ScreenBackground {
            ScrollView {
                VStack(spacing: 16) {
                    HStack {
                        GradientIcon(systemName: "checkmark.seal")
                        VStack(alignment: .leading) {
                            Text("Expert Application").font(.title.bold())
                            Text("Uses POST /experts/signup").foregroundStyle(ECTheme.muted)
                        }
                        Spacer()
                    }
                    ECCard {
                        VStack(spacing: 12) {
                            Group {
                                TextField("Full name", text: $fullName)
                                TextField("Email", text: $email).keyboardType(.emailAddress).textInputAutocapitalization(.never)
                                SecureField("Password", text: $password)
                                TextField("Phone", text: $phone).keyboardType(.phonePad)
                                TextField("Government ID", text: $governmentId)
                                TextField("Service city", text: $serviceCity)
                                TextField("PIN code", text: $pinCode).keyboardType(.numberPad)
                                TextField("Experience years", text: $experience).keyboardType(.numberPad)
                            }
                            .ecField()
                            TextField("Permanent address", text: $address, axis: .vertical).lineLimit(3).ecField()
                            TextField("Bio", text: $bio, axis: .vertical).lineLimit(4).ecField()
                            if !message.isEmpty { Text(message).font(.footnote.bold()).foregroundStyle(message.contains("submitted") ? .green : .red) }
                            PrimaryButton(title: "Submit Expert Application", systemName: "paperplane", loading: appState.isLoading) {
                                Task { await submit() }
                            }
                        }
                    }
                }
                .padding()
            }
        }
        .navigationBarTitleDisplayMode(.inline)
    }

    private func submit() async {
        await appState.run {
            let fields = [
                "full_name": fullName, "email": email, "password": password, "phone": phone,
                "government_id": governmentId, "skills": "General repair, Home service",
                "service_area": "\(serviceCity) - \(pinCode)", "service_city": serviceCity,
                "service_pincodes": pinCode, "bio": bio, "permanent_address": address,
                "experience_years": experience
            ]
            let _: Expert = try await APIClient.shared.multipart("/experts/signup", fields: fields, auth: false)
            message = "Expert application submitted."
        }
    }
}
