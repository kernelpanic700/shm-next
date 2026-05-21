import { NextRequest, NextResponse } from 'next/server';

export async function middleware(request: NextRequest) {
  const accessToken = request.cookies.get('access_token')?.value;
  const refreshToken = request.cookies.get('refresh_token')?.value;
  
  const isAuthPage = request.nextUrl.pathname.startsWith('/login');
  const isProtectedPage = !isAuthPage && request.nextUrl.pathname !== '/';
  
  // Allow access to login page and static assets
  if (isAuthPage || request.nextUrl.pathname.startsWith('/_next')) {
    return NextResponse.next();
  }
  
  // Check if user has valid tokens
  if (!accessToken && !refreshToken) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('callbackUrl', request.url);
    return NextResponse.redirect(loginUrl);
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};