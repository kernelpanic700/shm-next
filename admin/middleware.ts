// Middleware disabled for client-side auth
// The AuthGuard component handles authentication on the client side
export default function middleware() {
  return;
}

export const config = {
  matcher: [],
};