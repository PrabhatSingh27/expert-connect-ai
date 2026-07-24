const BACKEND_API_URL =
  process.env.BACKEND_API_URL ||
  process.env.NEXT_PUBLIC_BACKEND_API_URL ||
  "http://172.17.38.216:8000";

type RouteContext = {
  params: Promise<Record<string, never>>;
};

async function proxyToBackend(request: Request, context: RouteContext) {
  await context.params;
  const sourceUrl = new URL(request.url);
  const targetPath = sourceUrl.pathname.replace(/^\/api\/?/, "/");
  const targetUrl = new URL(targetPath, BACKEND_API_URL);
  targetUrl.search = sourceUrl.search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("connection");
  headers.delete("content-length");

  const init: RequestInit = {
    method: request.method,
    headers,
    cache: "no-store",
  };

  if (!["GET", "HEAD"].includes(request.method)) {
    init.body = await request.arrayBuffer();
  }

  try {
    const response = await fetch(targetUrl, init);
    const responseHeaders = new Headers(response.headers);
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("content-length");

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      { detail: `Backend is not reachable at ${BACKEND_API_URL}` },
      { status: 502 }
    );
  }
}

export function GET(request: Request, context: RouteContext) {
  return proxyToBackend(request, context);
}

export function POST(request: Request, context: RouteContext) {
  return proxyToBackend(request, context);
}

export function PUT(request: Request, context: RouteContext) {
  return proxyToBackend(request, context);
}

export function PATCH(request: Request, context: RouteContext) {
  return proxyToBackend(request, context);
}

export function DELETE(request: Request, context: RouteContext) {
  return proxyToBackend(request, context);
}
