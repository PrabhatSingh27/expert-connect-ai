import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case noData
    case backend(String)
    case network(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL: "Invalid backend URL."
        case .noData: "Backend returned no data."
        case .backend(let message): message
        case .network(let message): message
        }
    }
}

final class APIClient {
    static let shared = APIClient()
    var baseURL = UserDefaults.standard.string(forKey: "apiBaseURL") ?? "http://172.17.38.216:8000"
    var token: String? {
        get { UserDefaults.standard.string(forKey: "accessToken") }
        set { UserDefaults.standard.set(newValue, forKey: "accessToken") }
    }

    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .useDefaultKeys
        return decoder
    }()

    func saveBaseURL(_ value: String) {
        baseURL = value.trimmingCharacters(in: .whitespacesAndNewlines)
        UserDefaults.standard.set(baseURL, forKey: "apiBaseURL")
    }

    func request<T: Decodable, B: Encodable>(_ path: String, method: String = "GET", body: B? = Optional<EmptyBody>.none, auth: Bool = true) async throws -> T {
        guard let url = URL(string: baseURL + path) else { throw APIError.invalidURL }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if auth, let token { request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        if let body { request.httpBody = try JSONEncoder().encode(body) }
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            try validate(data: data, response: response)
            guard !data.isEmpty else { throw APIError.noData }
            return try decoder.decode(T.self, from: data)
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.network(error.localizedDescription)
        }
    }

    func requestNoBody<T: Decodable>(_ path: String, method: String = "GET", auth: Bool = true) async throws -> T {
        let empty: EmptyBody? = nil
        return try await request(path, method: method, body: empty, auth: auth)
    }

    func multipart<T: Decodable>(_ path: String, fields: [String: String], files: [MultipartFile] = [], method: String = "POST", auth: Bool = true) async throws -> T {
        guard let url = URL(string: baseURL + path) else { throw APIError.invalidURL }
        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        if auth, let token { request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        request.httpBody = makeMultipartBody(fields: fields, files: files, boundary: boundary)
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(data: data, response: response)
        return try decoder.decode(T.self, from: data)
    }

    private func validate(data: Data, response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else { return }
        guard (200..<300).contains(http.statusCode) else {
            let message = (try? decoder.decode(APIMessage.self, from: data)).flatMap { $0.detail ?? $0.message }
            throw APIError.backend(message ?? "Request failed with \(http.statusCode).")
        }
    }

    private func makeMultipartBody(fields: [String: String], files: [MultipartFile], boundary: String) -> Data {
        var data = Data()
        for (key, value) in fields where !value.isEmpty {
            data.append("--\(boundary)\r\n")
            data.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n")
            data.append("\(value)\r\n")
        }
        for file in files {
            data.append("--\(boundary)\r\n")
            data.append("Content-Disposition: form-data; name=\"\(file.fieldName)\"; filename=\"\(file.fileName)\"\r\n")
            data.append("Content-Type: \(file.mimeType)\r\n\r\n")
            data.append(file.data)
            data.append("\r\n")
        }
        data.append("--\(boundary)--\r\n")
        return data
    }
}

struct MultipartFile {
    let fieldName: String
    let fileName: String
    let mimeType: String
    let data: Data
}

private extension Data {
    mutating func append(_ string: String) {
        append(string.data(using: .utf8)!)
    }
}
