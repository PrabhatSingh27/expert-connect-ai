import Foundation

enum UserRole: String, Codable, CaseIterable, Identifiable {
    case admin, operatorRole = "operator", customer, expert, technician
    var id: String { rawValue }
    var title: String { rawValue == "operator" ? "operator" : rawValue.capitalized }
}

struct AuthUser: Codable, Identifiable {
    let id: FlexibleID
    let name: String
    let email: String
    let role: UserRole
    let accountType: String?
    let isExpert: Bool?
    let isAdmin: Bool?
    let isVerified: Bool?
}

struct LoginResponse: Codable {
    let accessToken: String?
    let access_token: String?
    let token: String?
    let tokenType: String?
    let token_type: String?
    let role: UserRole?
    let accountType: String?
    let isExpert: Bool?
    let isAdmin: Bool?
    let name: String?
    let user: AuthUser?
    var resolvedToken: String? { accessToken ?? access_token ?? token }
}

struct RegisterPayload: Encodable {
    let name: String
    let email: String
    let password: String
    let role: String
}

struct LoginPayload: Encodable {
    let email: String
    let password: String
}

struct Issue: Codable, Identifiable {
    let id: FlexibleID
    let title: String
    let description: String
    let status: String
    let priority: String?
    let category: String?
    let problemType: String?
    let problem_type: String?
    let urgency: String?
    let requiredSkills: [String]?
    let required_skills: [String]?
    let confidenceScore: Double?
    let confidence_score: Double?
    let aiExplanation: String?
    let ai_explanation: String?
    let preferredVisitDate: String?
    let preferred_visit_date: String?
    let preferredTime: String?
    let preferred_time: String?
    let location: String?
    let address: String?
    let pinCode: String?
    let pin_code: String?
    let assignedExpertId: FlexibleID?
    let assigned_expert_id: FlexibleID?
    let createdAt: String?
    let created_at: String?

    var displayProblem: String { problemType ?? problem_type ?? category ?? "Pending AI" }
    var displayPin: String { pinCode ?? pin_code ?? "" }
}

struct CreateIssuePayload: Encodable {
    let title: String
    let description: String
    let category: String?
    let priority: String?
    let urgency: String?
    let requiredSkills: [String]?
    let preferredVisitDate: String?
    let preferredTime: String?
    let location: String
    let address: String
    let pinCode: String
}

struct Expert: Codable, Identifiable {
    let id: FlexibleID
    let fullName: String?
    let full_name: String?
    let email: String?
    let phone: String?
    let skills: String?
    let serviceArea: String?
    let service_area: String?
    let serviceCity: String?
    let service_city: String?
    let servicePincodes: String?
    let service_pincodes: String?
    let bio: String?
    let permanentAddress: String?
    let permanent_address: String?
    let experienceYears: Int?
    let experience_years: Int?
    let isVerified: Bool?
    let is_verified: Bool?
    let isActive: Bool?
    let is_active: Bool?

    var displayName: String { fullName ?? full_name ?? email ?? "Expert" }
    var displayArea: String { serviceArea ?? service_area ?? serviceCity ?? service_city ?? "Service area pending" }
    var verified: Bool { isVerified ?? is_verified ?? false }
}

struct AvailabilitySlot: Codable, Identifiable {
    let id: FlexibleID
    let expertId: FlexibleID?
    let expert_id: FlexibleID?
    let date: String
    let startTime: String?
    let start_time: String?
    let endTime: String?
    let end_time: String?
    let isAvailable: Bool?
    let is_available: Bool?

    var timeRange: String { "\(startTime ?? start_time ?? "--") - \(endTime ?? end_time ?? "--")" }
}

struct AdminUser: Codable, Identifiable {
    let id: FlexibleID
    let name: String?
    let email: String
    let role: String
    let status: String?
    let isActive: Bool?
    let is_active: Bool?
    var displayName: String { name ?? email }
    var active: Bool { isActive ?? is_active ?? status == "active" }
}

struct AdminOverview: Codable {
    let totalUsers: Int?
    let total_users: Int?
    let totalExperts: Int?
    let total_experts: Int?
    let totalVerifiedExperts: Int?
    let total_verified_experts: Int?
    let totalIssues: Int?
    let total_issues: Int?
    let issuesByStatus: [String: Int]?
    let issues_by_status: [String: Int]?
}

struct Review: Codable, Identifiable {
    let id: FlexibleID
    let issueId: FlexibleID?
    let issue_id: FlexibleID?
    let expertId: FlexibleID?
    let expert_id: FlexibleID?
    let rating: Int
    let review: String?
    let createdAt: String?
    let created_at: String?
}

struct APIMessage: Codable {
    let message: String?
    let detail: String?
}

struct EmptyBody: Encodable {}

struct FlexibleID: Codable, Hashable, Identifiable, ExpressibleByStringLiteral, CustomStringConvertible {
    let value: String
    var id: String { value }
    var description: String { value }
    init(_ value: String) { self.value = value }
    init(stringLiteral value: String) { self.value = value }
    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let int = try? container.decode(Int.self) { value = String(int); return }
        if let string = try? container.decode(String.self) { value = string; return }
        throw DecodingError.typeMismatch(String.self, .init(codingPath: decoder.codingPath, debugDescription: "Expected string or int ID"))
    }
    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        if let int = Int(value) { try container.encode(int) } else { try container.encode(value) }
    }
}
