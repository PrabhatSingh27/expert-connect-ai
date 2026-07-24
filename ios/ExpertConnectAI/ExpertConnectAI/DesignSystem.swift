import SwiftUI

enum ECTheme {
    static let slate = Color(red: 15/255, green: 23/255, blue: 42/255)
    static let muted = Color(red: 100/255, green: 116/255, blue: 139/255)
    static let teal = Color(red: 20/255, green: 184/255, blue: 166/255)
    static let sky = Color(red: 56/255, green: 189/255, blue: 248/255)
    static let violet = Color(red: 167/255, green: 139/255, blue: 250/255)
    static let background = LinearGradient(colors: [Color(red: 240/255, green: 253/255, blue: 250/255), Color(red: 239/255, green: 246/255, blue: 255/255), Color.white], startPoint: .topLeading, endPoint: .bottomTrailing)
}

struct ScreenBackground<Content: View>: View {
    let content: Content
    init(@ViewBuilder content: () -> Content) { self.content = content() }
    var body: some View {
        ZStack {
            ECTheme.background.ignoresSafeArea()
            content
        }
    }
}

struct ECCard<Content: View>: View {
    let content: Content
    init(@ViewBuilder content: () -> Content) { self.content = content() }
    var body: some View {
        content
            .padding()
            .background(.white.opacity(0.82))
            .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 24).stroke(.white.opacity(0.7)))
            .shadow(color: .black.opacity(0.06), radius: 18, y: 8)
    }
}

struct GradientIcon: View {
    let systemName: String
    var body: some View {
        Image(systemName: systemName)
            .font(.title3.weight(.black))
            .foregroundStyle(ECTheme.slate)
            .frame(width: 48, height: 48)
            .background(LinearGradient(colors: [.teal.opacity(0.35), .cyan.opacity(0.32), .purple.opacity(0.28)], startPoint: .topLeading, endPoint: .bottomTrailing))
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
    }
}

struct PrimaryButton: View {
    let title: String
    var systemName: String?
    var loading = false
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            HStack {
                if loading { ProgressView().tint(.white) }
                if let systemName { Image(systemName: systemName) }
                Text(title).fontWeight(.black)
            }
            .frame(maxWidth: .infinity)
            .padding()
            .foregroundStyle(.white)
            .background(ECTheme.slate)
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        }
        .disabled(loading)
    }
}

struct StatTile: View {
    let title: String
    let value: String
    let icon: String
    var body: some View {
        ECCard {
            HStack {
                GradientIcon(systemName: icon)
                VStack(alignment: .leading, spacing: 4) {
                    Text(value).font(.title2.bold()).foregroundStyle(ECTheme.slate)
                    Text(title).font(.caption.weight(.bold)).foregroundStyle(ECTheme.muted)
                }
                Spacer()
            }
        }
    }
}

struct StatusPill: View {
    let text: String
    var body: some View {
        Text(text.replacingOccurrences(of: "_", with: " ").capitalized)
            .font(.caption.weight(.black))
            .padding(.horizontal, 10)
            .padding(.vertical, 7)
            .foregroundStyle(color)
            .background(color.opacity(0.12))
            .clipShape(Capsule())
    }
    private var color: Color {
        if ["closed", "resolved", "accepted", "active", "approved"].contains(text) { return .green }
        if ["rejected", "suspended"].contains(text) { return .red }
        if ["high", "critical"].contains(text) { return .orange }
        return .blue
    }
}

struct EmptyState: View {
    let title: String
    let text: String
    var body: some View {
        ECCard {
            VStack(spacing: 8) {
                Image(systemName: "tray").font(.largeTitle).foregroundStyle(ECTheme.teal)
                Text(title).font(.headline.bold())
                Text(text).font(.subheadline).foregroundStyle(ECTheme.muted).multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical)
        }
    }
}

extension View {
    func ecField() -> some View {
        padding()
            .background(.white.opacity(0.78))
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.black.opacity(0.08)))
    }
}
